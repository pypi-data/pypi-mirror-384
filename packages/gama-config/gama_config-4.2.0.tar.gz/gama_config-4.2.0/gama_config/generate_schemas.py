import os
import json
from gama_config.gama_vessel import VariantVesselConfigRoot
from gama_config.gama_gs import GamaGsConfig
from pydantic.json_schema import GenerateJsonSchema


class CustomGenerateJsonSchema(GenerateJsonSchema):
    def generate(self, schema, mode="validation"):
        json_schema = super().generate(schema, mode=mode)
        json_schema["$schema"] = self.schema_dialect
        return json_schema


def generate_schemas():
    """Generates the schemas for the config files"""

    SCHEMAS_PATH = os.path.join(os.path.dirname(__file__), "schemas")
    with open(os.path.join(SCHEMAS_PATH, "gama_vessel.schema.json"), "w") as f:
        main_model_schema = VariantVesselConfigRoot.model_json_schema()
        json.dump(main_model_schema, f, indent=2)
    with open(os.path.join(SCHEMAS_PATH, "gama_gs.schema.json"), "w") as f:
        main_model_schema = GamaGsConfig.model_json_schema()
        json.dump(main_model_schema, f, indent=2)


if __name__ == "__main__":
    print("Generating schemas...")
    generate_schemas()
