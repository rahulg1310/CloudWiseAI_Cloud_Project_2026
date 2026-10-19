# Novelty

CloudWiseAI does not invent a new forecasting algorithm. Its contribution is an integrated, evaluated and deployable FinOps workflow for MSMEs.

| Dimension | Existing approach / limitation | CloudWiseAI |
|---|---|---|
| New feature | Forecasting, anomaly detection and optimisation are studied separately, mostly on simulators or price lists. | One platform combining forecast, spend-anomaly detection and ranked recommendations on resource-level billing data, plus a data-grounded assistant. |
| Algorithm | Rolling 3-sigma rules flag every weekday dip and spike; deep models need heavy tuning. | Weekday-aware robust z-score (median and MAD of the same weekday over eight weeks); ridge forecaster chosen by rolling-origin backtest against seasonal-naive and ridge-XGBoost. Precision 1.00 vs 0.24; MAPE 0.45% vs 2.47%. |
| Cloud architecture | Enterprise FinOps suites or heavyweight pipelines. | Small, low-operations AWS stack designed around CloudFront and S3, API Gateway, one EC2 instance, private RDS and a re-runnable one-script setup (live deployment pending). |
| Security | Rarely evaluated in the reviewed work. | bcrypt and JWT, restricted CORS, private database, IAM role with Session Manager instead of SSH keys, CloudWatch and SNS alerts (designed). |

All accuracy figures come from a synthetic dataset and should not be read as field performance.
