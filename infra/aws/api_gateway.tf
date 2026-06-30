# API Gateway — local equivalent: FastAPI on :8000

resource "aws_apigatewayv2_api" "http" {
  name          = "${var.project_name}-api-${var.environment}"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["https://recruiter.example.com", "https://candidate.example.com"]
    allow_methods = ["GET", "POST", "PUT", "OPTIONS"]
    allow_headers = ["content-type", "x-api-key", "x-role", "authorization"]
  }
}

resource "aws_apigatewayv2_integration" "fastapi" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "HTTP_PROXY"
  integration_method     = "ANY"
  integration_uri        = "http://talentscreen-api.${var.environment}.internal/{proxy}"
  payload_format_version = "1.0"
}

resource "aws_apigatewayv2_route" "proxy" {
  api_id    = aws_apigatewayv2_api.http.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.fastapi.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_apigatewayv2_api_mapping" "custom_domain" {
  count = var.environment == "prod" ? 1 : 0

  api_id      = aws_apigatewayv2_api.http.id
  domain_name = aws_apigatewayv2_domain_name.api[0].id
  stage       = aws_apigatewayv2_stage.default.id
}

resource "aws_apigatewayv2_domain_name" "api" {
  count = var.environment == "prod" ? 1 : 0

  domain_name = "api.talentscreen.example.com"

  domain_name_configuration {
    certificate_arn = aws_acm_certificate.api[0].arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }
}

resource "aws_acm_certificate" "api" {
  count = var.environment == "prod" ? 1 : 0

  domain_name       = "api.talentscreen.example.com"
  validation_method = "DNS"
}
