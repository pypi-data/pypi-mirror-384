"""
FastSMCP subclass with integrated security features.
"""

from typing import Any, Dict, Optional

try:
    from fastmcp import FastMCP as SDKFastMCP
except ImportError:
    # Fallback for testing or when fastmcp is not available
    class SDKFastMCP:
        def __init__(self, *args, **kwargs):
            self.name = args[0] if args else "unknown"
        
        def run(self, **kwargs):
            print(f"Running {self.name} with transport")

from .tls import TLSContextFactory, tls_configured


class FastSMCP(SDKFastMCP):
    """
    Security-enhanced FastMCP server with conditional TLS and configuration injection.
    
    Automatically enables TLS when certificates are configured and injects
    security configuration into all decorated functions.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Initialize FastSMCP with security configuration.
        
        Args:
            *args: Positional arguments passed to FastMCP
            **kwargs: Keyword arguments, including optional smcp_cfg
        """
        # Extract SMCP configuration
        self.smcp_cfg = kwargs.pop("smcp_cfg", {})
        
        # Initialize base FastMCP
        super().__init__(*args, **kwargs)
        
        # Setup TLS if configured
        if tls_configured(self.smcp_cfg):
            self._setup_tls()
    
    def _setup_tls(self) -> None:
        """Setup TLS context if certificates are configured."""
        try:
            self._tls_context = TLSContextFactory.server_context(self.smcp_cfg)
        except Exception as e:
            print(f"Warning: Failed to setup TLS: {e}")
            self._tls_context = None
    
    def run(self, transport: str = "tcp", **kwargs) -> None:
        """
        Run the server with security enhancements.
        
        Args:
            transport: Transport protocol to use
            **kwargs: Additional keyword arguments for the server
        """
        # Inject SMCP configuration for decorators
        kwargs["_smcp_cfg"] = self.smcp_cfg
        
        # Enable TLS if configured
        if hasattr(self, "_tls_context") and self._tls_context:
            kwargs["ssl_context"] = self._tls_context
            if not transport.endswith("+tls"):
                transport = f"{transport}+tls"
            print(f"Starting server with TLS on {transport}")
        else:
            print(f"Starting server without TLS on {transport}")
        
        # Log security configuration status
        self._log_security_status()
        
        # Run the server
        super().run(transport=transport, **kwargs)
    
    def _log_security_status(self) -> None:
        """Log the status of security features."""
        from .logchain import log_security_event
        
        features = {
            "tls_enabled": hasattr(self, "_tls_context") and self._tls_context is not None,
            "host_allowlist_configured": bool(self.smcp_cfg.get("ALLOWED_HOSTS")),
            "input_filtering_configured": bool(self.smcp_cfg.get("SAFE_RE")),
            "confirmation_enabled": self.smcp_cfg.get("CONFIRMATION_ENABLED", True),
            "logging_enabled": bool(self.smcp_cfg.get("LOG_PATH")),
        }
        
        log_security_event("server_startup", features, self.smcp_cfg)
        
        # Print security status
        print("Security Features Status:")
        for feature, enabled in features.items():
            status = "✓" if enabled else "✗"
            print(f"  {status} {feature.replace('_', ' ').title()}")
    
    def get_security_config(self) -> Dict[str, Any]:
        """
        Get the current security configuration.
        
        Returns:
            Dictionary containing the current security configuration
        """
        return self.smcp_cfg.copy()
    
    def update_security_config(self, updates: Dict[str, Any]) -> None:
        """
        Update the security configuration.
        
        Args:
            updates: Dictionary of configuration updates
        """
        self.smcp_cfg.update(updates)
        
        # Re-setup TLS if configuration changed
        if any(key in updates for key in ["ca_path", "cert_path", "key_path"]):
            if tls_configured(self.smcp_cfg):
                self._setup_tls()
    
    def add_allowed_host(self, host: str) -> None:
        """
        Add a host to the allowlist.
        
        Args:
            host: Host to add to the allowlist
        """
        if "ALLOWED_HOSTS" not in self.smcp_cfg:
            self.smcp_cfg["ALLOWED_HOSTS"] = []
        
        if host not in self.smcp_cfg["ALLOWED_HOSTS"]:
            self.smcp_cfg["ALLOWED_HOSTS"].append(host)
    
    def remove_allowed_host(self, host: str) -> None:
        """
        Remove a host from the allowlist.
        
        Args:
            host: Host to remove from the allowlist
        """
        if "ALLOWED_HOSTS" in self.smcp_cfg and host in self.smcp_cfg["ALLOWED_HOSTS"]:
            self.smcp_cfg["ALLOWED_HOSTS"].remove(host)
    
    def enable_feature(self, feature: str, **kwargs) -> None:
        """
        Enable a security feature with configuration.
        
        Args:
            feature: Name of the feature to enable
            **kwargs: Feature-specific configuration
        """
        if feature == "input_filtering":
            self.smcp_cfg["SAFE_RE"] = kwargs.get("pattern", r"^[\w\s.,:;!?-]{1,2048}$")
            self.smcp_cfg["MAX_LEN"] = kwargs.get("max_length", 2048)
        
        elif feature == "confirmation":
            self.smcp_cfg["CONFIRMATION_ENABLED"] = True
            if "queue_file" in kwargs:
                self.smcp_cfg["QUEUE_FILE"] = kwargs["queue_file"]
        
        elif feature == "logging":
            if "log_path" not in kwargs:
                raise ValueError("log_path required for logging feature")
            self.smcp_cfg["LOG_PATH"] = kwargs["log_path"]
        
        elif feature == "host_allowlist":
            self.smcp_cfg["ALLOWED_HOSTS"] = kwargs.get("hosts", [])
        
        else:
            raise ValueError(f"Unknown feature: {feature}")
    
    def disable_feature(self, feature: str) -> None:
        """
        Disable a security feature.
        
        Args:
            feature: Name of the feature to disable
        """
        if feature == "input_filtering":
            self.smcp_cfg.pop("SAFE_RE", None)
            self.smcp_cfg.pop("MAX_LEN", None)
        
        elif feature == "confirmation":
            self.smcp_cfg["CONFIRMATION_ENABLED"] = False
        
        elif feature == "logging":
            self.smcp_cfg.pop("LOG_PATH", None)
        
        elif feature == "host_allowlist":
            self.smcp_cfg.pop("ALLOWED_HOSTS", None)
        
        elif feature == "tls":
            for key in ["ca_path", "cert_path", "key_path"]:
                self.smcp_cfg.pop(key, None)
            if hasattr(self, "_tls_context"):
                delattr(self, "_tls_context")
        
        else:
            raise ValueError(f"Unknown feature: {feature}")


def create_secure_app(name: str, **security_config) -> FastSMCP:
    """
    Create a FastSMCP app with security configuration.
    
    Args:
        name: Name of the MCP server
        **security_config: Security configuration options
        
    Returns:
        Configured FastSMCP instance
    """
    return FastSMCP(name, smcp_cfg=security_config)
