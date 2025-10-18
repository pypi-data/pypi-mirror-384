"""
Test the conditional activation of security guards.
"""

import pytest
from unittest.mock import Mock, patch
from smcp.decorators import tool, prompt, retrieval
from smcp.filters import InputValidationError
from smcp.allowlist import HostValidationError
from smcp.confirm import PendingApproval


class TestConditionalGuards:
    """Test that security guards only activate when configured."""
    
    def test_no_guards_when_no_config(self):
        """Test that no guards activate when no configuration is provided."""
        @tool()
        def test_function(param: str):
            return f"processed: {param}"
        
        # Should work without any security configuration
        result = test_function("test", _smcp_cfg={})
        assert result == "processed: test"
    
    def test_input_filter_activates_with_safe_re(self):
        """Test that input filtering activates when SAFE_RE is configured."""
        @prompt()
        def test_prompt(prompt: str):
            return f"response to: {prompt}"
        
        cfg = {"SAFE_RE": r"^[a-zA-Z\s]+$"}
        
        # Valid input should pass
        result = test_prompt("hello world", _smcp_cfg=cfg)
        assert result == "response to: hello world"
        
        # Invalid input should raise error
        with pytest.raises(InputValidationError):
            test_prompt("hello@world", _smcp_cfg=cfg)
    
    def test_host_allowlist_activates_with_allowed_hosts(self):
        """Test that host validation activates when ALLOWED_HOSTS is configured."""
        @tool()
        def test_api_call(target: str):
            return f"called: {target}"
        
        cfg = {"ALLOWED_HOSTS": ["api.example.com", "localhost"]}
        
        # Allowed host should pass
        result = test_api_call("api.example.com", target="api.example.com", _smcp_cfg=cfg)
        assert result == "called: api.example.com"
        
        # Disallowed host should raise error
        with pytest.raises(HostValidationError):
            test_api_call("evil.com", target="evil.com", _smcp_cfg=cfg)
    
    def test_confirmation_activates_with_confirm_flag(self):
        """Test that confirmation activates when confirm=True is set."""
        @tool(confirm=True)
        def dangerous_action(target: str):
            return f"deleted: {target}"
        
        cfg = {"CONFIRMATION_ENABLED": True}
        
        # Should raise PendingApproval
        with pytest.raises(PendingApproval):
            dangerous_action("important_file.txt", _smcp_cfg=cfg)
    
    def test_logging_activates_with_log_path(self):
        """Test that logging activates when LOG_PATH is configured."""
        with patch('smcp.logchain.log_event') as mock_log:
            @tool()
            def logged_function(param: str):
                return f"result: {param}"
            
            cfg = {"LOG_PATH": "/tmp/test.log"}
            
            result = logged_function("test", _smcp_cfg=cfg)
            assert result == "result: test"
            
            # Verify logging was called
            mock_log.assert_called_once()
    
    def test_multiple_guards_can_be_active(self):
        """Test that multiple guards can be active simultaneously."""
        @tool(confirm=True)
        def multi_guarded_function(prompt: str, target: str):
            return f"processed {prompt} for {target}"
        
        cfg = {
            "SAFE_RE": r"^[a-zA-Z\s]+$",
            "ALLOWED_HOSTS": ["localhost"],
            "CONFIRMATION_ENABLED": True,
            "LOG_PATH": "/tmp/test.log"
        }
        
        # Should trigger confirmation before other guards
        with pytest.raises(PendingApproval):
            multi_guarded_function(
                "hello world", 
                prompt="hello world",
                target="localhost",
                _smcp_cfg=cfg
            )
    
    def test_partial_configuration(self):
        """Test that only configured guards activate."""
        @tool()
        def partially_guarded(prompt: str, target: str):
            return f"processed {prompt} for {target}"
        
        # Only input filtering configured
        cfg = {"SAFE_RE": r"^[a-zA-Z\s]+$"}
        
        # Should validate prompt but not target
        result = partially_guarded(
            "hello world",
            prompt="hello world", 
            target="any.host.com",
            _smcp_cfg=cfg
        )
        assert result == "processed hello world for any.host.com"
        
        # Invalid prompt should still fail
        with pytest.raises(InputValidationError):
            partially_guarded(
                "hello@world",
                prompt="hello@world",
                target="any.host.com", 
                _smcp_cfg=cfg
            )


class TestDecoratorTypes:
    """Test that all decorator types work with security guards."""
    
    def test_tool_decorator_with_guards(self):
        """Test that tool decorator works with security guards."""
        @tool(confirm=True)
        def secure_tool(param: str):
            return f"tool result: {param}"
        
        cfg = {"CONFIRMATION_ENABLED": True}
        
        with pytest.raises(PendingApproval):
            secure_tool("test", _smcp_cfg=cfg)
    
    def test_prompt_decorator_with_guards(self):
        """Test that prompt decorator works with security guards."""
        @prompt()
        def secure_prompt(prompt: str):
            return f"prompt result: {prompt}"
        
        cfg = {"SAFE_RE": r"^[a-zA-Z\s]+$"}
        
        result = secure_prompt("hello", prompt="hello", _smcp_cfg=cfg)
        assert result == "prompt result: hello"
    
    def test_retrieval_decorator_with_guards(self):
        """Test that retrieval decorator works with security guards."""
        @retrieval()
        def secure_retrieval(query: str):
            return f"retrieval result: {query}"
        
        cfg = {"SAFE_RE": r"^[a-zA-Z\s]+$"}
        
        result = secure_retrieval("search", prompt="search", _smcp_cfg=cfg)
        assert result == "retrieval result: search"


class TestConfigurationInjection:
    """Test that configuration is properly injected."""
    
    def test_config_is_removed_from_kwargs(self):
        """Test that _smcp_cfg is removed from function kwargs."""
        received_kwargs = {}
        
        @tool()
        def capture_kwargs(**kwargs):
            nonlocal received_kwargs
            received_kwargs = kwargs.copy()
            return "result"
        
        cfg = {"SAFE_RE": r".*"}
        capture_kwargs(_smcp_cfg=cfg, other_param="value")
        
        # _smcp_cfg should be removed
        assert "_smcp_cfg" not in received_kwargs
        assert received_kwargs["other_param"] == "value"
    
    def test_empty_config_handling(self):
        """Test that empty configuration is handled gracefully."""
        @tool()
        def test_function(param: str):
            return f"result: {param}"
        
        # Empty config should not cause errors
        result = test_function("test", _smcp_cfg={})
        assert result == "result: test"
        
        # No config should not cause errors
        result = test_function("test")
        assert result == "result: test"
