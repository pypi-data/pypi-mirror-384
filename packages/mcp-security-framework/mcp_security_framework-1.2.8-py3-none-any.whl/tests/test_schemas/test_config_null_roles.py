"""
Tests for PermissionConfig with null roles_file

This module contains tests for the PermissionConfig validation
when roles_file is set to null, None, or empty values.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest
from mcp_security_framework.schemas.config import PermissionConfig


class TestPermissionConfigNullRoles:
    """Test suite for PermissionConfig with null roles_file."""

    def test_permission_config_with_none_roles_file(self):
        """Test PermissionConfig with None roles_file."""
        config = PermissionConfig(enabled=True, roles_file=None, default_role="guest")

        assert config.roles_file is None
        assert config.enabled is True
        assert config.default_role == "guest"

    def test_permission_config_with_empty_roles_file(self):
        """Test PermissionConfig with empty string roles_file."""
        config = PermissionConfig(enabled=True, roles_file="", default_role="guest")

        assert config.roles_file is None
        assert config.enabled is True
        assert config.default_role == "guest"

    def test_permission_config_with_string_null_roles_file(self):
        """Test PermissionConfig with string 'null' roles_file."""
        config = PermissionConfig(enabled=True, roles_file="null", default_role="guest")

        assert config.roles_file is None
        assert config.enabled is True
        assert config.default_role == "guest"

    def test_permission_config_with_valid_roles_file(self):
        """Test PermissionConfig with valid roles_file."""
        # Create a temporary file for testing
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"roles": {}}')
            temp_file = f.name

        try:
            config = PermissionConfig(
                enabled=True, roles_file=temp_file, default_role="guest"
            )

            assert config.roles_file == temp_file
            assert config.enabled is True
            assert config.default_role == "guest"
        finally:
            os.unlink(temp_file)

    def test_permission_config_with_nonexistent_roles_file(self):
        """Test PermissionConfig with nonexistent roles_file."""
        with pytest.raises(ValueError, match="Roles file does not exist"):
            PermissionConfig(
                enabled=True,
                roles_file="/nonexistent/path/roles.json",
                default_role="guest",
            )

    def test_permission_config_default_values(self):
        """Test PermissionConfig default values."""
        config = PermissionConfig()

        assert config.enabled is True
        assert config.roles_file is None
        assert config.default_role == "guest"
        assert config.admin_role == "admin"
        assert config.role_hierarchy == {}
        assert config.permission_cache_enabled is True
        assert config.permission_cache_ttl == 300
        assert config.wildcard_permissions is False
        assert config.strict_mode is True
        assert config.roles is None

    def test_permission_config_with_all_null_values(self):
        """Test PermissionConfig with all null-like values."""
        config = PermissionConfig(
            enabled=True,
            roles_file=None,
            default_role="guest",
            admin_role="admin",
            role_hierarchy={},
            permission_cache_enabled=True,
            permission_cache_ttl=300,
            wildcard_permissions=False,
            strict_mode=True,
            roles=None,
        )

        assert config.roles_file is None
        assert config.roles is None
        assert config.role_hierarchy == {}

    def test_permission_config_validation_edge_cases(self):
        """Test PermissionConfig validation with edge cases."""
        # Test with whitespace-only string
        config = PermissionConfig(enabled=True, roles_file="   ", default_role="guest")

        # Should be treated as empty and converted to None
        assert config.roles_file is None

    def test_permission_config_with_roles_dict(self):
        """Test PermissionConfig with inline roles dictionary."""
        config = PermissionConfig(
            enabled=True,
            roles_file=None,
            default_role="guest",
            roles={
                "admin": ["*"],
                "user": ["read:*", "write:own"],
                "guest": ["read:public"],
            },
        )

        assert config.roles_file is None
        assert config.roles is not None
        assert "admin" in config.roles
        assert "user" in config.roles
        assert "guest" in config.roles

    def test_permission_config_serialization(self):
        """Test PermissionConfig serialization with null values."""
        config = PermissionConfig(enabled=True, roles_file=None, default_role="guest")

        # Should serialize without errors
        config_dict = config.model_dump()
        assert "roles_file" in config_dict
        assert config_dict["roles_file"] is None

        # Should deserialize without errors
        config_dict["roles_file"] = None
        new_config = PermissionConfig(**config_dict)
        assert new_config.roles_file is None

    def test_permission_config_json_serialization(self):
        """Test PermissionConfig JSON serialization with null values."""
        config = PermissionConfig(enabled=True, roles_file=None, default_role="guest")

        # Should serialize to JSON without errors
        json_str = config.model_dump_json()
        assert "roles_file" in json_str
        assert "null" in json_str

        # Should deserialize from JSON without errors
        import json

        config_dict = json.loads(json_str)
        assert config_dict["roles_file"] is None

    def test_permission_config_validation_chain(self):
        """Test PermissionConfig validation chain with null values."""
        # Test that validation works with null values
        config = PermissionConfig(
            enabled=True,
            roles_file=None,
            default_role="guest",
            admin_role="admin",
            role_hierarchy={},
            permission_cache_enabled=True,
            permission_cache_ttl=300,
            wildcard_permissions=False,
            strict_mode=True,
            roles=None,
        )

        # All validations should pass
        assert config.enabled is True
        assert config.roles_file is None
        assert config.default_role == "guest"
        assert config.admin_role == "admin"
        assert config.role_hierarchy == {}
        assert config.permission_cache_enabled is True
        assert config.permission_cache_ttl == 300
        assert config.wildcard_permissions is False
        assert config.strict_mode is True
        assert config.roles is None

    def test_permission_config_field_validation(self):
        """Test PermissionConfig field validation with null values."""
        # Test that all fields can be set to null/None where appropriate
        config = PermissionConfig(
            enabled=True,
            roles_file=None,  # Can be None
            default_role="guest",  # Cannot be None
            admin_role="admin",  # Cannot be None
            role_hierarchy={},  # Cannot be None, but can be empty
            permission_cache_enabled=True,  # Cannot be None
            permission_cache_ttl=300,  # Cannot be None
            wildcard_permissions=False,  # Cannot be None
            strict_mode=True,  # Cannot be None
            roles=None,  # Can be None
        )

        # All fields should be valid
        assert config.roles_file is None
        assert config.roles is None
        assert config.role_hierarchy == {}
        assert config.enabled is True
        assert config.default_role == "guest"
        assert config.admin_role == "admin"
        assert config.permission_cache_enabled is True
        assert config.permission_cache_ttl == 300
        assert config.wildcard_permissions is False
        assert config.strict_mode is True

    def test_permission_config_equality(self):
        """Test PermissionConfig equality with null values."""
        config1 = PermissionConfig(enabled=True, roles_file=None, default_role="guest")

        config2 = PermissionConfig(enabled=True, roles_file=None, default_role="guest")

        # Should be equal
        assert config1 == config2

        # Test with different null representations
        config3 = PermissionConfig(enabled=True, roles_file="", default_role="guest")

        # Should be equal (empty string converted to None)
        assert config1 == config3

    def test_permission_config_copy(self):
        """Test PermissionConfig copy with null values."""
        config = PermissionConfig(enabled=True, roles_file=None, default_role="guest")

        # Should copy without errors
        config_copy = config.model_copy()
        assert config_copy == config
        assert config_copy.roles_file is None
        assert config_copy.default_role == "guest"

    def test_permission_config_mutability(self):
        """Test PermissionConfig mutability with null values."""
        config = PermissionConfig(enabled=True, roles_file=None, default_role="guest")

        # Pydantic models are mutable by default
        config.roles_file = "new_value"
        assert config.roles_file == "new_value"

        config.default_role = "new_role"
        assert config.default_role == "new_role"
