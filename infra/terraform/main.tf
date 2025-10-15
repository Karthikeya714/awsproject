# Terraform Configuration for Image Caption Generator

terraform {
  required_version = ">= 1.5"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # Backend configuration for state storage
  backend "s3" {
    # Configure these via terraform init -backend-config
    # bucket         = "my-terraform-state-bucket"
    # key            = "image-caption/terraform.tfstate"
    # region         = "us-east-1"
    # dynamodb_table = "terraform-state-lock"
    # encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "ImageCaptionGenerator"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}
