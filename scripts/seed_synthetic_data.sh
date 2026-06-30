#!/usr/bin/env bash
# Seed synthetic demo documents via the ingestion API (requires API + worker + Docker stack).
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
TENANT="${TENANT_ID:-demo-tenant}"

upload() {
  local file="$1"
  local doc_type="$2"
  echo "Uploading $file as $doc_type..."
  curl -s -X POST "${API_URL}/ingest" \
    -F "file=@${file}" \
    -F "doc_type=${doc_type}" \
    -F "tenant_id=${TENANT}" | python3 -m json.tool
}

upload data/synthetic/resume_alice_chen.txt resume
upload data/synthetic/resume_bob_martinez.txt resume
upload data/synthetic/resume_carol_singh.txt resume
upload data/synthetic/job_senior_java_cloud.md job_description
upload data/synthetic/interview_notes_senior_java.txt interview_notes

echo "Done. Check worker logs for ingestion completion."
