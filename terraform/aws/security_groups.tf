# ==============================================================================
# Phoenix AWS Security Groups (security_groups.tf)
# Granular ingress rules with strict port isolation
# ==============================================================================

# --- Application Server Security Group ---
resource "aws_security_group" "app_sg" {
  name        = "phoenix-${terraform.workspace}-app-sg"
  description = "Security rules for Phoenix Application Server"
  vpc_id      = aws_vpc.phoenix_vpc.id

  # Administrative SSH access
  ingress {
    description = "SSH from Administrator IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_ip]
  }

  # Public Web HTTP
  ingress {
    description = "Public HTTP Portal"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Public Web HTTPS
  ingress {
    description = "Public HTTPS Portal"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Internal NRPE Monitoring (from Nagios Server or internal VPC)
  ingress {
    description = "NRPE agent check from internal VPC"
    from_port   = 5666
    to_port     = 5666
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  # Outbound Internet
  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "phoenix-${terraform.workspace}-app-sg"
  }
}

# --- Puppet Master Security Group ---
resource "aws_security_group" "puppet_sg" {
  name        = "phoenix-${terraform.workspace}-puppet-sg"
  description = "Security rules for Puppet Master Server"
  vpc_id      = aws_vpc.phoenix_vpc.id

  ingress {
    description = "SSH from Administrator IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_ip]
  }

  # Puppet Master catalog compilation (Port 8140 restricted to VPC)
  ingress {
    description = "Puppet Agent catalog access from internal VPC"
    from_port   = 8140
    to_port     = 8140
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "phoenix-${terraform.workspace}-puppet-sg"
  }
}

# --- Nagios Monitoring Server Security Group ---
resource "aws_security_group" "nagios_sg" {
  name        = "phoenix-${terraform.workspace}-nagios-sg"
  description = "Security rules for Nagios Core Server"
  vpc_id      = aws_vpc.phoenix_vpc.id

  ingress {
    description = "SSH from Administrator IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_ip]
  }

  # Nagios Core Web UI (Port 80)
  ingress {
    description = "Nagios Core Web UI"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [var.admin_ip]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "phoenix-${terraform.workspace}-nagios-sg"
  }
}
