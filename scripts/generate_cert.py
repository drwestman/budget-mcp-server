#!/usr/bin/env python3
"""
SSL Certificate Generation Script for Budget MCP Server

Generates self-signed SSL certificates for development use.
Creates both the private key and certificate files needed for HTTPS.
"""
import os
import subprocess
import sys
from pathlib import Path


def generate_self_signed_cert(cert_dir="certs", days=365):
    """
    Generate self-signed SSL certificate and private key.
    
    Args:
        cert_dir (str): Directory to store certificate files
        days (int): Certificate validity period in days
    """
    # Create certificates directory
    cert_path = Path(cert_dir)
    cert_path.mkdir(exist_ok=True)
    
    key_file = cert_path / "server.key"
    cert_file = cert_path / "server.crt"
    
    print(f"Generating self-signed SSL certificate in {cert_dir}/")
    print(f"Certificate will be valid for {days} days")
    
    # Generate private key and certificate using openssl
    try:
        # Generate private key
        subprocess.run([
            "openssl", "genrsa", 
            "-out", str(key_file), 
            "2048"
        ], check=True, capture_output=True)
        
        # Generate self-signed certificate
        subprocess.run([
            "openssl", "req", "-new", "-x509",
            "-key", str(key_file),
            "-out", str(cert_file),
            "-days", str(days),
            "-subj", "/C=US/ST=Dev/L=Dev/O=Budget MCP Server/CN=localhost"
        ], check=True, capture_output=True)
        
        print(f"✓ Private key generated: {key_file}")
        print(f"✓ Certificate generated: {cert_file}")
        print()
        print("To use HTTPS with your MCP server, set these environment variables:")
        print(f"export SSL_CERT_FILE={cert_file.absolute()}")
        print(f"export SSL_KEY_FILE={key_file.absolute()}")
        print("export HTTPS_ENABLED=true")
        print()
        print("⚠️  This is a self-signed certificate for development only!")
        print("   Browsers will show security warnings that you'll need to accept.")
        
    except subprocess.CalledProcessError as e:
        print(f"Error generating certificate: {e}")
        if e.stderr:
            print(f"OpenSSL Error: {e.stderr.decode().strip()}")
        print("Make sure OpenSSL is installed on your system.")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: OpenSSL not found. Please install OpenSSL:")
        print("  Ubuntu/Debian: sudo apt-get install openssl")
        print("  macOS: brew install openssl")
        print("  Windows: Download from https://slproweb.com/products/Win32OpenSSL.html")
        sys.exit(1)


def main():
    """Main function to generate SSL certificates."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate self-signed SSL certificates")
    parser.add_argument("--cert-dir", default="certs", 
                       help="Directory to store certificate files (default: certs)")
    parser.add_argument("--days", type=int, default=365,
                       help="Certificate validity period in days (default: 365)")
    
    args = parser.parse_args()
    
    generate_self_signed_cert(args.cert_dir, args.days)


if __name__ == "__main__":
    main()