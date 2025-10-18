"""
TLS context factory and certificate helpers for mutual TLS authentication.
"""

import ssl
from pathlib import Path
from typing import Dict, Optional


class TLSContextFactory:
    """Factory for creating SSL contexts for mutual TLS authentication."""
    
    @classmethod
    def server_context(cls, cfg: Dict[str, str]) -> ssl.SSLContext:
        """
        Create an SSL context for a server with mutual TLS.
        
        Args:
            cfg: Configuration dictionary containing paths to certificates
            
        Returns:
            Configured SSL context for server-side mutual TLS
            
        Raises:
            FileNotFoundError: If certificate files don't exist
            ssl.SSLError: If certificate loading fails
        """
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        
        # Load server certificate and key
        cert_path = cfg["cert_path"]
        key_path = cfg["key_path"]
        context.load_cert_chain(cert_path, key_path)
        
        # Load CA certificate for client verification
        ca_path = cfg["ca_path"]
        context.load_verify_locations(ca_path)
        
        # Require client certificates
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = False  # We'll validate through CA
        
        return context
    
    @classmethod
    def client_context(cls, cfg: Dict[str, str]) -> ssl.SSLContext:
        """
        Create an SSL context for a client with mutual TLS.
        
        Args:
            cfg: Configuration dictionary containing paths to certificates
            
        Returns:
            Configured SSL context for client-side mutual TLS
        """
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        
        # Load client certificate and key
        cert_path = cfg["cert_path"]
        key_path = cfg["key_path"]
        context.load_cert_chain(cert_path, key_path)
        
        # Load CA certificate for server verification
        ca_path = cfg["ca_path"]
        context.load_verify_locations(ca_path)
        
        # Verify server certificates
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = True
        
        return context


def tls_configured(cfg: Dict[str, str]) -> bool:
    """
    Check if TLS is properly configured.
    
    Args:
        cfg: Configuration dictionary
        
    Returns:
        True if all required TLS configuration is present and files exist
    """
    required_keys = ["ca_path", "cert_path", "key_path"]
    
    # Check if all required keys are present
    if not all(key in cfg for key in required_keys):
        return False
    
    # Check if all certificate files exist
    for key in required_keys:
        path = Path(cfg[key])
        if not path.exists() or not path.is_file():
            return False
    
    return True


def validate_cert_paths(cfg: Dict[str, str]) -> None:
    """
    Validate that certificate paths exist and are readable.
    
    Args:
        cfg: Configuration dictionary containing certificate paths
        
    Raises:
        FileNotFoundError: If any certificate file is missing
        PermissionError: If any certificate file is not readable
    """
    required_keys = ["ca_path", "cert_path", "key_path"]
    
    for key in required_keys:
        if key not in cfg:
            raise FileNotFoundError(f"Missing required TLS configuration: {key}")
        
        path = Path(cfg[key])
        if not path.exists():
            raise FileNotFoundError(f"Certificate file not found: {path}")
        
        if not path.is_file():
            raise FileNotFoundError(f"Certificate path is not a file: {path}")
        
        # Test readability
        try:
            with open(path, 'rb') as f:
                f.read(1)
        except PermissionError:
            raise PermissionError(f"Cannot read certificate file: {path}")


def get_cert_info(cert_path: str) -> Dict[str, str]:
    """
    Extract basic information from a certificate file.
    
    Args:
        cert_path: Path to the certificate file
        
    Returns:
        Dictionary containing certificate information
    """
    try:
        import cryptography.x509
        from cryptography.hazmat.backends import default_backend
        
        with open(cert_path, 'rb') as f:
            cert_data = f.read()
        
        cert = cryptography.x509.load_pem_x509_certificate(cert_data, default_backend())
        
        return {
            "subject": str(cert.subject),
            "issuer": str(cert.issuer),
            "serial_number": str(cert.serial_number),
            "not_valid_before": cert.not_valid_before.isoformat(),
            "not_valid_after": cert.not_valid_after.isoformat(),
        }
    except ImportError:
        return {"error": "cryptography package not available"}
    except Exception as e:
        return {"error": str(e)}
