# HTTPS Setup Guide

This guide explains how to enable HTTPS for the Budget MCP Server using self-signed certificates for development.

## Quick Start

1. **Generate self-signed certificates:**
   ```bash
   python3 scripts/generate_cert.py
   ```

2. **Enable HTTPS:**
   ```bash
   export HTTPS_ENABLED=true
   python3 run.py
   ```

3. **Access the server:**
   ```
   https://127.0.0.1:8443/mcp
   ```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HTTPS_ENABLED` | Enable HTTPS mode | `false` |
| `SSL_CERT_FILE` | Path to SSL certificate file | `certs/server.crt` |
| `SSL_KEY_FILE` | Path to SSL private key file | `certs/server.key` |
| `HOST` | Server host address | `127.0.0.1` |
| `PORT` | Server port | `8000` (HTTP), `8443` (HTTPS) |

## Certificate Generation

### Using the provided script:
```bash
# Generate certificates in default 'certs/' directory
python3 scripts/generate_cert.py

# Generate certificates in custom directory
python3 scripts/generate_cert.py --cert-dir /path/to/certs

# Generate certificates with custom validity period
python3 scripts/generate_cert.py --days 730
```

### Manual certificate generation:
```bash
# Create certificates directory
mkdir -p certs

# Generate private key
openssl genrsa -out certs/server.key 2048

# Generate self-signed certificate
openssl req -new -x509 -key certs/server.key -out certs/server.crt -days 365 \
  -subj "/C=US/ST=Dev/L=Dev/O=Budget MCP Server/CN=localhost"
```

## Docker Setup

### Using Docker Compose

1. **Generate certificates:**
   ```bash
   python3 scripts/generate_cert.py
   ```

2. **Update environment variables in docker-compose.yml:**
   ```yaml
   environment:
     - HTTPS_ENABLED=true
     - PORT=8443  # Use different port for HTTPS
   ```

3. **Run with Docker:**
   ```bash
   # Production profile (default configuration uses HTTPS on port 8443)
   docker compose --profile prod up -d
   
   # Development profile (default configuration uses HTTPS on port 8443)
   docker compose up -d
   ```

### Manual Docker Run

```bash
# Build the image
docker build -t budget-mcp-server .

# Generate certificates
docker run --rm -v budget_certs:/app/certs budget-mcp-server \
  python3 scripts/generate_cert.py --cert-dir /app/certs

# Run with HTTPS
docker run -d \
  -p 8443:8443 \
  -e HTTPS_ENABLED=true \
  -e PORT=8443 \
  -v budget_data:/app/data \
  -v budget_certs:/app/certs \
  budget-mcp-server
```

## Security Considerations

### Development (Self-Signed Certificates)
- ⚠️ **Self-signed certificates will show browser warnings**
- Browsers will require you to accept the security warning
- Not suitable for production use

### Production Setup
For production, use certificates from a trusted Certificate Authority:

1. **Let's Encrypt (free):**
   ```bash
   # Install certbot
   sudo apt-get install certbot

   # Generate certificate
   sudo certbot certonly --standalone -d your-domain.com
   
   # Use the generated certificates
   export SSL_CERT_FILE=/etc/letsencrypt/live/your-domain.com/fullchain.pem
   export SSL_KEY_FILE=/etc/letsencrypt/live/your-domain.com/privkey.pem
   ```

2. **Commercial CA certificates:**
   - Purchase certificates from a trusted CA
   - Update `SSL_CERT_FILE` and `SSL_KEY_FILE` environment variables

## Troubleshooting

### Common Issues

1. **"Address already in use" error:**
   ```bash
   # Use a different port
   PORT=8443 HTTPS_ENABLED=true python3 run.py
   ```

2. **Certificate file not found:**
   ```bash
   # Generate certificates first
   python3 scripts/generate_cert.py
   
   # Or check file paths
   ls -la certs/
   ```

3. **Permission denied accessing certificate files:**
   ```bash
   # Fix file permissions
   chmod 600 certs/server.key
   chmod 644 certs/server.crt
   ```

4. **Browser security warnings:**
   - This is expected with self-signed certificates
   - Click "Advanced" → "Proceed to localhost (unsafe)"
   - Or add certificate to browser's trusted certificates

### Testing HTTPS Connection

```bash
# Test with curl (ignoring certificate validation)
curl -k https://localhost:8443/mcp

# Test with openssl
openssl s_client -connect localhost:8443 -servername localhost
```

## Implementation Details

The HTTPS implementation uses:
- **Custom Uvicorn server** with SSL support
- **FastMCP's `http_app()`** method to get the ASGI application
- **Standard SSL certificate files** (PEM format)
- **SSL context** with proper certificate chain loading

The server automatically detects HTTPS mode and uses the appropriate configuration:
- HTTP mode: Uses FastMCP's built-in server on port 8000
- HTTPS mode: Uses custom Uvicorn server with SSL configuration on port 8443

## Docker Configuration Notes

The default docker-compose.yml configuration now enables HTTPS by default with:
- `HTTPS_ENABLED=true`
- `PORT=8443`
- Certificate volume mounting from `./certs:/app/certs`

This ensures the Docker container has access to SSL certificates and runs in HTTPS mode.