!/usr/bin/env python3
"""
License key generation utility for SMCP Business Edition.
"""
import sys
import hmac
import hashlib
import secrets
import argparse
from datetime import datetime, timedelta, timezone

def generate_license_key(customer_id: str, cores: int, days: int, secret: str) -> str:
    """Generate a new license key."""
    # Generate expiry date
    expiry_date = datetime.now(timezone.utc) + timedelta(days=days)
    expiry_str = expiry_date.strftime('%Y%m%d')
    
    # Generate random nonce
    nonce = secrets.token_hex(8)
    
    # Create payload for signing
    payload = f"BZT.{customer_id}.{cores}.{expiry_str}.{nonce}"
    
    # Generate HMAC signature
    signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return f"{payload}.{signature}"

def main():
    parser = argparse.ArgumentParser(description='Generate SMCP Business Edition license keys')
    parser.add_argument('--customer', '-c', required=True, help='Customer ID')
    parser.add_argument('--cores', '-n', type=int, required=True, help='Number of cores')
    parser.add_argument('--days', '-d', type=int, required=True, help='Validity period in days')
    parser.add_argument('--secret', '-s', help='Server secret (default: use BIZTEAM_SERVER_SECRET env var)')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    
    args = parser.parse_args()
    
    # Get server secret
    secret = args.secret
    if not secret:
        import os
        secret = os.getenv('BIZTEAM_SERVER_SECRET')
        if not secret:
            print("Error: Server secret required. Use --secret or set BIZTEAM_SERVER_SECRET", file=sys.stderr)
            sys.exit(1)
    
    # Generate key
    try:
        license_key = generate_license_key(args.customer, args.cores, args.days, secret)
        
        # Output
        if args.output:
            with open(args.output, 'w') as f:
                f.write(license_key + '\n')
            print(f"License key written to {args.output}")
        else:
            print(license_key)
            
        # Log for audit (in production, this would go to a database)
        key_hash = hashlib.sha256(license_key.encode()).hexdigest()
        print(f"# Audit: Customer={args.customer}, Cores={args.cores}, Days={args.days}, Hash={key_hash}", file=sys.stderr)
        
    except Exception as e:
        print(f"Error generating license key: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
