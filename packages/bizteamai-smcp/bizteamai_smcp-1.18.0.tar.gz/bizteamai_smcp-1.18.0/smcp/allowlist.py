"""
Host allowlist validation for outbound connections.
"""

import ipaddress
import re
from typing import Dict, List, Union
from urllib.parse import urlparse


class HostValidationError(Exception):
    """Raised when a host fails allowlist validation."""
    pass


def validate_host(target: str, cfg: Dict[str, Union[str, List[str]]]) -> None:
    """
    Validate that a target host is in the allowlist.
    
    Args:
        target: Target host, URL, or IP address to validate
        cfg: Configuration dictionary containing ALLOWED_HOSTS
        
    Raises:
        HostValidationError: If the host is not in the allowlist
    """
    allowed_hosts = cfg.get("ALLOWED_HOSTS", [])
    if not allowed_hosts:
        return  # No allowlist configured, allow all
    
    # Extract hostname from URL if needed
    hostname = _extract_hostname(target)
    
    # Check against allowlist
    if not _is_host_allowed(hostname, allowed_hosts):
        raise HostValidationError(f"Host '{hostname}' not in allowlist")


def _extract_hostname(target: str) -> str:
    """
    Extract hostname from a target string (URL, hostname, or IP).
    
    Args:
        target: Target string to parse
        
    Returns:
        Extracted hostname or IP address
    """
    # If it looks like a URL, parse it
    if "://" in target:
        parsed = urlparse(target)
        return parsed.hostname or parsed.netloc
    
    # If it contains a port, strip it
    if ":" in target and not _is_ipv6(target):
        return target.split(":")[0]
    
    return target


def _is_ipv6(address: str) -> bool:
    """Check if a string is an IPv6 address."""
    try:
        ipaddress.IPv6Address(address)
        return True
    except ipaddress.AddressValueError:
        return False


def _is_host_allowed(hostname: str, allowed_hosts: List[str]) -> bool:
    """
    Check if a hostname is in the allowlist.
    
    Args:
        hostname: Hostname to check
        allowed_hosts: List of allowed hosts (can include patterns)
        
    Returns:
        True if the hostname is allowed
    """
    for allowed in allowed_hosts:
        if _host_matches(hostname, allowed):
            return True
    return False


def _host_matches(hostname: str, pattern: str) -> bool:
    """
    Check if a hostname matches an allowlist pattern.
    
    Supports:
    - Exact matches: "api.example.com"
    - Wildcard subdomains: "*.example.com"
    - IP addresses: "192.168.1.1"
    - IP ranges: "192.168.1.0/24"
    
    Args:
        hostname: Hostname to check
        pattern: Pattern to match against
        
    Returns:
        True if the hostname matches the pattern
    """
    # Exact match
    if hostname == pattern:
        return True
    
    # Wildcard subdomain match
    if pattern.startswith("*."):
        domain = pattern[2:]
        return hostname.endswith(f".{domain}") or hostname == domain
    
    # IP range match
    if "/" in pattern:
        try:
            network = ipaddress.ip_network(pattern, strict=False)
            address = ipaddress.ip_address(hostname)
            return address in network
        except (ipaddress.AddressValueError, ValueError):
            pass
    
    # Regex pattern match (if pattern contains regex characters)
    if any(char in pattern for char in r"[](){}+?^$|\\"):
        try:
            return bool(re.match(pattern, hostname))
        except re.error:
            pass
    
    return False


def add_host_to_allowlist(cfg: Dict[str, List[str]], host: str) -> None:
    """
    Add a host to the allowlist configuration.
    
    Args:
        cfg: Configuration dictionary to modify
        host: Host to add to the allowlist
    """
    if "ALLOWED_HOSTS" not in cfg:
        cfg["ALLOWED_HOSTS"] = []
    
    if host not in cfg["ALLOWED_HOSTS"]:
        cfg["ALLOWED_HOSTS"].append(host)


def remove_host_from_allowlist(cfg: Dict[str, List[str]], host: str) -> None:
    """
    Remove a host from the allowlist configuration.
    
    Args:
        cfg: Configuration dictionary to modify
        host: Host to remove from the allowlist
    """
    if "ALLOWED_HOSTS" in cfg and host in cfg["ALLOWED_HOSTS"]:
        cfg["ALLOWED_HOSTS"].remove(host)


def get_allowed_hosts(cfg: Dict[str, List[str]]) -> List[str]:
    """
    Get the current allowlist.
    
    Args:
        cfg: Configuration dictionary
        
    Returns:
        List of allowed hosts
    """
    return cfg.get("ALLOWED_HOSTS", [])
