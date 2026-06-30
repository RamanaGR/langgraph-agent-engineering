# Bedrock IAM — local equivalent: Ollama / LLM_PROVIDER swap

resource "aws_iam_role" "bedrock_invoke" {
  name = "${var.project_name}-bedrock-invoke-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = ["ecs-tasks.amazonaws.com", "lambda.amazonaws.com"] }
    }]
  })
}

resource "aws_iam_role_policy" "bedrock_invoke" {
  name = "bedrock-claude-titan"
  role = aws_iam_role.bedrock_invoke.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
        ]
        Resource = [
          "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.*",
          "arn:aws:bedrock:${var.aws_region}::foundation-model/amazon.titan-embed-text-v1",
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["bedrock:GetInferenceProfile", "bedrock:ListInferenceProfiles"]
        Resource = "*"
      },
    ]
  })
}

# Prompt cache uses Bedrock model ID via talentscreen.generation.llm.bedrock_stub
# Inference profiles can be configured per-account when enabling prompt caching.
