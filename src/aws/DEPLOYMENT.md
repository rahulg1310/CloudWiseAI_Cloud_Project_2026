# Deploying CloudWiseAI on AWS

This guide deploys the project with the services in the architecture diagram:

```
Browser ──HTTPS──> CloudFront ──> S3                      (React frontend, static files)
   │
   └──HTTPS──> API Gateway (HTTP API) ──HTTP──> EC2         (FastAPI backend, port 8000)
                                                  │
                                                  └──> RDS PostgreSQL (private, only EC2 can reach it)

CloudWatch alarms ──> SNS ──> email          IAM: admin user, EC2 role (Session Manager)
```

Region used everywhere: **Asia Pacific (Mumbai) `ap-south-1`**. Check the region name in the top right
of the console before every step. Resources in a different region will not find each other.

Not deployed (listed as future work in the report): Lambda ETL for CUR files, SageMaker training,
QuickSight. The ML runs on the EC2 instance through `scripts/run_analysis.py`.

> If a step says a service or instance type is not available on your plan, you are on the AWS Free plan.
> Upgrade to the Paid plan in **Billing and Cost Management** and carry on. New accounts keep their credits.

---

## Part 0 - Secure the account (10 minutes)

1. Sign in as the root user, open **IAM > Dashboard** and add **MFA** for the root user.
2. **IAM > Users > Create user** `cloudwise-admin`, tick *Provide user access to the AWS Management Console*,
   attach the policy `AdministratorAccess`, and sign in with this user from now on.
3. **Billing and Cost Management > Budgets > Create budget** with a monthly cost budget of about $5 and your email
   as the alert recipient.

Screenshot for the report: IAM users page.

## Part 1 - Security groups

**EC2 > Security Groups > Create security group** (use the default VPC):

| Name | Inbound rules |
|---|---|
| `cloudwise-api-sg` | Custom TCP, port `8000`, source `0.0.0.0/0` |
| `cloudwise-db-sg` | PostgreSQL, port `5432`, source = the security group `cloudwise-api-sg` |

No SSH port is opened. You will connect through Session Manager (Part 4).
Port 8000 is open to the internet because API Gateway has no fixed IP range. The report should mention that a
production setup would use a VPC Link and a private subnet instead.

## Part 2 - RDS PostgreSQL

**RDS > Create database**

- Creation method: **Standard create**, engine **PostgreSQL** (latest 16.x or 17.x offered)
- Template: **Free tier** if it is offered, otherwise **Dev/Test**
- DB instance identifier: `cloudwise-db`
- Master username `postgres`, **self managed** password. Write the password down.
- Instance class: smallest burstable one (`db.t4g.micro` or `db.t3.micro`), storage 20 GiB gp3, no autoscaling
- Multi-AZ: **No**
- Connectivity: default VPC, **Public access: No**, security group `cloudwise-db-sg` (remove `default`)
- Additional configuration: **Initial database name** `cloudwise`, backup retention 1 day,
  turn off Performance Insights and Enhanced Monitoring

It takes about 10 minutes. When the status is *Available*, open the database and copy the **Endpoint**
(`cloudwise-db.xxxxxxxx.ap-south-1.rds.amazonaws.com`).

Screenshot: RDS database summary (hide the password).

## Part 3 - IAM role for the server

**IAM > Roles > Create role** > AWS service > **EC2** > attach `AmazonSSMManagedInstanceCore` > name `cloudwise-ec2-role`.
This lets you open a shell on the server from the browser, with no SSH key.

## Part 4 - EC2 server

**EC2 > Launch instance**

- Name `cloudwise-api`
- AMI: **Amazon Linux 2023**
- Instance type: `t3.micro` (or whichever small type is marked free tier eligible). The setup script adds swap, so 1 GB is enough.
- Key pair: **Proceed without a key pair**
- Network settings: default VPC, **Auto-assign public IP: Enable**, select existing security group `cloudwise-api-sg`
- Storage: 12 GiB gp3
- Advanced details > **IAM instance profile**: `cloudwise-ec2-role`

