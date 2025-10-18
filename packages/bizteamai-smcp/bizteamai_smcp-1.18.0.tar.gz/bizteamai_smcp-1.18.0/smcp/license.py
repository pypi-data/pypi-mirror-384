"""
License verification and core limit enforcement for SMCP Business Edition.
"""
import os
import hmac
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class LicenseError(Exception):
    """Base exception for license-related errors."""
    pass

class LicenseExpiredError(LicenseError):
    """Raised when license has expired."""
    pass

class LicenseInvalidError(LicenseError):
    """Raised when license is invalid or corrupted."""
    pass

class CoreLimitExceededError(LicenseError):
    """Raised when CPU core limit is exceeded."""
    pass

def parse_license_key(key: str) -> dict:
    """Parse and validate license key format."""
    parts = key.strip().split('.')
    if len(parts) != 6 or parts[0] != 'BZT':
        raise LicenseInvalidError("Invalid license key format")
    
    return {
        'prefix': parts[0],
        'customer_id': parts[1],
        'cores': int(parts[2]),
        'expiry_utc': parts[3],
        'nonce': parts[4],
        'signature': parts[5]
    }

def verify_license_signature(key_data: dict, secret: str) -> bool:
    """Verify HMAC-SHA256 signature of license key."""
    payload = f"{key_data['prefix']}.{key_data['customer_id']}.{key_data['cores']}.{key_data['expiry_utc']}.{key_data['nonce']}"
    expected_sig = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_sig, key_data['signature'])

def check_license_expiry(expiry_str: str) -> bool:
    """Check if license has expired (24h grace period)."""
    try:
        expiry_date = datetime.strptime(expiry_str, '%Y%m%d').replace(tzinfo=timezone.utc)
        # Add 24 hour grace period
        grace_expiry = expiry_date.replace(hour=23, minute=59, second=59)
        return datetime.now(timezone.utc) > grace_expiry
    except ValueError:
        raise LicenseInvalidError("Invalid expiry date format")

def load_license_key() -> Optional[str]:
    """Load license key from file or environment variable."""
    # Check environment variable first
    key = os.getenv('BIZTEAM_LICENSE_KEY')
    if key:
        return key
    
    # Check license file
    license_file = os.getenv('BIZTEAM_LICENSE_FILE', '/etc/bizteam/license.txt')
    try:
        with open(license_file, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def verify_license(secret: str) -> Tuple[bool, dict]:
    """
    Verify license and return validity status and license data.
    
    Returns:
        Tuple of (is_valid, license_data)
    """
    license_key = load_license_key()
    if not license_key:
        return False, {}
    
    try:
        key_data = parse_license_key(license_key)
        
        # Verify signature
        if not verify_license_signature(key_data, secret):
            raise LicenseInvalidError("Invalid license signature")
        
        # Check expiry
        if check_license_expiry(key_data['expiry_utc']):
            raise LicenseExpiredError("License has expired")
        
        logger.info(f"License verified for customer {key_data['customer_id']}, cores: {key_data['cores']}")
        return True, key_data
        
    except (LicenseError, ValueError) as e:
        logger.error(f"License verification failed: {e}")
        return False, {}

def get_licensed_cores() -> int:
    """Get the number of licensed cores, or 0 if no valid license."""
    # In production, this would use a proper server secret
    server_secret = os.getenv('BIZTEAM_SERVER_SECRET', 'dev-secret-key')
    is_valid, license_data = verify_license(server_secret)
    return license_data.get('cores', 0) if is_valid else 0
