# ==============================================================================
# Phoenix AWS Infrastructure - VPC & Networking (main.tf)
# Supports dev/prod workspaces with workspace-aware naming
# ==============================================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = "Phoenix"
      Environment = terraform.workspace
      ManagedBy   = "Terraform"
    }
  }
}

# Fetch latest Ubuntu 22.04 LTS official AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# --- Virtual Private Cloud (VPC) ---
resource "aws_vpc" "phoenix_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "phoenix-${terraform.workspace}-vpc"
  }
}

# --- Internet Gateway ---
resource "aws_internet_gateway" "phoenix_igw" {
  vpc_id = aws_vpc.phoenix_vpc.id

  tags = {
    Name = "phoenix-${terraform.workspace}-igw"
  }
}

# --- Public Subnet ---
resource "aws_subnet" "phoenix_public_subnet" {
  vpc_id                  = aws_vpc.phoenix_vpc.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = true

  tags = {
    Name = "phoenix-${terraform.workspace}-public-subnet"
  }
}

# --- Route Table & Internet Route ---
resource "aws_route_table" "phoenix_public_rt" {
  vpc_id = aws_vpc.phoenix_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.phoenix_igw.id
  }

  tags = {
    Name = "phoenix-${terraform.workspace}-public-rt"
  }
}

# --- Route Table Association ---
resource "aws_route_table_association" "phoenix_public_rta" {
  subnet_id      = aws_subnet.phoenix_public_subnet.id
  route_table_id = aws_route_table.phoenix_public_rt.id
}
