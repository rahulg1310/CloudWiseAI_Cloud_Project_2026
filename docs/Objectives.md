# Objectives

1. **Unified FinOps platform.** Build a web platform (React, FastAPI, PostgreSQL) that stores resource-level daily billing data and serves it through authenticated REST APIs. *Criterion:* all dashboard views load from the API using the 15,950-row dataset.
2. **Cost forecasting.** Forecast the next three months of spend. *Criterion:* mean monthly MAPE at or below 5% for every horizon in a rolling-origin backtest, and better than a seasonal-naive baseline.
3. **Anomaly detection.** Detect abnormal spend with fewer false alarms than a rolling 3-sigma rule. *Criterion:* day-level precision and recall of at least 0.90 against the labelled injected events.
4. **Recommendations.** Produce at least five actionable, ranked recommendations with estimated monthly savings and written assumptions.
5. **AWS deployment.** Design the AWS deployment (S3 and CloudFront, API Gateway, EC2, RDS, IAM, CloudWatch/SNS) and prepare the scripts and guide. *Status:* designed and scripted; live deployment pending.
6. **Secure, assisted use.** Password hashing, token authentication, restricted network access, and an assistant that answers only from the user's data and is rate limited.

See the project report for the success criteria, evidence and test results.
