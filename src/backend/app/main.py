from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import database
from app.config import CORS_ORIGINS
from app.routers import anomalies, auth, costs, predictions, recommendations, utilization


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_pool()
    yield
    database.close_pool()


app = FastAPI(title="CloudWiseAI API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Frontend's VITE_API_URL is http://localhost:8000/api
app.include_router(auth.router, prefix="/api")
app.include_router(costs.router, prefix="/api")
app.include_router(utilization.router, prefix="/api")
app.include_router(anomalies.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")
app.include_router(predictions.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
