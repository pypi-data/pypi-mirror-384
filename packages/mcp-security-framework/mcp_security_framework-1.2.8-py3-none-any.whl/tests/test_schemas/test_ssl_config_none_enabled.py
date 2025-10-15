"""
Test suite for SSLConfig with None enabled field.

This module tests the critical bug fix for SSL configuration validation
when the enabled field is None, which was causing all Python clients to fail.

Author: Vasiliy Zdanovskiy <vasilyvz@gmail.com>
"""

import pytest
from mcp_security_framework.schemas.config import SSLConfig


class TestSSLConfigNoneEnabled:
    """Test suite for SSLConfig with None enabled field."""

    def test_ssl_config_with_none_enabled(self):
        """Test SSLConfig with enabled=None should not fail."""
        # This was the critical bug - should not raise validation error
        config = SSLConfig(enabled=None)
        assert config.enabled == False  # Should default to False
        assert config.verify == True  # Default value
        assert config.verify_mode == "CERT_REQUIRED"  # Default value

    def test_ssl_config_with_false_enabled(self):
        """Test SSLConfig with enabled=False."""
        config = SSLConfig(enabled=False)
        assert config.enabled == False
        assert config.verify == True
        assert config.verify_mode == "CERT_REQUIRED"

    def test_ssl_config_with_true_enabled(self):
        """Test SSLConfig with enabled=True."""
        config = SSLConfig(enabled=True, verify=False)
        assert config.enabled == True
        assert config.verify == False
        assert config.verify_mode == "CERT_REQUIRED"

    def test_ssl_config_with_string_enabled(self):
        """Test SSLConfig with enabled as string."""
        config = SSLConfig(enabled="true", verify=False)
        assert config.enabled == True
        
        config = SSLConfig(enabled="false", verify=False)
        assert config.enabled == False
        
        config = SSLConfig(enabled="1", verify=False)
        assert config.enabled == True
        
        config = SSLConfig(enabled="0", verify=False)
        assert config.enabled == False

    def test_ssl_config_with_integer_enabled(self):
        """Test SSLConfig with enabled as integer."""
        config = SSLConfig(enabled=1, verify=False)
        assert config.enabled == True
        
        config = SSLConfig(enabled=0, verify=False)
        assert config.enabled == False

    def test_ssl_config_with_verify_false_and_none_enabled(self):
        """Test SSLConfig with verify=False and enabled=None."""
        config = SSLConfig(
            enabled=None,
            verify=False,
            verify_mode="CERT_NONE",
            check_hostname=False
        )
        assert config.enabled == False
        assert config.verify == False
        assert config.verify_mode == "CERT_NONE"
        assert config.check_hostname == False

    def test_ssl_config_with_verify_false_and_true_enabled(self):
        """Test SSLConfig with verify=False and enabled=True."""
        config = SSLConfig(
            enabled=True,
            verify=False,
            verify_mode="CERT_NONE",
            check_hostname=False
        )
        assert config.enabled == True
        assert config.verify == False
        assert config.verify_mode == "CERT_NONE"
        assert config.check_hostname == False

    def test_ssl_config_validation_consistency(self):
        """Test SSLConfig validation consistency with None enabled."""
        # Test that validation doesn't require certificate files when enabled=None
        config = SSLConfig(
            enabled=None,
            verify=False,
            verify_mode="CERT_NONE"
        )
        # Should not raise validation error
        assert config.enabled == False
        assert config.verify == False

    def test_ssl_config_with_cert_files_and_none_enabled(self):
        """Test SSLConfig with certificate files and enabled=None."""
        # This should work without validation errors
        config = SSLConfig(
            enabled=None,
            verify=False  # Disable verification to avoid file existence check
        )
        assert config.enabled == False
        assert config.verify == False

    def test_ssl_config_edge_cases(self):
        """Test SSLConfig edge cases with enabled field."""
        # Test with empty string
        config = SSLConfig(enabled="")
        assert config.enabled == False
        
        # Test with whitespace
        config = SSLConfig(enabled="   ", verify=False)
        assert config.enabled == False  # Whitespace string is now handled as False
        
        # Test with "null" string
        config = SSLConfig(enabled="null", verify=False)
        assert config.enabled == False

    def test_ssl_config_serialization_with_none_enabled(self):
        """Test SSLConfig serialization with None enabled."""
        config = SSLConfig(enabled=None)
        
        # Test model_dump
        data = config.model_dump()
        assert data["enabled"] == False
        
        # Test model_dump_json
        json_data = config.model_dump_json()
        assert '"enabled":false' in json_data

    def test_ssl_config_from_dict_with_none_enabled(self):
        """Test SSLConfig creation from dictionary with None enabled."""
        config_dict = {
            "enabled": None,
            "verify": False,
            "verify_mode": "CERT_NONE",
            "check_hostname": False
        }
        
        config = SSLConfig(**config_dict)
        assert config.enabled == False
        assert config.verify == False
        assert config.verify_mode == "CERT_NONE"
        assert config.check_hostname == False

    def test_ssl_config_comprehensive_none_handling(self):
        """Test comprehensive None handling in SSLConfig."""
        # Test all fields that could be None
        config = SSLConfig(
            enabled=None,
            cert_file=None,
            key_file=None,
            ca_cert_file=None,
            client_cert_file=None,
            client_key_file=None,
            verify=None,  # This should also be handled
            verify_mode=None,  # This should use default
            check_hostname=None,  # This should also be handled
            check_expiry=None  # This should also be handled
        )
        
        assert config.enabled == False
        assert config.cert_file is None
        assert config.key_file is None
        assert config.ca_cert_file is None
        assert config.client_cert_file is None
        assert config.client_key_file is None
        assert config.verify == False  # Should default to False for None
        assert config.verify_mode == "CERT_REQUIRED"  # Should use default
        assert config.check_hostname == True  # Should default to True for None
        assert config.check_expiry == True  # Should default to True for None
