""
CPU core detection for licensing enforcement.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def get_physical_cores() -> int:
    """Get physical CPU core count."""
    try:
        import psutil
        physical = psutil.cpu_count(logical=False)
        if physical is None:
            physical = psutil.cpu_count(logical=True)
        return physical or 1
    except ImportError:
        # Fallback to os.cpu_count if psutil not available
        return os.cpu_count() or 1

def get_cgroup_cores() -> Optional[int]:
    """Get CPU limit from cgroup v2."""
    try:
        with open("/sys/fs/cgroup/cpu.max", "r") as f:
            content = f.read().strip()
            if content == "max":
                return None
            
            parts = content.split()
            if len(parts) >= 2:
                quota = int(parts[0])
                period = int(parts[1])
                return quota // period
            return None
    except (FileNotFoundError, ValueError, PermissionError):
        # Try cgroup v1
        try:
            with open("/sys/fs/cgroup/cpu/cpu.cfs_quota_us", "r") as f:
                quota = int(f.read().strip())
            with open("/sys/fs/cgroup/cpu/cpu.cfs_period_us", "r") as f:
                period = int(f.read().strip())
            
            if quota > 0:
                return quota // period
            return None
        except (FileNotFoundError, ValueError, PermissionError):
            return None

def detect_cores() -> int:
    """
    Detect available CPU cores considering both physical and cgroup limits.
    
    Returns:
        Number of detected cores
    """
    physical = get_physical_cores()
    cgroup = get_cgroup_cores()
    
    if cgroup is not None:
        detected = min(physical, cgroup)
        logger.debug(f"Core detection: physical={physical}, cgroup={cgroup}, detected={detected}")
    else:
        detected = physical
        logger.debug(f"Core detection: physical={physical}, cgroup=None, detected={detected}")
    
    return max(1, detected)  # Ensure at least 1 core
