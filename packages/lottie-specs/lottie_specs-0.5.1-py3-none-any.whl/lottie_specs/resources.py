import json
from importlib.resources import files


def schema_path():
    """
    Returns the path to the schema file
    """
    return files("lottie_specs.data").joinpath("lottie.schema.json")


def load_specs(*a, **kw):
    """
    Loads the schema file into python objects
    """
    with open(schema_path(*a, **kw)) as fp:
        return json.load(fp)