When it is *running*, tick the instance, click **Connect > Session Manager > Connect**.
(If the Connect button for Session Manager is greyed out, wait 3 minutes and refresh.)

In the shell that opens, run (replace the host and the CORS value later, see Part 7):

```bash
sudo -i
curl -fsSL https://raw.githubusercontent.com/rahulg1310/CloudWiseAI_Cloud_Project_2026/main/src/aws/ec2_setup.sh -o ec2_setup.sh
DB_HOST=cloudwise-db.xxxxxxxx.ap-south-1.rds.amazonaws.com bash ec2_setup.sh
```

It asks for the database password, then takes about 5 to 10 minutes: packages, Python libraries, loading
15,950 cost records, running anomaly detection, recommendations and the forecast. At the end you should see
`Done. The API is running.` and a line with the **API Gateway integration URL**. Copy it.

Check: `curl http://127.0.0.1:8000/api/health` prints `{"status":"ok"}`.

If it fails, the last lines say why. Common causes:

| Message | Cause |
|---|---|
| `connection timed out` to the RDS host | `cloudwise-db-sg` does not allow `cloudwise-api-sg`, or the two are in different VPCs |
| `password authentication failed` | wrong password; run again with `DB_PASSWORD=...` or retype it |
| `No space left on device` | storage too small, resize the volume in EC2 > Volumes |
| `$'\r': command not found` | the script was saved with Windows line endings; run `sed -i 's/\r$//' ec2_setup.sh` |

Screenshot: EC2 instance details page.

## Part 5 - API Gateway

**API Gateway > Create API > HTTP API > Build**

1. Integrations: **Add integration > HTTP**, method `ANY`, URL endpoint
   `http://<EC2 public DNS>:8000/api/{proxy}` (the setup script printed it)
2. API name `cloudwise-api`
3. Routes: method `ANY`, resource path `/api/{proxy+}` pointing at that integration
4. Stage: `$default` with auto-deploy
5. **Do not** configure CORS on API Gateway. FastAPI already answers CORS requests.

Copy the **Invoke URL** (`https://abc123.execute-api.ap-south-1.amazonaws.com`).
Check in a browser: `<Invoke URL>/api/health` shows `{"status":"ok"}`.

The frontend's API address is the Invoke URL plus `/api`.

Screenshot: API Gateway routes page.

## Part 6 - Frontend on S3 and CloudFront

On your laptop, in `src/frontend`, create a file named `.env.production` with one line
(your own Invoke URL, ending in `/api`):

```
VITE_API_URL=https://abc123.execute-api.ap-south-1.amazonaws.com/api
```

```bash
npm ci
npm run build
```

The `dist` folder is the website.

1. **S3 > Create bucket**: any unique name (e.g. `cloudwise-frontend-yourname`), region `ap-south-1`,
   keep **Block all public access** on.
2. Open the bucket > **Upload** > drag in everything *inside* `dist` (`index.html`, `assets`, `favicon.svg`).
3. **CloudFront > Create distribution**: origin = that S3 bucket, choose the option that allows **private access
   through CloudFront (Origin Access Control)** and let the console update the bucket policy.
   Default root object: `index.html`. Turn off the Web Application Firewall if it asks (extra cost).
4. When the distribution is created, open it > **Error pages** > create custom error responses for
   `403` and `404`: response page path `/index.html`, HTTP response code `200`.
   (Without this, reloading `/dashboard` shows an error because React Router handles the route, not S3.)
5. Wait until the status shows a date instead of *Deploying* (5 to 10 minutes). Copy the
   **Distribution domain name** (`dxxxxxxxx.cloudfront.net`).

If CloudFront is not available on your plan, enable *Static website hosting* on the bucket instead and make it public.
That version only serves HTTP, which still works because browsers allow an http page to call an https API.

Screenshots: S3 bucket contents and CloudFront distribution page.

## Part 7 - Let the frontend call the API (CORS)

Back in the Session Manager shell on EC2:

```bash
sudo -i
CORS_ORIGINS=https://dxxxxxxxx.cloudfront.net,http://localhost:5173 SKIP_DATA=1 bash ec2_setup.sh
```

