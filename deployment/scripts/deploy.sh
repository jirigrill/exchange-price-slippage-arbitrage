#!/bin/bash

# Bitcoin Arbitrage Monitor - Enhanced Deployment Script
# Supports multiple deployment profiles with optional monitoring and analytics services

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DOCKER_DIR="$PROJECT_ROOT/deployment/docker"

# Default deployment profile
DEPLOYMENT_PROFILE=""
GRAFANA_ENABLED=false
JUPYTER_ENABLED=false
INTERACTIVE_MODE=true

# Print colored output
print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${PURPLE}🚀 $1${NC}"
}

# Show usage information
show_usage() {
    echo "Bitcoin Arbitrage Monitor - Deployment Script"
    echo ""
    echo "Usage: $0 [OPTIONS] [PROFILE]"
    echo ""
    echo "PROFILES:"
    echo "  basic      - Core arbitrage monitoring only (default)"
    echo "  monitoring - Core + Grafana dashboards"
    echo "  analytics  - Core + Jupyter notebooks"
    echo "  full       - All services (Core + Grafana + Jupyter)"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help     Show this help message"
    echo "  -g, --grafana  Enable Grafana monitoring (can be combined with other profiles)"
    echo "  -j, --jupyter  Enable Jupyter analytics (can be combined with other profiles)"
    echo "  -y, --yes      Non-interactive mode (skip prompts)"
    echo ""
    echo "EXAMPLES:"
    echo "  $0                    # Interactive deployment (prompts for profile)"
    echo "  $0 basic              # Deploy core monitoring only"
    echo "  $0 monitoring         # Deploy with Grafana dashboards"
    echo "  $0 full               # Deploy all services"
    echo "  $0 basic --grafana    # Deploy core + Grafana"
    echo "  $0 -y monitoring      # Non-interactive monitoring deployment"
    echo ""
    echo "SERVICES:"
    echo "  • Core Arbitrage Monitor - Always included"
    echo "  • TimescaleDB Database - Always included"
    echo "  • Grafana Dashboards - Optional (port 3000)"
    echo "  • Jupyter Analytics - Optional (port 8888)"
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -g|--grafana)
                GRAFANA_ENABLED=true
                shift
                ;;
            -j|--jupyter)
                JUPYTER_ENABLED=true
                shift
                ;;
            -y|--yes)
                INTERACTIVE_MODE=false
                shift
                ;;
            basic|monitoring|analytics|full)
                DEPLOYMENT_PROFILE="$1"
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Interactive profile selection
select_deployment_profile() {
    if [[ "$INTERACTIVE_MODE" == "false" && -z "$DEPLOYMENT_PROFILE" ]]; then
        DEPLOYMENT_PROFILE="basic"
        return
    fi

    if [[ -z "$DEPLOYMENT_PROFILE" && "$INTERACTIVE_MODE" == "true" ]]; then
        echo ""
        print_header "Select Deployment Profile"
        echo ""
        echo "1) Basic      - Core arbitrage monitoring + database"
        echo "2) Monitoring - Core + Grafana dashboards (recommended for production)"
        echo "3) Analytics  - Core + Jupyter notebooks (for data analysis)"
        echo "4) Full       - All services (Core + Grafana + Jupyter)"
        echo ""
        
        while true; do
            read -p "Enter your choice (1-4) [default: 1]: " choice
            case $choice in
                1|"")
                    DEPLOYMENT_PROFILE="basic"
                    break
                    ;;
                2)
                    DEPLOYMENT_PROFILE="monitoring"
                    break
                    ;;
                3)
                    DEPLOYMENT_PROFILE="analytics"
                    break
                    ;;
                4)
                    DEPLOYMENT_PROFILE="full"
                    break
                    ;;
                *)
                    print_warning "Please enter 1, 2, 3, or 4"
                    ;;
            esac
        done
    fi

    # Set services based on profile
    case "$DEPLOYMENT_PROFILE" in
        basic)
            # Core services only (already set as defaults)
            ;;
        monitoring)
            GRAFANA_ENABLED=true
            ;;
        analytics)
            JUPYTER_ENABLED=true
            ;;
        full)
            GRAFANA_ENABLED=true
            JUPYTER_ENABLED=true
            ;;
        *)
            DEPLOYMENT_PROFILE="basic"
            ;;
    esac
}

# Check system requirements
check_requirements() {
    print_status "Checking system requirements..."

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first:"
        echo "   curl -fsSL https://get.docker.com -o get-docker.sh"
        echo "   sudo sh get-docker.sh"
        exit 1
    fi

    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker:"
        echo "   On macOS: Start Docker Desktop application"
        echo "   On Linux: sudo systemctl start docker"
        exit 1
    fi

    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first:"
        echo "   sudo apt install docker-compose"
        echo "   # or"
        echo "   sudo curl -L \"https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose"
        echo "   sudo chmod +x /usr/local/bin/docker-compose"
        exit 1
    fi

    print_success "All requirements satisfied"
}

# Setup environment and directories
setup_environment() {
    print_status "Setting up environment..."

    # Create necessary directories
    mkdir -p "$PROJECT_ROOT/logs"
    mkdir -p "$PROJECT_ROOT/data"
    
    # Copy environment file if it doesn't exist
    if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
        print_status "Creating .env file from template..."
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        print_warning "Please edit .env file with your configuration!"
        echo "   Key settings to configure:"
        echo "   - TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID (for alerts)"
        echo "   - Exchange API keys (optional, for enhanced features)"
        echo "   - MIN_PROFIT_PERCENTAGE (default: 0.1%)"
        echo ""
        
        if [[ "$INTERACTIVE_MODE" == "true" ]]; then
            read -p "Press Enter after editing .env file (or Ctrl+C to exit)..."
        else
            print_warning "Running in non-interactive mode. Please edit .env manually if needed."
        fi
    else
        print_success "Environment file (.env) already exists"
    fi

    # Change to Docker directory for compose operations
    cd "$DOCKER_DIR"
}

