terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "incept-terraform-state"
    key    = "multilingual-generation/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"
}

variable "app_name" {
  description = "Application name"
  default     = "incept-ml-gen"
}

# Create minimal VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "${var.app_name}-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
}

# Public Subnets
resource "aws_subnet" "public" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  
  map_public_ip_on_launch = true
  
  tags = {
    Name = "${var.app_name}-subnet-${count.index + 1}"
  }
}

# Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
}

# Route Table Associations
resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Data source for availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# ECR Repository
resource "aws_ecr_repository" "main" {
  name                 = "incept-multilingual-generation"
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "incept-cluster"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "main" {
  name              = "/ecs/${var.app_name}"
  retention_in_days = 7
}

# Security Group for ECS Tasks (using default VPC)
resource "aws_security_group" "ecs_tasks" {
  name        = "${var.app_name}-ecs-tasks-sg"
  description = "Security group for ECS tasks"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# AWS Secrets Manager secrets
resource "aws_secretsmanager_secret" "supabase_url" {
  name        = "incept/supabase-url"
  description = "Supabase project URL"
}

resource "aws_secretsmanager_secret" "supabase_anon_key" {
  name        = "incept/supabase-anon-key"
  description = "Supabase anonymous key"
}

resource "aws_secretsmanager_secret" "supabase_key" {
  name        = "incept/supabase-key"
  description = "Supabase service role key"
}

# ECS Task Definition
resource "aws_ecs_task_definition" "main" {
  family                   = var.app_name
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = "arn:aws:iam::913524910742:role/ecsTaskExecutionRole"
  
  container_definitions = jsonencode([
    {
      name      = "incept-multilingual-api"
      image     = "${aws_ecr_repository.main.repository_url}:latest"
      essential = true
      
      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]
      
      environment = [
        {
          name  = "PORT"
          value = "8000"
        },
        {
          name  = "AWS_DEFAULT_REGION"
          value = var.aws_region
        },
        {
          name  = "ENABLE_IMAGE_GENERATION"
          value = "true"
        },
        {
          name  = "FALCON_API_BASE_URL"
          value = "http://185.216.20.114:8000/v1"
        },
        {
          name  = "LLM_PROVIDER"
          value = "falcon"
        }
      ]
      
      secrets = [
        {
          name      = "OPENAI_API_KEY"
          valueFrom = "arn:aws:secretsmanager:us-east-1:913524910742:secret:incept/openai-api-key"
        },
        {
          name      = "HUGGINGFACE_TOKEN"
          valueFrom = "arn:aws:secretsmanager:us-east-1:913524910742:secret:incept/huggingface-token-W1wKJf"
        },
        {
          name      = "ANTHROPIC_API_KEY"
          valueFrom = "arn:aws:secretsmanager:us-east-1:913524910742:secret:incept/anthropic-api-key-b2jvgK"
        },
        {
          name      = "GEMINI_API_KEY"
          valueFrom = "arn:aws:secretsmanager:us-east-1:913524910742:secret:incept/gemini-api-key"
        },
        {
          name      = "SUPABASE_URL"
          valueFrom = aws_secretsmanager_secret.supabase_url.arn
        },
        {
          name      = "SUPABASE_ANON_KEY"
          valueFrom = aws_secretsmanager_secret.supabase_anon_key.arn
        },
        {
          name      = "SUPABASE_KEY"
          valueFrom = aws_secretsmanager_secret.supabase_key.arn
        },
        {
          name      = "MONGODB_URI"
          valueFrom = "arn:aws:secretsmanager:us-east-1:913524910742:secret:incept/mongodb-uri"
        },
        {
          name      = "POSTGRES_URI"
          valueFrom = "arn:aws:secretsmanager:us-east-1:913524910742:secret:incept/postgres-url"
        },
        {
          name      = "APP_API_KEYS"
          valueFrom = "arn:aws:secretsmanager:us-east-1:913524910742:secret:incept/app-api-keys-GqDnDj"
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.main.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
      
      healthCheck = {
        command     = ["CMD-SHELL", "python -c \"import requests; requests.get('http://localhost:8000/health', timeout=5).raise_for_status()\" || exit 1"]
        interval    = 60
        timeout     = 15
        retries     = 5
        startPeriod = 180
      }
    }
  ])
}

# ECS Service
resource "aws_ecs_service" "main" {
  name            = "incept-multilingual-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.main.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  
  network_configuration {
    security_groups  = [aws_security_group.ecs_tasks.id]
    subnets          = aws_subnet.public[*].id
    assign_public_ip = true
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.main.arn
    container_name   = "incept-multilingual-api"
    container_port   = 8000
  }
  
  depends_on = [aws_lb_listener.https]
  
  lifecycle {
    ignore_changes = [task_definition]
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.app_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets           = aws_subnet.public[*].id
  idle_timeout       = 600
}

# Security Group for ALB
resource "aws_security_group" "alb" {
  name        = "${var.app_name}-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Target Group
resource "aws_lb_target_group" "main" {
  name        = "${var.app_name}-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"
  
  health_check {
    enabled             = true
    healthy_threshold   = 3
    interval            = 300
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 120
    unhealthy_threshold = 5
  }
}

# SSL Certificate
resource "aws_acm_certificate" "main" {
  domain_name       = "uae-poc.inceptapi.com"
  validation_method = "DNS"
  
  lifecycle {
    create_before_destroy = true
  }
}

# Certificate Validation
resource "aws_acm_certificate_validation" "main" {
  certificate_arn = aws_acm_certificate.main.arn
}

# HTTP Listener (redirect to HTTPS)
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"
  
  default_action {
    type = "redirect"
    
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# HTTPS Listener
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate_validation.main.certificate_arn
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main.arn
  }
  
  depends_on = [aws_acm_certificate_validation.main]
}

# Outputs
output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = aws_ecr_repository.main.repository_url
}

output "cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "service_name" {
  description = "Name of the ECS service"
  value       = aws_ecs_service.main.name
}

output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "domain_validation_records" {
  description = "DNS validation records for SSL certificate"
  value = [
    for record in aws_acm_certificate.main.domain_validation_options : {
      name  = record.resource_record_name
      type  = record.resource_record_type
      value = record.resource_record_value
    }
  ]
}

output "api_url" {
  description = "HTTPS URL for the API"
  value       = "https://uae-poc.inceptapi.com"
}
