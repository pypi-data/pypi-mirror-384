"""
Tamper-proof logging with SHA-256 chaining for audit trails.
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class LogChain:
    """
    Append-only logger with SHA-256 chaining for tamper detection.
    
    Each log entry contains a hash of the previous entry, creating
    a chain that can detect tampering anywhere in the log.
    """
    
    def __init__(self, log_path: str):
        """
        Initialize the log chain.
        
        Args:
            log_path: Path to the log file
        """
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_log()
    
    def _initialize_log(self) -> None:
        """Initialize the log file if it doesn't exist."""
        if not self.log_path.exists():
            # Create genesis entry
            genesis_entry = {
                "sequence": 0,
                "timestamp": time.time(),
                "event_type": "genesis",
                "data": "Log chain initialized",
                "previous_hash": "0" * 64,  # Genesis has no previous hash
            }
            genesis_entry["hash"] = self._calculate_hash(genesis_entry)
            
            with open(self.log_path, 'w') as f:
                json.dump([genesis_entry], f, indent=2)
    
    def _calculate_hash(self, entry: Dict[str, Any]) -> str:
        """Calculate SHA-256 hash for a log entry."""
        # Create a copy without the hash field for calculation
        entry_copy = {k: v for k, v in entry.items() if k != "hash"}
        entry_json = json.dumps(entry_copy, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(entry_json.encode()).hexdigest()
    
    def _load_log(self) -> List[Dict[str, Any]]:
        """Load the current log entries."""
        try:
            with open(self.log_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_log(self, entries: List[Dict[str, Any]]) -> None:
        """Save log entries to disk."""
        with open(self.log_path, 'w') as f:
            json.dump(entries, f, indent=2, default=str)
    
    def _get_last_hash(self) -> str:
        """Get the hash of the last log entry."""
        entries = self._load_log()
        return entries[-1]["hash"] if entries else "0" * 64
    
    def append(self, event_type: str, data: Any) -> str:
        """
        Append a new entry to the log chain.
        
        Args:
            event_type: Type of event being logged
            data: Event data to log
            
        Returns:
            Hash of the new entry
        """
        entries = self._load_log()
        sequence = len(entries)
        previous_hash = self._get_last_hash()
        
        entry = {
            "sequence": sequence,
            "timestamp": time.time(),
            "event_type": event_type,
            "data": data,
            "previous_hash": previous_hash,
        }
        entry["hash"] = self._calculate_hash(entry)
        
        entries.append(entry)
        self._save_log(entries)
        
        return entry["hash"]
    
    def verify_chain(self) -> Tuple[bool, Optional[int]]:
        """
        Verify the integrity of the log chain.
        
        Returns:
            Tuple of (is_valid, first_invalid_sequence)
            is_valid is False if tampering is detected
            first_invalid_sequence is the sequence number of the first invalid entry
        """
        entries = self._load_log()
        
        if not entries:
            return True, None
        
        # Verify genesis entry
        if entries[0]["previous_hash"] != "0" * 64:
            return False, 0
        
        # Verify each entry's hash and chain
        for i, entry in enumerate(entries):
            # Verify the entry's own hash
            calculated_hash = self._calculate_hash(entry)
            if calculated_hash != entry["hash"]:
                return False, i
            
            # Verify the chain (except for genesis)
            if i > 0:
                if entry["previous_hash"] != entries[i-1]["hash"]:
                    return False, i
        
        return True, None
    
    def get_entries(self, start_sequence: int = 0, end_sequence: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get log entries in a range.
        
        Args:
            start_sequence: Starting sequence number (inclusive)
            end_sequence: Ending sequence number (inclusive, None for all)
            
        Returns:
            List of log entries in the specified range
        """
        entries = self._load_log()
        
        if end_sequence is None:
            end_sequence = len(entries) - 1
        
        return [entry for entry in entries 
                if start_sequence <= entry["sequence"] <= end_sequence]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the log chain."""
        entries = self._load_log()
        
        if not entries:
            return {"total_entries": 0, "chain_valid": True}
        
        is_valid, invalid_seq = self.verify_chain()
        
        event_types = {}
        for entry in entries:
            event_type = entry["event_type"]
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        return {
            "total_entries": len(entries),
            "chain_valid": is_valid,
            "first_invalid_sequence": invalid_seq,
            "first_entry_time": entries[0]["timestamp"] if entries else None,
            "last_entry_time": entries[-1]["timestamp"] if entries else None,
            "event_type_counts": event_types,
        }


# Global logger instance
_logger = None


def get_logger(cfg: Dict[str, Any]) -> Optional[LogChain]:
    """Get or create the global logger if logging is enabled."""
    global _logger
    
    log_path = cfg.get("LOG_PATH")
    if not log_path:
        return None
    
    if _logger is None:
        _logger = LogChain(log_path)
    
    return _logger


def log_event(function_name: str, args: Tuple, kwargs: Dict[str, Any], result: Any, cfg: Dict[str, Any]) -> None:
    """
    Log a function execution event.
    
    Args:
        function_name: Name of the executed function
        args: Function arguments
        kwargs: Function keyword arguments
        result: Function result
        cfg: Configuration dictionary
    """
    logger = get_logger(cfg)
    if not logger:
        return
    
    # Remove sensitive data from kwargs for logging
    safe_kwargs = {k: v for k, v in kwargs.items() if not k.startswith("_")}
    
    event_data = {
        "function": function_name,
        "args": args,
        "kwargs": safe_kwargs,
        "result_type": type(result).__name__,
        "result_size": len(str(result)) if result is not None else 0,
        "success": True,
    }
    
    logger.append("function_execution", event_data)


def log_security_event(event_type: str, details: Dict[str, Any], cfg: Dict[str, Any]) -> None:
    """
    Log a security-related event.
    
    Args:
        event_type: Type of security event
        details: Event details
        cfg: Configuration dictionary
    """
    logger = get_logger(cfg)
    if not logger:
        return
    
    event_data = {
        "security_event_type": event_type,
        "details": details,
    }
    
    logger.append("security_event", event_data)


def log_error(function_name: str, error: Exception, args: Tuple, kwargs: Dict[str, Any], cfg: Dict[str, Any]) -> None:
    """
    Log an error event.
    
    Args:
        function_name: Name of the function that errored
        error: The exception that occurred
        args: Function arguments
        kwargs: Function keyword arguments
        cfg: Configuration dictionary
    """
    logger = get_logger(cfg)
    if not logger:
        return
    
    safe_kwargs = {k: v for k, v in kwargs.items() if not k.startswith("_")}
    
    event_data = {
        "function": function_name,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "args": args,
        "kwargs": safe_kwargs,
    }
    
    logger.append("function_error", event_data)
