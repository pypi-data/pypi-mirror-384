"""
Test the FastSMCP subclass with security integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from smcp.app_wrapper import FastSMCP


class TestFastSMCPSecurity:
    """Test FastSMCP security integration."""
    
    def test_initialization_without_security_config(self):
        """Test that FastSMCP initializes without security configuration."""
        app = FastSMCP("test-server")
        assert app.smcp_cfg == {}
        assert not hasattr(app, "_tls_context")
    
    def test_initialization_with_security_config(self):
        """Test that FastSMCP initializes with security configuration."""
        cfg = {
            "ALLOWED_HOSTS": ["localhost"],
            "SAFE_RE": r"^[a-zA-Z\s]+$"
        }
        app = FastSMCP("test-server", smcp_cfg=cfg)
        assert app.smcp_cfg == cfg
    
    @patch('smcp.app_wrapper.tls_configured')
    @patch('smcp.app_wrapper.TLSContextFactory')
    def test_tls_setup_when_configured(self, mock_tls_factory, mock_tls_configured):
        """Test that TLS is set up when certificates are configured."""
        mock_tls_configured.return_value = True
        mock_context = Mock()
        mock_tls_factory.server_context.return_value = mock_context
        
        cfg = {
            "ca_path": "ca.pem",
            "cert_path": "server.pem", 
            "key_path": "server.key"
        }
        
        app = FastSMCP("test-server", smcp_cfg=cfg)
        
        assert hasattr(app, "_tls_context")
        assert app._tls_context == mock_context
        mock_tls_factory.server_context.assert_called_once_with(cfg)
    
    @patch('smcp.app_wrapper.tls_configured')
    def test_no_tls_setup_when_not_configured(self, mock_tls_configured):
        """Test that TLS is not set up when certificates are not configured."""
        mock_tls_configured.return_value = False
        
        app = FastSMCP("test-server", smcp_cfg={})
        
        assert not hasattr(app, "_tls_context")
    
    @patch('smcp.app_wrapper.tls_configured')
    @patch('smcp.app_wrapper.TLSContextFactory')
    def test_tls_setup_failure_handling(self, mock_tls_factory, mock_tls_configured):
        """Test handling of TLS setup failures."""
        mock_tls_configured.return_value = True
        mock_tls_factory.server_context.side_effect = Exception("Certificate error")
        
        cfg = {
            "ca_path": "ca.pem",
            "cert_path": "server.pem",
            "key_path": "server.key"
        }
        
        # Should not raise exception, but should not have TLS context
        app = FastSMCP("test-server", smcp_cfg=cfg)
        assert not hasattr(app, "_tls_context") or app._tls_context is None
    
    def test_config_injection_during_run(self):
        """Test that configuration is injected during run."""
        cfg = {"SAFE_RE": r"^[a-zA-Z\s]+$"}
        app = FastSMCP("test-server", smcp_cfg=cfg)
        
        # Mock the parent run method
        with patch.object(app.__class__.__bases__[0], 'run') as mock_run:
            app.run()
            
            # Verify config was injected
            mock_run.assert_called_once()
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["_smcp_cfg"] == cfg
    
    def test_tls_transport_modification(self):
        """Test that transport is modified when TLS is enabled."""
        app = FastSMCP("test-server", smcp_cfg={})
        app._tls_context = Mock()  # Simulate TLS context
        
        with patch.object(app.__class__.__bases__[0], 'run') as mock_run:
            app.run(transport="tcp")
            
            # Verify transport was modified and SSL context was set
            mock_run.assert_called_once()
            call_args, call_kwargs = mock_run.call_args
            assert call_kwargs["ssl_context"] == app._tls_context
            assert call_kwargs.get("transport") == "tcp+tls" or call_args[0] == "tcp+tls"
    
    def test_security_config_methods(self):
        """Test security configuration management methods."""
        app = FastSMCP("test-server", smcp_cfg={})
        
        # Test get_security_config
        config = app.get_security_config()
        assert config == {}
        
        # Test update_security_config
        updates = {"SAFE_RE": r"^[a-zA-Z]+$"}
        app.update_security_config(updates)
        assert app.smcp_cfg["SAFE_RE"] == r"^[a-zA-Z]+$"
        
        # Test add_allowed_host
        app.add_allowed_host("example.com")
        assert "example.com" in app.smcp_cfg["ALLOWED_HOSTS"]
        
        # Test remove_allowed_host
        app.remove_allowed_host("example.com")
        assert "example.com" not in app.smcp_cfg.get("ALLOWED_HOSTS", [])
    
    def test_feature_enablement(self):
        """Test security feature enable/disable methods."""
        app = FastSMCP("test-server", smcp_cfg={})
        
        # Test enable input filtering
        app.enable_feature("input_filtering", pattern=r"^[a-zA-Z]+$", max_length=100)
        assert app.smcp_cfg["SAFE_RE"] == r"^[a-zA-Z]+$"
        assert app.smcp_cfg["MAX_LEN"] == 100
        
        # Test enable confirmation
        app.enable_feature("confirmation", queue_file="/tmp/queue.json")
        assert app.smcp_cfg["CONFIRMATION_ENABLED"] is True
        assert app.smcp_cfg["QUEUE_FILE"] == "/tmp/queue.json"
        
        # Test enable logging
        app.enable_feature("logging", log_path="/var/log/smcp.log")
        assert app.smcp_cfg["LOG_PATH"] == "/var/log/smcp.log"
        
        # Test enable host allowlist
        app.enable_feature("host_allowlist", hosts=["localhost", "example.com"])
        assert app.smcp_cfg["ALLOWED_HOSTS"] == ["localhost", "example.com"]
        
        # Test invalid feature
        with pytest.raises(ValueError):
            app.enable_feature("invalid_feature")
    
    def test_feature_disablement(self):
        """Test security feature disable methods."""
        app = FastSMCP("test-server", smcp_cfg={
            "SAFE_RE": r"^[a-zA-Z]+$",
            "MAX_LEN": 100,
            "CONFIRMATION_ENABLED": True,
            "LOG_PATH": "/var/log/smcp.log",
            "ALLOWED_HOSTS": ["localhost"],
            "ca_path": "ca.pem",
            "cert_path": "server.pem",
            "key_path": "server.key"
        })
        app._tls_context = Mock()  # Simulate TLS context
        
        # Test disable input filtering
        app.disable_feature("input_filtering")
        assert "SAFE_RE" not in app.smcp_cfg
        assert "MAX_LEN" not in app.smcp_cfg
        
        # Test disable confirmation
        app.disable_feature("confirmation")
        assert app.smcp_cfg["CONFIRMATION_ENABLED"] is False
        
        # Test disable logging
        app.disable_feature("logging")
        assert "LOG_PATH" not in app.smcp_cfg
        
        # Test disable host allowlist
        app.disable_feature("host_allowlist")
        assert "ALLOWED_HOSTS" not in app.smcp_cfg
        
        # Test disable TLS
        app.disable_feature("tls")
        assert "ca_path" not in app.smcp_cfg
        assert "cert_path" not in app.smcp_cfg
        assert "key_path" not in app.smcp_cfg
        assert not hasattr(app, "_tls_context")
        
        # Test invalid feature
        with pytest.raises(ValueError):
            app.disable_feature("invalid_feature")
    
    @patch('smcp.app_wrapper.log_security_event')
    def test_security_status_logging(self, mock_log):
        """Test that security status is logged on startup."""
        cfg = {
            "ALLOWED_HOSTS": ["localhost"],
            "SAFE_RE": r"^[a-zA-Z]+$",
            "LOG_PATH": "/var/log/smcp.log"
        }
        app = FastSMCP("test-server", smcp_cfg=cfg)
        
        with patch.object(app.__class__.__bases__[0], 'run'):
            app.run()
            
            # Verify security event was logged
            mock_log.assert_called_once()
            call_args = mock_log.call_args[0]
            assert call_args[0] == "server_startup"
            
            features = call_args[1]
            assert features["host_allowlist_configured"] is True
            assert features["input_filtering_configured"] is True
            assert features["logging_enabled"] is True


class TestCreateSecureApp:
    """Test the create_secure_app convenience function."""
    
    def test_create_secure_app(self):
        """Test that create_secure_app creates a properly configured FastSMCP instance."""
        from smcp.app_wrapper import create_secure_app
        
        app = create_secure_app(
            "test-server",
            SAFE_RE=r"^[a-zA-Z]+$",
            ALLOWED_HOSTS=["localhost"]
        )
        
        assert isinstance(app, FastSMCP)
        assert app.smcp_cfg["SAFE_RE"] == r"^[a-zA-Z]+$"
        assert app.smcp_cfg["ALLOWED_HOSTS"] == ["localhost"]
