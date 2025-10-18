#!/usr/bin/env python3
"""
License key revocation utility for SMCP Business Edition.
"""
import sys
import hmac
import hashlib
import argparse
import json
import os
from datetime import datetime

def revoke_license_key(license_key: str, reason: str = "") -> str:
    """Revoke a license key by adding its hash to the revocation list."""
    # Calculate key hash
    key_hash = hashlib.sha256(license_key.encode()).hexdigest()
    
    # Create revocation entry
    revocation_entry = {
        "hash": key_hash,
        "revoked_at": datetime.utcnow().isoformat() + "Z",
        "reason": reason
    }
    
    return key_hash, revocation_entry

def main():
    parser = argparse.ArgumentParser(description='Revoke SMCP Business Edition license keys')
    parser.add_argument('--key', '-k', required=True, help='License key to revoke')
    parser.add_argument('--reason', '-r', help='Reason for revocation')
    parser.add_argument('--revocation-db', '-d', 
                       default='/var/lib/bizteam/revocation.db',
                       help='Revocation database file')
    parser.add_argument('--output-json', '-o', help='Output revocation list as JSON')
    
    args = parser.parse_args()
    
    try:
        key_hash, revocation_entry = revoke_license_key(args.key, args.reason or "")
        
        # Load existing revocation database
        revocation_list = {}
        if os.path.exists(args.revocation_db):
            try:
                with open(args.revocation_db, 'r') as f:
                    revocation_list = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                revocation_list = {}
        
        # Add new revocation
        revocation_list[key_hash] = revocation_entry
        
        # Save updated database
        os.makedirs(os.path.dirname(args.revocation_db), exist_ok=True)
        with open(args.revocation_db, 'w') as f:
            json.dump(revocation_list, f, indent=2)
        
        print(f"License key revoked: {key_hash[:16]}...")
        print(f"Revocation database updated: {args.revocation_db}")
        
        # Output JSON list if requested
        if args.output_json:
            json_output = {
                "revoked": list(revocation_list.keys()),
                "updated_at": datetime.utcnow().isoformat() + "Z"
            }
            with open(args.output_json, 'w') as f:
                json.dump(json_output, f, indent=2)
            print(f"JSON revocation list written to: {args.output_json}")
        
    except Exception as e:
        print(f"Error revoking license key: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
