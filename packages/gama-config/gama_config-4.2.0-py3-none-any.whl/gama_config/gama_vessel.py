# IMPORTANT
# After changing this file, run `python3 -m gama_config.generate_schemas`
# To re-generate the json schemas

import os
from enum import Enum
from typing import Any, List, Union, Literal, Optional
from gama_config import LogLevel
from greenstream_config.types import Camera
from pydantic import Field, BaseModel, ConfigDict, RootModel, field_validator

DEFAULT_NAMESPACE_VESSEL = "vessel_1"


class Mode(str, Enum):
    SIMULATOR = "simulator"
    HARDWARE = "hardware"
    STUBS = "stubs"
    HITL_SIMULATOR = "hitl_simulator"

    def __str__(self):
        return self.value


class Network(str, Enum):
    SHARED = "shared"
    HOST = "host"

    def __str__(self):
        return self.value


class Variant(str, Enum):
    WHISKEY_BRAVO = "whiskey_bravo"
    EDUCAT = "educat"
    ORACLE_2_2 = "oracle_2_2"
    ORACLE_22 = "oracle_22"
    ARMIDALE = "armidale"
    WAVEFLYER = "waveflyer"
    DMAK = "dmak"
    MARS = "mars"
    FREMANTLE = "fremantle"
    BLUE_BOAT = "blue_boat"
    TENGGARA = "tenggara"
    TACK = "tack"
    AUSTAL_M_USV = "austal_m_usv"

    def __str__(self):
        return self.value


class SubVariant(str, Enum):
    M_USV = "m_usv"
    RHIB = "rhib"

    def __str__(self):
        return self.value


class AutopilotType(str, Enum):
    STANDARD_AUTOPILOT = "standard_autopilot"
    PREDICTIVE_AUTOPILOT = "predictive_autopilot"

    def __str__(self):
        return self.value


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
        description="IP/host/interface of the discovery server.",
    )


class Ports(BaseModel):
    host: str = Field(
        default="http://localhost",
        description="Host for the GAMA services. This will tell other apps where to find GAMA. It should be the hostname or IP of the machine running GAMA.",
    )
    ui: int = Field(
        default=3000,
        description="Port for the GAMA UI. Note, the ENV server will run on this + 100",
    )
    chart_tiler: int = Field(default=3001, description="Port for the Chart Tiler service")
    chart_api: int = Field(default=3002, description="Port for the Chart API service")
    docs: int = Field(default=3003, description="Port for the GAMA documentation server")
    mission_plan_runner: int = Field(
        default=3004, description="Port for the Mission Plan Runner service"
    )
    greenstream_signalling: int = Field(
        default=3005, description="Port for the Greenstream signalling server"
    )
    greenstream_ui: int = Field(default=3006, description="Port for the Greenstream UI")
    tapedeck: int = Field(default=3007, description="Port for the Tapedeck service")
    data_bridge: int = Field(default=3010, description="Port for the Data Bridge service")
    gs_data_bridge: int = Field(
        default=3011, description="Port for the Ground Station Data Bridge service"
    )


Discovery = Union[DiscoveryZenoh, DiscoveryFastDDS, DiscoverySimple]


class GamaVesselConfig(BaseModel):
    model_config = ConfigDict(
        json_encoders={
            Variant: lambda v: v.value,
            SubVariant: lambda v: v.value,
            Mode: lambda v: v.value,
            LogLevel: lambda v: v.value,
            Network: lambda v: v.value,
        },
    )

    variant: Variant
    display_name: str = "GAMA Vessel"
    namespace_vessel: str = DEFAULT_NAMESPACE_VESSEL
    namespace_groundstation: str = "groundstation"
    mode: Mode = Mode.SIMULATOR
    network: Network = Network.HOST
    prod: bool = False
    log_level: LogLevel = LogLevel.INFO
    cameras: Optional[List[Camera]] = None
    record: bool = False
    advanced_configuration: Optional[dict[str, str]] = None
    components: Any = Field(default_factory=dict)
    log_directory: str = "~/greenroom/gama/logs"
    recording_directory: str = "~/greenroom/gama/recordings"
    charts_directory: str = "~/greenroom/charts"
    discovery: Discovery = Field(
        default_factory=DiscoverySimple,
        discriminator="type",
    )
    autopilot_types: List[AutopilotType] = Field(
        default=[AutopilotType.STANDARD_AUTOPILOT],
    )
    ports: Ports = Field(
        default_factory=Ports,
        description="Ports configuration for various GAMA services",
    )

    @field_validator("autopilot_types")
    def ensure_non_empty_list(cls, autopilot_types_list):
        if not autopilot_types_list:
            raise ValueError("autopilot_types must contain at least one value")
        return autopilot_types_list


