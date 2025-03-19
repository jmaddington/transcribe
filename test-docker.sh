#!/bin/bash
# Enhanced Docker testing script with improved diagnostics
set -e

# Color support for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test result tracking
TESTS_PASSED=0
TESTS_FAILED=0
WARNINGS=0

# Helper functions
log_info() {
    echo -e "${BLUE}INFO:${NC} $1"
}

log_success() {
    echo -e "${GREEN}SUCCESS:${NC} $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

log_warning() {
    echo -e "${YELLOW}WARNING:${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

log_error() {
    echo -e "${RED}ERROR:${NC} $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

test_endpoint() {
    local url=$1
    local expected_status=$2
    local test_name=$3
    local actual_status
    
    log_info "Testing $test_name..."
    actual_status=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$actual_status" -eq "$expected_status" ]; then
        log_success "$test_name returned $actual_status as expected"
    else
        log_error "$test_name returned $actual_status (expected $expected_status)"
    fi
}

header() {
    echo -e "\n${BLUE}=========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=========================================${NC}\n"
}

# Main script
header "Docker Configuration Test for Audio Transcription Tool"
log_info "Testing started at $(date)"

# Check system requirements
header "System Requirements Check"

# Check for Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed or not in PATH"
    exit 1
else
    docker_version=$(docker --version)
    log_success "Docker is installed: $docker_version"
fi

# Check for Docker Compose (either standalone or integrated)
DOCKER_COMPOSE_CMD=""
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
    compose_version=$(docker-compose --version)
    log_success "Docker Compose standalone is installed: $compose_version"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
    compose_version=$(docker compose version)
    log_success "Docker Compose plugin is installed: $compose_version"
else
    log_error "Docker Compose is not installed or not in PATH"
    exit 1
fi

# Check Docker daemon status
if docker info &> /dev/null; then
    log_success "Docker daemon is running"
else
    log_error "Docker daemon is not running"
    exit 1
fi

# Check required files and directories
header "Configuration Files Check"

# Create required directories
log_info "Creating required directories..."
mkdir -p data uploads temp_audio logs
log_success "Directories created/verified"

# Make sure we have the production env file
if [ ! -f .env.prod ]; then
    log_error ".env.prod file not found!"
    exit 1
else
    log_success ".env.prod file exists"
fi

# Check for Caddyfile
if [ ! -f Caddyfile ]; then
    log_warning "Caddyfile not found - this is required for the full setup with Caddy"
else
    log_success "Caddyfile exists"
fi

# Check if OpenAI API key is set
if grep -q "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" .env.prod; then
    log_warning "You're using the placeholder API key in .env.prod. For testing to work properly, you should update it with a real key."
    log_info "For the purpose of this test, we'll proceed anyway"
else
    log_success "OpenAI API key appears to be configured in .env.prod"
fi

# Check if ports 8000, 80, and 443 are available
log_info "Checking if required ports are available..."

check_port() {
    local port=$1
    if netstat -tuln | grep -q ":$port "; then
        log_warning "Port $port is already in use. This may cause conflicts."
    else
        log_success "Port $port is available"
    fi
}

check_port 8000
check_port 80
check_port 443

# Build and test the simple setup
header "Testing Simple Docker Setup"

# Ensure any existing containers are stopped
log_info "Stopping any existing containers from previous runs..."
$DOCKER_COMPOSE_CMD -f docker-compose.simple.yml down 2>/dev/null || true

# Build the Docker image
log_info "Building Docker image..."
$DOCKER_COMPOSE_CMD -f docker-compose.simple.yml build

# Start the containers
log_info "Starting containers with docker-compose.simple.yml..."
$DOCKER_COMPOSE_CMD -f docker-compose.simple.yml up -d

# Wait for the application to start
log_info "Waiting for the application to start (15 seconds)..."
sleep 15

# Check if the container is running
log_info "Checking container status..."
CONTAINER_ID=$($DOCKER_COMPOSE_CMD -f docker-compose.simple.yml ps -q app)
if [ -z "$CONTAINER_ID" ]; then
    log_error "Container ID not found. The container may not have started."
    log_info "Checking logs for errors:"
    $DOCKER_COMPOSE_CMD -f docker-compose.simple.yml logs app
    exit 1
fi

CONTAINER_STATUS=$(docker inspect -f '{{.State.Status}}' $CONTAINER_ID)

if [ "$CONTAINER_STATUS" != "running" ]; then
    log_error "Container is not running! Status: $CONTAINER_STATUS"
    log_info "Checking logs for errors:"
    $DOCKER_COMPOSE_CMD -f docker-compose.simple.yml logs app
    exit 1
else
    log_success "Container is running with status: $CONTAINER_STATUS"
fi

# Check Docker health status
HEALTH_STATUS=$(docker inspect -f '{{.State.Health.Status}}' $CONTAINER_ID)
if [ "$HEALTH_STATUS" = "healthy" ]; then
    log_success "Container health check is passing: $HEALTH_STATUS"
elif [ "$HEALTH_STATUS" = "starting" ]; then
    log_warning "Container health check still in initial state: $HEALTH_STATUS"
else
    log_error "Container health check failed: $HEALTH_STATUS"
    log_info "Checking logs for errors:"
    $DOCKER_COMPOSE_CMD -f docker-compose.simple.yml logs app
fi

# Test API endpoints
test_endpoint "http://localhost:8000/" 200 "Home page"
test_endpoint "http://localhost:8000/health" 200 "Health check endpoint"

# Check if health endpoint returns valid JSON with expected fields
health_response=$(curl -s http://localhost:8000/health)
if echo "$health_response" | grep -q '"status":"healthy"'; then
    log_success "Health endpoint returned valid status"
else
    log_error "Health endpoint did not return expected status field"
    log_info "Response: $health_response"
fi

# Print container info
log_info "Application container information:"
$DOCKER_COMPOSE_CMD -f docker-compose.simple.yml ps app

log_info "Container logs:"
$DOCKER_COMPOSE_CMD -f docker-compose.simple.yml logs app --tail 20

log_success "Simple setup test completed"
log_info "To stop the containers, run: $DOCKER_COMPOSE_CMD -f docker-compose.simple.yml down"
log_info "To access the application, visit: http://localhost:8000"

# Ask if user wants to test full setup with Caddy
header "Testing Full Docker Setup with Caddy"

# Check if this is an automated test with no user input
if [ "$1" = "--full" ]; then
    test_caddy="y"
else
    echo -e "${BLUE}Do you want to test the full setup with Caddy? (y/n)${NC}"
    read -r test_caddy
fi

if [ "$test_caddy" = "y" ] || [ "$test_caddy" = "Y" ]; then
    # Stop the simple setup
    log_info "Stopping simple setup containers..."
    $DOCKER_COMPOSE_CMD -f docker-compose.simple.yml down

    # Start the full setup
    log_info "Starting full setup with Caddy..."
    $DOCKER_COMPOSE_CMD up -d
    
    log_info "Waiting for the application to start (15 seconds)..."
    sleep 15
    
    log_info "Containers status:"
    $DOCKER_COMPOSE_CMD ps
    
    # Check if containers are running
    if $DOCKER_COMPOSE_CMD ps | grep -q "caddy"; then
        log_success "Caddy container is running"
    else
        log_error "Caddy container is not running"
    fi
    
    if $DOCKER_COMPOSE_CMD ps | grep -q "app"; then
        log_success "App container is running"
    else
        log_error "App container is not running"
    fi
    
    log_info "Caddy container logs:"
    $DOCKER_COMPOSE_CMD logs caddy --tail 20
    
    log_success "Full setup test completed"
    
    log_info "NOTE: For Caddy to work properly in production, you need to:"
    log_info "1. Update the domain in Caddyfile from 'transcribe.example.com' to your actual domain"
    log_info "2. Ensure your server is reachable on ports 80 and 443"
    log_info "3. Point your domain's DNS records to your server"
    
    log_info "To stop the containers, run: $DOCKER_COMPOSE_CMD down"
else
    log_info "Skipping full setup test"
    log_info "To stop the simple setup containers, run: $DOCKER_COMPOSE_CMD -f docker-compose.simple.yml down"
fi

# Print test results summary
header "Test Results Summary"
echo -e "${GREEN}Tests passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests failed: $TESTS_FAILED${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"

# Final message
if [ $TESTS_FAILED -eq 0 ]; then
    log_success "All Docker tests completed successfully!"
else
    log_error "Some Docker tests failed. Please check the logs for details."
fi

echo -e "${BLUE}Testing completed at: $(date)${NC}"
