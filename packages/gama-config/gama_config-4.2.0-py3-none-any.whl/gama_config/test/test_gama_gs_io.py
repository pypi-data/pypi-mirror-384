import tempfile
import pytest
from pathlib import Path
from pydantic import ValidationError

from gama_config.gama_gs_io import GsConfigIO
from gama_config.gama_gs import GamaGsConfig, Mode, LogLevel, Network


class TestGsConfigIO:
    def test_get_path_default_directory(self):
        """Test that get_path returns correct default path."""
        config_io = GsConfigIO()
        expected_path = Path("~/.config/greenroom/gama_gs.yml").expanduser()
        assert config_io.get_path() == expected_path

    def test_get_path_custom_directory(self):
        """Test that get_path returns correct path with custom directory."""
        config_io = GsConfigIO("custom/subdir")
        expected_path = Path("~/.config/greenroom/custom/subdir/gama_gs.yml").expanduser()
        assert config_io.get_path() == expected_path

    def test_parse_empty_config(self):
        """Test parsing empty configuration dictionary."""
        config_io = GsConfigIO()
        result = config_io.parse({})
        assert isinstance(result, GamaGsConfig)

    def test_parse_config_with_values(self):
        """Test parsing configuration dictionary with specific values."""
        config_io = GsConfigIO()
        config_dict = {
            "vessel_ip": None,
            "log_level": "info",
            "mode": "none",
            "network": "shared",
            "prod": False,
        }
        result = config_io.parse(config_dict)
        assert result.log_level == LogLevel.INFO
        assert result.mode == Mode.NONE
        assert result.network == Network.SHARED
        assert result.prod is False

    def test_parse_none_config(self):
        """Test parsing None configuration."""
        config_io = GsConfigIO()
        result = config_io.parse({})
        assert isinstance(result, GamaGsConfig)

    def test_write_and_read_config(self):
        """Test writing and reading configuration to/from temporary directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_io = GsConfigIO(temp_dir)

            test_config = GamaGsConfig(
                log_level=LogLevel.INFO,
                mode=Mode.NONE,
                network=Network.SHARED,
                prod=False,
            )

            config_io.write(test_config)

            config_path = config_io.get_path()
            assert config_path.exists()

            read_config = config_io.read()

            assert read_config.log_level == LogLevel.INFO
            assert read_config.mode == Mode.NONE
            assert read_config.network == Network.SHARED
            assert read_config.prod is False

    def test_write_creates_parent_directory(self):
        """Test that write creates parent directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = f"{temp_dir}/nested/subdir"
            config_io = GsConfigIO(nested_path)

            test_config = GamaGsConfig(mode=Mode.NONE)

            config_io.write(test_config)

            config_path = config_io.get_path()
            assert config_path.exists()
            assert config_path.parent.exists()

    def test_write_includes_schema_header(self):
        """Test that written file includes YAML schema header."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_io = GsConfigIO(temp_dir)
            test_config = GamaGsConfig(mode=Mode.NONE)

            config_io.write(test_config)

            config_path = config_io.get_path()
            with open(config_path) as f:
                content = f.read()

            expected_header = f"# yaml-language-server: $schema={GsConfigIO.schema_url}"
            assert content.startswith(expected_header)

    def test_read_nonexistent_file_raises_error(self):
        """Test that reading a non-existent file raises FileNotFoundError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_io = GsConfigIO(f"{temp_dir}/nonexistent")

            with pytest.raises(FileNotFoundError, match="Could not find config file"):
                config_io.read()

    def test_parse_invalid_mode_raises_error(self):
        """Test that parsing invalid mode raises ValidationError."""
        config_io = GsConfigIO()
        config_dict = {
            "vessel_ip": None,
            "log_level": "info",
            "mode": "goblin",
            "network": "shared",
            "prod": False,
        }
        with pytest.raises(ValidationError, match="Input should be.*logitech_extreme"):
            config_io.parse(config_dict)

    def test_parse_invalid_network_raises_error(self):
        """Test that parsing invalid network raises ValidationError."""
        config_io = GsConfigIO()
        config_dict = {
            "vessel_ip": None,
            "log_level": "info",
            "mode": "none",
            "network": "starlink",
            "prod": False,
        }
        with pytest.raises(ValidationError, match="Input should be.*host"):
            config_io.parse(config_dict)
