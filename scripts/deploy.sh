#!/usr/bin/env bash
set -euo pipefail

# Repeatable deployment script for Gemini Enterprise Agent Platform (Agent Runtime)
PROJECT="${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project 2>/dev/null || echo "hybrid-vertex")}"
REGION="${GEMINI_LOCATION:-us-central1}"

echo "============================================================"
echo "🚀 Deploying omnimeme to Gemini Enterprise Agent Platform"
echo "Project: ${PROJECT}"
echo "Region:  ${REGION}"
echo "============================================================"

# Ensure required GCP APIs are enabled
gcloud services enable \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  aiplatform.googleapis.com \
  run.googleapis.com \
  --project="${PROJECT}" >/dev/null 2>&1 || true

# Execute agents-cli deploy
uv run agents-cli deploy \
  --project "${PROJECT}" \
  --region "${REGION}" \
  --no-confirm-project \
  "$@"

echo "============================================================"
echo "✅ Deployment submitted! Checking deployment status..."
echo "============================================================"

uv run agents-cli deploy --status --project "${PROJECT}" --region "${REGION}"
