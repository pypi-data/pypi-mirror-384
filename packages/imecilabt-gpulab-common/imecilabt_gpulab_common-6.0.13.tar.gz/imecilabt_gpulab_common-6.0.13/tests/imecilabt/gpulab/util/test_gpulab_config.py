"""Tests for gpulab_config module."""

import tempfile
from pathlib import Path

import pytest
from imecilabt.gpulab.util.gpulab_config import (
    BaseConfig,
    discard_pem_certs,
    discard_pem_privkeys,
)
from pydantic import Field, ValidationError


class TestDiscardPemCerts:
    """Test discard_pem_certs function."""

    def test_discard_single_certificate(self) -> None:
        """Test discarding a single certificate."""
        pem_content = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA1234567890
-----END RSA PRIVATE KEY-----
-----BEGIN CERTIFICATE-----
MIIDXTCCAkWgAwIBAgIJAKz
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
AnotherCertificate
-----END CERTIFICATE-----
"""
        result = discard_pem_certs(pem_content)
        assert "-----BEGIN RSA PRIVATE KEY-----" in result
        assert "-----END RSA PRIVATE KEY-----" in result
        assert "-----BEGIN CERTIFICATE-----" not in result
        assert "-----END CERTIFICATE-----" not in result
        assert "MIIDXTCCAkWgAwIBAgIJAKz" not in result
        assert "AnotherCertificate" not in result

    def test_discard_multiple_certificates(self) -> None:
        """Test discarding multiple certificates."""
        pem_content = """Some header text
-----BEGIN CERTIFICATE-----
Certificate 1 content
-----END CERTIFICATE-----
Some middle text
-----BEGIN CERTIFICATE-----
Certificate 2 content
-----END CERTIFICATE-----
Some footer text"""
        result = discard_pem_certs(pem_content)
        assert "Some header text" in result
        assert "Some middle text" in result
        assert "Some footer text" in result
        assert "Certificate 1 content" not in result
        assert "Certificate 2 content" not in result

    def test_no_certificates(self) -> None:
        """Test with content that has no certificates."""
        pem_content = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA1234567890
-----END RSA PRIVATE KEY-----
Some other content"""
        result = discard_pem_certs(pem_content)
        assert result == pem_content

    def test_empty_string(self) -> None:
        """Test with empty string."""
        result = discard_pem_certs("")
        assert result == ""

    def test_preserves_newlines(self) -> None:
        """Test that newlines are preserved correctly."""
        pem_content = "Line 1\n-----BEGIN CERTIFICATE-----\nCert\n-----END CERTIFICATE-----\nLine 2\n"
        result = discard_pem_certs(pem_content)
        assert result == "Line 1\nLine 2\n"


class TestDiscardPemPrivkeys:
    """Test discard_pem_privkeys function."""

    def test_discard_rsa_private_key(self) -> None:
        """Test discarding RSA private key."""
        pem_content = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA1234567890
ABCDEFGHIJKLMNOP
-----END RSA PRIVATE KEY-----
-----BEGIN CERTIFICATE-----
Certificate content
-----END CERTIFICATE-----
"""
        result = discard_pem_privkeys(pem_content)
        assert "-----BEGIN RSA PRIVATE KEY-----" not in result
        assert "-----END RSA PRIVATE KEY-----" not in result
        assert "MIIEowIBAAKCAQEA1234567890" not in result
        assert "-----BEGIN CERTIFICATE-----" in result
        assert "Certificate content" in result

    def test_discard_generic_private_key(self) -> None:
        """Test discarding generic private key."""
        pem_content = """-----BEGIN PRIVATE KEY-----
PrivateKeyContent
-----END PRIVATE KEY-----
Some other text"""
        result = discard_pem_privkeys(pem_content)
        assert "-----BEGIN PRIVATE KEY-----" not in result
        assert "PrivateKeyContent" not in result
        assert "Some other text" in result

    def test_discard_multiple_private_keys(self) -> None:
        """Test discarding multiple private keys."""
        pem_content = """-----BEGIN RSA PRIVATE KEY-----
Key 1
-----END RSA PRIVATE KEY-----
Middle text
-----BEGIN PRIVATE KEY-----
Key 2
-----END PRIVATE KEY-----
End text"""
        result = discard_pem_privkeys(pem_content)
        assert "Key 1" not in result
        assert "Key 2" not in result
        assert "Middle text" in result
        assert "End text" in result

    def test_no_private_keys(self) -> None:
        """Test with content that has no private keys."""
        pem_content = """-----BEGIN CERTIFICATE-----
Certificate content
-----END CERTIFICATE-----"""
        result = discard_pem_privkeys(pem_content)
        assert result == pem_content

    def test_empty_string(self) -> None:
        """Test with empty string."""
        result = discard_pem_privkeys("")
        assert result == ""

    def test_preserves_newlines(self) -> None:
        """Test that newlines are preserved correctly."""
        pem_content = "Line 1\n-----BEGIN PRIVATE KEY-----\nKey\n-----END PRIVATE KEY-----\nLine 2\n"
        result = discard_pem_privkeys(pem_content)
        assert result == "Line 1\nLine 2\n"


class TestBaseConfig:
    """Test BaseConfig class."""

    class SampleConfig(BaseConfig):
        """Sample config for testing."""

        name: str = Field(default="default_name")
        value: int = Field(default=42)
        enabled: bool = Field(default=True)

    def test_load_from_ymlstr(self) -> None:
        """Test loading from YAML string."""
        yaml_str = """
