# libadctf

A Python library for [describe your library's purpose here].

## Installation

### From PyPI (when published)

```bash
pip install libadctf
```

### Development installation with uv

```bash
# Clone the repository
git clone https://github.com/yourusername/libadctf.git
cd libadctf

# Install in development mode
uv pip install -e .
```

## Usage

```python
from libadctf import main, hello_world

# Use the main function
result = main()

# Use other functions
message = hello_world()
print(message)
```

## Development

This project uses `uv` for dependency management and packaging.

### Setting up development environment

```bash
# Install development dependencies
uv pip install -e ".[dev]"
```

### Running tests

```bash
pytest
```

### Building the package

```bash
uv build
```

### Publishing to PyPI

```bash
# Build the package
uv build

# Publish to PyPI (requires API token)
uv publish
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request