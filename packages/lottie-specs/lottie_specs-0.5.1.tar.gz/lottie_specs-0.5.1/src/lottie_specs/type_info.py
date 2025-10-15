import json
import collections
from .schema import Schema, SchemaPath


class TypeSystem:
    """
    Type system view around the lottie schema
    """

    def __init__(self, schema: Schema):
        self.types = {}
        self.modules = {}
        schema.type = self
        self.schema = schema

        for name, value in (schema / "$defs").items():
            self.modules[name] = Module(self, value)

        for type in self.types.values():
            type.resolve()

    def from_path(self, path: SchemaPath) -> "Type":
        if isinstance(path, str):
            path = SchemaPath(path)
        path.ensure_defs()
        return self.types[str(path)]

    @staticmethod
    def load(path):
        with open(path) as file:
            schema_data = Schema(json.load(file))
        return TypeSystem(schema_data)

    def resolve_type(self, schema: Schema):
        """
        Extracts type info from the schema's `type` or `$ref`

        Returns:
            * a string for builtin types (eg: `number`)
            * a Type instance for complex types
            * an array when there is the possibility for multiple types
            * None if the type cannot be determined
        """
        if "oneOf" in schema:
            local_type = schema.get("type", None)
            if local_type is not None:
                return local_type
            return [self.resolve_type(choice) for choice in schema / "oneOf"]
        if "$ref" in schema:
            return self.types[schema["$ref"]]
        return schema.get("type", None)

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.schema.get("$id"))


class Type:
    """
    Base wrapper for type information
    """

    def __init__(self, type_system: TypeSystem, schema: Schema):
        self.type_system = type_system
        self.schema = schema
        self.ref = str(schema.path)
        self.slug = schema.path.chunks[-1]
        self.title = schema.get("title", self.slug)
        self.description = schema.get("description", self.title)
        id_chunks = list(schema.path.chunks)
        id_chunks.pop(0)
        self.id = "-".join(map(str, id_chunks))
        schema.type = self

    def resolve(self):
        pass

    def __repr__(self):
        return "<%s %s %s>" % (self.__class__.__name__, self.schema.path, self.id)

    def __eq__(self, o):
        return isinstance(o, Type) and self.id == o.id


class ListOfType:
    def __init__(self, item_type: Type):
        self.item_type = item_type

    def __eq__(self, o):
        return isinstance(o, ListOfType) and self.item_type == o.item_type


class Property(Type):
    """
    Represents a class data memeber
    """

    def __init__(self, name: str, type_system: TypeSystem, schema: Schema):
        super().__init__(type_system, schema)
        self.name = name
        self.const = schema.get("const", None)
        self.default = schema.get("default", None)
        self.required = False

    def resolve_type(self, schema: Schema):
        if "oneOf" in schema:
            local_type = schema.get("type", None)
            if local_type is not None:
                return local_type
            return [self.resolve_type(choice) for choice in schema / "oneOf"]
        if "$ref" in schema:
            return self.type_system.types[schema["$ref"]]
        return schema.get("type", None)

    def resolve(self):
        self.type = self.type_system.resolve_type(self.schema)
        if "items" in self.schema:
            self.type = ListOfType(self.type_system.resolve_type(self.schema / "items"))

    def merge(self, duplicates):
        type = self.type
        for duplicate in duplicates:
            duplicate.resolve()
            other_type = duplicate.type
            if type != other_type:
                if not isinstance(type, list):
                    type = [type, other_type]
                elif other_type not in type:
                    type.append(other_type)

            if duplicate.const is not None:
                self.const = None

            if duplicate.description and duplicate.description not in self.description:
                self.description += " or " + duplicate.description

        self.type = type


class RequiredProperties:
    """
    Handles complex property requirements
    """

    def __init__(self, sets=None):
        self.sets = sets or []

    def add_set(self, data: set):
        self.sets.append(data)

    def merge(self, other: "RequiredProperties"):
        if not self.sets:
            self.sets = list(other.sets)
            return
        if not other.sets:
            return

        new_sets = []
        for my_set in self.sets:
            for other_set in other.sets:
                if other_set:
                    new_sets.append(my_set | other_set)

        self.sets = new_sets

    def is_simple(self):
        return len(self.sets) < 1

    def has(self, value):
        if len(self.sets) == 1:
            return value in self.sets
        elif len(self.sets) == 0:
            return False


