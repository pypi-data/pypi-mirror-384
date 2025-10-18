# SMCP Business Edition

Professional secure MCP server implementation with advanced licensing and enterprise features.

## Key Features

- **Core-based Licensing**: License validation based on CPU core usage
- **Runtime Enforcement**: Graceful enforcement with 15-minute grace period
- **Automatic Renewal**: Hot-reload license keys without restarts
- **Revocation Support**: Remote revocation list checking
- **Enterprise Security**: All community features plus advanced compliance
- **Professional Support**: Priority support and SLA guarantees
- **Seamless Upgrade**: Same import (`import smcp`) as community edition

## Installation

### Business Edition
#### From Private PyPI Server
```bash
pip install --extra-index-url https://bizteamai.com/pypi/simple/ smcp-biz
```

#### With Upload Authentication (for contributors)
```bash
# For uploading packages (requires token authentication)
pip install --extra-index-url https://<upload-token>@bizteamai.com/pypi/simple/ bizteam-smcp-biz
```

**Note**: 
- Package name is `smcp-biz` but imports as `smcp` for seamless upgrade from community edition
- Public downloads don't require authentication
- Upload operations require a valid token
- Private PyPI server hosted at `https://bizteamai.com/pypi/`

### Community Edition

The community edition (`bizteam-smcp`) is available on PyPI.org:
```bash
# Community edition from PyPI.org
pip install bizteam-smcp

# Or from private PyPI
pip install --extra-index-url https://bizteamai.com/pypi/simple/  bizteam-smcp
```

## License Configuration

Set your license file path:
```bash
export BIZTEAM_LICENSE_FILE=/etc/bizteam/license.txt
```

Or set the license key directly:
```bash
export BIZTEAM_LICENSE_KEY="BZT.customer.cores.expiry.nonce.signature"
```

## Development Mode

For development and testing:
```bash
export BIZTEAM_DEV_MODE=1  # Disables license checking
```

## Usage

```python
import smcp  # Same import as community edition
# Business edition will be used if installed
```

## CLI Tools

Enhanced CLI tools included:
```bash
smcp-gen-key    # Generate license keys
smcp-approve    # Approve pending actions
smcp-mkcert     # Certificate generation
smcp-revoke     # License revocation
```

## Support

- **Technical Support**: support@bizteamai.com
- **Sales Inquiries**: sales@bizteamai.com
- **GitHub**: https://github.com/bizteamai/smcp-biz

## License

This is commercial software distributed under a proprietary license. A valid license key is required for production use.
