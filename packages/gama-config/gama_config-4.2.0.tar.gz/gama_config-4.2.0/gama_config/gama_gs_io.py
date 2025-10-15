import yaml
import os
from typing import Any
from pathlib import Path

from gama_config.helpers import YamlDumper
from gama_config.gama_gs import GamaGsConfig


class GsConfigIO:
    """Configuration I/O handler for GAMA Ground Station configuration files."""

    file_name = "gama_gs.yml"
    schema_url = "https://greenroom-robotics.github.io/gama/schemas/gama_gs.schema.json"

    def __init__(self, config_directory: str | Path = ""):
        """Initialize GsConfigIO with a configurable config directory.

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
        """Returns the full path to the ground station configuration file."""
        return self.config_directory / self.file_name

    def parse(self, config: dict[str, Any]) -> GamaGsConfig:
        """Parse a configuration dictionary into a GamaGsConfig object."""
        return GamaGsConfig(**config or {})

    def read(self) -> GamaGsConfig:
        """Read and parse the ground station configuration file."""
        path = self.get_path()
        try:
            with open(path) as stream:
                return self.parse(yaml.safe_load(stream))
        except FileNotFoundError:
            raise FileNotFoundError(f"Could not find config file: {path}")
        except Exception as e:
            raise ValueError(f"Could not parse config file {path} - {e}")

    def write(self, config: GamaGsConfig):
        """Write a GamaGsConfig object to the configuration file."""
        path = self.get_path()
        # Make the parent dir if it doesn't exist
        os.makedirs(path.parent, exist_ok=True)
        json_string = config.model_dump(mode="json")
        with open(path, "w") as stream:
            print(f"Writing: {path}")
            headers = f"# yaml-language-server: $schema={GsConfigIO.schema_url}"
            data = "\n".join([headers, yaml.dump(json_string, Dumper=YamlDumper, sort_keys=True)])
            stream.write(data)

    def serialise(self, config: GamaGsConfig) -> str:
        """Serialize a GamaGsConfig object to YAML string."""
        return yaml.dump(config.model_dump_json(), default_flow_style=True, sort_keys=True)
