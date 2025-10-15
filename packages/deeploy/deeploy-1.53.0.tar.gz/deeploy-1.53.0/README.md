<div align="center">

<a href="https://deeploy.ml"><img src="./docs/content/img/Logo%20(original).png" width="250px"></a>

**Deeploy - Deploy AI with confidence**

[![PyPi license](https://img.shields.io/pypi/l/deeploy.svg?color=blue)](https://img.shields.io/pypi/l/deeploy.svg?color=blue)
[![PyPI version shields.io](https://img.shields.io/pypi/v/deeploy.svg)](https://img.shields.io/pypi/v/deeploy.svg)
[![CI](https://gitlab.com/deeploy-ml/deeploy-python-client/badges/master/pipeline.svg)](https://gitlab.com/deeploy-ml/deeploy-python-client/pipelines)

</div>

---

## Deeploy Python Client

Python client for working with Deeploy. This client for the Deeploy is build with the following goals:

1. Simplify communication with the Deeploy API from your (local) Python environment.
2. Simplify creation of custom model, explainer and transformer images to deploy on Deeploy with template generation via CLI.
3. Ease the step from (local) development to production ML workloads.

Detailed documentation for this Python module can be found [here](https://docs.deeploy.ml/python-client/introduction).

## Python Version Support

This package supports Python 3.10, 3.11, and 3.12.

## Getting started with the CLI

Use the CLI as a starting point for creating your custom model, explainer and transformer images to deploy on Deeploy. To spawn a sample project:

```bash
deeploy generate-template -n <project_name> -i model -i transformer -i explainer
```

```-n <project_name>``` Specifies the name of project. The project is generated under directory ***custom_<project_name>***\
```-i model``` Generates model template \
```-i explainer``` Generates explainer template \
```-i transformer``` Generates transformer template

More instructions about internal working is available in generated README that is created when you generate the sample project.

To start working with the templates move into the generated directory and follow instructions there.

```bash
cd custom_<project_name>
```
