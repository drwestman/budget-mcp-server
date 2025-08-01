#!/usr/bin/env python3
"""
SSL Certificate Generation Script for Budget MCP Server

Generates self-signed SSL certificates for development use.
Creates both the private key and certificate files needed for HTTPS.
"""

import socket
import subprocess
import sys
from pathlib import Path


def get_system_hostname() -> str:
    """
    Get the system hostname, falling back to localhost if detection fails.
    
    Returns:
        str: System hostname or 'localhost' as fallback
    """
    try:
        return socket.gethostname()
    except Exception:
        return "localhost"


def generate_self_signed_cert(
    cert_dir: str = "certs", days: int = 365, hostname: str | None = None
) -> None:
    """
    Generate self-signed SSL certificate and private key.

    Args:
        cert_dir (str): Directory to store certificate files
        days (int): Certificate validity period in days
        hostname (str): Hostname to include in certificate (auto-detects system hostname if None)
    """
    # Create certificates directory
    cert_path = Path(cert_dir)
    cert_path.mkdir(exist_ok=True)

    key_file = cert_path / "server.key"
    cert_file = cert_path / "server.crt"
    config_file = cert_path / "cert.conf"

    # Use provided hostname or auto-detect system hostname
    if hostname is None:
        hostname = get_system_hostname()

    print(f"Generating self-signed SSL certificate in {cert_dir}/")
    print(f"Certificate will be valid for {days} days")
    print(f"Certificate hostname: {hostname}")

    # Create OpenSSL config for SAN extensions
    alt_names = [f"DNS.1 = {hostname}"]
    if hostname != "localhost":
        alt_names.append("DNS.2 = localhost")
    alt_names.append("IP.1 = 127.0.0.1")

    san_config = f"""[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = Dev
L = Dev
O = Budget MCP Server
CN = {hostname}

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
{chr(10).join(alt_names)}
"""

    # Write config file
    with open(config_file, "w") as f:
        f.write(san_config)

    # Generate private key and certificate using openssl
    try:
        # Generate private key
        subprocess.run(
            ["openssl", "genrsa", "-out", str(key_file), "2048"],
            check=True,
            capture_output=True,
        )

        # Generate self-signed certificate with SAN
        subprocess.run(
            [
                "openssl",
                "req",
                "-new",
                "-x509",
                "-key",
                str(key_file),
                "-out",
                str(cert_file),
                "-days",
                str(days),
                "-config",
                str(config_file),
                "-extensions",
                "v3_req",
            ],
            check=True,
            capture_output=True,
        )

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
        print(
            "  Windows: Download from https://slproweb.com/products/Win32OpenSSL.html"
        )
        sys.exit(1)
    finally:
        # Clean up config file
        if config_file.exists():
            config_file.unlink()


def main() -> None:
    """Main function to generate SSL certificates."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate self-signed SSL certificates"
    )
    parser.add_argument(
        "--cert-dir",
        default="certs",
        help="Directory to store certificate files (default: certs)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="Certificate validity period in days (default: 365)",
    )
    parser.add_argument(
        "--hostname", help="Hostname to include in certificate (default: auto-detect system hostname)"
    )

    args = parser.parse_args()

    generate_self_signed_cert(args.cert_dir, args.days, args.hostname)


if __name__ == "__main__":
    main()
