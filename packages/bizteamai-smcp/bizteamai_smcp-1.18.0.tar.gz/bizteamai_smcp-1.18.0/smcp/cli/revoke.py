#!/usr/bin/env python3
"""
License revocation utility for SMCP Business Edition.
"""
import sys
import hashlib
import argparse
import json
import os
from datetime import datetime, timezone

REVOCATION_FILE = '/etc/bizteam/revocation.json'

def load_revocation_list():
    """Load the revocation list."""
    try:
        with open(REVOCATION_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'revoked_keys': [], 'last_updated': None}

def save_revocation_list(revocation_data):
    """Save the revocation list."""
    os.makedirs(os.path.dirname(REVOCATION_FILE), exist_ok=True)
    with open(REVOCATION_FILE, 'w') as f:
        json.dump(revocation_data, f, indent=2)

def revoke_license_key(license_key: str, reason: str = ""):
    """Revoke a license key by adding its hash to the revocation list."""
    key_hash = hashlib.sha256(license_key.encode()).hexdigest()
    
    revocation_data = load_revocation_list()
    
    # Check if already revoked
    for entry in revocation_data['revoked_keys']:
        if entry['hash'] == key_hash:
            print(f"License key already revoked: {key_hash}")
            return
    
    # Add to revocation list
    revocation_data['revoked_keys'].append({
        'hash': key_hash,
        'revoked_at': datetime.now(timezone.utc).isoformat(),
        'reason': reason
    })
    revocation_data['last_updated'] = datetime.now(timezone.utc).isoformat()
    
    save_revocation_list(revocation_data)
    print(f"License key revoked: {key_hash}")

def main():
    parser = argparse.ArgumentParser(description='Revoke SMCP Business Edition license keys')
    parser.add_argument('license_key', help='License key to revoke')
    parser.add_argument('--reason', '-r', default='', help='Reason for revocation')
    parser.add_argument('--list', '-l', action='store_true', help='List all revoked keys')
    
    args = parser.parse_args()
    
    if args.list:
        revocation_data = load_revocation_list()
        print("Revoked license keys:")
        for entry in revocation_data['revoked_keys']:
            print(f"  {entry['hash']} - {entry['revoked_at']} - {entry['reason']}")
        return
    
    try:
        revoke_license_key(args.license_key, args.reason)
    except Exception as e:
        print(f"Error revoking license key: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
