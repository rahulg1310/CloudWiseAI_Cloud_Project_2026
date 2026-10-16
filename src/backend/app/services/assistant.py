"""
AI assistant: answers questions about the user's AWS costs.

How it works (no fine-tuning, no vector database):
  1. The router reads the current cost, anomaly, recommendation, utilization and forecast data.
  2. format_context() turns that into a compact text snapshot.
  3. The snapshot goes into the system prompt together with the user's question and recent chat history.
  4. ask_llm() sends it to the configured provider and returns the reply text.

The model only ever sees aggregated numbers and resource IDs from this app's own tables.
Pure functions plus one HTTP call: no database access here.
"""

import logging
import re

import httpx

from app import config

log = logging.getLogger("cloudwise.assistant")

MAX_HISTORY_MESSAGES = 10
MAX_MESSAGE_CHARS = 2000
MAX_HISTORY_CHARS = 12000   # about 3,000 tokens; keeps snapshot + history inside a small local model's context

SYSTEM_PROMPT = """You are CloudWise Assistant, an AWS cost (FinOps) analyst inside the CloudWiseAI dashboard.

How to answer:
- Use only the data snapshot below. Quote figures exactly as given and say which period or resource they refer to.
- If the snapshot does not contain what is needed (a specific day's cause, a service that is not listed, anything after the latest date), say so plainly and suggest where to look in AWS, for example Cost Explorer or CloudTrail. Never guess numbers and never invent causes.
- Anomaly notes describe what happened (spend versus baseline), not why. You may suggest likely causes, but label them as hypotheses.
- Savings figures are estimates built on stated assumptions. Present them as estimates, not guarantees.
- Forecast "accuracy" is accuracy measured on past data, not a guarantee about the future.
- You can only read data. You cannot change anything in AWS, so describe what the user would do themselves.
- Be concise: lead with the answer, then a few short sentences or hyphen bullets.
- Write plain text only. Do not use markdown: no asterisks for bold, no # headings, no tables, no backticks.
- Stay on cloud cost topics and politely decline unrelated requests."""


class LLMError(Exception):
    """The provider could not be reached or returned something unusable.

    `user_hint` is an optional message that is safe to show in the UI (never contains keys).
    It is used for local-setup problems the developer can fix, like Ollama not running.
    """

    def __init__(self, message, user_hint=None):
        super().__init__(message)
        self.user_hint = user_hint


# ---------------------------------------------------------------- context

def _usd(value):
    return f"${float(value):,.2f}"


def format_context(data):
    """Turn the gathered cost data (a dict, see routers/assistant.py) into prompt text."""
    if not data:
        return "DATA SNAPSHOT\nNo cost data has been loaded yet, so you cannot answer questions about spending."

    s = data["summary"]
    lines = [
        "DATA SNAPSHOT",
        f"Latest data: {data['as_of']}. \"Current month\" means {data['period']}.",
        f"- Current month spend: {_usd(s['totalCost'])} ({s['monthOverMonthChange']:+.1f}% vs previous month)",
        f"- Next month forecast: {_usd(s['forecastedCost'])}",
        f"- Open recommendations: {len(data['recommendations'])}, estimated savings {_usd(s['potentialSavings'])} per month",
        f"- Anomaly events in the last 90 days: {s['anomalyCount']}",
        "",
        "Spend by service, current month:",
    ]
    lines += [f"- {b['service']}: {_usd(b['cost'])} ({b['percent']}%)" for b in data["breakdown"]]

    lines += ["", "Monthly spend by service, most recent 3 months:"]
    for period, services in data["monthly_by_service"].items():
        lines.append(f"- {period}: " + ", ".join(f"{name} {_usd(cost)}" for name, cost in services))

    lines += ["", "Total spend per day, last 14 days:",
              ", ".join(f"{t['date'][5:]} {_usd(t['cost'])}" for t in data["trend"])]

    lines += ["", "Most expensive resources, last 30 days:"]
    lines += [f"- {r['resource_id']} ({r['service']}, {r['region']}): {_usd(r['cost'])}" for r in data["top_resources"]]

    lines += ["", "Detected anomalies, newest first (expected/actual are per-day averages during the event):"]
    if data["anomalies"]:
        for a in data["anomalies"]:
            lines.append(f"- {a['date']} | {a['service']} | severity {a['severity']} | expected {_usd(a['expectedCost'])}/day, "
                         f"actual {_usd(a['actualCost'])}/day (+{a['deviation']:.0f}%) | {a['note']}")
    else:
        lines.append("- none")

    lines += ["", "Recommendations (estimated savings per month; assumptions are in each description):"]
    if data["recommendations"]:
        for i, r in enumerate(data["recommendations"], start=1):
            lines.append(f"{i}. {r['title']} [{r['service']}, {r['category']}, {r['effort']} effort] - "
                         f"{_usd(r['potentialSavings'])}/month - {r['description']}")
    else:
        lines.append("- none")

    problems = [u for u in data["utilization"] if u["status"] != "Healthy"]
    healthy = len(data["utilization"]) - len(problems)
    lines += ["", f"Resource utilization, last 30 days ({healthy} healthy resources not listed):"]
    for u in problems:
        if u["status"] == "Unattached":
            usage = "no instance attached"
        else:
            usage = f"average CPU {u['utilization']}%"
        lines.append(f"- {u['resource']} ({u['type']}): {u['status']}, {usage}, cost {_usd(u['cost'])}")
    if not problems:
        lines.append("- none")

    p = data["predictions"]
    lines += ["", "Forecast" + (f" (model: {p['model']})" if p.get("model") else "") + ":"]
    if p["forecast"]:
        lines += [f"- {f['month']}: {_usd(f['cost'])} (backtest accuracy {f['confidence']:.0%})" for f in p["forecast"]]
    else:
        lines.append("- not generated yet")

    return "\n".join(lines)


