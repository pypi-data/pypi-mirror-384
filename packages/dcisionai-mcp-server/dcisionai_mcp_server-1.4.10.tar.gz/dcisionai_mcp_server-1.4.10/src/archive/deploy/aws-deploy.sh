#!/bin/bash

# DcisionAI MCP Server - AWS Deployment Script
# Deploys the MCP server to AWS ECS with zero-dependency setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
AWS_REGION=${AWS_REGION:-us-east-1}
CLUSTER_NAME=${CLUSTER_NAME:-dcisionai-mcp-cluster}
SERVICE_NAME=${SERVICE_NAME:-dcisionai-mcp-service}
TASK_DEFINITION=${TASK_DEFINITION:-dcisionai-mcp-task}
REPOSITORY_NAME=${REPOSITORY_NAME:-dcisionai-mcp-server}
IMAGE_TAG=${IMAGE_TAG:-latest}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found. Please install AWS CLI first."
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install Docker first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Create ECR repository
create_ecr_repository() {
    print_status "Creating ECR repository..."
    
    if aws ecr describe-repositories --repository-names $REPOSITORY_NAME --region $AWS_REGION &> /dev/null; then
        print_warning "ECR repository already exists"
    else
        aws ecr create-repository --repository-name $REPOSITORY_NAME --region $AWS_REGION
        print_success "ECR repository created"
    fi
}

