# GAMA Config

GAMA Config is used to load config stored inside the `.gama` folder.

## Install

* `pip install -e ./libs/gama_config`
* or...
* `pip install gama_config` (Public on [PyPi](https://pypi.org/project/gama-config/))

### Generating schemas

After changing the dataclasses, you can generate the schemas with:

```bash
python3 -m gama_config.generate_schemas
```

## Running tests

```bash
python3 -m pytest -v ./libs/gama_config
```