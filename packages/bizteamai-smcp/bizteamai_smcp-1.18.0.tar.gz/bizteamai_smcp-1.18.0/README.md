# SMCP - Secure Model Context Protocol

A security-focused wrapper library for MCP (Model Context Protocol) servers, providing multiple layers of protection through conditional guards that activate only when needed.

## Features

- **Conditional Security Guards**: Each security layer activates only when its required configuration is present
- **Mutual TLS Support**: Automatic certificate-based authentication
- **Host Allowlisting**: Outbound connection validation
- **Input Sanitization**: Prompt and parameter filtering
- **Destructive Action Confirmation**: Queue-based approval system for dangerous operations
- **Tamper-proof Logging**: SHA-chained append-only audit logs
- **Universal Coverage**: Same decorator factory works for tools, prompts, and retrieval

## Quick Start

```python
from smcp import FastSMCP as FastMCP
from smcp import tool, prompt

# Configure security features (all optional)
cfg = {
    "ca_path": "ca.pem",
    "cert_path": "server.pem", 
    "key_path": "server.key",
    "ALLOWED_HOSTS": ["api.internal.local", "10.0.0.5"],
    "SAFE_RE": r"^[\w\s.,:;!?-]{1,2048}$",
    "LOG_PATH": "/var/log/smcp.log"
}

app = FastMCP("myserver", smcp_cfg=cfg)

@tool(confirm=True)  # Requires approval
def delete_user(uid: str):
    ...

@prompt()  # Auto-filtered if SAFE_RE present
def chat(prompt: str):
    ...
```

## Security Guards

| Feature | Activation Trigger | Purpose |
|---------|-------------------|---------|
| Mutual TLS | `ca_path`, `cert_path`, `key_path` in config | Certificate-based authentication |
| Host Allowlist | Non-empty `ALLOWED_HOSTS` | Outbound connection validation |
| Input Filtering | `SAFE_RE` or `MAX_LEN` defined | Sanitize prompts and parameters |
| Action Confirmation | `confirm=True` on decorator | Queue destructive operations for approval |
| Audit Logging | `LOG_PATH` set | Tamper-proof operation logging |

## CLI Tools

```bash
# Generate certificates
smcp-mkcert --ca-name "MyCA" --server-name "myserver.local"

# Approve queued actions  
smcp-approve <action-id>
```

## Installation

### From PyPI.org (Public)

```bash
pip install bizteam-smcp
```

### From Private PyPI Server

```bash
# Using private PyPI server
pip install --extra-index-url https://bizteamai.com/pypi/simple/ bizteam-smcp
```

### Upgrading to Business Edition

For additional features and enterprise support, a business edition is available:

```bash
pip install --extra-index-url https://bizteamai.com/pypi/simple/ bizteam-smcp-biz
```

**Contact**: [business@bizteamai.com](mailto:business@bizteamai.com) for more information.

## License

MIT License
