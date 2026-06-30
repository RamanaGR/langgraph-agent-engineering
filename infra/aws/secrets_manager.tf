resource "aws_secretsmanager_secret" "app" {
  name        = "${var.project_name}/${var.environment}/app"
  description = "TalentScreen API keys, DB URL, Bedrock config"
}

resource "aws_secretsmanager_secret_version" "app" {
  secret_id = aws_secretsmanager_secret.app.id

  secret_string = jsonencode({
    api_key_recruiter  = "REPLACE_ME"
    api_key_candidate  = "REPLACE_ME"
    langfuse_public_key = ""
    langfuse_secret_key = ""
    anthropic_api_key   = ""
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}
