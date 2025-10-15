import pathlib
from setuptools import setup, find_namespace_packages

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "Readme.md").read_text(encoding="utf-8")

setup(
    name="lottie_specs",
    # version="1.0.1",
    version="0.5.1",  # Dev version, until we release properly, after that sync with lottie-specs versioning
    description="Tools to load the Lottie standard specs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lottie/lottie-specs-python",
    author="Lottie Animation Community",
    packages=find_namespace_packages(where="src"),
    package_data={"lottie_specs.data": ["*.json"]},
    package_dir={"": "src"},
    python_requires=">=3.10, <4",
    scripts=[
        "bin/enumerate-props.py",
        "bin/render_shape.py",
        "bin/schema-merge.py",
        "bin/schema-validate.py",
    ],
    extras_require={
        "docs": [
            "lxml==5.4.0",
            "html5lib==1.1",
            "source_translator==1.0.1",
            "graphviz==0.20.1",
            "mkdocs==1.6.1",
            "latex2mathml==3.77.0"
        ],
        "render": [
            "lottie==0.7.2",
            "source_translator==1.1.0",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/lottie/lottie-specs-python/issues",
        "Source": "https://github.com/lottie/lottie-specs-python",
    },
    # entry_points={
    #     "mkdocs.plugins": []
    # }
)
