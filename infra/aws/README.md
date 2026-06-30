# TalentScreen AWS Terraform (reference)

Reference infrastructure mapping the **local Docker stack** to AWS production services. Not applied in the portfolio repo (no AWS credentials required).

## Local → AWS mapping

| Local | AWS resource | Terraform file |
|-------|--------------|----------------|
| MinIO | S3 + Lambda ingest trigger | `s3.tf`, `lambda_ingest.tf` |
| FastAPI :8000 | API Gateway HTTP API | `api_gateway.tf` |
| Ollama | Bedrock Claude + Titan embeddings | `bedrock_iam.tf` |
| Postgres | RDS PostgreSQL 16 | `rds.tf` |
| Redis | ElastiCache Redis 7 | `elasticache.tf` |
| Milvus Docker | Milvus on EKS | `eks_milvus/` |
| `.env` secrets | Secrets Manager | `secrets_manager.tf` |

## Usage (interview / future deploy)

```bash
cd infra/aws
terraform init
terraform plan -var="vpc_id=vpc-xxx" -var='private_subnet_ids=["subnet-a","subnet-b"]'
```

Set `environment=prod` to enable EKS Milvus cluster resources.

## Swap-in notes

1. Point `LLM_PROVIDER=bedrock` and `EMBEDDING_PROVIDER=bedrock` in the app.
2. Replace `MINIO_*` with S3 SDK using the documents bucket output.
3. Use `DATABASE_URL` from Secrets Manager `database` secret.
4. Redis URL from ElastiCache primary endpoint.
5. Milvus host from EKS internal service DNS.

See [docs/aws-mapping.md](../../docs/aws-mapping.md) for the full narrative.
