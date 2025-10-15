# IMPORTANT
# After changing this file, run `python3 -m gama_config.generate_schemas`
# To re-generate the json schemas

import os
from pydantic import BaseModel, Field
from enum import Enum
from typing import Literal, Union
from gama_config import LogLevel

DEFAULT_NAMESPACE_GROUNDSTATION = "groundstation"


class Mode(str, Enum):
    NONE = "none"
    XBOX = "xbox"
    XBOX_SERIES_X = "xbox_series_x"
    THRUSTMASTER = "thrustmaster"
    THRUSTMASTER_COMBO = "thrustmaster_combo"
    WARTHOG = "warthog"
    WARTHOG_COMBO = "warthog_combo"
    AERONAV = "aeronav"
    SINGLE_UNKNOWN = "single_unknown"
    DUAL_UNKNOWN = "dual_unknown"
    GLADIATOR = "gladiator"
    LOGITECH_EXTREME = "logitech_extreme"
    PLAYSTATION_DUAL_SENSE = "playstation_dual_sense"


class Network(str, Enum):
    SHARED = "shared"
    HOST = "host"


class DiscoverySimple(BaseModel):
    type: Literal["simple"] = "simple"
    ros_domain_id: int = Field(
        default=0,
        description="ROS domain ID",
    )
    own_ip: str = Field(
        default="0.0.0.0",
        description="IP/host/interface address of the primary network interface. This is where DDS traffic will route to.",
    )


class DiscoveryFastDDS(BaseModel):
    type: Literal["fastdds"] = "fastdds"
    with_discovery_server: bool = Field(
        default=True, description="Run the discovery server. It will bind to 0.0.0.0:11811"
    )
    discovery_server_ip: str = Field(
        default="0.0.0.0",
        description="IP/host/interface of the discovery server. Assumes port of 11811",
    )
    own_ip: str = Field(
        default="0.0.0.0",
        description="IP/host/interface address of the primary network interface. This is where DDS traffic will route to.",
    )


class DiscoveryZenoh(BaseModel):
    type: Literal["zenoh"] = "zenoh"
    with_discovery_server: bool = Field(default=True, description="Run the zenoh router")
    discovery_server_ip: str = Field(
        default="0.0.0.0",
        description="IP/host/interface of the discovery server. Assumes port of 7447",
    )


Discovery = Union[DiscoveryZenoh, DiscoveryFastDDS, DiscoverySimple]


class GamaGsConfig(BaseModel):
    namespace_vessel: str = "vessel_1"
    namespace_groundstation: str = DEFAULT_NAMESPACE_GROUNDSTATION
    mode: Mode = Mode.NONE
    buttons: bool = False
    network: Network = Network.SHARED
    prod: bool = False
    log_level: LogLevel = LogLevel.INFO
    remote_cmd_override: bool = False
    discovery: Discovery = Field(
        default_factory=DiscoverySimple,
        discriminator="type",
    )
    ui: bool = False


def get_gs_config_io():
    """Get a GsConfigIO instance using the GAMA_CONFIG_DIR environment variable."""
    from gama_config.gama_gs_io import GsConfigIO

    config_dir = os.environ.get("GAMA_CONFIG_DIR")
    if config_dir is None:
        raise ValueError("GAMA_CONFIG_DIR environment variable is not set.")
    return GsConfigIO(config_directory=config_dir)
