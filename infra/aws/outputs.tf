output "documents_bucket" {
  description = "S3 bucket for raw recruiting documents (maps to local MinIO)"
  value       = aws_s3_bucket.documents.id
}

output "api_gateway_url" {
  description = "API Gateway invoke URL (maps to local FastAPI)"
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "rds_endpoint" {
  description = "RDS Postgres endpoint (canonical chunks + checkpointer)"
  value       = aws_db_instance.postgres.address
}

output "elasticache_endpoint" {
  description = "ElastiCache Redis endpoint (query cache + ingestion queue)"
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
}

output "bedrock_invoke_role_arn" {
  description = "IAM role for Bedrock Claude + Titan embeddings"
  value       = aws_iam_role.bedrock_invoke.arn
}

output "ingest_lambda_arn" {
  description = "Lambda triggered by S3 uploads (maps to ARQ worker)"
  value       = aws_lambda_function.ingest.arn
}
