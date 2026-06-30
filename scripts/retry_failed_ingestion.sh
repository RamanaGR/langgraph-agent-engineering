#!/usr/bin/env bash
# Re-queue failed/pending documents for ingestion (after worker fixes).
set -euo pipefail

docker compose exec -T postgres psql -U talentscreen -d talentscreen <<'SQL'
UPDATE documents
SET status = 'pending', error_message = NULL, updated_at = NOW()
WHERE status IN ('failed', 'processing');
SELECT document_id, filename, status FROM documents ORDER BY created_at;
SQL

echo "Re-enqueue from API by re-running seed or POST /ingest with new files."
echo "For same files, run: docker compose exec -T postgres psql -U talentscreen -d talentscreen -c \"DELETE FROM documents WHERE status='failed';\""