# Build and push Docker image
build_and_push_image() {
    print_status "Building and pushing Docker image..."
    
    # Get ECR login token
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com
    
    # Build image
    docker build -t $REPOSITORY_NAME:$IMAGE_TAG .
    
    # Tag image
    ECR_URI=$(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com/$REPOSITORY_NAME:$IMAGE_TAG
    docker tag $REPOSITORY_NAME:$IMAGE_TAG $ECR_URI
    
    # Push image
    docker push $ECR_URI
    
    print_success "Docker image built and pushed to ECR"
    echo $ECR_URI
}

# Create ECS cluster
create_ecs_cluster() {
    print_status "Creating ECS cluster..."
    
    if aws ecs describe-clusters --clusters $CLUSTER_NAME --region $AWS_REGION &> /dev/null; then
        print_warning "ECS cluster already exists"
    else
        aws ecs create-cluster --cluster-name $CLUSTER_NAME --region $AWS_REGION
        print_success "ECS cluster created"
    fi
}

# Create task definition
create_task_definition() {
    print_status "Creating ECS task definition..."
    
    ECR_URI=$(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com/$REPOSITORY_NAME:$IMAGE_TAG
    
    cat > task-definition.json << EOF
{
    "family": "$TASK_DEFINITION",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "512",
    "memory": "1024",
    "executionRoleArn": "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/ecsTaskExecutionRole",
    "containerDefinitions": [
        {
            "name": "dcisionai-mcp-server",
            "image": "$ECR_URI",
            "portMappings": [
                {
                    "containerPort": 8000,
                    "protocol": "tcp"
                }
            ],
            "environment": [
                {
                    "name": "AWS_DEFAULT_REGION",
                    "value": "$AWS_REGION"
                }
            ],
            "secrets": [
                {
                    "name": "DCISIONAI_ACCESS_TOKEN",
                    "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):secret:dcisionai/access-token"
                },
                {
                    "name": "DCISIONAI_GATEWAY_URL",
                    "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):secret:dcisionai/gateway-url"
                }
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/dcisionai-mcp-server",
                    "awslogs-region": "$AWS_REGION",
                    "awslogs-stream-prefix": "ecs"
                }
            },
            "healthCheck": {
                "command": ["CMD-SHELL", "dcisionai-mcp-server health-check || exit 1"],
                "interval": 30,
                "timeout": 5,
                "retries": 3,
                "startPeriod": 60
            }
        }
    ]
}
EOF
    
    aws ecs register-task-definition --cli-input-json file://task-definition.json --region $AWS_REGION
    print_success "Task definition created"
}

# Create CloudWatch log group
create_log_group() {
    print_status "Creating CloudWatch log group..."
    
    if aws logs describe-log-groups --log-group-name-prefix "/ecs/dcisionai-mcp-server" --region $AWS_REGION | grep -q "/ecs/dcisionai-mcp-server"; then
        print_warning "Log group already exists"
    else
        aws logs create-log-group --log-group-name "/ecs/dcisionai-mcp-server" --region $AWS_REGION
        print_success "CloudWatch log group created"
    fi
}

# Create secrets in Secrets Manager
create_secrets() {
    print_status "Creating secrets in Secrets Manager..."
    
    # Check if secrets already exist
    if aws secretsmanager describe-secret --secret-id "dcisionai/access-token" --region $AWS_REGION &> /dev/null; then
        print_warning "Access token secret already exists"
    else
        read -p "Enter your DCISIONAI_ACCESS_TOKEN: " -s ACCESS_TOKEN
        echo
        aws secretsmanager create-secret --name "dcisionai/access-token" --secret-string "$ACCESS_TOKEN" --region $AWS_REGION
        print_success "Access token secret created"
    fi
    
    if aws secretsmanager describe-secret --secret-id "dcisionai/gateway-url" --region $AWS_REGION &> /dev/null; then
        print_warning "Gateway URL secret already exists"
    else
        read -p "Enter your DCISIONAI_GATEWAY_URL: " GATEWAY_URL
        aws secretsmanager create-secret --name "dcisionai/gateway-url" --secret-string "$GATEWAY_URL" --region $AWS_REGION
        print_success "Gateway URL secret created"
    fi
}

# Deploy service
deploy_service() {
    print_status "Deploying ECS service..."
    
    # Get default VPC and subnets
    VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query "Vpcs[0].VpcId" --output text --region $AWS_REGION)
    SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query "Subnets[0:2].SubnetId" --output text --region $AWS_REGION)
    
    # Create security group
    SECURITY_GROUP_ID=$(aws ec2 create-security-group --group-name dcisionai-mcp-sg --description "Security group for DcisionAI MCP Server" --vpc-id $VPC_ID --region $AWS_REGION --query "GroupId" --output text)
    aws ec2 authorize-security-group-ingress --group-id $SECURITY_GROUP_ID --protocol tcp --port 8000 --cidr 0.0.0.0/0 --region $AWS_REGION
    
    # Create or update service
    if aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION &> /dev/null; then
        aws ecs update-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --task-definition $TASK_DEFINITION --region $AWS_REGION
        print_success "ECS service updated"
    else
        aws ecs create-service \
            --cluster $CLUSTER_NAME \
            --service-name $SERVICE_NAME \
            --task-definition $TASK_DEFINITION \
            --desired-count 1 \
            --launch-type FARGATE \
            --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_IDS],securityGroups=[$SECURITY_GROUP_ID],assignPublicIp=ENABLED}" \
            --region $AWS_REGION
        print_success "ECS service created"
    fi
}

# Main deployment function
main() {
    echo "🚀 DcisionAI MCP Server - AWS Deployment"
    echo "========================================"
    echo
    
    check_prerequisites
    create_ecr_repository
    ECR_URI=$(build_and_push_image)
    create_ecs_cluster
    create_log_group
    create_secrets
    create_task_definition
    deploy_service
    
    print_success "🎉 Deployment completed successfully!"
    echo
    echo "Your MCP server is now running on AWS ECS!"
    echo "Service URL: http://$(aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION --query "services[0].loadBalancers[0].hostname" --output text):8000"
    echo
    echo "To check service status:"
    echo "aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION"
    echo
    echo "To view logs:"
    echo "aws logs tail /ecs/dcisionai-mcp-server --follow --region $AWS_REGION"
}

# Run main function
main "$@"
