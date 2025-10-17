# Hoppr CycloneDX Models

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/hoppr-cyclonedx-models?logo=python&style=plastic)
[![PyPI - Version](https://img.shields.io/pypi/v/hoppr-cyclonedx-models?style=plastic)](https://pypi.org/project/hoppr-cyclonedx-models)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/hoppr-cyclonedx-models?style=plastic)](https://pypi.org/project/hoppr-cyclonedx-models)
[![PyPI - License](https://img.shields.io/pypi/l/hoppr-cyclonedx-models?style=plastic)](LICENSE)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json&style=plastic)](https://python-poetry.org/)

Serializable CycloneDX Models. Quickly get up and running with models generated directly off the specification.

Current generated models can be found [here](hoppr_cyclonedx_models).

## Installation

Install using `pip install --upgrade hoppr-cyclonedx-models` or `poetry add hoppr-cyclonedx-models`.

## A Simple Example

```python
>>> from hoppr_cyclonedx_models.cyclonedx_1_5 import Component
>>> data = {"type": "library", "purl": "pkg:pypi/django@1.11.1", "name": "django", "version": "1.11.1"}
>>> component = Component(**data)
>>> component
>>> print(component)
Component(
    type='library',
    mime_type=None,
    bom_ref=None,
    supplier=None,
    author=None,
    publisher=None,
    group=None,
    name='django',
    version='1.11.1',
    description=None,
    scope=<Scope.REQUIRED: 'required'>,
    hashes=None,
    licenses=None,
    copyright=None,
    cpe=None,
    purl='pkg:pypi/django@1.11.1',
    swid=None,
    modified=None,
    pedigree=None,
    externalReferences=None,
    components=None,
    evidence=None,
    releaseNotes=None,
    modelCard=None,
    data=None,
    properties=None,
    signature=None
)
```

## Contributing

For guidance setting up a development environment and how to contribute to `hoppr-cyclonedx-models`,
see [Contributing to Hoppr](https://hoppr.dev/docs/development/contributing).
