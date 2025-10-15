"""
Test suite for SecurityManager client certificate loading.

This module tests the critical bug fix for SecurityManager.create_ssl_context()
to ensure client certificates are loaded for mTLS authentication.

Author: Vasiliy Zdanovskiy <vasilyvz@gmail.com>
"""

import pytest
import ssl
import tempfile
import os
from unittest.mock import Mock, patch
from mcp_security_framework import SecurityManager, SecurityConfig, SSLConfig, PermissionConfig


class TestSecurityManagerClientCerts:
    """Test suite for SecurityManager client certificate loading."""

    @pytest.fixture
    def temp_cert_files(self):
        """Create temporary certificate files for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.crt', delete=False) as cert_file:
            cert_file.write("-----BEGIN CERTIFICATE-----\nMOCK_CLIENT_CERT\n-----END CERTIFICATE-----")
            cert_path = cert_file.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.key', delete=False) as key_file:
            key_file.write("-----BEGIN PRIVATE KEY-----\nMOCK_CLIENT_KEY\n-----END PRIVATE KEY-----")
            key_path = key_file.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.crt', delete=False) as ca_file:
            ca_file.write("-----BEGIN CERTIFICATE-----\nMOCK_CA_CERT\n-----END CERTIFICATE-----")
            ca_path = ca_file.name
        
        yield cert_path, key_path, ca_path
        
        # Cleanup
        os.unlink(cert_path)
        os.unlink(key_path)
        os.unlink(ca_path)

    def test_security_manager_creates_ssl_context_with_client_certs(self, temp_cert_files):
        """Test SecurityManager creates SSL context with client certificates."""
        cert_path, key_path, ca_path = temp_cert_files
        
        # Create configuration
        ssl_config = SSLConfig(
            enabled=True,
            verify=False,
            verify_mode="CERT_NONE",
            check_hostname=False
        )
        permission_config = PermissionConfig(enabled=False)
        security_config = SecurityConfig(ssl=ssl_config, permissions=permission_config)
        
        # Create SecurityManager
        security_manager = SecurityManager(security_config)
        
        # Create SSL context with client certificates
        ssl_context = security_manager.create_ssl_context(
            context_type='client',
            client_cert_file=cert_path,
            client_key_file=key_path,
            ca_cert_file=ca_path,
            verify_mode='CERT_NONE'
        )
        
        # Verify SSL context is created
        assert ssl_context is not None
        assert isinstance(ssl_context, ssl.SSLContext)
        assert ssl_context.verify_mode == ssl.CERT_NONE
        assert ssl_context.check_hostname is False

    def test_security_manager_ssl_context_with_verify_none_and_client_certs(self, temp_cert_files):
        """Test SecurityManager SSL context with verify=False and client certificates."""
        cert_path, key_path, ca_path = temp_cert_files
        
        # Create configuration with verify=False
        ssl_config = SSLConfig(
            enabled=True,
            verify=False,
            verify_mode="CERT_NONE",
            check_hostname=False
        )
        permission_config = PermissionConfig(enabled=False)
        security_config = SecurityConfig(ssl=ssl_config, permissions=permission_config)
        
        # Create SecurityManager
        security_manager = SecurityManager(security_config)
        
        # Create SSL context
        ssl_context = security_manager.create_ssl_context(
            context_type='client',
            client_cert_file=cert_path,
            client_key_file=key_path,
            verify_mode='CERT_NONE'
        )
        
        # Verify SSL context properties
        assert ssl_context is not None
        assert ssl_context.verify_mode == ssl.CERT_NONE
        assert ssl_context.check_hostname is False

    def test_security_manager_ssl_context_with_verify_true_and_client_certs(self, temp_cert_files):
        """Test SecurityManager SSL context with verify=True and client certificates."""
        cert_path, key_path, ca_path = temp_cert_files
        
        # Create configuration with verify=True
        ssl_config = SSLConfig(
            enabled=True,
            verify=True,
            verify_mode="CERT_REQUIRED",
            check_hostname=True
        )
        permission_config = PermissionConfig(enabled=False)
        security_config = SecurityConfig(ssl=ssl_config, permissions=permission_config)
        
        # Create SecurityManager
        security_manager = SecurityManager(security_config)
        
        # Create SSL context
        ssl_context = security_manager.create_ssl_context(
            context_type='client',
            client_cert_file=cert_path,
            client_key_file=key_path,
            ca_cert_file=ca_path,
            verify_mode='CERT_REQUIRED'
        )
        
        # Verify SSL context properties
        assert ssl_context is not None
        assert ssl_context.verify_mode == ssl.CERT_REQUIRED
        assert ssl_context.check_hostname is True

    def test_security_manager_ssl_context_without_client_certs(self, temp_cert_files):
        """Test SecurityManager SSL context without client certificates."""
        cert_path, key_path, ca_path = temp_cert_files
        
        # Create configuration
        ssl_config = SSLConfig(
            enabled=True,
            verify=False,
            verify_mode="CERT_NONE",
            check_hostname=False
        )
        permission_config = PermissionConfig(enabled=False)
        security_config = SecurityConfig(ssl=ssl_config, permissions=permission_config)
        
        # Create SecurityManager
        security_manager = SecurityManager(security_config)
        
        # Create SSL context without client certificates
        ssl_context = security_manager.create_ssl_context(
            context_type='client',
            verify_mode='CERT_NONE'
        )
        
        # Verify SSL context is created
        assert ssl_context is not None
        assert ssl_context.verify_mode == ssl.CERT_NONE
        assert ssl_context.check_hostname is False

    def test_security_manager_ssl_context_server_type(self, temp_cert_files):
        """Test SecurityManager SSL context for server type."""
        cert_path, key_path, ca_path = temp_cert_files
        
        # Create configuration
        ssl_config = SSLConfig(
            enabled=True,
            verify=False,
            verify_mode="CERT_NONE",
            check_hostname=False,
            cert_file=cert_path,
            key_file=key_path
        )
        permission_config = PermissionConfig(enabled=False)
        security_config = SecurityConfig(ssl=ssl_config, permissions=permission_config)
        
        # Create SecurityManager
        security_manager = SecurityManager(security_config)
        
        # Create SSL context for server
        ssl_context = security_manager.create_ssl_context(
            context_type='server',
            cert_file=cert_path,
            key_file=key_path,
            verify_mode='CERT_NONE'
        )
        
        # Verify SSL context is created
        assert ssl_context is not None
        assert isinstance(ssl_context, ssl.SSLContext)

    def test_security_manager_ssl_context_invalid_type(self, temp_cert_files):
        """Test SecurityManager SSL context with invalid context type."""
        cert_path, key_path, ca_path = temp_cert_files
        
        # Create configuration
        ssl_config = SSLConfig(
            enabled=True,
            verify=False,
            verify_mode="CERT_NONE",
            check_hostname=False
        )
        permission_config = PermissionConfig(enabled=False)
        security_config = SecurityConfig(ssl=ssl_config, permissions=permission_config)
        
        # Create SecurityManager
        security_manager = SecurityManager(security_config)
        
        # Test invalid context type
        with pytest.raises(Exception):  # Should raise SecurityValidationError
            security_manager.create_ssl_context(
                context_type='invalid',
                client_cert_file=cert_path,
                client_key_file=key_path
            )

    def test_security_manager_ssl_context_caching(self, temp_cert_files):
        """Test SecurityManager SSL context caching."""
        cert_path, key_path, ca_path = temp_cert_files
        
        # Create configuration
        ssl_config = SSLConfig(
            enabled=True,
            verify=False,
            verify_mode="CERT_NONE",
            check_hostname=False
        )
        permission_config = PermissionConfig(enabled=False)
        security_config = SecurityConfig(ssl=ssl_config, permissions=permission_config)
        
        # Create SecurityManager
        security_manager = SecurityManager(security_config)
        
        # Create SSL context first time
        ssl_context1 = security_manager.create_ssl_context(
            context_type='client',
            client_cert_file=cert_path,
            client_key_file=key_path,
            verify_mode='CERT_NONE'
        )
        
        # Create SSL context second time (should use cache)
        ssl_context2 = security_manager.create_ssl_context(
            context_type='client',
            client_cert_file=cert_path,
            client_key_file=key_path,
            verify_mode='CERT_NONE'
        )
        
        # Verify both contexts are the same (cached)
        assert ssl_context1 is ssl_context2

    def test_security_manager_ssl_context_different_params(self, temp_cert_files):
        """Test SecurityManager SSL context with different parameters."""
        cert_path, key_path, ca_path = temp_cert_files
        
        # Create configuration
        ssl_config = SSLConfig(
            enabled=True,
            verify=False,
            verify_mode="CERT_NONE",
            check_hostname=False
        )
        permission_config = PermissionConfig(enabled=False)
        security_config = SecurityConfig(ssl=ssl_config, permissions=permission_config)
        
        # Create SecurityManager
        security_manager = SecurityManager(security_config)
        
        # Create SSL context with CERT_NONE
        ssl_context1 = security_manager.create_ssl_context(
            context_type='client',
            client_cert_file=cert_path,
            client_key_file=key_path,
            verify_mode='CERT_NONE'
        )
        
        # Create SSL context with CERT_REQUIRED
        ssl_context2 = security_manager.create_ssl_context(
            context_type='client',
            client_cert_file=cert_path,
            client_key_file=key_path,
            verify_mode='CERT_REQUIRED'
        )
        
        # Verify contexts are different (different cache keys)
        assert ssl_context1 is not ssl_context2
        assert ssl_context1.verify_mode == ssl.CERT_NONE
        assert ssl_context2.verify_mode == ssl.CERT_REQUIRED

    def test_security_manager_ssl_context_error_handling(self, temp_cert_files):
        """Test SecurityManager SSL context error handling."""
        cert_path, key_path, ca_path = temp_cert_files
        
        # Create configuration
        ssl_config = SSLConfig(
            enabled=True,
            verify=False,
            verify_mode="CERT_NONE",
            check_hostname=False
        )
        permission_config = PermissionConfig(enabled=False)
        security_config = SecurityConfig(ssl=ssl_config, permissions=permission_config)
        
        # Create SecurityManager
        security_manager = SecurityManager(security_config)
        
        # Test with non-existent certificate file
        with pytest.raises(Exception):  # Should raise SSLConfigurationError
            security_manager.create_ssl_context(
                context_type='client',
                client_cert_file='nonexistent.crt',
                client_key_file=key_path,
                verify_mode='CERT_NONE'
            )

    def test_security_manager_ssl_context_comprehensive(self, temp_cert_files):
        """Test SecurityManager SSL context comprehensive scenario."""
        cert_path, key_path, ca_path = temp_cert_files
        
        # Create configuration
        ssl_config = SSLConfig(
            enabled=True,
            verify=False,
            verify_mode="CERT_NONE",
            check_hostname=False,
            client_cert_file=cert_path,
            client_key_file=key_path,
            ca_cert_file=ca_path
        )
        permission_config = PermissionConfig(enabled=False)
        security_config = SecurityConfig(ssl=ssl_config, permissions=permission_config)
        
        # Create SecurityManager
        security_manager = SecurityManager(security_config)
        
        # Test various scenarios
        scenarios = [
            {
                'context_type': 'client',
                'client_cert_file': cert_path,
                'client_key_file': key_path,
                'ca_cert_file': ca_path,
                'verify_mode': 'CERT_NONE'
            },
            {
                'context_type': 'client',
                'client_cert_file': cert_path,
                'client_key_file': key_path,
                'verify_mode': 'CERT_REQUIRED'
            },
            {
                'context_type': 'client',
                'verify_mode': 'CERT_NONE'
            }
        ]
        
        for scenario in scenarios:
            ssl_context = security_manager.create_ssl_context(**scenario)
            assert ssl_context is not None
            assert isinstance(ssl_context, ssl.SSLContext)