Everything else (database password, JWT secret) is remembered. Open `https://dxxxxxxxx.cloudfront.net`,
create an account, and check every page loads.

**Test checklist** (take a screenshot of each for the report):

- [ ] Landing page, sign up, sign in
- [ ] Dashboard with real numbers (not the mock-data fallback)
- [ ] Cost analysis, utilization, anomalies, recommendations, predictions
- [ ] Reload `/dashboard` directly (should not 404)
- [ ] AI assistant says it is not set up. That is expected, the deployed version has no LLM key. Demo the assistant locally with Ollama.

## Part 8 - Monitoring and alerts (CloudWatch + SNS)

Open **CloudShell** (the `>_` icon in the console's top bar). It already has AWS credentials.
Replace the values in capitals.

```bash
REGION=ap-south-1
TOPIC=$(aws sns create-topic --name cloudwise-alerts --region $REGION --query TopicArn --output text)
aws sns subscribe --topic-arn $TOPIC --protocol email --notification-endpoint YOUR@EMAIL --region $REGION
# open the confirmation email from AWS and click "Confirm subscription"

aws cloudwatch put-metric-alarm --region $REGION --alarm-name cloudwise-ec2-cpu-high \
  --namespace AWS/EC2 --metric-name CPUUtilization --dimensions Name=InstanceId,Value=INSTANCE_ID \
  --statistic Average --period 300 --evaluation-periods 2 --threshold 70 \
  --comparison-operator GreaterThanThreshold --alarm-actions $TOPIC

aws cloudwatch put-metric-alarm --region $REGION --alarm-name cloudwise-api-5xx \
  --namespace AWS/ApiGateway --metric-name 5xx --dimensions Name=ApiId,Value=API_ID \
  --statistic Sum --period 300 --evaluation-periods 1 --threshold 5 \
  --comparison-operator GreaterThanOrEqualToThreshold --treat-missing-data notBreaching --alarm-actions $TOPIC
```

`INSTANCE_ID` is on the EC2 page (`i-...`), `API_ID` is the short id in the API Gateway Invoke URL (`abc123`).
Test that email alerts reach you:
`aws sns publish --topic-arn $TOPIC --message "CloudWiseAI test alert" --region $REGION`

Screenshots: CloudWatch alarms list, the confirmation or alert email, the EC2 CPU graph.

## Part 9 - Updating later

Code change on GitHub, then on EC2: `sudo -i; SKIP_DATA=1 bash ec2_setup.sh` (downloads the latest code and restarts).
Frontend change: rebuild, upload `dist` again, then **CloudFront > Invalidations > Create** with path `/*`.

## Part 10 - Delete everything when you are done

Credits are spent while resources exist, even if nobody uses the site. After the viva and the final screenshots,
delete in this order:

1. CloudFront distribution (disable it first, then delete)
2. S3 bucket (empty it, then delete)
3. API Gateway API
4. EC2 instance (terminate)
5. RDS database (untick *Create final snapshot*)
6. Security groups, IAM role `cloudwise-ec2-role`, SNS topic, CloudWatch alarms
7. Check **Billing and Cost Management > Bills** the next day

## Troubleshooting

| Symptom | Check |
|---|---|
| Frontend shows mock data | browser dev tools > Network: is the request going to the API Gateway URL? Wrong `VITE_API_URL` means rebuild and re-upload. |
| Network tab shows a CORS error | `CORS_ORIGINS` on EC2 must contain the exact CloudFront URL with `https://` and no trailing slash (Part 7). |
| `{"message":"Not Found"}` from API Gateway | route must be `ANY /api/{proxy+}` and the integration URL must end in `/api/{proxy}`. |
| `{"message":"Service Unavailable"}` or timeout | EC2 is stopped, the API crashed (`sudo journalctl -u cloudwise -n 50`), or port 8000 is not open in `cloudwise-api-sg`. |
| EC2 public DNS changed | it changes after a stop and start. Update the API Gateway integration URL, or allocate an Elastic IP. |
