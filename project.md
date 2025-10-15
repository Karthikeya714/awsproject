Prompt to give Cursor — Build a production-ready Image → Caption Generator (Streamlit + AWS) — deliverable: deployable repo + infra + docs

Use this exact prompt when creating a task for Cursor. It is intentionally exhaustive: architecture, implementation details, infra as code, CI/CD, security, monitoring, tests, deployment and acceptance criteria. Do not ask follow-ups — deliver the complete production-ready system with the items listed below.

Project summary (short)

Build a production-ready Image-to-Caption Generator web app using Streamlit as the frontend and AWS for storage, ML inference, authentication, hosting, and monitoring. The app must allow authenticated users to upload images, generate high-quality captions (creative & concise), store images & captions, and serve at scale behind HTTPS. The repo must include code, infra-as-code, CI/CD, automated tests, documentation, and an ops runbook.

Priority & deadline

Priority: production-ready
Target delivery: "within 1 business day" — the deliverable must be shipped as a working production deployment that meets the acceptance criteria below.

Tech stack (must use)

Frontend: Streamlit (Python) — single-page app, responsive, accessible.

Backend inference options (one or more; implement as chosen and provide alternatives):

Amazon Bedrock (preferred if available): call for generative captioning.

Amazon SageMaker endpoint (Hugging Face model like BLIP or ViT-GPT2) — provide containerized model and deployment.

Lambda + model-hosting on SageMaker or invoking external Hugging Face Inference API as fallback.

Storage: Amazon S3 (images + thumbnails)

Metadata DB: Amazon DynamoDB (captions, user history, timestamps) or RDS (Postgres) if relational features needed (choose one and justify).

Authentication: Amazon Cognito (user pool + hosted UI) with optional social sign-ins.

Infrastructure as Code: Terraform (preferred) or CloudFormation (ok if chosen, but Terraform is preferred). All infra should be reusable and parameterized.

Containerization: Docker — build a production image for Streamlit app.

CI/CD: GitHub Actions pipeline to build, test, image push to ECR, deploy via Terraform and/or ECS/Fargate (or Cloud Run equivalent), run smoke tests.

Observability: CloudWatch logs & metrics, X-Ray optional, and error reporting (Sentry or CloudWatch Alarms).

Secrets: AWS Secrets Manager or Parameter Store (SSM) — no secrets in repo.

Optional: use AWS WAF + CloudFront for CDN and security.

Functional requirements (explicit)

Upload: Authenticated users upload images (JPEG/PNG, up to 10 MB) via Streamlit UI.

Storage: Uploaded image saved to S3 (private). Create and store a 300px thumbnail in S3.

Captioning pipeline:

Preprocess image (resize/normalize).

First step (optional): call Rekognition to extract labels/entities to augment prompt.

Main step: call Bedrock or SageMaker endpoint to generate a caption. Provide a fallback: call Hugging Face Inference API if Bedrock/SageMaker are unavailable.

Return 2 variants: concise (<= 10 words) and creative (1–2 sentences).

Storage of results: Save caption(s) and metadata (user_id, s3_url, thumbnail_url, labels, model, confidences, timestamp) in DynamoDB (or RDS).

History: Authenticated user can view their past uploads and captions (paginated).

Presigned URL: Serve images to frontend with short-lived presigned URLs.

Rate limiting & abuse prevention: Implement per-user rate limit (e.g., 60 requests/hour) via API Gateway usage plans or a simple token-bucket in the backend.

Admin interface: small admin page (protected by IAM or admin role) to view usage metrics & flush queue.

Internationalization: produce captions in English only for v1. (Note: prepare points in README for i18n extension.)

Logging & monitoring: capture request traces, errors, and usage metrics. Provide CloudWatch dashboards and at least two alarms (high error rate, high latency).

Privacy & compliance: images stored encrypted at rest (S3 SSE). No storing of PII; if a user requests deletion, provide a mechanism to remove their images + DB records.

Non-functional requirements

HTTPS only, valid TLS cert (ACM + CloudFront or ALB).

Scalability: use serverless where possible (Lambda + API Gateway / Fargate for Streamlit if necessary). App must handle bursts (scale to N concurrent requests — choose reasonable defaults and document them).

