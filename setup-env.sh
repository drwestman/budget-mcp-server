#!/bin/bash

# Budget MCP Server Environment Setup Script
# This script helps you configure the .env file for the Budget MCP Server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
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

# Function to prompt for input with default value
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    
    if [ -n "$default" ]; then
        read -p "$prompt [$default]: " input
        if [ -z "$input" ]; then
            eval "$var_name=\"$default\""
        else
            eval "$var_name=\"$input\""
        fi
    else
        read -p "$prompt: " input
        eval "$var_name=\"$input\""
    fi
}

# Function to generate secure bearer token
generate_bearer_token() {
    if command -v openssl &> /dev/null; then
        openssl rand -hex 32
    else
        # Fallback if openssl is not available
        print_warning "OpenSSL not found. Using fallback method for token generation."
        head -c 32 /dev/urandom | xxd -p -c 32
    fi
}

# Function to backup existing .env file
backup_env_file() {
    if [ -f ".env" ]; then
        local backup_file=".env.backup.$(date +%Y%m%d_%H%M%S)"
        cp ".env" "$backup_file"
        print_info "Backed up existing .env file to $backup_file"
    fi
}

# Function to check if certificates exist
check_certificates() {
    local cert_file="$1"
    local key_file="$2"
    
    if [ -f "$cert_file" ] && [ -f "$key_file" ]; then
        return 0
    else
        return 1
    fi
}

# Function to offer certificate generation
offer_cert_generation() {
    echo
    print_info "HTTPS is enabled but SSL certificates are not found."
    print_info "Expected certificate file: $SSL_CERT_FILE"
    print_info "Expected key file: $SSL_KEY_FILE"
    echo
    
    read -p "Would you like to generate self-signed certificates now? (y/n) [y]: " generate_certs
    generate_certs=${generate_certs:-y}
    
    if [[ "$generate_certs" =~ ^[Yy]$ ]]; then
        if [ -f "scripts/generate_cert.py" ]; then
            print_info "Generating SSL certificates..."
            python3 scripts/generate_cert.py
            if [ $? -eq 0 ]; then
                print_success "SSL certificates generated successfully!"
            else
                print_error "Failed to generate SSL certificates."
                exit 1
            fi
        else
            print_error "Certificate generation script not found: scripts/generate_cert.py"
            print_info "You can manually generate certificates or disable HTTPS."
            exit 1
        fi
    else
        print_warning "HTTPS enabled but no certificates will be generated."
        print_info "Make sure to provide valid SSL certificates before starting the server."
    fi
}

# Main script
echo "======================================================"
echo "    Budget MCP Server Environment Setup Script"
echo "======================================================"
echo
print_info "This script will help you configure the .env file for the Budget MCP Server."
print_info "Press Enter to accept default values shown in brackets."
echo

# Check for existing .env file
if [ -f ".env" ]; then
    print_warning "An existing .env file was found."
    read -p "Do you want to overwrite it? (y/n) [n]: " overwrite
    overwrite=${overwrite:-n}
    
    if [[ "$overwrite" =~ ^[Yy]$ ]]; then
        backup_env_file
        print_info "Proceeding with new configuration..."
    else
        print_info "Exiting without changes."
        exit 0
    fi
fi

# Environment selection
echo
print_info "=== Environment Configuration ==="
echo "1. development (default) - Debug enabled, database reset on start"
echo "2. production - Optimized for production, database persists"
echo "3. testing - In-memory database for testing"
echo

prompt_with_default "Select environment (1-3)" "1" "env_choice"

case "$env_choice" in
    1|"development")
        APP_ENV="development"
        DATABASE_FILE_DEFAULT="budget_app.duckdb"
        ;;
    2|"production")
        APP_ENV="production"
        DATABASE_FILE_DEFAULT="./data/budget_app.duckdb"
        ;;
    3|"testing")
        APP_ENV="testing"
        DATABASE_FILE_DEFAULT=":memory:"
        ;;
    *)
        APP_ENV="development"
        DATABASE_FILE_DEFAULT="budget_app.duckdb"
        print_warning "Invalid choice. Using development environment."
        ;;
esac

# Database configuration
echo
print_info "=== Database Configuration ==="
prompt_with_default "Database file path" "$DATABASE_FILE_DEFAULT" "DATABASE_FILE"

