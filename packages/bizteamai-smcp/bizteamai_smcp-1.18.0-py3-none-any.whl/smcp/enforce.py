"""
License enforcement with grace period and core limit checking.
"""
import os
import time
import threading
import logging
from typing import Optional
from .cpu import detect_cores
from .license import get_licensed_cores, CoreLimitExceededError

logger = logging.getLogger(__name__)

class LicenseEnforcer:
    """Handles license enforcement with grace periods."""
    
    def __init__(self):
        self._timer: Optional[threading.Timer] = None
        self._grace_active = False
        self._warned = False
        self._ignore_cores = '--ignore-cores' in os.sys.argv if hasattr(os, 'sys') else False
        
    def check_core_limit(self) -> None:
        """Check if current core usage exceeds license limit."""
        licensed_cores = get_licensed_cores()
        detected_cores = detect_cores()
        
        logger.info(f"SMCP cores licensed={licensed_cores} detected={detected_cores}")
        
        # If no license or ignore flag, allow operation
        if licensed_cores == 0 and not self._ignore_cores:
            logger.warning("No valid license found - running in evaluation mode")
            return
            
        if self._ignore_cores:
            logger.warning("Running with --ignore-cores flag - this is for emergency use only")
            # Start emergency timer (30 seconds)
            threading.Timer(30.0, self._emergency_abort).start()
            return
        
        if detected_cores > licensed_cores:
            if not self._warned:
                logger.warning(f"Core limit exceeded: using {detected_cores} cores, licensed for {licensed_cores}")
                self._warned = True
                self._start_grace_timer()
            elif not self._grace_active:
                # Grace period expired
                raise CoreLimitExceededError(
                    f"Core limit exceeded: using {detected_cores} cores, licensed for {licensed_cores}. "
                    f"Grace period expired."
                )
        else:
            # Within limits - reset warning and cancel timer
            if self._grace_active:
                logger.info("Core usage within limits - grace period cancelled")
                self._cancel_grace_timer()
            self._warned = False
    
    def _start_grace_timer(self) -> None:
        """Start 15-minute grace period timer."""
        if self._timer:
            self._timer.cancel()
        
        self._grace_active = True
        logger.warning("Starting 15-minute grace period for core limit violation")
        self._timer = threading.Timer(15 * 60.0, self._grace_expired)  # 15 minutes
        self._timer.start()
    
    def _cancel_grace_timer(self) -> None:
        """Cancel active grace timer."""
        if self._timer:
            self._timer.cancel()
            self._timer = None
        self._grace_active = False
    
    def _grace_expired(self) -> None:
        """Called when grace period expires."""
        self._grace_active = False
        logger.error("Grace period expired - core limit still exceeded")
        # In a real implementation, this would terminate the process
        # For now, we'll raise an exception
        raise CoreLimitExceededError("Grace period expired - core limit exceeded")
    
    def _emergency_abort(self) -> None:
        """Called when emergency ignore timer expires."""
        logger.error("Emergency operation time expired")
        # Exit after 30 seconds when using --ignore-cores
        os._exit(1)

# Global enforcer instance
_enforcer = LicenseEnforcer()

def check_license_compliance() -> None:
    """Check license compliance - call this at application startup."""
    global _enforcer
    _enforcer.check_core_limit()

def is_licensed() -> bool:
    """Check if application has a valid license."""
    return get_licensed_cores() > 0
