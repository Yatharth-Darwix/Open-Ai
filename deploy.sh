#!/bin/bash

# Configuration
PROJECT_ID=${1:-"email-automation-darwix"}
SERVICE_NAME="openai-monitor"
REGION="us-central1"
# Modern Artifact Registry URL structure
IMAGE_URL="us-central1-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/$SERVICE_NAME"

# Function to read variables from .env
load_env() {
  if [ -f backend/.env ]; then
    export $(grep -v '^#' backend/.env | xargs)
  else
    echo "Error: backend/.env file not found!"
    exit 1
  fi
}

echo "--- Deploying OpenAI Monitor to Google Cloud Run ---"
echo "Project ID: $PROJECT_ID"

# 1. Load Environment Variables
echo "Loading configuration from .env..."
load_env

if [ -z "$OPENAI_ADMIN_KEY" ]; then
  echo "Error: OPENAI_ADMIN_KEY is missing in .env"
  exit 1
fi

# 2. Create env.yaml for safe deployment
# This avoids command-line parsing errors with spaces/commas in email lists
echo "Generating temporary env.yaml..."
cat > env.yaml <<EOF
OPENAI_ADMIN_KEY: "$OPENAI_ADMIN_KEY"
SMTP_EMAIL: "$SMTP_EMAIL"
SMTP_PASSWORD: "$SMTP_PASSWORD"
SMTP_SERVER: "$SMTP_SERVER"
SMTP_PORT: "$SMTP_PORT"
ALERT_THRESHOLD: "$ALERT_THRESHOLD"
ALERT_RECIPIENT_EMAIL: "$ALERT_RECIPIENT_EMAIL"
INITIAL_TOTAL_DEPOSITED: "0.0"
EOF

# 3. Build and Deploy
echo "Building and Deploying to Cloud Run..."
# We use the source deploy command which handles the build + deploy in one step
# and often automatically creates the necessary Artifact Registry repo.
gcloud run deploy $SERVICE_NAME \
  --source . \
  --project $PROJECT_ID \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --env-vars-file env.yaml

# Cleanup
rm env.yaml

echo "--- Deployment Complete! ---"
echo "Note: If your container restarts, the balance will reset to 0.0 (or INITIAL_TOTAL_DEPOSITED)."
echo "You should use the 'Sync Balance' button on the dashboard to correct it."
