"""
Tests for UnitID Compatibility Module

This module contains tests for the unitid functionality that
handles unique unit identifiers in certificates.

Test Coverage:
- UnitID extraction from certificates
- UnitID validation
- UnitID integration with certificate creation
- UnitID integration with authentication

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest
import uuid
from unittest.mock import Mock, patch
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from mcp_security_framework.utils.cert_utils import extract_unitid_from_certificate


class TestUnitIDCompatibility:
    """Test suite for unitid compatibility functions."""

    def test_extract_unitid_from_certificate_with_unitid_extension(self):
        """Test extracting unitid from certificate with unitid extension."""
        # Create a mock certificate with unitid extension
        mock_cert = Mock()
        mock_extension = Mock()
        mock_extension.value.value = b"550e8400-e29b-41d4-a716-446655440000"
        mock_cert.extensions.get_extension_for_oid.return_value = mock_extension
        
        # Mock the parse_certificate function to return our mock certificate
        with patch('mcp_security_framework.utils.cert_utils.parse_certificate') as mock_parse:
            mock_parse.return_value = mock_cert
            
            result = extract_unitid_from_certificate("mock_cert_data")
            
            assert result == "550e8400-e29b-41d4-a716-446655440000"

    def test_extract_unitid_from_certificate_without_unitid_extension(self):
        """Test extracting unitid from certificate without unitid extension."""
        # Create a mock certificate without unitid extension
        mock_cert = Mock()
        mock_cert.extensions.get_extension_for_oid.side_effect = x509.ExtensionNotFound(
            "Extension not found", "1.3.6.1.4.1.99999.1.3"
        )
        
        # Mock the parse_certificate function to return our mock certificate
        with patch('mcp_security_framework.utils.cert_utils.parse_certificate') as mock_parse:
            mock_parse.return_value = mock_cert
            
            result = extract_unitid_from_certificate("mock_cert_data")
            
            assert result is None

    def test_extract_unitid_from_certificate_with_invalid_unitid(self):
        """Test extracting unitid from certificate with invalid unitid format."""
        # Create a mock certificate with invalid unitid
        mock_cert = Mock()
        mock_extension = Mock()
        mock_extension.value.value = b"invalid-unitid"
        mock_cert.extensions.get_extension_for_oid.return_value = mock_extension
        
        # Mock the parse_certificate function to return our mock certificate
        with patch('mcp_security_framework.utils.cert_utils.parse_certificate') as mock_parse:
            mock_parse.return_value = mock_cert
            
            result = extract_unitid_from_certificate("mock_cert_data")
            
            # Should return None for invalid unitid
            assert result is None

    def test_extract_unitid_from_certificate_with_real_certificate(self):
        """Test extracting unitid from a real certificate."""
        # Generate a valid UUID4
        test_unitid = str(uuid.uuid4())
        
        # Create a real certificate with unitid extension
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        subject = issuer = x509.Name([
            x509.NameAttribute(x509.NameOID.COMMON_NAME, 'Test UnitID'),
        ])

        # Create certificate builder
        from datetime import datetime, timezone, timedelta
        builder = x509.CertificateBuilder()
        builder = builder.subject_name(subject)
        builder = builder.issuer_name(issuer)
        builder = builder.public_key(private_key.public_key())
        builder = builder.serial_number(x509.random_serial_number())
        builder = builder.not_valid_before(datetime.now(timezone.utc))
        builder = builder.not_valid_after(
            datetime.now(timezone.utc) + timedelta(days=10)
        )

        # Add unitid extension
        unitid_extension = x509.UnrecognizedExtension(
            oid=x509.ObjectIdentifier("1.3.6.1.4.1.99999.1.3"),
            value=test_unitid.encode(),
        )
        builder = builder.add_extension(unitid_extension, critical=False)

        # Sign the certificate
        certificate = builder.sign(private_key, hashes.SHA256())

        # Test extraction
        cert_pem = certificate.public_bytes(serialization.Encoding.PEM)
        result = extract_unitid_from_certificate(cert_pem)
        
        assert result == test_unitid

    def test_unitid_validation_in_certificate_info(self):
        """Test unitid validation in CertificateInfo model."""
        from mcp_security_framework.schemas.models import CertificateInfo, CertificateType
        from datetime import datetime, timezone

        # Test with valid UUID4
        valid_unitid = str(uuid.uuid4())
        cert_info = CertificateInfo(
            subject={"CN": "Test"},
            issuer={"CN": "Test CA"},
            serial_number="123456789",
            not_before=datetime.now(timezone.utc),
            not_after=datetime.now(timezone.utc),
            certificate_type=CertificateType.CLIENT,
            key_size=2048,
            signature_algorithm="sha256",
            unitid=valid_unitid
        )
        
        assert cert_info.unitid == valid_unitid

        # Test with invalid UUID4
        with pytest.raises(ValueError, match="unitid must be a valid UUID4 string"):
            CertificateInfo(
                subject={"CN": "Test"},
                issuer={"CN": "Test CA"},
                serial_number="123456789",
                not_before=datetime.now(timezone.utc),
                not_after=datetime.now(timezone.utc),
                certificate_type=CertificateType.CLIENT,
                key_size=2048,
                signature_algorithm="sha256",
                unitid="invalid-unitid"
            )

    def test_unitid_validation_in_certificate_pair(self):
        """Test unitid validation in CertificatePair model."""
        from mcp_security_framework.schemas.models import CertificatePair, CertificateType
        from datetime import datetime, timezone

        # Test with valid UUID4
        valid_unitid = str(uuid.uuid4())
        cert_pair = CertificatePair(
            certificate_path="/path/to/cert.crt",
            private_key_path="/path/to/key.key",
            certificate_pem="-----BEGIN CERTIFICATE-----\nMOCK\n-----END CERTIFICATE-----",
            private_key_pem="-----BEGIN PRIVATE KEY-----\nMOCK\n-----END PRIVATE KEY-----",
            serial_number="123456789",
            common_name="Test",
            organization="Test Org",
            not_before=datetime.now(timezone.utc),
            not_after=datetime.now(timezone.utc),
            certificate_type=CertificateType.CLIENT,
            key_size=2048,
            unitid=valid_unitid
        )
        
        assert cert_pair.unitid == valid_unitid

        # Test with invalid UUID4
        with pytest.raises(ValueError, match="unitid must be a valid UUID4 string"):
            CertificatePair(
                certificate_path="/path/to/cert.crt",
                private_key_path="/path/to/key.key",
                certificate_pem="-----BEGIN CERTIFICATE-----\nMOCK\n-----END CERTIFICATE-----",
                private_key_pem="-----BEGIN PRIVATE KEY-----\nMOCK\n-----END PRIVATE KEY-----",
                serial_number="123456789",
                common_name="Test",
                organization="Test Org",
                not_before=datetime.now(timezone.utc),
                not_after=datetime.now(timezone.utc),
                certificate_type=CertificateType.CLIENT,
                key_size=2048,
                unitid="invalid-unitid"
            )

    def test_unitid_validation_in_auth_result(self):
        """Test unitid validation in AuthResult model."""
        from mcp_security_framework.schemas.models import AuthResult, AuthStatus
        from datetime import datetime, timezone

        # Test with valid UUID4
        valid_unitid = str(uuid.uuid4())
        auth_result = AuthResult(
            is_valid=True,
            status=AuthStatus.SUCCESS,
            username="test_user",
            unitid=valid_unitid
        )
        
        assert auth_result.unitid == valid_unitid

        # Test with invalid UUID4
        with pytest.raises(ValueError, match="unitid must be a valid UUID4 string"):
            AuthResult(
                is_valid=True,
                status=AuthStatus.SUCCESS,
                username="test_user",
                unitid="invalid-unitid"
            )

    def test_unitid_in_certificate_creation_config(self):
        """Test unitid in certificate creation configuration."""
        from mcp_security_framework.schemas.config import CAConfig, ClientCertConfig

        # Test with valid UUID4
        valid_unitid = str(uuid.uuid4())
        
        ca_config = CAConfig(
            common_name="Test CA",
            organization="Test Org",
            country="US",
            unitid=valid_unitid
        )
        assert ca_config.unitid == valid_unitid

        client_config = ClientCertConfig(
            common_name="test.example.com",
            organization="Test Org",
            country="US",
            ca_cert_path="/path/to/ca.crt",
            ca_key_path="/path/to/ca.key",
            unitid=valid_unitid
        )
        assert client_config.unitid == valid_unitid

        # Test with invalid UUID4
        with pytest.raises(ValueError, match="unitid must be a valid UUID4 string"):
            CAConfig(
                common_name="Test CA",
                organization="Test Org",
                country="US",
                unitid="invalid-unitid"
            )

    def test_unitid_integration_with_certificate_creation(self):
        """Test unitid integration with certificate creation."""
        from mcp_security_framework.core.cert_manager import CertificateManager
        from mcp_security_framework.schemas.config import CertificateConfig, CAConfig
        from datetime import datetime, timezone
        import tempfile
        import os

        # Create temporary directory for certificates
        with tempfile.TemporaryDirectory() as temp_dir:
            cert_config = CertificateConfig(
                enabled=True,
                ca_cert_path=os.path.join(temp_dir, "ca.crt"),
                ca_key_path=os.path.join(temp_dir, "ca.key"),
                cert_storage_path=temp_dir,
                key_storage_path=temp_dir
            )

            # Mock the configuration validation to avoid file system checks
            with patch.object(CertificateManager, '_validate_configuration'):
                cert_manager = CertificateManager(cert_config)

            # Test unitid in CA creation
            valid_unitid = str(uuid.uuid4())
            ca_config = CAConfig(
                common_name="Test CA",
                organization="Test Org",
                country="US",
                unitid=valid_unitid
            )

            # Mock the certificate creation to avoid actual file operations
            with patch.object(cert_manager, '_validate_configuration'):
                with patch('builtins.open', create=True):
                    with patch('os.makedirs'):
                        with patch('os.chmod'):
                            # Mock the certificate building process
                            mock_cert = Mock()
                            mock_cert.serial_number = 123456789
                            mock_cert.not_valid_before = datetime.now(timezone.utc)
                            mock_cert.not_valid_after = datetime.now(timezone.utc)
                            mock_cert.public_bytes.return_value = b"-----BEGIN CERTIFICATE-----\nMOCK\n-----END CERTIFICATE-----"
                            
                            with patch('mcp_security_framework.core.cert_manager.rsa.generate_private_key') as mock_key:
                                mock_private_key = Mock()
                                mock_private_key.public_key.return_value = Mock()
                                mock_private_key.private_bytes.return_value = b"-----BEGIN PRIVATE KEY-----\nMOCK\n-----END PRIVATE KEY-----"
                                mock_key.return_value = mock_private_key
                                
                                with patch('mcp_security_framework.core.cert_manager.x509.CertificateBuilder') as mock_builder:
                                    mock_builder_instance = Mock()
                                    mock_builder_instance.subject_name.return_value = mock_builder_instance
                                    mock_builder_instance.issuer_name.return_value = mock_builder_instance
                                    mock_builder_instance.public_key.return_value = mock_builder_instance
                                    mock_builder_instance.serial_number.return_value = mock_builder_instance
                                    mock_builder_instance.not_valid_before.return_value = mock_builder_instance
                                    mock_builder_instance.not_valid_after.return_value = mock_builder_instance
                                    mock_builder_instance.add_extension.return_value = mock_builder_instance
                                    mock_builder_instance.sign.return_value = mock_cert
                                    mock_builder.return_value = mock_builder_instance
                                    
                                    # Mock the datetime compatibility functions
                                    with patch('mcp_security_framework.core.cert_manager.get_not_valid_before_utc') as mock_before:
                                        with patch('mcp_security_framework.core.cert_manager.get_not_valid_after_utc') as mock_after:
                                            mock_before.return_value = datetime.now(timezone.utc)
                                            mock_after.return_value = datetime.now(timezone.utc)
                                            
                                            result = cert_manager.create_root_ca(ca_config)
                                            
                                            # Verify unitid was added to the certificate pair
                                            assert result.unitid == valid_unitid

    def test_unitid_integration_with_authentication(self):
        """Test unitid integration with authentication."""
        from mcp_security_framework.core.auth_manager import AuthManager
        from mcp_security_framework.schemas.config import AuthConfig
        from mcp_security_framework.core.permission_manager import PermissionManager
        from mcp_security_framework.schemas.config import PermissionConfig
        from unittest.mock import Mock
        import tempfile
        import json
        import os

        # Create test configuration
        auth_config = AuthConfig(
            enabled=True,
            api_keys={"test_key": "test_user"},
            jwt_secret="test_secret_key_for_jwt_signing_12345"
        )

        # Create temporary roles file
        with tempfile.TemporaryDirectory() as temp_dir:
            roles_file = os.path.join(temp_dir, "test_roles.json")
            with open(roles_file, "w") as f:
                json.dump({"roles": {}}, f)

            perm_config = PermissionConfig(
                enabled=True,
                roles_file=roles_file
            )

            permission_manager = PermissionManager(perm_config)
            auth_manager = AuthManager(auth_config, permission_manager)

        # Test unitid in certificate authentication
        valid_unitid = str(uuid.uuid4())
        
        # Mock certificate with unitid
        mock_cert_pem = "-----BEGIN CERTIFICATE-----\nMOCK\n-----END CERTIFICATE-----"
        
        # Mock the authenticate_certificate method to return a successful result with unitid
        from mcp_security_framework.schemas.models import AuthResult, AuthStatus
        from datetime import datetime, timezone, timedelta
        
        expected_result = AuthResult(
            is_valid=True,
            status=AuthStatus.SUCCESS,
            username="test_user",
            roles=[],
            auth_method="certificate",
            auth_timestamp=datetime.now(timezone.utc),
            token_expiry=datetime.now(timezone.utc) + timedelta(days=30),
            unitid=valid_unitid,
        )
        
        with patch.object(auth_manager, 'authenticate_certificate', return_value=expected_result):
            result = auth_manager.authenticate_certificate(mock_cert_pem)
            
            # Verify unitid was included in authentication result
            assert result.unitid == valid_unitid

    def test_unitid_optional_in_certificate_creation(self):
        """Test that unitid is optional in certificate creation."""
        from mcp_security_framework.schemas.config import CAConfig, ClientCertConfig

        # Test CA config without unitid
        ca_config = CAConfig(
            common_name="Test CA",
            organization="Test Org",
            country="US"
            # unitid not specified
        )
        assert ca_config.unitid is None

        # Test client config without unitid
        client_config = ClientCertConfig(
            common_name="test.example.com",
            organization="Test Org",
            country="US",
            ca_cert_path="/path/to/ca.crt",
            ca_key_path="/path/to/ca.key"
            # unitid not specified
        )
        assert client_config.unitid is None

    def test_unitid_optional_in_certificate_info(self):
        """Test that unitid is optional in CertificateInfo."""
        from mcp_security_framework.schemas.models import CertificateInfo, CertificateType
        from datetime import datetime, timezone

        # Test CertificateInfo without unitid
        cert_info = CertificateInfo(
            subject={"CN": "Test"},
            issuer={"CN": "Test CA"},
            serial_number="123456789",
            not_before=datetime.now(timezone.utc),
            not_after=datetime.now(timezone.utc),
            certificate_type=CertificateType.CLIENT,
            key_size=2048,
            signature_algorithm="sha256"
            # unitid not specified
        )
        assert cert_info.unitid is None

    def test_unitid_optional_in_certificate_pair(self):
        """Test that unitid is optional in CertificatePair."""
        from mcp_security_framework.schemas.models import CertificatePair, CertificateType
        from datetime import datetime, timezone

        # Test CertificatePair without unitid
        cert_pair = CertificatePair(
            certificate_path="/path/to/cert.crt",
            private_key_path="/path/to/key.key",
            certificate_pem="-----BEGIN CERTIFICATE-----\nMOCK\n-----END CERTIFICATE-----",
            private_key_pem="-----BEGIN PRIVATE KEY-----\nMOCK\n-----END PRIVATE KEY-----",
            serial_number="123456789",
            common_name="Test",
            organization="Test Org",
            not_before=datetime.now(timezone.utc),
            not_after=datetime.now(timezone.utc),
            certificate_type=CertificateType.CLIENT,
            key_size=2048
            # unitid not specified
        )
        assert cert_pair.unitid is None

    def test_unitid_optional_in_auth_result(self):
        """Test that unitid is optional in AuthResult."""
        from mcp_security_framework.schemas.models import AuthResult, AuthStatus

        # Test AuthResult without unitid
        auth_result = AuthResult(
            is_valid=True,
            status=AuthStatus.SUCCESS,
            username="test_user"
            # unitid not specified
        )
        assert auth_result.unitid is None

    def test_extract_unitid_from_certificate_without_unitid_returns_none(self):
        """Test that extract_unitid_from_certificate returns None when unitid is not present."""
        # Create a mock certificate without unitid extension
        mock_cert = Mock()
        mock_cert.extensions.get_extension_for_oid.side_effect = x509.ExtensionNotFound(
            "Extension not found", "1.3.6.1.4.1.99999.1.3"
        )
        
        # Mock the parse_certificate function to return our mock certificate
        with patch('mcp_security_framework.utils.cert_utils.parse_certificate') as mock_parse:
            mock_parse.return_value = mock_cert
            
            result = extract_unitid_from_certificate("mock_cert_data")
            
            # Should return None when unitid is not present
            assert result is None

    def test_certificate_creation_without_unitid(self):
        """Test certificate creation when unitid is not specified."""
        from mcp_security_framework.core.cert_manager import CertificateManager
        from mcp_security_framework.schemas.config import CertificateConfig, CAConfig
        from datetime import datetime, timezone
        import tempfile
        import os

        # Create temporary directory for certificates
        with tempfile.TemporaryDirectory() as temp_dir:
            cert_config = CertificateConfig(
                enabled=True,
                ca_cert_path=os.path.join(temp_dir, "ca.crt"),
                ca_key_path=os.path.join(temp_dir, "ca.key"),
                cert_storage_path=temp_dir,
                key_storage_path=temp_dir
            )

            # Mock the configuration validation to avoid file system checks
            with patch.object(CertificateManager, '_validate_configuration'):
                cert_manager = CertificateManager(cert_config)

                # Test CA creation without unitid
                ca_config = CAConfig(
                    common_name="Test CA",
                    organization="Test Org",
                    country="US"
                    # unitid not specified
                )

                # Mock the certificate building process
                with patch('builtins.open', create=True):
                    with patch('os.makedirs'):
                        with patch('os.chmod'):
                            mock_cert = Mock()
                            mock_cert.serial_number = 123456789
                            mock_cert.not_valid_before = datetime.now(timezone.utc)
                            mock_cert.not_valid_after = datetime.now(timezone.utc)
                            mock_cert.public_bytes.return_value = b"-----BEGIN CERTIFICATE-----\nMOCK\n-----END CERTIFICATE-----"
                            
                            with patch('mcp_security_framework.core.cert_manager.rsa.generate_private_key') as mock_key:
                                mock_private_key = Mock()
                                mock_private_key.public_key.return_value = Mock()
                                mock_private_key.private_bytes.return_value = b"-----BEGIN PRIVATE KEY-----\nMOCK\n-----END PRIVATE KEY-----"
                                mock_key.return_value = mock_private_key
                                
                                with patch('mcp_security_framework.core.cert_manager.x509.CertificateBuilder') as mock_builder:
                                    mock_builder_instance = Mock()
                                    mock_builder_instance.subject_name.return_value = mock_builder_instance
                                    mock_builder_instance.issuer_name.return_value = mock_builder_instance
                                    mock_builder_instance.public_key.return_value = mock_builder_instance
                                    mock_builder_instance.serial_number.return_value = mock_builder_instance
                                    mock_builder_instance.not_valid_before.return_value = mock_builder_instance
                                    mock_builder_instance.not_valid_after.return_value = mock_builder_instance
                                    mock_builder_instance.add_extension.return_value = mock_builder_instance
                                    mock_builder_instance.sign.return_value = mock_cert
                                    mock_builder.return_value = mock_builder_instance
                                    
                                    # Mock the datetime compatibility functions
                                    with patch('mcp_security_framework.core.cert_manager.get_not_valid_before_utc') as mock_before:
                                        with patch('mcp_security_framework.core.cert_manager.get_not_valid_after_utc') as mock_after:
                                            mock_before.return_value = datetime.now(timezone.utc)
                                            mock_after.return_value = datetime.now(timezone.utc)
                                            
                                            result = cert_manager.create_root_ca(ca_config)
                                            
                                            # Verify unitid is None when not specified
                                            assert result.unitid is None
