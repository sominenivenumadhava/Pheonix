# ==============================================================================
# Phoenix Terraform Variables (variables.tf)
# Configurable inputs supporting dev and prod workspaces
# ==============================================================================

variable "aws_region" {
  description = "AWS deployment region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for Phoenix VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for public subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "availability_zone" {
  description = "Availability zone for public subnet"
  type        = string
  default     = "us-east-1a"
}

variable "admin_ip" {
  description = "Administrator IP address allowed for SSH management (CIDR format)"
  type        = string
  default     = "0.0.0.0/0"
}

variable "instance_type_app" {
  description = "EC2 instance size for Application Server (free tier: t3.micro / t2.micro)"
  type        = string
  default     = "t3.micro"
}

variable "instance_type_puppet" {
  description = "EC2 instance size for Puppet Master (free tier / small: t3.small / t3.micro)"
  type        = string
  default     = "t3.small"
}

variable "instance_type_nagios" {
  description = "EC2 instance size for Nagios Server (free tier: t3.micro)"
  type        = string
  default     = "t3.micro"
}

variable "key_name" {
  description = "Name of existing AWS EC2 key pair for SSH access"
  type        = string
  default     = "phoenix-demo-key"
}
