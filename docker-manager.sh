#!/bin/bash
# Docker management script for Meera Multilingual Grievance System

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
COMPOSE_DEV_FILE="$SCRIPT_DIR/docker-compose.dev.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Check dependencies
check_dependencies() {
    print_header "Checking Dependencies"
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        echo "Please install Docker from https://docs.docker.com/get-docker/"
        exit 1
    fi
    print_success "Docker is installed: $(docker --version)"
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        echo "Please install Docker Compose from https://docs.docker.com/compose/install/"
        exit 1
    fi
    print_success "Docker Compose is installed: $(docker-compose --version)"
    
    echo ""
}

# Build Docker image
build_image() {
    print_header "Building Docker Image"
    
    docker build -t meera-app:latest "$SCRIPT_DIR"
    
    if [ $? -eq 0 ]; then
        print_success "Docker image built successfully"
    else
        print_error "Failed to build Docker image"
        exit 1
    fi
    echo ""
}

# Setup environment
setup_env() {
    print_header "Setting up Environment"
    
    if [ ! -f "$ENV_FILE" ]; then
        print_info "Creating .env file from template..."
        cp "$SCRIPT_DIR/.env.example" "$ENV_FILE"
        print_success ".env file created"
        echo "Please edit .env and add your API keys:"
        print_info "nano $ENV_FILE"
        echo ""
        exit 0
    else
        print_success ".env file already exists"
    fi
    echo ""
}

# Start services
start_services() {
    local mode=${1:-"prod"}
    print_header "Starting Services ($mode mode)"
    
    if [ "$mode" = "dev" ]; then
        docker-compose -f "$COMPOSE_DEV_FILE" up -d
    else
        docker-compose -f "$COMPOSE_FILE" up -d
    fi
    
    if [ $? -eq 0 ]; then
        print_success "Services started successfully"
        
        sleep 5
        echo ""
        print_info "Waiting for services to be ready..."
        
        # Wait for API to be ready
        for i in {1..30}; do
            if curl -s http://localhost:8000/health > /dev/null 2>&1; then
                print_success "API is ready on http://localhost:8000"
                break
            fi
            echo -n "."
            sleep 1
        done
        echo ""
    else
        print_error "Failed to start services"
        exit 1
    fi
    echo ""
}

# Stop services
stop_services() {
    print_header "Stopping Services"
    
    docker-compose -f "$COMPOSE_FILE" stop
    
    if [ $? -eq 0 ]; then
        print_success "Services stopped successfully"
    else
        print_error "Failed to stop services"
        exit 1
    fi
    echo ""
}

# View logs
view_logs() {
    local service=${1:-"meera-main"}
    print_header "Viewing logs for: $service"
    
    docker-compose logs -f "$service"
}

# View status
view_status() {
    print_header "Service Status"
    
    docker-compose ps
    echo ""
}

# Run tests
run_tests() {
    print_header "Running Tests"
    
    docker-compose exec meera-main python test_meera_direct.py
    
    if [ $? -eq 0 ]; then
        print_success "Tests passed"
    else
        print_error "Tests failed"
        exit 1
    fi
    echo ""
}

# Backup database
backup_database() {
    print_header "Backing up Database"
    
    local backup_file="$SCRIPT_DIR/backups/backup_$(date +%Y%m%d_%H%M%S).sql"
    mkdir -p "$SCRIPT_DIR/backups"
    
    docker-compose exec -T postgres pg_dump -U meera grievances > "$backup_file"
    
    if [ $? -eq 0 ]; then
        print_success "Database backed up to: $backup_file"
    else
        print_error "Failed to backup database"
        exit 1
    fi
    echo ""
}

# Restore database
restore_database() {
    local backup_file=$1
    
    if [ -z "$backup_file" ] || [ ! -f "$backup_file" ]; then
        print_error "Backup file not found: $backup_file"
        echo "Usage: $0 restore <backup_file>"
        exit 1
    fi
    
    print_header "Restoring Database from: $backup_file"
    
    docker-compose exec -T postgres psql -U meera grievances < "$backup_file"
    
    if [ $? -eq 0 ]; then
        print_success "Database restored successfully"
    else
        print_error "Failed to restore database"
        exit 1
    fi
    echo ""
}

# Clean up
cleanup() {
    print_header "Cleaning Up"
    
    read -p "This will remove all containers and volumes. Continue? (y/N) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v
        print_success "Cleanup completed"
    else
        print_info "Cleanup cancelled"
    fi
    echo ""
}

# Health check
health_check() {
    print_header "Health Check"
    
    # API health
    print_info "Checking API health..."
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "API is healthy"
    else
        print_error "API is not responding"
    fi
    
    # Database health
    print_info "Checking Database health..."
    if docker-compose exec -T postgres pg_isready -U meera > /dev/null 2>&1; then
        print_success "Database is healthy"
    else
        print_error "Database is not responding"
    fi
    
    # Redis health
    print_info "Checking Redis health..."
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        print_success "Redis is healthy"
    else
        print_error "Redis is not responding"
    fi
    
    echo ""
}

# Show help
show_help() {
    cat << EOF
${BLUE}Meera Docker Management Script${NC}

Usage: $0 <command> [options]

Commands:
    setup              Setup environment and configuration
    build              Build Docker image
    start [dev|prod]   Start services (default: production)
    stop               Stop services
    status             Show service status
    logs [service]     View service logs (default: meera-main)
    test               Run test suite
    health             Check service health
    backup             Backup database
    restore <file>     Restore database from backup
    clean              Remove all containers and volumes
    shell <service>    Open shell in service container
    help               Show this help message

Examples:
    $0 setup
    $0 build
    $0 start dev
    $0 logs meera-main
    $0 test
    $0 health
    $0 backup
    $0 restore backups/backup_20260327_133530.sql
    $0 shell meera-main

Environment:
    Set API keys in .env file before running start

Services:
    - meera-main: Main API server (port 8000)
    - postgres: PostgreSQL database (port 5432)
    - redis: Redis cache (port 6379)
    - pgadmin: Database UI (port 5050) - dev only
    - redis-commander: Cache UI (port 8081) - dev only

EOF
}

# Main script logic
main() {
    local command=${1:-"help"}
    
    case "$command" in
        setup)
            check_dependencies
            setup_env
            ;;
        build)
            check_dependencies
            build_image
            ;;
        start)
            check_dependencies
            setup_env
            start_services "${2:-prod}"
            ;;
        stop)
            stop_services
            ;;
        status)
            view_status
            ;;
        logs)
            view_logs "${2:-meera-main}"
            ;;
        test)
            run_tests
            ;;
        health)
            health_check
            ;;
        backup)
            backup_database
            ;;
        restore)
            restore_database "$2"
            ;;
        shell)
            docker-compose exec "${2:-meera-main}" bash
            ;;
        clean)
            cleanup
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            echo "Run '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
