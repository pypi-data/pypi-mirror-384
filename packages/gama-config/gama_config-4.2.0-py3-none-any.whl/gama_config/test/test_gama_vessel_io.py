import tempfile
import pytest
from pathlib import Path
from pydantic import ValidationError

from gama_config.gama_vessel_io import VesselConfigIO
from gama_config.gama_vessel import (
    WaveflyerVesselConfig,
    Mode,
    Variant,
    LogLevel,
    Network,
    EducatVesselConfig,
)


class TestVesselConfigIO:
    def test_get_path_default_directory(self):
        """Test that get_path returns correct default path."""
        config_io = VesselConfigIO()
        expected_path = Path("~/.config/greenroom/gama_vessel.yml").expanduser()
        assert config_io.get_path() == expected_path

    def test_get_path_custom_directory(self):
        """Test that get_path returns correct path with custom directory."""
        config_io = VesselConfigIO("custom/subdir")
        expected_path = Path("~/.config/greenroom/custom/subdir/gama_vessel.yml").expanduser()
        assert config_io.get_path() == expected_path

    def test_parse_empty_config_raises_error(self):
        """Test parsing empty configuration dictionary raises ValidationError."""
        config_io = VesselConfigIO()
        with pytest.raises(
            ValidationError, match="Unable to extract tag using discriminator 'variant'"
        ):
            config_io.parse({})

    def test_parse_educat_config_with_values(self):
        """Test parsing configuration dictionary with educat variant."""
        config_io = VesselConfigIO()
        config_dict = {
            "variant": "educat",
            "namespace_vessel": "vessel_1",
            "namespace_groundstation": "groundstation",
            "mode": "simulator",
            "network": "host",
            "prod": False,
            "log_level": "info",
            "ubiquity_user": "",
            "ubiquity_pass": "",
            "ubiquity_ip": "",
            "cameras": None,
            "record": False,
            "components": {
                "autopilot": {"pid": [1, 2, 3]},
            },
            "advanced_configuration": {"first_launch_arg": "value", "second_launch_arg": "value"},
        }
        result = config_io.parse(config_dict)
        assert isinstance(result, EducatVesselConfig)
        assert result.namespace_vessel == "vessel_1"
        assert result.namespace_groundstation == "groundstation"
        assert result.mode == Mode.SIMULATOR
        assert result.network == Network.HOST
        assert result.prod is False
        assert result.log_level == LogLevel.INFO
        assert result.cameras is None
        assert result.record is False
        assert result.components == {"autopilot": {"pid": [1, 2, 3]}}
        assert result.advanced_configuration == {
            "first_launch_arg": "value",
            "second_launch_arg": "value",
        }

    def test_parse_waveflyer_config(self):
        """Test parsing configuration dictionary with waveflyer variant."""
        config_io = VesselConfigIO()
        config_dict = {
            "variant": "waveflyer",
            "namespace_vessel": "vessel_1",
            "namespace_groundstation": "groundstation",
            "mode": "simulator",
            "network": "host",
            "prod": False,
            "log_level": "info",
            "ubiquity_user": "",
            "ubiquity_pass": "",
            "ubiquity_ip": "",
            "cameras": None,
            "record": False,
            "advanced_configuration": {"random_launch_arg": "value"},
        }
        result = config_io.parse(config_dict)
        assert isinstance(result, WaveflyerVesselConfig)
        assert result.variant == Variant.WAVEFLYER
        assert result.namespace_vessel == "vessel_1"
        assert result.namespace_groundstation == "groundstation"
        assert result.mode == Mode.SIMULATOR
        assert result.network == Network.HOST
        assert result.prod is False
        assert result.log_level == LogLevel.INFO
        assert result.cameras is None
        assert result.record is False
        assert result.components == {}
        assert result.advanced_configuration == {"random_launch_arg": "value"}

    def test_write_and_read_educat_config(self):
        """Test writing and reading educat configuration to/from temporary directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_io = VesselConfigIO(temp_dir)

            test_config = EducatVesselConfig(
                namespace_vessel="test_vessel",
                namespace_groundstation="test_gs",
                mode=Mode.SIMULATOR,
                network=Network.HOST,
                prod=False,
                log_level=LogLevel.INFO,
                cameras=None,
                record=False,
                components={"autopilot": {"pid": [1, 2, 3]}},
                advanced_configuration={"test_arg": "value"},
            )

            config_io.write(test_config)

            config_path = config_io.get_path()
            assert config_path.exists()

            read_config = config_io.read()

            assert isinstance(read_config, EducatVesselConfig)
            assert read_config.namespace_vessel == "test_vessel"
            assert read_config.namespace_groundstation == "test_gs"
            assert read_config.mode == Mode.SIMULATOR
            assert read_config.network == Network.HOST
            assert read_config.prod is False
            assert read_config.log_level == LogLevel.INFO
            assert read_config.cameras is None
            assert read_config.record is False
            assert read_config.components == {"autopilot": {"pid": [1, 2, 3]}}
            assert read_config.advanced_configuration == {"test_arg": "value"}

    def test_write_creates_parent_directory(self):
        """Test that write creates parent directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = f"{temp_dir}/nested/subdir"
            config_io = VesselConfigIO(nested_path)

            test_config = EducatVesselConfig()

            config_io.write(test_config)

            config_path = config_io.get_path()
            assert config_path.exists()
            assert config_path.parent.exists()

    def test_write_includes_schema_header(self):
        """Test that written file includes YAML schema header."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_io = VesselConfigIO(temp_dir)
            test_config = EducatVesselConfig()

            config_io.write(test_config)

            config_path = config_io.get_path()
            with open(config_path) as f:
                content = f.read()

            expected_header = f"# yaml-language-server: $schema={VesselConfigIO.schema_url}"
            assert content.startswith(expected_header)

    def test_read_nonexistent_file_raises_error(self):
        """Test that reading a non-existent file raises FileNotFoundError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_io = VesselConfigIO(f"{temp_dir}/nonexistent")

            with pytest.raises(FileNotFoundError, match="Could not find config file"):
                config_io.read()

    def test_parse_invalid_mode_raises_error(self):
        """Test that parsing invalid mode raises ValidationError."""
        config_io = VesselConfigIO()
        config_dict = {
            "cameras": None,
            "log_level": "info",
            "mode": "goblin",
            "network": "host",
            "prod": False,
            "ubiquity_ip": "",
            "ubiquity_pass": "",
            "ubiquity_user": "",
            "variant": "educat",
        }
        with pytest.raises(ValidationError, match="Input should be.*hitl_simulator"):
            config_io.parse(config_dict)

    def test_parse_invalid_variant_raises_error(self):
        """Test that parsing invalid variant raises ValidationError."""
        config_io = VesselConfigIO()
        config_dict = {
            "cameras": None,
            "log_level": "info",
            "mode": "stubs",
            "network": "host",
            "prod": False,
            "ubiquity_ip": "",
            "ubiquity_pass": "",
            "ubiquity_user": "",
            "variant": "killer-robot",
        }
        with pytest.raises(
            ValidationError,
            match="Input tag 'killer-robot'.*does not match any of the expected tags",
        ):
            config_io.parse(config_dict)

    def test_parse_invalid_camera_type_raises_error(self):
        """Test that parsing invalid camera type raises ValidationError."""
        config_io = VesselConfigIO()
        config_dict = {
            "cameras": [
                {
                    "name": "bow",
                    "order": 0,
                    "type": 89,  # Should be string
                }
            ],
            "log_level": "info",
            "mode": "stubs",
            "network": "host",
            "prod": False,
            "ubiquity_ip": "",
            "ubiquity_pass": "",
            "ubiquity_user": "",
            "variant": "educat",
        }
        with pytest.raises(ValidationError, match="Input should be a valid string"):
            config_io.parse(config_dict)

    def test_write_excludes_default_values(self):
        """Test that written config excludes fields with default values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_io = VesselConfigIO(temp_dir)

            # Create a config with only variant set (all other fields will use defaults)
            test_config = EducatVesselConfig()

            config_io.write(test_config)

            config_path = config_io.get_path()
            with open(config_path) as f:
                content = f.read()

            # Verify default port values are not in the YAML output
            assert "ui: 3000" not in content
            assert "chart_tiler: 3001" not in content
            assert "chart_api: 3002" not in content

            # Verify default other values are not in the YAML output
            assert "display_name: GAMA Vessel" not in content
            assert "namespace_vessel: vessel_1" not in content
            assert "mode: simulator" not in content
            assert "network: host" not in content
            assert "prod: false" not in content
            assert "log_level: info" not in content

            # Verify only the variant is present (as it's required)
            assert "variant: educat" in content

    def test_serialise_excludes_default_values(self):
        """Test that serialise method excludes fields with default values."""
        config_io = VesselConfigIO()
        test_config = EducatVesselConfig()

        serialised = config_io.serialise(test_config)

        # Verify default port values are not in the serialized output
        assert "ui: 3000" not in serialised
        assert "chart_tiler: 3001" not in serialised
        assert "chart_api: 3002" not in serialised

        # Verify default other values are not in the serialized output
        assert "display_name: GAMA Vessel" not in serialised
        assert "namespace_vessel: vessel_1" not in serialised
        assert "mode: simulator" not in serialised
        assert "network: host" not in serialised
        assert "prod: false" not in serialised
        assert "log_level: info" not in serialised

        # Verify only the variant is present (as it's required)
        assert "variant: educat" in serialised

    def test_write_with_include_defaults_flag(self):
        """Test that written config includes defaults when include_defaults=True."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_io = VesselConfigIO(temp_dir)

            # Create a config with defaults
            test_config = EducatVesselConfig()

            # Write with include_defaults=True
            config_io.write(test_config, include_defaults=True)

            config_path = config_io.get_path()
            with open(config_path) as f:
                content = f.read()

            # Verify default port values ARE included in the YAML output
            assert "ui: 3000" in content
            assert "chart_tiler: 3001" in content
            assert "chart_api: 3002" in content

            # Verify default other values ARE included in the YAML output
            assert "display_name: GAMA Vessel" in content
            assert "namespace_vessel: vessel_1" in content
            assert "mode: simulator" in content
            assert "network: host" in content
            assert "prod: false" in content
            assert "log_level: info" in content

            # Verify variant is still present
            assert "variant: educat" in content
