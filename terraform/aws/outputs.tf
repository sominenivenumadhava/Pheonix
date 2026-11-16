# ==============================================================================
# Phoenix Terraform Outputs (outputs.tf)
# IP addresses and infrastructure metadata for Ansible inventory binding
# ==============================================================================

output "active_workspace" {
  description = "Current Terraform workspace"
  value       = terraform.workspace
}

output "vpc_id" {
  description = "ID of Phoenix VPC"
  value       = aws_vpc.phoenix_vpc.id
}

output "public_subnet_id" {
  description = "ID of Phoenix Public Subnet"
  value       = aws_subnet.phoenix_public_subnet.id
}

output "app_server_public_ip" {
  description = "Public IP address of Phoenix Application Server"
  value       = aws_instance.app_server.public_ip
}

output "app_server_private_ip" {
  description = "Private IP address of Phoenix Application Server"
  value       = aws_instance.app_server.private_ip
}

output "puppet_master_public_ip" {
  description = "Public IP address of Puppet Master Server"
  value       = aws_instance.puppet_master.public_ip
}

output "puppet_master_private_ip" {
  description = "Private IP address of Puppet Master Server"
  value       = aws_instance.puppet_master.private_ip
}

output "nagios_server_public_ip" {
  description = "Public IP address of Nagios Monitoring Server"
  value       = aws_instance.nagios_server.public_ip
}

output "nagios_server_private_ip" {
  description = "Private IP address of Nagios Monitoring Server"
  value       = aws_instance.nagios_server.private_ip
}