# ---------------------------------------------------------------- history

def build_messages(history, message):
    """Clean client-supplied history and append the new question.

    The client is not trusted: only user/assistant roles, capped length, capped count,
    and the conversation must start with a user message (a provider requirement).
    """
    cleaned = []
    for item in history[-MAX_HISTORY_MESSAGES:]:
        role = item.get("role")
        text = str(item.get("text", "")).strip()[:MAX_MESSAGE_CHARS]
        if role in ("user", "assistant") and text:
            cleaned.append({"role": role, "content": text})

    while len(cleaned) > 1 and sum(len(m["content"]) for m in cleaned) > MAX_HISTORY_CHARS:
        cleaned.pop(0)

    while cleaned and cleaned[0]["role"] != "user":
        cleaned.pop(0)

    cleaned.append({"role": "user", "content": message.strip()[:MAX_MESSAGE_CHARS]})
    return cleaned


# ---------------------------------------------------------------- provider calls

def ask_llm(system, messages):
    """Send the conversation to the configured provider and return the reply text."""
    provider = config.LLM_PROVIDER
    try:
        if provider == "anthropic":
            response = httpx.post(
                f"{config.LLM_BASE_URL}/v1/messages",
                headers={"x-api-key": config.LLM_API_KEY, "anthropic-version": "2023-06-01"},
                json={"model": config.LLM_MODEL, "max_tokens": config.LLM_MAX_TOKENS,
                      "system": system, "messages": messages},
                timeout=config.LLM_TIMEOUT_SECONDS,
            )
        elif provider == "openai":
            response = httpx.post(
                f"{config.LLM_BASE_URL}/v1/chat/completions",
                headers={"Authorization": f"Bearer {config.LLM_API_KEY}"},
                json={"model": config.LLM_MODEL, "max_tokens": config.LLM_MAX_TOKENS,
                      "messages": [{"role": "system", "content": system}] + messages},
                timeout=config.LLM_TIMEOUT_SECONDS,
            )
        elif provider == "ollama":
            response = httpx.post(
                f"{config.LLM_BASE_URL}/api/chat",
                json={"model": config.LLM_MODEL, "stream": False,
                      "messages": [{"role": "system", "content": system}] + messages,
                      "options": {"num_ctx": config.OLLAMA_NUM_CTX, "num_predict": config.LLM_MAX_TOKENS}},
                timeout=config.LLM_TIMEOUT_SECONDS,
            )
        else:
            raise LLMError(f"Unknown LLM_PROVIDER '{provider}' (use 'anthropic', 'openai' or 'ollama')")
    except httpx.ConnectError as error:
        if provider == "ollama":
            raise LLMError(f"cannot reach Ollama at {config.LLM_BASE_URL}", user_hint=(
                "I can't reach Ollama. Start it with 'ollama serve' (or open the Ollama app) "
                "and check that LLM_BASE_URL in the backend .env is correct.")) from error
        raise LLMError(f"request failed: {error.__class__.__name__}") from error
    except httpx.TimeoutException as error:
        hint = ("Ollama took too long to answer. The first question after startup loads the model and can be slow, "
                "so try again. If it keeps happening, use a smaller model or raise LLM_TIMEOUT_SECONDS.") if provider == "ollama" else None
        raise LLMError(f"request timed out after {config.LLM_TIMEOUT_SECONDS}s", user_hint=hint) from error
    except httpx.HTTPError as error:
        raise LLMError(f"request failed: {error.__class__.__name__}") from error

    if response.status_code != 200:
        if provider == "ollama" and response.status_code == 404:
            raise LLMError(f"ollama 404: {response.text[:300]}", user_hint=(
                f"Ollama doesn't have the model '{config.LLM_MODEL}'. Download it with: ollama pull {config.LLM_MODEL}"))
        # the body explains auth / model-name / quota problems; it never contains our key
        raise LLMError(f"{provider} returned {response.status_code}: {response.text[:300]}")

    try:
        body = response.json()
        if provider == "anthropic":
            reply = "".join(block.get("text", "") for block in body["content"] if block.get("type") == "text")
        elif provider == "ollama":
            reply = body["message"]["content"] or ""
            # reasoning models (qwen3, deepseek-r1) can put their thinking inline in the reply
            reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.DOTALL)
        else:
            reply = body["choices"][0]["message"]["content"] or ""
    except (ValueError, KeyError, IndexError, TypeError) as error:
        raise LLMError("unexpected response format") from error

    reply = reply.strip()
    if not reply:
        raise LLMError("empty reply")
    return reply
