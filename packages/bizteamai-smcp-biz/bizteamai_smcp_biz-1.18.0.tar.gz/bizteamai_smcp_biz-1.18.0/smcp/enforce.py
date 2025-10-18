"""
License enforcement with grace period and core monitoring.
"""
import os
import sys
import time
import threading
import logging
from typing import Optional

from .cpu import detect_cores
from .license import get_licensed_cores, get_customer_id

logger = logging.getLogger(__name__)

class EnforcementTimer:
    """Manages the 15-minute grace period timer."""
    
    def __init__(self):
        self._timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()
        self._violations_logged = set()
    
    def start_timer(self, used_cores: int, licensed_cores: int):
        """Start or restart the 15-minute grace period timer."""
        with self._lock:
            # Cancel existing timer
            if self._timer:
                self._timer.cancel()
            
            # Log violation (once per cores combination)
            violation_key = f"{used_cores}>{licensed_cores}"
            if violation_key not in self._violations_logged:
                logger.warning(
                    f"License violation: using {used_cores} cores, licensed for {licensed_cores}. "
                    f"Grace period: 15 minutes."
                )
                self._violations_logged.add(violation_key)
            
            # Start new timer for 15 minutes (900 seconds)
            self._timer = threading.Timer(900.0, self._enforce_shutdown)
            self._timer.daemon = True
            self._timer.start()
            logger.info("Grace period timer started (15 minutes)")
    
    def cancel_timer(self):
        """Cancel the grace period timer."""
        with self._lock:
            if self._timer:
                self._timer.cancel()
                self._timer = None
                logger.info("Grace period timer cancelled - back within license limits")
    
    def _enforce_shutdown(self):
        """Called when grace period expires."""
        customer_id = get_customer_id() or "unknown"
        used_cores = detect_cores()
        licensed_cores = get_licensed_cores()
        
        logger.error(
            f"License enforcement: Grace period expired. "
            f"Customer: {customer_id}, Used: {used_cores}, Licensed: {licensed_cores}"
        )
        
        # Check for emergency override
        if os.getenv('BIZTEAM_EMERGENCY_OVERRIDE') == '1':
            logger.critical("EMERGENCY OVERRIDE ACTIVE - Continuing with unlicensed usage")
            # Exit after 30 seconds as specified
            threading.Timer(30.0, lambda: os._exit(1)).start()
            return
        
        # Force shutdown
        logger.critical("Shutting down due to license violation")
        os._exit(1)

# Global enforcement timer instance
_enforcement_timer = EnforcementTimer()

def check_compliance() -> bool:
    """
    Check if current core usage is within license limits.
    
    Returns:
        True if compliant, False if in violation
    """
    used_cores = detect_cores()
    licensed_cores = get_licensed_cores()
    customer_id = get_customer_id() or "unknown"
    
    # Log current status
    logger.info(f"bizteam cores licensed={licensed_cores} used={used_cores}")
    
    if used_cores <= licensed_cores:
        # Within limits - cancel any active timer
        _enforcement_timer.cancel_timer()
        return True
    else:
        # Violation - start/restart timer
        _enforcement_timer.start_timer(used_cores, licensed_cores)
        return False

def start_enforcement():
    """Start the enforcement monitoring system."""
    # Check for emergency flags
    if os.getenv('BIZTEAM_IGNORE_CORES') == '1':
        logger.warning("Core enforcement disabled via BIZTEAM_IGNORE_CORES")
        # Still log usage but don't enforce
        used_cores = detect_cores()
        licensed_cores = get_licensed_cores()
        logger.warning(f"UNLICENSED USAGE: cores used={used_cores}, licensed={licensed_cores}")
        # Exit after 30 seconds as specified for emergency runs
        threading.Timer(30.0, lambda: os._exit(0)).start()
        return
    
    # Initial compliance check
    compliant = check_compliance()
    
    if not compliant:
        logger.warning("Starting in license violation state")
    
    # Start periodic monitoring (every 30 seconds)
    def monitor_loop():
        while True:
            time.sleep(30)
            try:
                check_compliance()
            except Exception as e:
                logger.error(f"Error during compliance check: {e}")
    
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()
    logger.info("License enforcement monitoring started")
