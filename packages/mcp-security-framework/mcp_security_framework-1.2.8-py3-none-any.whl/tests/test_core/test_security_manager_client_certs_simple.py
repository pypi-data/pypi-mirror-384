"""
Simplified test suite for SecurityManager client certificate loading.

This module tests the critical bug fix for SecurityManager.create_ssl_context()
to ensure client certificates are loaded for mTLS authentication.

Author: Vasiliy Zdanovskiy <vasilyvz@gmail.com>
"""

import pytest
import ssl
from unittest.mock import Mock, patch, MagicMock
from mcp_security_framework import SecurityManager, SecurityConfig, SSLConfig, PermissionConfig


class TestSecurityManagerClientCertsSimple:
    """Simplified test suite for SecurityManager client certificate loading."""

    def test_security_manager_ssl_context_without_client_certs(self):
        """Test SecurityManager SSL context without client certificates."""
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
        assert isinstance(ssl_context, ssl.SSLContext)
        assert ssl_context.verify_mode == ssl.CERT_NONE
        assert ssl_context.check_hostname is False

    def test_security_manager_ssl_context_server_type(self):
        """Test SecurityManager SSL context for server type."""
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
        
        # Create SSL context for server
        ssl_context = security_manager.create_ssl_context(
            context_type='server',
            verify_mode='CERT_NONE'
        )
        
        # Verify SSL context is created
        assert ssl_context is not None
        assert isinstance(ssl_context, ssl.SSLContext)

    def test_security_manager_ssl_context_invalid_type(self):
        """Test SecurityManager SSL context with invalid context type."""
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
                verify_mode='CERT_NONE'
            )

    def test_security_manager_ssl_context_caching(self):
        """Test SecurityManager SSL context caching."""
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
            verify_mode='CERT_NONE'
        )
        
        # Create SSL context second time (should use cache)
        ssl_context2 = security_manager.create_ssl_context(
            context_type='client',
            verify_mode='CERT_NONE'
        )
        
        # Verify both contexts are the same (cached)
        assert ssl_context1 is ssl_context2

    def test_security_manager_ssl_context_different_params(self):
        """Test SecurityManager SSL context with different parameters."""
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
            verify_mode='CERT_NONE'
        )
        
        # Create SSL context with CERT_REQUIRED
        ssl_context2 = security_manager.create_ssl_context(
            context_type='client',
            verify_mode='CERT_REQUIRED'
        )
        
        # Verify contexts are different (different cache keys)
        assert ssl_context1 is not ssl_context2
        assert ssl_context1.verify_mode == ssl.CERT_NONE
        assert ssl_context2.verify_mode == ssl.CERT_REQUIRED

    @patch('ssl.SSLContext.load_cert_chain')
    def test_security_manager_ssl_context_with_mocked_client_certs(self, mock_load_cert_chain):
        """Test SecurityManager SSL context with mocked client certificates."""
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
        
        # Create SSL context with client certificates (mocked)
        ssl_context = security_manager.create_ssl_context(
            context_type='client',
            client_cert_file='client.crt',
            client_key_file='client.key',
            verify_mode='CERT_NONE'
        )
        
        # Verify SSL context is created
        assert ssl_context is not None
        assert isinstance(ssl_context, ssl.SSLContext)
        assert ssl_context.verify_mode == ssl.CERT_NONE
        assert ssl_context.check_hostname is False
        
        # Verify that load_cert_chain was called (this is the fix!)
        mock_load_cert_chain.assert_called_once_with('client.crt', 'client.key')

    @patch('ssl.SSLContext.load_cert_chain')
    def test_security_manager_ssl_context_with_mocked_client_certs_verify_true(self, mock_load_cert_chain):
        """Test SecurityManager SSL context with mocked client certificates and verify=True."""
        # Create configuration
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
        
        # Create SSL context with client certificates (mocked)
        ssl_context = security_manager.create_ssl_context(
            context_type='client',
            client_cert_file='client.crt',
            client_key_file='client.key',
            verify_mode='CERT_REQUIRED'
        )
        
        # Verify SSL context is created
        assert ssl_context is not None
        assert isinstance(ssl_context, ssl.SSLContext)
        assert ssl_context.verify_mode == ssl.CERT_REQUIRED
        assert ssl_context.check_hostname is True
        
        # Verify that load_cert_chain was called (this is the fix!)
        mock_load_cert_chain.assert_called_once_with('client.crt', 'client.key')

    def test_security_manager_ssl_context_comprehensive(self):
        """Test SecurityManager SSL context comprehensive scenario."""
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
        
        # Test various scenarios
        scenarios = [
            {
                'context_type': 'client',
                'verify_mode': 'CERT_NONE'
            },
            {
                'context_type': 'client',
                'verify_mode': 'CERT_REQUIRED'
            },
            {
                'context_type': 'server',
                'verify_mode': 'CERT_NONE'
            }
        ]
        
        for scenario in scenarios:
            ssl_context = security_manager.create_ssl_context(**scenario)
            assert ssl_context is not None
            assert isinstance(ssl_context, ssl.SSLContext)

    @patch('ssl.SSLContext.load_cert_chain')
    def test_security_manager_ssl_context_client_certs_loading_fix(self, mock_load_cert_chain):
        """Test that the client certificate loading fix works correctly."""
        # This test verifies that the fix in SSLManager.create_client_context()
        # correctly loads client certificates even when verify=False
        
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
        
        # Test 1: verify=False with client certificates should load certificates
        ssl_context1 = security_manager.create_ssl_context(
            context_type='client',
            client_cert_file='client.crt',
            client_key_file='client.key',
            verify_mode='CERT_NONE'
        )
        
        assert ssl_context1 is not None
        assert ssl_context1.verify_mode == ssl.CERT_NONE
        assert ssl_context1.check_hostname is False
        
        # Verify that load_cert_chain was called (this is the fix!)
        mock_load_cert_chain.assert_called_with('client.crt', 'client.key')
        
        # Reset mock for next test
        mock_load_cert_chain.reset_mock()
        
        # Test 2: verify=True with client certificates should also load certificates
        ssl_context2 = security_manager.create_ssl_context(
            context_type='client',
            client_cert_file='client.crt',
            client_key_file='client.key',
            verify_mode='CERT_REQUIRED'
        )
        
        assert ssl_context2 is not None
        assert ssl_context2.verify_mode == ssl.CERT_REQUIRED
        
        # Verify that load_cert_chain was called again
        mock_load_cert_chain.assert_called_with('client.crt', 'client.key')
        
        # Reset mock for next test
        mock_load_cert_chain.reset_mock()
        
        # Test 3: verify=False without client certificates should not call load_cert_chain
        ssl_context3 = security_manager.create_ssl_context(
            context_type='client',
            verify_mode='CERT_NONE'
        )
        
        assert ssl_context3 is not None
        assert ssl_context3.verify_mode == ssl.CERT_NONE
        
        # Verify that load_cert_chain was NOT called
        mock_load_cert_chain.assert_not_called()