Security: least-privilege IAM roles, runtime secrets in Secrets Manager, input validation on uploads (MIME + content sniffing), S3 bucket policies to block public access.

Performance: average caption latency < 2s for Rekognition+Bedrock path if Bedrock is used; otherwise document expected latencies and tradeoffs.

Cost-conscious defaults: use smaller instance sizes by default and document scaling/cost tradeoffs.

Observability & alerting: included as infra + basic dashboard.

Test coverage: unit tests for Python backend logic (>=70% coverage goal); integration tests for the API endpoints and S3/Dynamo flows using local mocks (moto) or test AWS account resources.

Deliverables (must be included in the repo / deliverable)

GitHub repo with:

README.md — project overview, architecture diagram (SVG/PNG), setup, env vars, runbook.

LICENSE (MIT or user preference).

CONTRIBUTING.md, PR_TEMPLATE.md, CODE_OF_CONDUCT.md.

Source code:

app/streamlit_app.py (main Streamlit app).

backend/ modules (captioning, s3, auth, db, models).

requirements.txt or pyproject.toml.

Dockerfile (production-ready).

Infrastructure:

infra/terraform/ with modules for: VPC (if needed), S3, DynamoDB/RDS, Cognito, IAM roles, ECR, ECS/Fargate or Lambda + API Gateway, CloudFront/ALB, CloudWatch dashboards & alarms.

infra/terraform/variables.tf with clear defaults and a README_infra.md.

CI/CD:

.github/workflows/ci.yml — lint, unit tests, build docker, run integration tests (mocked), push to ECR.

.github/workflows/cd.yml — terraform plan/apply (using GitHub Actions OIDC) to deploy to target AWS account (instructions for secrets & permissions).

Infra deployment scripts:

scripts/deploy.sh, scripts/destroy.sh (optional wrapper).

Tests:

Unit and integration tests (pytest).

tests/e2e_smoke.py that runs a full upload → caption → DB check (can use a test AWS account or localstack; if real AWS needed, document required env vars).

Docs:

README.md with quickstart (local + prod), environment variables, AWS permissions and policy snippets, cost estimate ranges, and troubleshooting.

RUNBOOK.md with steps to rotate credentials, scale, and rollback.

Postman collection or cURL examples for API endpoints.

Health checks & readiness probe for the Streamlit container.

Architecture diagram (topology + dataflow) in docs/architecture.png or .svg.

Changelog with implementation notes and any tradeoffs.

Optional: Terraform outputs include CloudFront URL / Load Balancer DNS, Cognito test user, and an operation script to create the first admin user.

Acceptance criteria (must pass)

Repo builds and runs locally with docker-compose up (Streamlit + a mocked backend or localstack).

terraform apply (with provided variables) deploys infra and returns an accessible HTTPS URL for the app.

Uploading a test image produces 2 captions (concise + creative) visible in UI and stored in DB.

Images are stored encrypted in S3 and served via presigned URLs.

Cognito authentication works: signup, login, view history.

CI pipeline runs: tests pass, Docker image builds, Terraform plan runs.

Monitoring: CloudWatch dashboard exists and alarms are documented & created by Terraform.

Security: IAM policies provided are least-privilege and reviewed.

All secrets are stored in Secrets Manager (no plaintext secrets in repo).

Provide a short video (or GIF) walkthrough of the app being used (optional but highly preferred).

Implementation specifics & code expectations
Streamlit app

Clean UI: upload zone, preview, caption variants, history, account area.

Use async/threads to avoid blocking UI during remote inference.

Proper error-handling & user-friendly messages (e.g., “Image too large”, “Service unavailable — try again later”).

Component organization: pages/, components/ (reusable UI items).

Captioning code

Abstract captioning provider as an interface with implementations: BedrockProvider, SageMakerProvider, HFProvider. The app chooses provider based on environment variable or failover chain.

Prompt engineering: include Rekognition labels (optional) in the prompt. Provide sample prompt templates in code and README.

Rate-limit or queue long-running jobs; return progress to user.

IAM & least privilege

Provide example IAM JSON policies for:

S3 read/write limited to the specific bucket prefix.

