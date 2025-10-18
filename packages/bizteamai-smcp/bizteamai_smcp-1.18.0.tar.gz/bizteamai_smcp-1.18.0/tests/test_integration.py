"""
Integration tests for multiple security guards working together.
"""

import pytest
from unittest.mock import patch, Mock
from smcp import FastSMCP, tool, prompt
from smcp.filters import InputValidationError
from smcp.allowlist import HostValidationError
from smcp.confirm import PendingApproval


class TestIntegration:
    """Test integration of multiple security features."""
    
    def test_complete_security_stack(self):
        """Test all security features working together."""
        cfg = {
            "ca_path": "ca.pem",
            "cert_path": "server.pem",
            "key_path": "server.key",
            "ALLOWED_HOSTS": ["api.internal.local"],
            "SAFE_RE": r"^[\w\s.,:;!?-]{1,100}$",
            "CONFIRMATION_ENABLED": True,
            "LOG_PATH": "/var/log/smcp.log"
        }
        
        app = FastSMCP("secure-server", smcp_cfg=cfg)
        
        @tool(confirm=True)
        def secure_delete(target: str, prompt: str):
            return f"deleted {target}"
        
        # Test that confirmation is triggered before other validations
        with pytest.raises(PendingApproval):
            secure_delete(
                "file.txt",
                target="api.internal.local",
                prompt="delete this file",
                _smcp_cfg=cfg
            )
    
    def test_partial_security_configuration(self):
        """Test that partial security configuration works correctly."""
        # Only input filtering enabled
        cfg = {"SAFE_RE": r"^[a-zA-Z\s]+$"}
        
        @tool()
        def partially_secured(prompt: str, target: str):
            return f"processed {prompt} for {target}"
        
        # Valid prompt, any target should work
        result = partially_secured(
            "hello world",
            prompt="hello world",
            target="any.host.com",
            _smcp_cfg=cfg
        )
        assert result == "processed hello world for any.host.com"
        
        # Invalid prompt should fail
        with pytest.raises(InputValidationError):
            partially_secured(
                "hello@world",
                prompt="hello@world", 
                target="any.host.com",
                _smcp_cfg=cfg
            )
    
    def test_incremental_security_adoption(self):
        """Test that security can be adopted incrementally."""
        app = FastSMCP("incremental-server", smcp_cfg={})
        
        @tool()
        def evolving_function(prompt: str, target: str):
            return f"result for {prompt} -> {target}"
        
        # Start with no security
        result = evolving_function(
            "test@input",
            prompt="test@input",
            target="any.host",
            _smcp_cfg={}
        )
        assert "test@input" in result
        
        # Add input filtering
        app.enable_feature("input_filtering", pattern=r"^[a-zA-Z\s]+$")
        
        with pytest.raises(InputValidationError):
            evolving_function(
                "test@input",
                prompt="test@input",
                target="any.host",
                _smcp_cfg=app.smcp_cfg
            )
        
        # Add host allowlist
        app.enable_feature("host_allowlist", hosts=["trusted.com"])
        
        with pytest.raises(HostValidationError):
            evolving_function(
                "test input",
                prompt="test input",
                target="untrusted.com",
                _smcp_cfg=app.smcp_cfg
            )
    
    def test_error_handling_with_multiple_guards(self):
        """Test error handling when multiple guards could fail."""
        cfg = {
            "SAFE_RE": r"^[a-zA-Z\s]+$",
            "ALLOWED_HOSTS": ["trusted.com"]
        }
        
        @tool()
        def multi_validated(prompt: str, target: str):
            return "success"
        
        # Input validation should fail first
        with pytest.raises(InputValidationError):
            multi_validated(
                "bad@input",
                prompt="bad@input",
                target="untrusted.com",  # This would also fail host validation
                _smcp_cfg=cfg
            )
        
        # Host validation should fail when input is valid
        with pytest.raises(HostValidationError):
            multi_validated(
                "good input",
                prompt="good input",
                target="untrusted.com",
                _smcp_cfg=cfg
            )
        
        # Both validations should pass
        result = multi_validated(
            "good input",
            prompt="good input", 
            target="trusted.com",
            _smcp_cfg=cfg
        )
        assert result == "success"
    
    @patch('smcp.logchain.log_event')
    def test_logging_with_security_events(self, mock_log):
        """Test that security events are properly logged."""
        cfg = {
            "SAFE_RE": r"^[a-zA-Z\s]+$",
            "LOG_PATH": "/var/log/smcp.log"
        }
        
        @tool()
        def logged_function(prompt: str):
            return f"processed: {prompt}"
        
        # Successful execution should be logged
        result = logged_function("hello", prompt="hello", _smcp_cfg=cfg)
        assert result == "processed: hello"
        mock_log.assert_called_once()
        
        # Failed validation should not trigger function logging
        mock_log.reset_mock()
        with pytest.raises(InputValidationError):
            logged_function("bad@input", prompt="bad@input", _smcp_cfg=cfg)
        
        # log_event should not be called for failed validation
        mock_log.assert_not_called()
    
    def test_configuration_precedence(self):
        """Test that runtime configuration takes precedence over defaults."""
        # App with default config
        app_cfg = {"SAFE_RE": r"^[a-zA-Z]+$"}  # Only letters
        app = FastSMCP("test-server", smcp_cfg=app_cfg)
        
        @tool()
        def configurable_function(prompt: str):
            return f"result: {prompt}"
        
        # Should fail with default config
        with pytest.raises(InputValidationError):
            configurable_function("hello world", prompt="hello world", _smcp_cfg=app_cfg)
        
        # Should pass with runtime override
        runtime_cfg = {"SAFE_RE": r"^[a-zA-Z\s]+$"}  # Letters and spaces
        result = configurable_function("hello world", prompt="hello world", _smcp_cfg=runtime_cfg)
        assert result == "result: hello world"
    
    def test_feature_interaction_isolation(self):
        """Test that security features don't interfere with each other."""
        cfg = {
            "SAFE_RE": r"^[a-zA-Z\s]+$",
            "ALLOWED_HOSTS": ["api.example.com"],
            "CONFIRMATION_ENABLED": False,  # Disabled
            "LOG_PATH": "/var/log/smcp.log"
        }
        
        @tool()
        def isolated_function(prompt: str, target: str):
            return f"processed {prompt} for {target}"
        
        # All non-confirmation features should work
        with patch('smcp.logchain.log_event') as mock_log:
            result = isolated_function(
                "hello world",
                prompt="hello world",
                target="api.example.com", 
                _smcp_cfg=cfg
            )
            
            assert result == "processed hello world for api.example.com"
            mock_log.assert_called_once()
        
        # Confirmation should not trigger
        @tool(confirm=True)
        def confirmation_disabled(param: str):
            return f"executed: {param}"
        
        # Should execute immediately without confirmation
        result = confirmation_disabled("test", _smcp_cfg=cfg)
        assert result == "executed: test"
