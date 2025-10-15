"""
Simple tests for SSL Manager with verify=false

This module contains simplified tests for the SSLManager when verify=false
is set in the configuration, ensuring proper handling of SSL
verification disabled scenarios.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest
import ssl
import tempfile
import os
from unittest.mock import Mock, patch
from mcp_security_framework.core.ssl_manager import SSLManager
from mcp_security_framework.schemas.config import SSLConfig


class TestSSLVerifyFalseSimple:
    """Simple test suite for SSLManager with verify=false."""

    @pytest.fixture
    def temp_cert_files(self):
        """Create temporary certificate files for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.crt', delete=False) as cert_file:
            cert_file.write("-----BEGIN CERTIFICATE-----\nMOCK_CERT\n-----END CERTIFICATE-----")
            cert_path = cert_file.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.key', delete=False) as key_file:
            key_file.write("-----BEGIN PRIVATE KEY-----\nMOCK_KEY\n-----END PRIVATE KEY-----")
            key_path = key_file.name
        
        yield cert_path, key_path
        
        # Cleanup
        os.unlink(cert_path)
        os.unlink(key_path)

    def test_create_client_context_with_verify_false(self, temp_cert_files):
        """Test client SSL context creation with verify=false."""
        cert_path, key_path = temp_cert_files
        config = SSLConfig(
            enabled=True,
            verify=False,
            verify_mode="CERT_NONE",
            check_hostname=False,
            cert_file=cert_path,
            key_file=key_path
        )
        
        ssl_manager = SSLManager(config)
        
        # Should create context without verification
        context = ssl_manager.create_client_context()
        
        assert context.verify_mode == ssl.CERT_NONE
        assert context.check_hostname is False

    def test_create_client_context_with_verify_true(self, temp_cert_files):
        """Test client SSL context creation with verify=true."""
        cert_path, key_path = temp_cert_files
        config = SSLConfig(
            enabled=True,
            verify=True,
            verify_mode="CERT_REQUIRED",
            check_hostname=True,
            cert_file=cert_path,
            key_file=key_path
        )
        
        ssl_manager = SSLManager(config)
        
        # Should create context with verification
        with patch('ssl.create_default_context') as mock_create:
            mock_context = Mock()
            mock_context.verify_mode = ssl.CERT_REQUIRED
            mock_context.check_hostname = True
            mock_create.return_value = mock_context
            
            context = ssl_manager.create_client_context()
            
            assert context.verify_mode == ssl.CERT_REQUIRED
            assert context.check_hostname is True

    def test_create_client_context_verify_false_ignores_certificates(self, temp_cert_files):
        """Test that verify=false ignores certificate loading."""
        cert_path, key_path = temp_cert_files
        config = SSLConfig(
            enabled=True,
            verify=False,
            verify_mode="CERT_NONE",
            ca_cert_file=cert_path,
            client_cert_file=cert_path,
            client_key_file=key_path,
            cert_file=cert_path,
            key_file=key_path
        )
        
        ssl_manager = SSLManager(config)
        
        # Should create context without loading certificates for verification
        context = ssl_manager.create_client_context()
        
        assert context.verify_mode == ssl.CERT_NONE
        assert context.check_hostname is False

    def test_create_client_context_verify_mode_cert_none(self, temp_cert_files):
        """Test client SSL context creation with verify_mode=CERT_NONE."""
        cert_path, key_path = temp_cert_files
        config = SSLConfig(
            enabled=True,
            verify=True,  # verify=true but verify_mode=CERT_NONE should override
            verify_mode="CERT_NONE",
            check_hostname=False,
            cert_file=cert_path,
            key_file=key_path
        )
        
        ssl_manager = SSLManager(config)
        
        # Should create context without verification
        context = ssl_manager.create_client_context()
        
        assert context.verify_mode == ssl.CERT_NONE
        assert context.check_hostname is False

    def test_create_client_context_verify_false_self_signed(self, temp_cert_files):
        """Test client SSL context creation with verify=false for self-signed certificates."""
        cert_path, key_path = temp_cert_files
        config = SSLConfig(
            enabled=True,
            verify=False,
            verify_mode="CERT_NONE",
            check_hostname=False,
            cert_file=cert_path,
            key_file=key_path
        )
        
        ssl_manager = SSLManager(config)
        
        # Should create context that accepts self-signed certificates
        context = ssl_manager.create_client_context()
        
        assert context.verify_mode == ssl.CERT_NONE
        assert context.check_hostname is False

    def test_create_client_context_verify_false_caching(self, temp_cert_files):
        """Test that verify=false contexts are cached correctly."""
        cert_path, key_path = temp_cert_files
        config = SSLConfig(
            enabled=True,
            verify=False,
            verify_mode="CERT_NONE",
            cert_file=cert_path,
            key_file=key_path
        )
        
        ssl_manager = SSLManager(config)
        
        # Create context twice
        context1 = ssl_manager.create_client_context()
        context2 = ssl_manager.create_client_context()
        
        # Should return the same cached context
        assert context1 is context2

    def test_create_client_context_verify_false_different_configs(self, temp_cert_files):
        """Test that different verify configurations create different contexts."""
        cert_path, key_path = temp_cert_files
        
        config1 = SSLConfig(
            enabled=True,
            verify=False,
            verify_mode="CERT_NONE",
            cert_file=cert_path,
            key_file=key_path
        )
        
        config2 = SSLConfig(
            enabled=True,
            verify=True,
            verify_mode="CERT_REQUIRED",
            cert_file=cert_path,
            key_file=key_path
        )
        
        ssl_manager1 = SSLManager(config1)
        ssl_manager2 = SSLManager(config2)
        
        # Should create different contexts
        context1 = ssl_manager1.create_client_context()
        context2 = ssl_manager2.create_client_context()
        
        assert context1.verify_mode != context2.verify_mode
        assert context1.check_hostname != context2.check_hostname

    def test_create_client_context_verify_false_integration(self, temp_cert_files):
        """Test integration with verify=false."""
        cert_path, key_path = temp_cert_files
        config = SSLConfig(
            enabled=True,
            verify=False,
            verify_mode="CERT_NONE",
            check_hostname=False,
            cert_file=cert_path,
            key_file=key_path
        )
        
        ssl_manager = SSLManager(config)
        
        # Should create context that can be used for HTTPS connections
        context = ssl_manager.create_client_context()
        
        # Verify context properties
        assert context.verify_mode == ssl.CERT_NONE
        assert context.check_hostname is False
        
        # Should be usable for HTTPS connections
        assert hasattr(context, 'wrap_socket')
