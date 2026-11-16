# ==============================================================================
# Phoenix AWS EC2 Instances (ec2.tf)
# Provisions 3 Free-Tier instances with user_data bootstrapping
# ==============================================================================

# --- Application Server ---
resource "aws_instance" "app_server" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type_app
  subnet_id                   = aws_subnet.phoenix_public_subnet.id
  vpc_security_group_ids      = [aws_security_group.app_sg.id]
  key_name                    = var.key_name
  associate_public_ip_address = true
  user_data                   = file("${path.module}/scripts/bootstrap_app.sh")

  root_block_device {
    volume_size           = 20
    volume_type           = "gp3"
    delete_on_termination = true
  }

  tags = {
    Name = "phoenix-${terraform.workspace}-app-server"
    Role = "Application"
  }
}

# --- Puppet Master Server ---
resource "aws_instance" "puppet_master" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type_puppet
  subnet_id                   = aws_subnet.phoenix_public_subnet.id
  vpc_security_group_ids      = [aws_security_group.puppet_sg.id]
  key_name                    = var.key_name
  associate_public_ip_address = true
  user_data                   = file("${path.module}/scripts/bootstrap_puppet.sh")

  root_block_device {
    volume_size           = 20
    volume_type           = "gp3"
    delete_on_termination = true
  }

  tags = {
    Name = "phoenix-${terraform.workspace}-puppet-master"
    Role = "PuppetMaster"
  }
}

# --- Nagios Monitoring Server ---
resource "aws_instance" "nagios_server" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type_nagios
  subnet_id                   = aws_subnet.phoenix_public_subnet.id
  vpc_security_group_ids      = [aws_security_group.nagios_sg.id]
  key_name                    = var.key_name
  associate_public_ip_address = true
  user_data                   = file("${path.module}/scripts/bootstrap_nagios.sh")

  root_block_device {
    volume_size           = 20
    volume_type           = "gp3"
    delete_on_termination = true
  }

  tags = {
    Name = "phoenix-${terraform.workspace}-nagios-server"
    Role = "NagiosServer"
  }
}
