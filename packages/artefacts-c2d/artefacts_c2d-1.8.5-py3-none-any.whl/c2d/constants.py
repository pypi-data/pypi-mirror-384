from importlib.resources import files

import yaml


def _get_capabilities() -> tuple:
    """
    Get known capabilities from file local to the package.

    If the file is found, it is parsed as YAML and returns the data.
    If the file is not found, raises an error, as undesired situation.
    """
    capabilities = files("c2d").joinpath("capabilities.yml")
    if capabilities.is_file():
        with capabilities.open("r") as f:
            data = yaml.safe_load(f.read())
            return (data["version"], data["tags"])
    else:
        raise Exception(
            "Missing capabilities file. Broken package? A fix may be to reinstall the package."
        )


CURRENT_ARTEFACTS_INFRA_VERSION, SUPPORTED_IMAGE_TAGS = _get_capabilities()

LEGACY_FRAMEWORK_LAST_SUPPORTED = {
    "noetic": "0.7.0",
    "galactic": "0.7.0",
    "challenge2022": "0.9.3",
}
