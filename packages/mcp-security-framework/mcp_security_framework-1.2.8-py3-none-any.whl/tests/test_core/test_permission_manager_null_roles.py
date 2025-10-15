"""
Tests for PermissionManager with null roles_file

This module contains tests for the PermissionManager when roles_file
is set to null or None, ensuring graceful handling of this configuration.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest
from unittest.mock import patch
from mcp_security_framework.core.permission_manager import PermissionManager
from mcp_security_framework.schemas.config import PermissionConfig
from mcp_security_framework.schemas.models import ValidationResult, ValidationStatus


class TestPermissionManagerNullRoles:
    """Test suite for PermissionManager with null roles_file."""

    def test_permission_manager_with_null_roles_file(self):
        """Test PermissionManager initialization with null roles_file."""
        config = PermissionConfig(enabled=True, roles_file=None, default_role="guest")

        # Should not raise an exception
        perm_manager = PermissionManager(config)

        # Should have empty roles
        assert perm_manager._roles == {}

        # Should be able to validate access with default role
        result = perm_manager.validate_access(["guest"], ["read:public"])
        assert isinstance(result, ValidationResult)

    def test_permission_manager_with_empty_roles_file(self):
        """Test PermissionManager initialization with empty roles_file."""
        config = PermissionConfig(enabled=True, roles_file="", default_role="guest")

        # Should not raise an exception
        perm_manager = PermissionManager(config)

        # Should have empty roles
        assert perm_manager._roles == {}

    def test_permission_manager_with_string_null_roles_file(self):
        """Test PermissionManager initialization with string 'null' roles_file."""
        config = PermissionConfig(enabled=True, roles_file="null", default_role="guest")

        # Should not raise an exception
        perm_manager = PermissionManager(config)

        # Should have empty roles
        assert perm_manager._roles == {}

    def test_permission_manager_validation_with_empty_roles(self):
        """Test permission validation when no roles are loaded."""
        config = PermissionConfig(enabled=True, roles_file=None, default_role="guest")

        perm_manager = PermissionManager(config)

        # Test validation with guest role
        result = perm_manager.validate_access(["guest"], ["read:public"])
        assert isinstance(result, ValidationResult)

        # Test validation with unknown role
        result = perm_manager.validate_access(["unknown"], ["read:public"])
        assert isinstance(result, ValidationResult)
        assert result.status == ValidationStatus.INVALID

    def test_permission_manager_get_effective_permissions_empty_roles(self):
        """Test getting effective permissions when no roles are loaded."""
        config = PermissionConfig(enabled=True, roles_file=None, default_role="guest")

        perm_manager = PermissionManager(config)

        # Should return empty set for any role
        permissions = perm_manager.get_effective_permissions(["guest"])
        assert permissions == set()

        permissions = perm_manager.get_effective_permissions(["admin"])
        assert permissions == set()

    def test_permission_manager_export_roles_config_empty(self):
        """Test exporting roles configuration when no roles are loaded."""
        config = PermissionConfig(enabled=True, roles_file=None, default_role="guest")

        perm_manager = PermissionManager(config)

        # Should export empty configuration
        exported = perm_manager.export_roles_config()
        assert "roles" in exported
        assert exported["roles"] == {}
        assert "permissions" in exported
        assert exported["permissions"] == {}

    def test_permission_manager_cache_operations_empty_roles(self):
        """Test cache operations when no roles are loaded."""
        config = PermissionConfig(
            enabled=True,
            roles_file=None,
            default_role="guest",
            permission_cache_enabled=True,
        )

        perm_manager = PermissionManager(config)

        # Cache operations should work without errors
        perm_manager.clear_cache()
        perm_manager.clear_permission_cache()

        # Cache should be empty
        assert len(perm_manager._permission_cache) == 0

    def test_permission_manager_role_operations_empty_roles(self):
        """Test role operations when no roles are loaded."""
        config = PermissionConfig(enabled=True, roles_file=None, default_role="guest")

        perm_manager = PermissionManager(config)

        # Role operations should work without errors
        roles = perm_manager.get_all_roles()
        assert roles == []

        # Getting role permissions should work (returns empty for unknown roles)
        permissions = perm_manager.get_role_permissions("test_role")
        assert permissions == []

    def test_permission_manager_hierarchy_operations_empty_roles(self):
        """Test hierarchy operations when no roles are loaded."""
        config = PermissionConfig(enabled=True, roles_file=None, default_role="guest")

        perm_manager = PermissionManager(config)

        # Hierarchy operations should work without errors
        hierarchy = perm_manager.get_role_hierarchy()
        assert hierarchy == {}

        # Checking hierarchy should work
        is_hierarchy = perm_manager.check_role_hierarchy("child", "parent")
        assert is_hierarchy is False

    def test_permission_manager_permission_operations_empty_roles(self):
        """Test permission operations when no roles are loaded."""
        config = PermissionConfig(enabled=True, roles_file=None, default_role="guest")

        perm_manager = PermissionManager(config)

        # Permission operations should work without errors
        # Note: get_all_permissions doesn't exist, so we test role permissions instead
        permissions = perm_manager.get_role_permissions("guest")
        assert permissions == []

    def test_permission_manager_validation_with_wildcards_empty_roles(self):
        """Test wildcard permission validation when no roles are loaded."""
        config = PermissionConfig(
            enabled=True,
            roles_file=None,
            default_role="guest",
            wildcard_permissions=True,
        )

        perm_manager = PermissionManager(config)

        # Wildcard validation should work without errors
        result = perm_manager.validate_access(["guest"], ["*"])
        assert isinstance(result, ValidationResult)

        result = perm_manager.validate_access(["guest"], ["read:*"])
        assert isinstance(result, ValidationResult)

    def test_permission_manager_strict_mode_empty_roles(self):
        """Test strict mode validation when no roles are loaded."""
        config = PermissionConfig(
            enabled=True, roles_file=None, default_role="guest", strict_mode=True
        )

        perm_manager = PermissionManager(config)

        # Strict mode validation should work without errors
        result = perm_manager.validate_access(["guest"], ["read:public"])
        assert isinstance(result, ValidationResult)

        result = perm_manager.validate_access(["unknown"], ["read:public"])
        assert isinstance(result, ValidationResult)
        assert result.status == ValidationStatus.INVALID

    def test_permission_manager_cache_ttl_empty_roles(self):
        """Test cache TTL operations when no roles are loaded."""
        config = PermissionConfig(
            enabled=True,
            roles_file=None,
            default_role="guest",
            permission_cache_enabled=True,
            permission_cache_ttl=300,
        )

        perm_manager = PermissionManager(config)

        # Cache TTL operations should work without errors
        assert perm_manager._cache_enabled is True

        # Cache should be empty but functional
        permissions = perm_manager.get_effective_permissions(["guest"])
        assert permissions == set()

    def test_permission_manager_error_handling_empty_roles(self):
        """Test error handling when no roles are loaded."""
        config = PermissionConfig(enabled=True, roles_file=None, default_role="guest")

        perm_manager = PermissionManager(config)

        # Error handling should work without errors
        try:
            perm_manager.validate_access([], ["read:public"])
        except Exception as e:
            pytest.fail(f"validate_access raised an exception: {e}")

        try:
            perm_manager.validate_access(["guest"], [])
        except Exception as e:
            pytest.fail(f"validate_access raised an exception: {e}")

    def test_permission_manager_logging_empty_roles(self):
        """Test logging when no roles are loaded."""
        config = PermissionConfig(enabled=True, roles_file=None, default_role="guest")

        # Should not raise an exception during initialization
        with patch(
            "mcp_security_framework.core.permission_manager.logging.getLogger"
        ) as mock_logger:
            mock_logger_instance = mock_logger.return_value
            perm_manager = PermissionManager(config)

            # Should log warning about empty roles configuration
            mock_logger_instance.warning.assert_called_with(
                "No roles file specified, using empty roles configuration"
            )

    def test_permission_manager_integration_empty_roles(self):
        """Test full integration when no roles are loaded."""
        config = PermissionConfig(
            enabled=True,
            roles_file=None,
            default_role="guest",
            permission_cache_enabled=True,
            wildcard_permissions=True,
            strict_mode=True,
        )

        # Should initialize without errors
        perm_manager = PermissionManager(config)

        # All operations should work
        assert perm_manager._roles == {}
        assert perm_manager._hierarchy == {}
        assert perm_manager._permission_cache == {}
        assert perm_manager._cache_enabled is True

        # Validation should work
        result = perm_manager.validate_access(["guest"], ["read:public"])
        assert isinstance(result, ValidationResult)

        # Cache operations should work
        perm_manager.clear_cache()
        assert len(perm_manager._permission_cache) == 0
