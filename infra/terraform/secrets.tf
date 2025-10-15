# AWS Secrets Manager Configuration

# KMS key for secrets encryption
resource "aws_kms_key" "secrets" {
  description             = "KMS key for Secrets Manager"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-secrets-key-${var.environment}"
    }
  )
}

resource "aws_kms_alias" "secrets" {
  name          = "alias/${var.project_name}-secrets-${var.environment}"
  target_key_id = aws_kms_key.secrets.key_id
}

# Secrets Manager Secret
resource "aws_secretsmanager_secret" "app_secrets" {
  name        = "${var.project_name}-secrets-${var.environment}"
  description = "Application secrets for Image Caption Generator"
  kms_key_id  = aws_kms_key.secrets.id

  recovery_window_in_days = 7

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-secrets-${var.environment}"
    }
  )
}

# Secret Version with default values
resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id

  secret_string = jsonencode({
    hf_api_key        = ""
    sagemaker_endpoint = ""
    # Add other secrets as needed
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# Rotation Lambda (optional - for future implementation)
# resource "aws_lambda_function" "secret_rotation" {
#   ...
# }