# Build and deploy services
deploy_services() {
    print_header "Deploying Bitcoin Arbitrage Monitor ($DEPLOYMENT_PROFILE profile)"
    
    # Build the Docker image
    print_status "Building Docker image..."
    docker-compose build

    # Prepare compose command based on enabled services
    COMPOSE_CMD="docker-compose"
    COMPOSE_FILES="-f docker-compose.yml"
    
    if [[ "$GRAFANA_ENABLED" == "true" ]]; then
        COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.grafana.yml"
    fi
    
    if [[ "$JUPYTER_ENABLED" == "true" ]]; then
        COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.jupyter.yml"
    fi

    # Start services
    print_status "Starting services..."
    eval "$COMPOSE_CMD $COMPOSE_FILES up -d"

    # Wait for services to start
    print_status "Waiting for services to start..."
    sleep 10

    # Check service health
    check_service_health
}

# Check if services are running properly
check_service_health() {
    print_status "Checking service health..."

    # Check core arbitrage monitor
    if docker-compose ps arbitrage-monitor | grep -q "Up"; then
        print_success "Core arbitrage monitor is running"
    else
        print_error "Core arbitrage monitor failed to start"
        show_logs_and_exit
    fi

    # Check TimescaleDB
    if docker-compose ps timescaledb | grep -q "Up"; then
        print_success "TimescaleDB is running"
    else
        print_error "TimescaleDB failed to start"
        show_logs_and_exit
    fi

    # Check optional services
    if [[ "$GRAFANA_ENABLED" == "true" ]]; then
        if eval "docker-compose -f docker-compose.yml -f docker-compose.grafana.yml ps grafana" | grep -q "Up"; then
            print_success "Grafana is running"
        else
            print_warning "Grafana failed to start (check logs)"
        fi
    fi

    if [[ "$JUPYTER_ENABLED" == "true" ]]; then
        if eval "docker-compose -f docker-compose.jupyter.yml ps jupyter" | grep -q "Up"; then
            print_success "Jupyter is running"
        else
            print_warning "Jupyter failed to start (check logs)"
        fi
    fi
}

# Show logs and exit on critical failure
show_logs_and_exit() {
    print_error "Critical services failed to start. Showing logs:"
    docker-compose logs --tail=50
    exit 1
}

# Display deployment summary
show_deployment_summary() {
    echo ""
    print_header "Deployment Complete!"
    echo ""
    print_success "Bitcoin Arbitrage Monitor is running successfully!"
    echo ""
    
    echo -e "${CYAN}📊 Active Services:${NC}"
    echo "  • Core Arbitrage Monitor"
    echo "  • TimescaleDB Database"
    
    if [[ "$GRAFANA_ENABLED" == "true" ]]; then
        echo "  • Grafana Monitoring Dashboard"
    fi
    
    if [[ "$JUPYTER_ENABLED" == "true" ]]; then
        echo "  • Jupyter Analytics Notebooks"
    fi
    echo ""

    echo -e "${CYAN}🌐 Service URLs:${NC}"
    
    if [[ "$GRAFANA_ENABLED" == "true" ]]; then
        echo "  📊 Grafana Dashboard: http://localhost:3000"
        echo "      Default login: admin/admin"
    fi
    
    if [[ "$JUPYTER_ENABLED" == "true" ]]; then
        echo "  📓 Jupyter Notebooks: http://localhost:8888"
        echo "      Token: Check .env file for JUPYTER_TOKEN"
    fi
    echo ""

    echo -e "${CYAN}🛠️  Management Commands:${NC}"
    echo "  View live logs:      cd $DOCKER_DIR && docker-compose logs -f"
    echo "  Stop all services:   cd $DOCKER_DIR && docker-compose down"
    
    if [[ "$GRAFANA_ENABLED" == "true" || "$JUPYTER_ENABLED" == "true" ]]; then
        STOP_CMD="docker-compose"
        if [[ "$GRAFANA_ENABLED" == "true" ]]; then
            STOP_CMD="$STOP_CMD -f docker-compose.grafana.yml"
        fi
        if [[ "$JUPYTER_ENABLED" == "true" ]]; then
            STOP_CMD="$STOP_CMD -f docker-compose.jupyter.yml"
        fi
        echo "  Stop all services:   cd $DOCKER_DIR && $STOP_CMD down"
    fi
    
    echo "  Restart services:    cd $DOCKER_DIR && docker-compose restart"
    echo "  Update & restart:    git pull && cd $DOCKER_DIR && docker-compose build && docker-compose up -d"
    echo "  Access container:    cd $DOCKER_DIR && docker-compose exec arbitrage-monitor bash"
    echo ""

    echo -e "${CYAN}📋 Quick Status Check:${NC}"
    docker-compose ps
    echo ""

    echo -e "${CYAN}📈 Recent Logs:${NC}"
    docker-compose logs --tail=10 arbitrage-monitor
}

# Main deployment flow
main() {
    # Clear screen for better presentation
    clear
    
    print_header "Bitcoin Arbitrage Monitor - Deployment Script"
    echo ""

    # Parse command line arguments
    parse_arguments "$@"

    # Interactive profile selection if needed
    select_deployment_profile

    # Check system requirements
    check_requirements

    # Setup environment
    setup_environment

    # Deploy services
    deploy_services

    # Show deployment summary
    show_deployment_summary
}

# Run main function with all arguments
main "$@"