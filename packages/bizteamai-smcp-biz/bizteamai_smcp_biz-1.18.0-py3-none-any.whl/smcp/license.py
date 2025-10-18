"""
License parsing, verification, and management for SMCP Business Edition.
"""
import os
import hmac
import hashlib
import logging
import requests
from datetime import datetime, timezone
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Global license state
_license_info: Optional[Dict[str, Any]] = None
_server_secret = "default-dev-secret-change-in-production"  # Should be from env in production

class LicenseError(Exception):
    """License validation error."""
    pass

def parse_license_key(key: str) -> Dict[str, Any]:
    """
    Parse a license key in format: BZT.<custID>.<cores>.<expiryUTC>.<nonce>.<sig>
    
    Args:
        key: License key string
        
    Returns:
        Dictionary with parsed components
        
    Raises:
        LicenseError: If key format is invalid
    """
    parts = key.strip().split('.')
    if len(parts) != 6 or parts[0] != 'BZT':
        raise LicenseError("Invalid license key format")
    
    try:
        return {
            'prefix': parts[0],
            'customer_id': parts[1],
            'cores': int(parts[2]),
            'expiry': parts[3],
            'nonce': parts[4],
            'signature': parts[5]
        }
    except ValueError as e:
        raise LicenseError(f"Invalid license key data: {e}")

def verify_signature(license_data: Dict[str, Any], secret: str) -> bool:
    """
    Verify the HMAC signature of a license key.
    
    Args:
        license_data: Parsed license data
        secret: Server secret for verification
        
    Returns:
        True if signature is valid
    """
    payload = f"BZT.{license_data['customer_id']}.{license_data['cores']}.{license_data['expiry']}.{license_data['nonce']}"
    
    expected_sig = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_sig, license_data['signature'])

def check_expiry(license_data: Dict[str, Any]) -> bool:
    """
    Check if license has expired (with 24h grace period).
    
    Args:
        license_data: Parsed license data
        
    Returns:
        True if license is still valid
    """
    try:
        expiry_date = datetime.strptime(license_data['expiry'], '%Y%m%d')
        expiry_date = expiry_date.replace(tzinfo=timezone.utc)
        
        # Add 24 hour grace period
        from datetime import timedelta
        grace_expiry = expiry_date + timedelta(hours=24)
        
        now = datetime.now(timezone.utc)
        return now <= grace_expiry
    except ValueError:
        return False

def check_revocation(license_key: str) -> bool:
    """
    Check if license key is revoked by querying remote revocation list.
    
    Args:
        license_key: Full license key
        
    Returns:
        True if license is NOT revoked
    """
    try:
        # Calculate key hash
        key_hash = hashlib.sha256(license_key.encode()).hexdigest()
        
        # Check if revocation checking is disabled
        if os.getenv('BIZTEAM_SKIP_REVOCATION') == '1':
            logger.debug("Revocation checking disabled")
            return True
        
        # Fetch revocation list (with timeout)
        revocation_url = os.getenv('BIZTEAM_REVOCATION_URL', 'https://revocation.bizteam.com/v1/list')
        response = requests.get(revocation_url, timeout=5)
        
        if response.status_code == 200:
            revoked_hashes = response.json().get('revoked', [])
            if key_hash in revoked_hashes:
                logger.warning(f"License key is revoked: {key_hash[:16]}...")
                return False
        else:
            logger.warning(f"Could not check revocation list: HTTP {response.status_code}")
        
        return True
        
    except requests.RequestException as e:
        logger.warning(f"Revocation check failed: {e}")
        # Fail open - allow license if revocation check fails
        return True
    except Exception as e:
        logger.error(f"Unexpected error during revocation check: {e}")
        return True

def load_license_key() -> Optional[str]:
    """
    Load license key from environment or file.
    
    Returns:
        License key string or None if not found
    """
    # Try environment variable first
    key = os.getenv('BIZTEAM_LICENSE_KEY')
    if key:
        return key.strip()
    
    # Try license file
    license_file = os.getenv('BIZTEAM_LICENSE_FILE', '/etc/bizteam/license.txt')
    try:
        with open(license_file, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.error(f"License file not found: {license_file}")
        return None
    except Exception as e:
        logger.error(f"Error reading license file: {e}")
        return None

def verify_license() -> Optional[Dict[str, Any]]:
    """
    Load and verify the license key.
    
    Returns:
        Verified license data or None if invalid
    """
    global _license_info
    
    # Load license key
    key = load_license_key()
    if not key:
        logger.error("No license key found")
        return None
    
    try:
        # Parse license
        license_data = parse_license_key(key)
        
        # Get server secret
        secret = os.getenv('BIZTEAM_SERVER_SECRET', _server_secret)
        
        # Verify signature
        if not verify_signature(license_data, secret):
            logger.error("License signature verification failed")
            return None
        
        # Check expiry
        if not check_expiry(license_data):
            logger.error("License has expired")
            return None
        
        # Check revocation
        if not check_revocation(key):
            logger.error("License has been revoked")
            return None
        
        # Cache license info
        _license_info = license_data
        logger.info(f"License verified for customer {license_data['customer_id']}")
        return license_data
        
    except LicenseError as e:
        logger.error(f"License validation failed: {e}")
        return None

def get_licensed_cores() -> int:
    """
    Get the number of cores licensed.
    
    Returns:
        Number of licensed cores, or 0 if no valid license
    """
    if _license_info:
        return _license_info['cores']
    
    # Try to verify license if not cached
    license_data = verify_license()
    return license_data['cores'] if license_data else 0

def get_customer_id() -> Optional[str]:
    """
    Get the customer ID from the license.
    
    Returns:
        Customer ID or None if no valid license
    """
    if _license_info:
        return _license_info['customer_id']
    
    # Try to verify license if not cached
    license_data = verify_license()
    return license_data['customer_id'] if license_data else None
