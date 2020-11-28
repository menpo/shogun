import sys
from distutils.version import StrictVersion

from setuptools import find_packages, setup

PY_VER = StrictVersion(f"{sys.version_info.major}.{sys.version_info.minor}")


def get_version_and_cmdclass(package_path):
    """Load version.py module without importing the whole package.
    Template code from miniver
    """
    import os
    from importlib.util import module_from_spec, spec_from_file_location

    spec = spec_from_file_location("version", os.path.join(package_path, "_version.py"))
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.__version__, module.cmdclass


with open("README.md", "r") as fh:
    long_description = fh.read()


# Require dataclasses backport if Python <= 3.6
install_requires = []
if PY_VER <= StrictVersion("3.6"):
    install_requires.append("dataclasses")


version, cmdclass = get_version_and_cmdclass("shogun")
setup(
    name="shogun",
    version=version,
    cmdclass=cmdclass,
    description="Opinionated Typed Configuration",
    long_description=long_description,
    author="The Menpo Team",
    author_email="hello@menpo.org",
    url="https://github.com/menpo/shogun",
    packages=find_packages(),
    install_requires=install_requires,
    tests_require=[
        "attrs>=20",
        "pytest>=5.0",
        "pytest-mock>=1.0",
        "pytest-black>=0.3",
        "pytest-cov>=2.0",
        "black>=20.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
