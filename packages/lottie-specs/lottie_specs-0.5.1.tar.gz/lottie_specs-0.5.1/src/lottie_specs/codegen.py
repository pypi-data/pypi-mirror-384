import collections


class ModuleDeps:
    """
    Represent dependencies from external modules
    """

    def __init__(self):
        self.deps = collections.defaultdict(set)

    def add(self, module: str, name: str):
        self.deps[module].add(name)

    def string_for_item(self, item) -> str:
        """
        Python import string
        """
        module, deps = item
        return "from %s import %s" % (module, ", ".join(sorted(deps)))

    def __iter__(self):
        return iter(sorted(self.deps.items(), key=lambda a: a[0].replace(".", "~")))


class InternalDeps:
    """
    Represents and resolves internal dependencies
    """

    def __init__(self):
        self.deps = collections.defaultdict(set)

    def add(self, dependant: str, dependency: str):
        self.deps[dependant].add(dependency)

    def init(self, dependant: str):
        self.deps[dependant] = set()

    def resolve(self):
        prev_deps = -1
        deps = dict(self.deps)
        resolved = set()
        while len(deps):
            if len(deps) == prev_deps:
                raise Exception("Dependency cycle %s" % deps.keys())

            new_deps = {}
            for name, dependencies in deps.items():
                dependencies = dependencies - resolved
                if not dependencies:
                    resolved.add(name)
                    yield name
                else:
                    new_deps[name] = dependencies

            prev_deps = len(deps)
            deps = new_deps
