#!python

import sys
import json
import pathlib
import argparse

from lottie_specs.schema import SchemaPath, Schema
from lottie_specs.markdown import lottie_markdown

# By default, tool expects a link for all schema files.
# This is generally true, but may not always be the case
unneeded_links = [
    ("shapes", "base-gradient"),
    ("layers", "unknown-layer"),
    ("shapes", "unknown-shape")
]


class Validator:
    def __init__(self):
        self.valid_refs = set()
        self.expected_refs = set()
        self.has_error = False
        self.root = None

    def validate(self, schema_root):
        self.root = Schema(schema_root, None)
        self.check_version(self.root)
        self.collect_defs(self.root / "$defs")
        self.validate_recursive(self.root)
        for unused in (self.expected_refs - self.valid_refs):
            self.show_error("Unused def: %s" % unused)

    def show_error(self, msg):
        self.has_error = True
        print(msg)

    def error(self, schema: Schema, message):
        self.show_error("%s: %s" % (schema.path, message))

    def validate_ref(self, schema: Schema):
        if schema.value in self.valid_refs:
            return

        if SchemaPath(schema.value).walk(self.root) is None:
            self.error(schema, "Invalid $ref: %s" % schema.value)
            return

        self.valid_refs.add(schema.value)

    def validate_schema(self, schema: Schema):
        if "type" in schema:
            type = schema["type"]
            if type not in ("object", "array", "number", "integer", "boolean", "string"):
                self.error(schema, "Unknown type: %s" % type)
        if "$ref" in schema:
            self.validate_ref(schema / "$ref")

    def validate_recursive(self, schema: Schema):
        self.validate_schema(schema)
        for child in schema:
            self.validate_recursive(child)

    def collect_defs(self, schema):
        for child in schema:
            if "type" in child:
                self.expected_refs.add(str(child.path))
            else:
                self.collect_defs(child)

    def check_version(self, schema: Schema):
        version_number = schema.get("$version", None)
        if version_number is None:
            return

        major_version = version_number // 10000
        minor_version = (version_number % 10000) // 100
        patch_version = version_number % 100

        components = [major_version, minor_version]
        if patch_version != 0:
            components.append(patch_version)

        version_string = ".".join(map(str, components))

        if version_string not in schema["$id"]:
            self.error(schema, "Mismatched URI version - expected: %s" % version_string)

    def get_page(self, ref: str, name: str, html_path: pathlib.Path, file_cache: dict):
        if name in file_cache:
            return file_cache[name]
        file = html_path / name / "index.html"
        while True:
            if not file.exists():
                file_cache[name] = None
                self.show_error("%s: Missing page %s" % (ref, name))
                return None

            dom = lxml.html.parse(str(file))

            # Handle redirects
            redirect = dom.xpath(".//meta[@http-equiv='refresh']/@content")
            if redirect:
                file = (file.parent / redirect[0].split("url=")[-1] / "index.html").resolve()
                continue

            page_data = dom.xpath(".//*[@id]/@id")
            file_cache[name] = page_data
            return page_data

    def check_links(self, html_path: pathlib.Path):
        checked = set()
        file_cache = {}
        ts = lottie_markdown.typed_schema(self.root)

        for link in unneeded_links:
            checked.add(link)

        for ref in self.expected_refs:
            link = ts.from_path(ref).link
            key = (link.page, link.anchor)
            if key in checked:
                continue
            checked.add(key)

            page_data = self.get_page(ref, link.page, html_path, file_cache)
            if page_data and link.anchor not in page_data:
                self.show_error("%s: Missing anchor %s.md %s" % (ref, link.page, link.anchor))


if __name__ == "__main__":
    root = pathlib.Path()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--schema",
        help="Schema file to validate",
        type=pathlib.Path,
        default=root / "docs" / "lottie.schema.json"
    )
    parser.add_argument("--html", help="Path to the html to check links", type=pathlib.Path)
    parser.add_argument("--ignore", "-i", help="refs to ignore", action="append", default=[])
    args = parser.parse_args()
    for ignored in args.ignore:
        unneeded_links.append(tuple(ignored.split("/")))

    with open(args.schema) as file:
        data = json.load(file)

    validator = Validator()
    validator.validate(data)

    if args.html:
        import lxml.html
        validator.check_links(args.html)

    if validator.has_error:
        sys.exit(1)