class ArmidaleVesselConfig(GamaVesselConfig):
    variant: Literal[Variant.ARMIDALE] = Variant.ARMIDALE


class EducatVesselConfig(GamaVesselConfig):
    variant: Literal[Variant.EDUCAT] = Variant.EDUCAT


class Oracle22VesselConfig(GamaVesselConfig):
    variant: Literal[Variant.ORACLE_22] = Variant.ORACLE_22


class Oracle2_2VesselConfig(GamaVesselConfig):
    variant: Literal[Variant.ORACLE_2_2] = Variant.ORACLE_2_2


class WaveflyerVesselConfig(GamaVesselConfig):
    variant: Literal[Variant.WAVEFLYER] = Variant.WAVEFLYER


class WhiskeyBravoVesselConfig(GamaVesselConfig):
    variant: Literal[Variant.WHISKEY_BRAVO] = Variant.WHISKEY_BRAVO


class DMAKVesselConfig(GamaVesselConfig):
    variant: Literal[Variant.DMAK] = Variant.DMAK


class MarsVesselConfig(GamaVesselConfig):
    variant: Literal[Variant.MARS] = Variant.MARS


class FremantleVesselConfig(GamaVesselConfig):
    variant: Literal[Variant.FREMANTLE] = Variant.FREMANTLE


class BlueBoatVesselConfig(GamaVesselConfig):
    variant: Literal[Variant.BLUE_BOAT] = Variant.BLUE_BOAT


class TenggaraVesselConfig(GamaVesselConfig):
    variant: Literal[Variant.TENGGARA] = Variant.TENGGARA


class TackVesselConfig(GamaVesselConfig):
    variant: Literal[Variant.TACK] = Variant.TACK


class Austal_M_USV(GamaVesselConfig):
    variant: Literal[Variant.AUSTAL_M_USV] = Variant.AUSTAL_M_USV
    sub_variant: SubVariant = Field(
        default=SubVariant.M_USV, description="Sub-variant configuration for Austal M_USV vessel"
    )


VariantVesselConfig = Union[
    ArmidaleVesselConfig,
    EducatVesselConfig,
    Oracle22VesselConfig,
    Oracle2_2VesselConfig,
    WaveflyerVesselConfig,
    WhiskeyBravoVesselConfig,
    DMAKVesselConfig,
    MarsVesselConfig,
    FremantleVesselConfig,
    BlueBoatVesselConfig,
    TenggaraVesselConfig,
    TackVesselConfig,
    Austal_M_USV,
]

DEFAULT_VARIANT_CONFIGS_MAP: dict[Variant, VariantVesselConfig] = {
    Variant.ARMIDALE: ArmidaleVesselConfig(),
    Variant.EDUCAT: EducatVesselConfig(),
    Variant.ORACLE_22: Oracle22VesselConfig(),
    Variant.ORACLE_2_2: Oracle2_2VesselConfig(),
    Variant.WAVEFLYER: WaveflyerVesselConfig(),
    Variant.WHISKEY_BRAVO: WhiskeyBravoVesselConfig(),
    Variant.DMAK: DMAKVesselConfig(),
    Variant.MARS: MarsVesselConfig(),
    Variant.FREMANTLE: FremantleVesselConfig(),
    Variant.BLUE_BOAT: BlueBoatVesselConfig(),
    Variant.TENGGARA: TenggaraVesselConfig(),
    Variant.TACK: TackVesselConfig(),
    Variant.AUSTAL_M_USV: Austal_M_USV(),
}


class VariantVesselConfigRoot(RootModel):
    root: VariantVesselConfig = Field(..., discriminator="variant")


def get_vessel_config_io():
    """Get a VesselConfigIO instance using the GAMA_CONFIG_DIR environment variable."""
    from gama_config.gama_vessel_io import VesselConfigIO

    config_dir = os.environ.get("GAMA_CONFIG_DIR")
    if config_dir is None:
        raise ValueError("GAMA_CONFIG_DIR environment variable is not set.")
    return VesselConfigIO(config_directory=config_dir)
