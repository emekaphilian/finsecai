#!/bin/bash
# Production Deployment Script for FinSecAI
# Usage: ./deploy.sh [staging|production] [aws|gcp|azure]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-staging}
CLOUD_PROVIDER=${2:-aws}
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DEPLOYMENT_LOG="$SCRIPT_DIR/deployment_$(date +%Y%m%d_%H%M%S).log"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
    exit 1
}

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."
    
    # Check required tools
    for tool in docker docker-compose git python3 aws; do
        if ! command -v $tool &> /dev/null; then
            log_error "$tool is not installed"
        fi
    done
    
    # Check Python dependencies
    if ! python3 -c "import streamlit" &> /dev/null; then
        log_error "Python dependencies not installed. Run: pip install -r requirements.txt"
    fi
    
    # Check environment file
    if [ ! -f ".env.$ENVIRONMENT" ]; then
        log_error ".env.$ENVIRONMENT file not found. Copy from .env.production.template"
    fi
    
    # Check Docker daemon
    if ! docker ps > /dev/null 2>&1; then
        log_error "Docker daemon is not running"
    fi
    
    log_success "Pre-deployment checks passed"
}

# Run smoke tests
run_smoke_tests() {
    log_info "Running smoke tests..."
    
    python3 utils/smoke_test.py --verbose || log_error "Smoke tests failed"
    
    log_success "Smoke tests passed"
}

# Build Docker image
build_docker_image() {
    log_info "Building Docker image..."
    
    local registry=$1
    local version=$(git describe --tags --always)
    local image_name="$registry/finsecai:$version"
    
    docker build -t "$image_name" -f Dockerfile.prod . || log_error "Docker build failed"
    docker tag "$image_name" "$registry/finsecai:latest"
    
    log_success "Docker image built: $image_name"
}

# Push to container registry
push_docker_image() {
    log_info "Pushing Docker image to registry..."
    
    local registry=$1
    docker push "$registry/finsecai:latest" || log_error "Docker push failed"
    
    log_success "Docker image pushed to registry"
}

# Deploy to AWS
deploy_aws() {
    log_info "Deploying to AWS..."
    
    # Get AWS configuration
    local aws_region=$(aws configure get region)
    local ecr_registry=$(aws ecr describe-repositories --repository-names finsecai \
        --region "$aws_region" --query 'repositories[0].repositoryUri' --output text 2>/dev/null || echo "")
    
    if [ -z "$ecr_registry" ]; then
        log_info "Creating ECR repository..."
        ecr_registry=$(aws ecr create-repository --repository-name finsecai \
            --region "$aws_region" --query 'repository.repositoryUri' --output text)
    fi
    
    # Build and push
    build_docker_image "$ecr_registry"
    push_docker_image "$ecr_registry"
    
    # Update ECS task definition
    log_info "Updating ECS task definition..."
    # TODO: Implement ECS update logic
    
    log_success "AWS deployment completed"
}

# Deploy to GCP
deploy_gcp() {
    log_info "Deploying to Google Cloud..."
    
    local project_id=$(gcloud config get-value project)
    local registry="gcr.io/$project_id"
    
    # Configure Docker for GCP
    gcloud auth configure-docker gcr.io
    
    # Build and push
    build_docker_image "$registry"
    push_docker_image "$registry"
    
    # Deploy to Cloud Run
    log_info "Deploying to Cloud Run..."
    gcloud run deploy finsecai \
        --image "$registry/finsecai:latest" \
        --region us-central1 \
        --platform managed \
        --memory 2Gi \
        --cpu 1 \
        --env-vars-file .env.$ENVIRONMENT
    
    log_success "GCP deployment completed"
}

# Deploy to Azure
deploy_azure() {
    log_info "Deploying to Azure..."
    
    local registry="${AZURE_REGISTRY_NAME}.azurecr.io"
    
    # Login to Azure Container Registry
    az acr login --name "${AZURE_REGISTRY_NAME}"
    
    # Build and push
    build_docker_image "$registry"
    push_docker_image "$registry"
    
    # Deploy to App Service
    log_info "Deploying to App Service..."
    az webapp deployment container config \
        --name finsecai \
        --resource-group "${AZURE_RESOURCE_GROUP}"
    
    log_success "Azure deployment completed"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Load environment
    source ".env.$ENVIRONMENT"
    
    # Run migrations
    psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
        -f sql/init_production_db.sql || log_error "Database migrations failed"
    
    log_success "Database migrations completed"
}

# Run post-deployment tests
post_deployment_tests() {
    log_info "Running post-deployment tests..."
    
    # Wait for service to be ready
    sleep 10
    
    # Health check
    if ! curl -f http://localhost:8506/_stcore/health > /dev/null 2>&1; then
        log_error "Health check failed"
    fi
    
    # Run smoke tests
    python3 utils/smoke_test.py --verbose || log_error "Post-deployment smoke tests failed"
    
    log_success "Post-deployment tests passed"
}

# Main deployment flow
main() {
    log_info "Starting deployment to $ENVIRONMENT on $CLOUD_PROVIDER"
    log_info "Deployment log: $DEPLOYMENT_LOG"
    
    # Pre-deployment
    pre_deployment_checks
    run_smoke_tests
    
    # Deploy based on cloud provider
    case "$CLOUD_PROVIDER" in
        aws)
            deploy_aws
            ;;
        gcp)
            deploy_gcp
            ;;
        azure)
            deploy_azure
            ;;
        *)
            log_error "Unknown cloud provider: $CLOUD_PROVIDER"
            ;;
    esac
    
    # Post-deployment
    run_migrations
    
    # Only run post-deployment tests for local deployments
    if [ "$ENVIRONMENT" = "local" ]; then
        post_deployment_tests
    fi
    
    log_success "Deployment to $ENVIRONMENT completed successfully!"
    log_info "Next steps:"
    log_info "1. Monitor the application at https://yourdomain.com"
    log_info "2. Check metrics at http://grafana:3000"
    log_info "3. Review logs in CloudWatch/Cloud Logging/Monitor"
    log_info "4. Set up monitoring alerts"
}

# Run main
main
