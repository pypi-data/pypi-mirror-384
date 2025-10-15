import yaml
import os
from typing import Any
from pathlib import Path

from gama_config.helpers import YamlDumper
from gama_config.gama_vessel import VariantVesselConfig, VariantVesselConfigRoot


class VesselConfigIO:
    """Configuration I/O handler for GAMA Vessel configuration files."""

    file_name = "gama_vessel.yml"
    schema_url = "https://greenroom-robotics.github.io/gama/schemas/gama_vessel.schema.json"

    def __init__(self, config_directory: str | Path = ""):
        """Initialize VesselConfigIO with a configurable config directory.

        Args:
            config_directory: Base configuration directory path. Defaults to ~/.config/greenroom
        """
        if str(config_directory).startswith("~"):
            self.config_directory = Path(config_directory).expanduser()
        else:
            self.config_directory = (
                Path("~/.config/greenroom").joinpath(config_directory).expanduser()
            )

    def get_path(self) -> Path:
        """Returns the full path to the vessel configuration file."""
        return self.config_directory / self.file_name

    def parse(self, config: dict[str, Any]) -> VariantVesselConfig:
        """Parse a configuration dictionary into a VariantVesselConfig object."""
        return VariantVesselConfigRoot(root=config or {}).root  # type: ignore[return-value]

    def read(self) -> VariantVesselConfig:
        """Read and parse the vessel configuration file."""
        path = self.get_path()
        try:
            with open(path) as stream:
                return self.parse(yaml.safe_load(stream))
        except FileNotFoundError:
            raise FileNotFoundError(f"Could not find config file: {path}")
        except Exception as e:
            raise ValueError(f"Could not parse config file {path} - {e}")

    def write(self, config: VariantVesselConfig, include_defaults: bool = False):
        """Write a VariantVesselConfig object to the configuration file."""
        path = self.get_path()
        # Make the parent dir if it doesn't exist
        os.makedirs(path.parent, exist_ok=True)

        if include_defaults:
            json_string = config.model_dump(mode="json")
        else:
            json_string = config.model_dump(mode="json", exclude_defaults=True)
            # Always include variant field as it's required for discriminated union parsing
            if "variant" not in json_string:
                json_string["variant"] = config.variant.value
        with open(path, "w") as stream:
            print(f"Writing: {path}")
            headers = f"# yaml-language-server: $schema={VesselConfigIO.schema_url}"
            data = "\n".join([headers, yaml.dump(json_string, Dumper=YamlDumper, sort_keys=True)])
            stream.write(data)

    def serialise(self, config: VariantVesselConfig) -> str:
        """Serialize a VariantVesselConfig object to YAML string."""
        json_data = config.model_dump(mode="json", exclude_defaults=True)
        # Always include variant field as it's required for discriminated union parsing
        if "variant" not in json_data:
            json_data["variant"] = config.variant.value
        return yaml.dump(json_data, default_flow_style=True, sort_keys=True)
