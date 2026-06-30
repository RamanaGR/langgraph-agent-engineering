variable "aws_region" {
  description = "AWS region for TalentScreen production mapping"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment name"
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Resource name prefix"
  type        = string
  default     = "talentscreen"
}

variable "vpc_id" {
  description = "VPC ID for RDS, ElastiCache, and EKS Milvus"
  type        = string
  default     = ""
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for data plane services"
  type        = list(string)
  default     = []
}

variable "bedrock_model_id" {
  description = "Bedrock Claude model for generation"
  type        = string
  default     = "anthropic.claude-3-sonnet-20240229-v1:0"
}
