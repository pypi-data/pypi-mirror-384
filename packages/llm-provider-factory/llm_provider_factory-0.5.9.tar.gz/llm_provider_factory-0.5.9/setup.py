"""Setup script for LLM Provider Factory."""

from setuptools import setup, find_packages

setup(
    name="llm-provider-factory",
    use_scm_version=True,
    setup_requires=["setuptools-scm"],
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)