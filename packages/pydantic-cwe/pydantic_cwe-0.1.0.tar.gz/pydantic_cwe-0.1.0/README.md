# pydantic-cwe

`pydantic-cwe` provides a structured, object-oriented way to work with the Common Weakness Enumeration (CWE) database. 
By modeling CWE entries as Pydantic objects, this library enables developers and security researchers to 
programmatically access, validate, and manipulate CWE data with ease. Ideal for static analysis tools, vulnerability 
scanners, or custom security pipelines.

## Installation

```bash
pip install pydantic-cwe
```

## Usage

### Loading a CWE catalog

```python
from pydantic_cwe import Loader

# Create a loader instance
loader = Loader()

# Load the catalog
catalog = loader.load()

# Print some basic information about the catalog
print(f"Catalog Name: {catalog.name}")
print(f"Catalog Version: {catalog.version}")
print(f"Catalog Date: {catalog.date}")
print(f"Number of weaknesses: {len(catalog.weaknesses.weaknesses)}")
```

### Working with weaknesses

```python
from pydantic_cwe import Loader

loader = Loader()
catalog = loader.load()

# Get weaknesses ordered by ID
for weakness in catalog.get_ordered_weaknesses():
    if weakness.status == 'Deprecated':
        continue

    print(f"ID: {weakness.id}")
    print(f"Name: {weakness.name}")
    print(f"Abstraction: {weakness.abstraction}")
    print(f"Structure: {weakness.structure}")
    print(f"Status: {weakness.status}")
    print(f"Description: {weakness.description}")
```

## Project Structure

The project follows a standard Python library structure:

- `examples/`: Example scripts
- `pydantic_cwe/`: Main package directory
  - `models`: Pydantic models for CWE data
  - `__init__.py`: Package initialization and exports
  - `loader.py`: XML loading and parsing functionality
- `tests/`: Unit tests

## Development

### Setting up the development environment

```bash
# Clone the repository
git clone https://github.com/epicosy/pydantic-cwe.git
cd pydantic-cwe

# Create a virtual environment
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Install development dependencies
pip install -e ".[test]"
```

### Running tests

```bash
pytest
```
