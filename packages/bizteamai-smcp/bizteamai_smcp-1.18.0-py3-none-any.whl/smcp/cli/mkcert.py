#!/usr/bin/env python3
"""
Certificate generation tool for SMCP.

Creates a private CA and generates server/client certificates for mutual TLS.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

try:
    from cryptography import x509
    from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from datetime import datetime, timedelta
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


def generate_private_key() -> "rsa.RSAPrivateKey":
    """Generate a new RSA private key."""
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )


def create_ca_certificate(
    private_key: "rsa.RSAPrivateKey", 
    ca_name: str, 
    days: int = 365
) -> "x509.Certificate":
    """Create a self-signed CA certificate."""
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SMCP"),
        x509.NameAttribute(NameOID.COMMON_NAME, ca_name),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=days)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName(ca_name),
        ]),
        critical=False,
    ).add_extension(
        x509.BasicConstraints(ca=True, path_length=None),
        critical=True,
    ).add_extension(
        x509.KeyUsage(
            digital_signature=True,
            content_commitment=False,
            key_encipherment=False,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=True,
            crl_sign=True,
            encipher_only=False,
            decipher_only=False,
        ),
        critical=True,
    ).sign(private_key, hashes.SHA256())
    
    return cert


def create_server_certificate(
    private_key: "rsa.RSAPrivateKey",
    ca_cert: "x509.Certificate",
    ca_private_key: "rsa.RSAPrivateKey",
    server_name: str,
    days: int = 365
) -> "x509.Certificate":
    """Create a server certificate signed by the CA."""
    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SMCP"),
        x509.NameAttribute(NameOID.COMMON_NAME, server_name),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        ca_cert.subject
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=days)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName(server_name),
            x509.DNSName("localhost"),
            x509.IPAddress("127.0.0.1"),
        ]),
        critical=False,
    ).add_extension(
        x509.BasicConstraints(ca=False, path_length=None),
        critical=True,
    ).add_extension(
        x509.KeyUsage(
            digital_signature=True,
            content_commitment=False,
            key_encipherment=True,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=False,
            crl_sign=False,
            encipher_only=False,
            decipher_only=False,
        ),
        critical=True,
    ).add_extension(
        x509.ExtendedKeyUsage([
            ExtendedKeyUsageOID.SERVER_AUTH,
        ]),
        critical=True,
    ).sign(ca_private_key, hashes.SHA256())
    
    return cert


def create_client_certificate(
    private_key: "rsa.RSAPrivateKey",
    ca_cert: "x509.Certificate", 
    ca_private_key: "rsa.RSAPrivateKey",
    client_name: str,
    days: int = 365
) -> "x509.Certificate":
    """Create a client certificate signed by the CA."""
    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SMCP"),
        x509.NameAttribute(NameOID.COMMON_NAME, client_name),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        ca_cert.subject
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=days)
    ).add_extension(
        x509.BasicConstraints(ca=False, path_length=None),
        critical=True,
    ).add_extension(
        x509.KeyUsage(
            digital_signature=True,
            content_commitment=False,
            key_encipherment=True,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=False,
            crl_sign=False,
            encipher_only=False,
            decipher_only=False,
        ),
        critical=True,
    ).add_extension(
        x509.ExtendedKeyUsage([
            ExtendedKeyUsageOID.CLIENT_AUTH,
        ]),
        critical=True,
    ).sign(ca_private_key, hashes.SHA256())
    
    return cert


def save_private_key(private_key: "rsa.RSAPrivateKey", path: Path) -> None:
    """Save a private key to a PEM file."""
    with open(path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    os.chmod(path, 0o600)  # Make private key readable only by owner


def save_certificate(cert: "x509.Certificate", path: Path) -> None:
    """Save a certificate to a PEM file."""
    with open(path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))


def generate_certificates(
    output_dir: Path,
    ca_name: str,
    server_name: str,
    client_name: Optional[str] = None,
    days: int = 365
) -> None:
    """Generate a complete certificate set."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating certificates in {output_dir}")
    
    # Generate CA
    print("1. Generating CA private key...")
    ca_private_key = generate_private_key()
    save_private_key(ca_private_key, output_dir / "ca-key.pem")
    
    print("2. Creating CA certificate...")
    ca_cert = create_ca_certificate(ca_private_key, ca_name, days)
    save_certificate(ca_cert, output_dir / "ca.pem")
    
    # Generate server certificate
    print("3. Generating server private key...")
    server_private_key = generate_private_key()
    save_private_key(server_private_key, output_dir / "server-key.pem")
    
    print("4. Creating server certificate...")
    server_cert = create_server_certificate(
        server_private_key, ca_cert, ca_private_key, server_name, days
    )
    save_certificate(server_cert, output_dir / "server.pem")
    
    # Generate client certificate if requested
    if client_name:
        print("5. Generating client private key...")
        client_private_key = generate_private_key()
        save_private_key(client_private_key, output_dir / "client-key.pem")
        
        print("6. Creating client certificate...")
        client_cert = create_client_certificate(
            client_private_key, ca_cert, ca_private_key, client_name, days
        )
        save_certificate(client_cert, output_dir / "client.pem")
    
    print("\nCertificate generation complete!")
    print(f"Files created in {output_dir}:")
    print("  ca.pem           - CA certificate")
    print("  ca-key.pem       - CA private key")
    print("  server.pem       - Server certificate")
    print("  server-key.pem   - Server private key")
    if client_name:
        print("  client.pem       - Client certificate")
        print("  client-key.pem   - Client private key")
    
    print(f"\nCertificates valid for {days} days")


def main() -> None:
    """Main entry point for the mkcert CLI tool."""
    if not CRYPTOGRAPHY_AVAILABLE:
        print("Error: cryptography package is required for certificate generation")
        print("Install it with: pip install cryptography")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(
        description="Generate certificates for SMCP mutual TLS"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=Path("./certs"),
        help="Output directory for certificates (default: ./certs)"
    )
    parser.add_argument(
        "--ca-name",
        default="SMCP-CA",
        help="Name for the Certificate Authority (default: SMCP-CA)"
    )
    parser.add_argument(
        "--server-name",
        default="smcp-server",
        help="Server name for certificate (default: smcp-server)"
    )
    parser.add_argument(
        "--client-name",
        help="Client name for certificate (optional)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="Certificate validity period in days (default: 365)"
    )
    
    args = parser.parse_args()
    
    try:
        generate_certificates(
            output_dir=args.output_dir,
            ca_name=args.ca_name,
            server_name=args.server_name,
            client_name=args.client_name,
            days=args.days
        )
    except Exception as e:
        print(f"Error generating certificates: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
