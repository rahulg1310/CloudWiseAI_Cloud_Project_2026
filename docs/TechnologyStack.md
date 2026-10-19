# Technology Stack

## Frontend
- React (Vite), React Router, Context API
- Tailwind CSS
- Axios, lucide-react icons
- Hand-built SVG charts (no chart library)

## Backend
- FastAPI (Python), REST API
- PostgreSQL with psycopg2
- bcrypt password hashing, JWT (HS256) authentication

## AI / Machine Learning
- Pandas, NumPy, Scikit-learn (ridge regression), XGBoost
- Weekday-aware robust z-score for anomaly detection
- Optional assistant through Ollama (local), Anthropic or OpenAI

## AWS (designed; live deployment pending)
- S3 and CloudFront (frontend), API Gateway (HTTPS entry), EC2 (FastAPI and analysis scripts)
- RDS PostgreSQL, IAM, CloudWatch and SNS

## Future work
- AWS Lambda (CUR ingestion), Amazon SageMaker (training), Amazon QuickSight