class Class(Type):
    """
    Class type, contains multiple properties and exposes inheritance
    """

    def __init__(self, type_system: TypeSystem, schema: Schema):
        super().__init__(type_system, schema)

        self.base_refs = []
        self.properties = {}
        self.bases = []
        self.derived = []
        self.concrete_descendants = []
        self.duplicate_props = collections.defaultdict(list)
        self.required = RequiredProperties()

        if "allOf" in schema:
            for item in schema / "allOf":
                if "$ref" in item:
                    self.base_refs.append(item.get("$ref"))
                else:
                    self.get_properties(item)

        if "oneOf" in schema:
            for item in schema / "oneOf":
                self.get_properties(item)

        self.get_properties(schema)

    def get_properties(self, schema: Schema):
        if "properties" in schema:
            for name, value in (schema / "properties").items():
                if (
                    isinstance(value.schema, dict) and
                    len(value.schema) == 1 and
                    list(value.schema.keys())[0] == "not"
                ):
                    continue
                prop = Property(name, self.type_system, value)
                if name in self.properties:
                    self.duplicate_props[name].append(prop)
                else:
                    self.properties[name] = prop
        self.required.merge(self.get_required(schema))

    def get_required(self, schema):
        required = RequiredProperties()
        if "required" in schema:
            required.merge(RequiredProperties([set(schema["required"])]))

        if "if" in schema:
            r1 = self.get_required(schema / "if")
            r2 = self.get_required(schema / "else") if "else" in schema else RequiredProperties()
            required.merge(RequiredProperties(r1.sets + r2.sets))

        return required

    def resolve(self):
        for ref in self.base_refs:
            base = self.type_system.types[ref]
            self.bases.append(base)
            base.derived.append(self)
            self.required.merge(base.required)

        for name, prop in self.properties.items():
            prop.resolve()
            prop.merge(self.duplicate_props[name])
            prop.required = self.required.has(name)

    def all_properties(self, props=None):
        if props is None:
            props = {}

        for base in self.bases:
            base.all_properties(props)

        props.update(self.properties)
        return props


class ConcreteClass(Type):
    """
    When a class has multiple subtypes this represents the type for the base class
    """

    def __init__(self, type_system: TypeSystem, schema: Schema):
        super().__init__(type_system, schema)
        self.abstract_ref = self.ref.replace("/all-", "/")[:-1]
        self.concrete = []

    def resolve(self):
        self.abstract = self.type_system.types[self.abstract_ref]
        for schema in self.schema / "oneOf":
            self.concrete.append(self.type_system.from_path(schema.get("$ref")))
        self.abstract.concrete_descendants = self.concrete


class EnumValue(Type):
    """
    Value within an Enum
    """

    def __init__(self, type_system: TypeSystem, schema: Schema):
        super().__init__(type_system, schema)
        self.value = self.schema.get("const")
        if self.description == self.title:
            self.description = None


class Enum(Type):
    """
    Enumeration
    """

    def __init__(self, type_system: TypeSystem, schema: Schema):
        super().__init__(type_system, schema)
        self.values = [
            EnumValue(type_system, value)
            for value in schema / "oneOf"
        ]


class Module(Type):
    """
    Logical module, contains multiple types
    """

    def __init__(self, type_system: TypeSystem, schema: Schema):
        super().__init__(type_system, schema)
        self.types = {}

        for name, value in schema.items():
            type = self.make_type(name, value)
            self.type_system.types[type.ref] = type
            self.types[type.slug] = type

    def make_type(self, name: str, schema: Schema):
        type = schema.get("type", None)
        if type == "object":
            return Class(self.type_system, schema)

        if type in ("integer", "string") and "oneOf" in schema:
            return Enum(self.type_system, schema)

        if name.startswith("all-"):
            return ConcreteClass(self.type_system, schema)

        return Type(self.type_system, schema)
