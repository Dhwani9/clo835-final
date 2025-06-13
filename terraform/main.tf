provider "aws" {
  region = "us-east-1"
}

# Get the default VPC
data "aws_vpc" "default" {
  default = true
}

# Security Group allowing SSH and ports 8081-8083
resource "aws_security_group" "web_sg" {
  name        = "webapp-sg"
  description = "Allow SSH and custom app ports"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "Allow SSH from anywhere (lab use only)"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allow HTTP app access on 8081"
    from_port   = 8081
    to_port     = 8081
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allow HTTP app access on 8082"
    from_port   = 8082
    to_port     = 8082
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allow HTTP app access on 8083"
    from_port   = 8083
    to_port     = 8083
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "WebAppSG"
  }
}

# ECR Repositories
resource "aws_ecr_repository" "webapp" {
  name = "webapp-repo"
}

resource "aws_ecr_repository" "mysql" {
  name = "mysql-repo"
}

# EC2 Instance
resource "aws_instance" "webserver" {
  ami                    = "ami-0c02fb55956c7d316" # Amazon Linux 2
  instance_type          = "t2.micro"
  key_name               = "terraform-key" # Replace with your actual key pair name
  associate_public_ip_address = true
  vpc_security_group_ids = [aws_security_group.web_sg.id]

  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install docker -y
              service docker start
              usermod -a -G docker ec2-user
              EOF

  tags = {
    Name = "CLO835-Webserver"
  }
}