name: test_config
value: 123
enabled: false
"""
        config = self.SampleConfig.load_from_ymlstr(yaml_str)
        assert config.name == "test_config"
        assert config.value == 123
        assert config.enabled is False

    def test_load_from_ymlstr_with_defaults(self) -> None:
        """Test loading from YAML string with missing fields using defaults."""
        yaml_str = """
name: partial_config
"""
        config = self.SampleConfig.load_from_ymlstr(yaml_str)
        assert config.name == "partial_config"
        assert config.value == 42  # default value
        assert config.enabled is True  # default value

    def test_load_from_file(self) -> None:
        """Test loading from YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("name: file_config\nvalue: 999\nenabled: true\n")
            temp_file = f.name

        try:
            config = self.SampleConfig.load_from_file(temp_file)
            assert config.name == "file_config"
            assert config.value == 999
            assert config.enabled is True
        finally:
            Path(temp_file).unlink()

    def test_save_to_file_and_load_back(self) -> None:
        """Test saving to file and loading it back."""
        config = self.SampleConfig(name="save_test", value=777, enabled=False)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_file = f.name

        try:
            config.save_to_file(temp_file)
            loaded_config = self.SampleConfig.load_from_file(temp_file)

            assert loaded_config.name == "save_test"
            assert loaded_config.value == 777
            assert loaded_config.enabled is False
        finally:
            Path(temp_file).unlink()

    def test_save_to_dict_deprecated(self) -> None:
        """Test save_to_dict (deprecated method)."""
        config = self.SampleConfig(name="dict_test", value=555, enabled=True)

        with pytest.deprecated_call():
            result = config.save_to_dict()

        assert isinstance(result, dict)
        assert result["name"] == "dict_test"
        assert result["value"] == 555
        assert result["enabled"] is True

    def test_load_from_dict_deprecated(self) -> None:
        """Test load_from_dict (deprecated method)."""
        config_dict = {"name": "from_dict", "value": 888, "enabled": False}

        with pytest.deprecated_call():
            config = self.SampleConfig.load_from_dict(config_dict)

        assert config.name == "from_dict"
        assert config.value == 888
        assert config.enabled is False

    def test_model_dump_replaces_save_to_dict(self) -> None:
        """Test that model_dump can replace save_to_dict."""
        config = self.SampleConfig(name="modern_test", value=111, enabled=True)
        result = config.model_dump()

        assert isinstance(result, dict)
        assert result["name"] == "modern_test"
        assert result["value"] == 111
        assert result["enabled"] is True

    def test_model_validate_replaces_load_from_dict(self) -> None:
        """Test that model_validate can replace load_from_dict."""
        config_dict = {"name": "modern_load", "value": 222, "enabled": False}
        config = self.SampleConfig.model_validate(config_dict)

        assert config.name == "modern_load"
        assert config.value == 222
        assert config.enabled is False

    def test_invalid_yaml_raises_error(self) -> None:
        """Test that invalid YAML raises an error."""
        invalid_yaml = """
name: test
value: not_a_number
"""
        with pytest.raises(ValidationError):
            self.SampleConfig.load_from_ymlstr(invalid_yaml)

    def test_invalid_file_raises_error(self) -> None:
        """Test that loading from non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            self.SampleConfig.load_from_file("/nonexistent/path/config.yaml")


class TestComplexPemContent:
    """Test with more complex PEM content scenarios."""

    def test_discard_certs_mixed_content(self) -> None:
        """Test discarding certs with mixed PEM content."""
        pem_content = """-----BEGIN RSA PRIVATE KEY-----
PrivateKeyLine1
PrivateKeyLine2
-----END RSA PRIVATE KEY-----
-----BEGIN CERTIFICATE-----
CertLine1
CertLine2
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
AnotherCertLine1
-----END CERTIFICATE-----
-----BEGIN PUBLIC KEY-----
PublicKeyContent
-----END PUBLIC KEY-----
"""
        result = discard_pem_certs(pem_content)
        assert "PrivateKeyLine1" in result
        assert "PrivateKeyLine2" in result
        assert "PublicKeyContent" in result
        assert "CertLine1" not in result
        assert "CertLine2" not in result
        assert "AnotherCertLine1" not in result

    def test_discard_privkeys_mixed_content(self) -> None:
        """Test discarding private keys with mixed PEM content."""
        pem_content = """-----BEGIN RSA PRIVATE KEY-----
RSAKeyContent
-----END RSA PRIVATE KEY-----
-----BEGIN PRIVATE KEY-----
GenericKeyContent
-----END PRIVATE KEY-----
-----BEGIN CERTIFICATE-----
CertContent
-----END CERTIFICATE-----
-----BEGIN PUBLIC KEY-----
PublicKeyContent
-----END PUBLIC KEY-----
"""
        result = discard_pem_privkeys(pem_content)
        assert "RSAKeyContent" not in result
        assert "GenericKeyContent" not in result
        assert "CertContent" in result
        assert "PublicKeyContent" in result

    def test_both_functions_together(self) -> None:
        """Test using both discard functions together."""
        pem_content = """-----BEGIN PRIVATE KEY-----
PrivKey
-----END PRIVATE KEY-----
-----BEGIN CERTIFICATE-----
Cert
-----END CERTIFICATE-----
-----BEGIN PUBLIC KEY-----
PubKey
-----END PUBLIC KEY-----
"""
        # First remove private keys
        result = discard_pem_privkeys(pem_content)
        # Then remove certificates
        result = discard_pem_certs(result)

        assert "PrivKey" not in result
        assert "Cert" not in result
        assert "PubKey" in result
        assert "-----BEGIN PUBLIC KEY-----" in result
        assert "-----END PUBLIC KEY-----" in result
