#!python
import pathlib
import argparse

from lottie_specs.schema import Schema
from lottie_specs import type_info


def collect_ts(typesys: type_info.TypeSystem):
    data = []
    for name, mod in typesys.modules.items():
        collect_mod(name, mod, data)
    return data


def collect_mod(mod_name: str, mod: type_info.Module, data: list):
    for type_name, type in mod.types.items():
        prefix = "%s.%s." % (mod_name, type_name)
        if isinstance(type, type_info.Class):
            collect_class(prefix, type, data)
        elif isinstance(type, type_info.Enum):
            collect_enum(prefix, type, data)


def collect_class(prefix: str, cls: type_info.Class, data: list):
    for prop in cls.properties.keys():
        data.append(prefix + prop)


def collect_enum(prefix: str, cls: type_info.Enum, data: list):
    for val in cls.values:
        data.append(prefix + val.title)


parser = argparse.ArgumentParser()
parser.add_argument("schema", type=pathlib.Path)

args = parser.parse_args()
typesys = type_info.TypeSystem.load(args.schema)

print("\n".join(sorted(collect_ts(typesys))))