# Bearer token configuration
echo
print_info "=== Authentication Configuration ==="
print_info "Bearer token is required for HTTP transport security."

read -p "Auto-generate secure bearer token? (y/n) [y]: " auto_generate
auto_generate=${auto_generate:-y}

if [[ "$auto_generate" =~ ^[Yy]$ ]]; then
    BEARER_TOKEN=$(generate_bearer_token)
    print_success "Generated secure bearer token: ${BEARER_TOKEN:0:8}..."
else
    prompt_with_default "Enter bearer token (leave empty to disable auth)" "" "BEARER_TOKEN"
fi

# Server configuration
echo
print_info "=== Server Configuration ==="
prompt_with_default "Host address" "127.0.0.1" "HOST"
prompt_with_default "Port number" "8000" "PORT"
prompt_with_default "MCP endpoint path" "/mcp" "MCP_PATH"

# HTTPS configuration
echo
print_info "=== HTTPS Configuration ==="
read -p "Enable HTTPS? (y/n) [n]: " enable_https
enable_https=${enable_https:-n}

if [[ "$enable_https" =~ ^[Yy]$ ]]; then
    HTTPS_ENABLED="true"
    prompt_with_default "SSL certificate file path" "certs/server.crt" "SSL_CERT_FILE"
    prompt_with_default "SSL private key file path" "certs/server.key" "SSL_KEY_FILE"
    
    # Check if certificates exist
    if ! check_certificates "$SSL_CERT_FILE" "$SSL_KEY_FILE"; then
        offer_cert_generation
    fi
else
    HTTPS_ENABLED="false"
    SSL_CERT_FILE="certs/server.crt"
    SSL_KEY_FILE="certs/server.key"
fi

# Create .env file
echo
print_info "=== Creating .env file ==="

cat > .env << EOF
# Budget MCP Server Environment Configuration
# Generated by setup-env.sh on $(date)

# Application Environment
APP_ENV=$APP_ENV

# Database Configuration
DATABASE_FILE=$DATABASE_FILE

# Authentication Configuration
BEARER_TOKEN=$BEARER_TOKEN

# Server Configuration
HOST=$HOST
PORT=$PORT
MCP_PATH=$MCP_PATH

# HTTPS Configuration
HTTPS_ENABLED=$HTTPS_ENABLED
SSL_CERT_FILE=$SSL_CERT_FILE
SSL_KEY_FILE=$SSL_KEY_FILE
EOF

print_success ".env file created successfully!"

# Display configuration summary
echo
print_info "=== Configuration Summary ==="
echo "Environment: $APP_ENV"
echo "Database: $DATABASE_FILE"
echo "Authentication: $([ -n "$BEARER_TOKEN" ] && echo "Enabled" || echo "Disabled")"
echo "Server: $HOST:$PORT$MCP_PATH"
echo "HTTPS: $HTTPS_ENABLED"
if [ "$HTTPS_ENABLED" = "true" ]; then
    echo "SSL Certificate: $SSL_CERT_FILE"
    echo "SSL Key: $SSL_KEY_FILE"
fi

echo
print_info "=== Next Steps ==="
echo "1. Review the generated .env file"
echo "2. Install dependencies: uv sync"
echo "3. Start the server: python3 run.py"
echo "4. For stdio transport (legacy): python3 run_stdio.py"

if [ "$APP_ENV" = "development" ]; then
    echo
    print_info "Development mode notes:"
    echo "- Database will be reset on each server start"
    echo "- Debug logging is enabled"
    echo "- Bearer token authentication warnings are shown if not configured"
fi

if [ "$APP_ENV" = "production" ]; then
    echo
    print_info "Production mode notes:"
    echo "- Bearer token is required for server to start"
    echo "- Database persists between server restarts"
    echo "- Optimized logging levels"
fi

if [ "$HTTPS_ENABLED" = "true" ]; then
    echo
    print_info "HTTPS mode notes:"
    echo "- Self-signed certificates will show browser warnings"
    echo "- For production, use certificates from a trusted CA"
    echo "- Consider using a reverse proxy (nginx, traefik) for production HTTPS"
fi

echo
print_success "Setup complete! Your Budget MCP Server is ready to run."