# PLINKFORMMATER

This repository is designed to transform genotype data from the Muster SNPs/download endpoint into PLINK-compatible data, which can then be processed by PyLMM. The primary aim is to facilitate genomic data transformation for linear mixed models. This tool should, in theory, also work with GEMMA and other software that consumes standard PLINK file formats, though it has been primarily tested with PyLMM.

## Getting Started

### Prerequisites
To use this repository, you must have the following dependencies installed:

+ Python 3.8 or above
+ PLINK 2.0
+ Poetry

**Install dependencies**:
```
poetry install
```

**Activate virtual environment**:
```
poetry shell
```

**Install PLINK**: 

You can download PLINK from the [official website](https://www.cog-genomics.org/plink/2.0/). Ensure the PLINK executable is in your system's PATH, or you can specify the path to the PLINK binary in your environment settings.

To verify PLINK installation, run:
```
plink2 --version
```

## Tests

To run tests run the following command:
```
pytest -s tests
```

## Publishing to Pypi

0. Update version

```
poetry version patch
```

1. Build any changes

```
poetry build
```

2. Set the correct PyPI repository URL

```
poetry config repositories.pypi https://upload.pypi.org/legacy/
```

3. Set API token

```
poetry config pypi-token.pypi pypi-YourActualTokenHere
```

4. Publish

```
poetry publish
```
