# AWS Deployment

Step-by-step guide: [DEPLOYMENT.md](DEPLOYMENT.md). Backend installer for the server: [ec2_setup.sh](ec2_setup.sh).

## Deployed

| Service | Role in CloudWiseAI |
|---|---|
| Amazon S3 + CloudFront | host the React frontend over HTTPS |
| API Gateway (HTTP API) | public HTTPS entry point, forwards `/api/*` to the backend |
| Amazon EC2 | runs the FastAPI backend and the ML analysis scripts |
| Amazon RDS (PostgreSQL) | stores cost records, users and analysis results; reachable only from EC2 |
| CloudWatch + SNS | alarms on EC2 CPU and API errors, delivered by email |
| IAM | EC2 role for Session Manager (no SSH key); admin user created, MFA not enabled |

## Future work (not built)

- AWS Lambda ETL that parses uploaded AWS Cost and Usage Report files from S3 into the database
- Amazon SageMaker for training and hosting the forecasting model (it currently runs on EC2)
- Amazon QuickSight dashboards
- Cognito instead of the in-app JWT login, and a VPC Link so EC2 is not publicly reachable
