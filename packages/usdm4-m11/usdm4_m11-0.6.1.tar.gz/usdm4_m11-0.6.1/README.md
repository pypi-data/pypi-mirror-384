# USDM4 M11 Protocol Package

A Python package for processing M11 protocol documents and converting them to USDM format.

## Installation

```bash
pip install -e .
```

Or install the dependencies directly from the requirements.txt file:

```bash
pip install -r requirements.txt
```

This package uses a src-based layout, with the package code located in the `src/usdm4_m11` directory.

## Usage

```python
from usdm4_m11 import M11Protocol

# Initialize the protocol processor
protocol = M11Protocol(filepath="path/to/m11_protocol.docx", system_name="YourSystem", system_version="1.0.0")

# Process the protocol
await protocol.process()

# Convert to USDM format
usdm_data = protocol.to_usdm()
```

# Build

Build as a normal package

- Run `pytest`, ensure coverage and all tests pass
- Run `ruff format`
- Run `ruff check`, ensure no errors
- Build with `python3 -m build --sdist --wheel`
- Upload to pypi.org using `twine upload dist/*`
