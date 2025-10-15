import re

import setuptools

with open("docs/pypi.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

VERSIONFILE = "deeploy/_version.py"
VERSIONRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
version_string = open(VERSIONFILE, "rt").read()
mo = re.search(VERSIONRE, version_string, re.M)
if mo:
    version = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))

setuptools.setup(
    name="deeploy",
    version=version,
    description="The official Deeploy client for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Tim Kleinloog",
    author_email="opensource@deeploy.ml",
    packages=setuptools.find_packages(),
    package_data={"": ["*.j2", "*.bst", "*.dill", "*.json"]},
    include_package_data=True,
    url="https://gitlab.com/deeploy-ml/deeploy-python-client",
    project_urls={
        "Documentation": "https://deeploy-ml.gitlab.io/deeploy-python-client/",
        "Deeploy website": "https://deeploy.ml",
    },
    install_requires=[
        "pydantic <3, >2",
        "requests>=2.31.0",
        "joblib==1.4.2",
        "dill==0.3.7",
        "click",
        "Jinja2",
        "numpy",
        "pandas",
    ],
    extras_require={
        "fair": [
            "numpy>=1.17.2",
            "pandas>=0.25.1",
            "scikit-learn>=0.22.1",
            "fairlearn>=0.5.0",
            "fairsd~=0.1.0",
        ],
        "docker": [
            "kserve[storage]==0.15.1",
            "nest-asyncio~=1.4.0",
            "attrs>=23.1.0"
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10, <3.13",
    entry_points={"console_scripts": ["deeploy = deeploy.cli.deeploycli:main"]},
)