Rekognition access (if used) limited to DetectLabels and specific resources.

SageMaker invoke or Bedrock access limited to specific models.

DynamoDB limited to the table.

Secrets Manager read for the app role.

Security & compliance

S3: BlockPublicAccess, SSE (SSE-S3 or SSE-KMS). If using KMS, provide KMS key creation in Terraform.

Use Cognito user pool for auth and restrict S3 access via signed URLs (not public S3 GET).

Enforce input file validation and strip EXIF metadata before storing (or provide opt-in).

Provide data deletion API /delete_user_data that removes S3 objects and DB entries for a user.

CI/CD & deployment

Use OIDC GitHub Actions workflow with a minimal IAM role for Terraform apply (document required permissions).

Build and push Docker image to ECR; deploy to ECS/Fargate or ECR image used by Lambda container; alternatively use Elastic Beanstalk if simpler.

Provide manual rollback steps and automated terraform state storage (S3 backend + state locking via DynamoDB).

Testing & QA

Unit-tests for caption logic, S3 upload/download, DB writes.

Integration tests using moto or localstack, with a flag to run against real AWS resources if env vars present.

Load test script (simple wrk or locust job) to demonstrate handling N concurrent requests; include results summary.

Operational & handover items

RUNBOOK.md with:

How to rotate secrets.

How to scale (ECS task count, SageMaker endpoint instance types).

How to delete user data (privacy compliance).

Troubleshooting common errors (permission denied, model timeout).

Cost estimation section in README (expected monthly cost bands: low / medium / high usage).

Maintenance plan: how to update the model (retraining/fine-tuning) and redeploy endpoint.

Final delivery must include a short summary message: what was implemented, any deviations and why, and next recommended improvements.

Example environment variables (placeholders)

Provide a .env.example file with:

AWS_REGION=us-east-1
S3_BUCKET=my-image-caption-bucket
DYNAMO_TABLE=image_captions
COGNITO_USER_POOL_ID=us-east-1_xxxxx
COGNITO_CLIENT_ID=xxxxxxxx
CAPTION_PROVIDER=bedrock   # or sagemaker | hf
BEDROCK_MODEL_ID=anthropic.claude-v2
SAGEMAKER_ENDPOINT=caption-endpoint
HF_API_KEY=hf_xxx
SECRETS_MANAGER_ARN=arn:aws:secretsmanager:...

Policy, privacy & legal notes (must be included)

Display a clear privacy notice about image storage, retention period, and deletion instructions.

Provide an option to delete user images & captions permanently.

Provide a retention default (e.g., images retained 90 days unless user deletes) — make retention configurable in Terraform.

Communication & deliverable expectations to attach to the PR

Small README in PR with deployment checklist and any manual steps.

Tag the release v1.0-production.

Provide merge commit message and a short demo GIF (in repo docs/demo.gif).

Acceptance testing checklist to run after deployment

Register user via Cognito hosted UI and sign in.

Upload a 1.2 MB JPG via Streamlit UI — confirm thumbnail & original in S3.

Confirm captions (concise + creative) appear and persisted in DB.

Validate presigned URL serves image via HTTPS.

Simulate high load (10 concurrent users) and confirm no critical errors.

Trigger a delete user data flow and confirm S3 + DB cleaned.

Confirm CloudWatch alarms trigger on simulated errors (e.g., intentionally fail model endpoint).

Extra notes for Cursor (developer guidance)

If Bedrock is not available in the target account or region, default to SageMaker hosting a Hugging Face image-captioning model (BLIP or ViT-GPT2) and provide performance trade-offs.

For speed: using Rekognition to get labels and seeding the caption prompt is optional but recommended — implement as an opt-in toggle.

Keep the code modular and well-documented. Use type hints and pydantic for config validation.

Prioritize security and least privilege over convenience in deployment.

If any AWS permission or account-level action is required (create IAM role, enable Bedrock), list them clearly in the PR and the README.

Final line to add to the issue/task (copy this)

Deliver a production-ready Image→Caption Generator (Streamlit + AWS) with infra as code, CI/CD, tests, documentation, and monitoring. Follow the detailed requirements in the attached spec. Do not request clarifications — deliver the full system and document any tradeoffs.