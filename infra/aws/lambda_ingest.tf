# Ingestion Lambda — local equivalent: ARQ worker + ingestion pipeline

resource "aws_iam_role" "ingest_lambda" {
  name = "${var.project_name}-ingest-lambda-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "ingest_lambda" {
  name = "ingest-s3-secrets"
  role = aws_iam_role.ingest_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:ListBucket"]
        Resource = [
          aws_s3_bucket.documents.arn,
          "${aws_s3_bucket.documents.arn}/*",
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = [aws_secretsmanager_secret.app.arn]
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = ["arn:aws:logs:*:*:*"]
      },
    ]
  })
}

resource "aws_lambda_function" "ingest" {
  function_name = "${var.project_name}-ingest-${var.environment}"
  role          = aws_iam_role.ingest_lambda.arn
  handler       = "handler.ingest_document"
  runtime       = "python3.11"
  timeout       = 300
  memory_size   = 1024

  # Package talentscreen ingestion worker container image or zip in CI
  filename = "${path.module}/lambda_placeholder.zip"

  environment {
    variables = {
      DATABASE_URL   = "postgresql://${aws_db_instance.postgres.username}:@:${aws_db_instance.postgres.endpoint}/${aws_db_instance.postgres.db_name}"
      MILVUS_HOST    = "milvus.${var.project_name}.svc.cluster.local"
      SECRETS_ARN    = aws_secretsmanager_secret.app.arn
      BEDROCK_REGION = var.aws_region
    }
  }
}

resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingest.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.documents.arn
}
