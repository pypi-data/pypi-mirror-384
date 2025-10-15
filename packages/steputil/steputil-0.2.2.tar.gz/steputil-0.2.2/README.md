# steputil

Utilities to simplify creation of pipeline steps.

## Installation

```bash
pip install steputil
```

## Usage

```python
import steputil

# Add usage examples here
```

## Development

### Setup

1. Clone the repository:
```bash
git clone https://github.com/k-pipe/step-util.git
cd step-util
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src/ tests/
```

### Type Checking

```bash
mypy src/
```

## Publishing

This package is automatically published to PyPI when a new release is created on GitHub.

To create a new release:
1. Update the version in `pyproject.toml`
2. Create a new git tag: `git tag v0.1.0`
3. Push the tag: `git push origin v0.1.0`

The GitHub Action will automatically build and publish the package to PyPI.

## License

MIT License - see LICENSE file for details.
