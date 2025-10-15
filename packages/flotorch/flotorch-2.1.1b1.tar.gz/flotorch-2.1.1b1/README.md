# Flotorch Python

A modular Python framework for AI agents and LLM interactions with support for multiple AI frameworks.

## Features

- **Modular Design**: Install only what you need
- **SDK Core**: Foundation for all AI interactions
- **ADK Integration**: Google Agent Development Kit support
- **Future Modules**: CrewAI, AutoGen, LangGraph support (coming soon)
- **Flexible Dependencies**: Choose your installation level

## Installation

### Option 1: Install everything (Recommended)
```bash
# Install all modules and dependencies
pip install flotorch
```

### Option 2: Install specific modules only
```bash
# Install only SDK (core functionality)
pip install flotorch[sdk]

# Install SDK + ADK (Google Agent Development Kit)
pip install flotorch[adk]
```

### Option 3: Development installation
```bash
# Install in development mode with all dependencies
pip install -e .

# Install with development tools
pip install -e .[dev]
```

### Option 4: Beta/Pre-release installation
```bash
# Install latest beta version
pip install --pre flotorch

# Install specific beta version
pip install flotorch==0.1.0b1

# Install beta with pre-release flag
pip install --pre flotorch==0.1.0b1

# Install beta with ADK
pip install --pre flotorch[adk]

# Install specific beta version with ADK
pip install --pre flotorch[adk]==0.1.0b1

# Install beta with SDK only
pip install --pre flotorch[sdk]

# Install specific beta version with SDK
pip install --pre flotorch[sdk]==0.1.0b1
```

**Note**: The `--pre` flag is required to install beta/pre-release versions. Without it, pip will only install stable releases.



## Module Dependencies

### SDK (Core) - Always included
- `httpx>=0.24` - HTTP client
- `pydantic>=1.10` - Data validation
- `openai>=1.0.0` - OpenAI API client

### ADK Module
- **Requires**: SDK dependencies
- **Adds**: `google-adk>=1.5.0`

### Development Tools
- `build>=0.10.0` - Package building
- `twine>=4.0.0` - PyPI upload
- `pytest>=7.0.0` - Testing
- `black>=23.0.0` - Code formatting
- `flake8>=6.0.0` - Linting
- `mypy>=1.0.0` - Type checking

## Project Structure

```
flotorch/
├── __init__.py
├── sdk/           # Core SDK functionality
│   ├── __init__.py
│   ├── llm.py     # LLM client
│   └── utils/     # Shared utilities
├── adk/           # Google Agent Development Kit
│   ├── __init__.py
│   ├── agent.py   # ADK agent wrapper
│   └── llm.py     # ADK LLM integration
└── utils/         # Shared utilities
    ├── http_utils.py
    ├── llm_utils.py
    ├── logging_utils.py
    └── memory_utils.py
```

## Development

### Easy Building with Makefile

The easiest way to build and manage your package is using the provided Makefile:

#### Direct Version Specification (Recommended)
```bash
# Build with specific version
make build VERSION=0.1.0
make build-beta VERSION=0.1.0b1
make build-prod VERSION=0.1.0

# Test with specific version
make test VERSION=0.1.0

# Publish with specific version
make publish-test VERSION=0.1.0b1
make publish-prod VERSION=0.1.0

# Full workflow with specific version
make all VERSION=0.1.0b1
```

#### Interactive Commands (prompts for version)
```bash
# Interactive builds (if no VERSION specified)
make build          # Prompts: "Enter version (e.g., 0.1.0):"
make build-beta     # Prompts: "Enter beta version (e.g., 0.1.0b1):"
make build-prod     # Prompts: "Enter production version (e.g., 0.1.0):"

# Interactive testing and publishing
make test           # Prompts: "Enter version to test (e.g., 0.1.0):"
make publish-test   # Prompts: "Enter version to publish (e.g., 0.1.0b1):"
make publish-prod   # Prompts: "Enter version to publish (e.g., 0.1.0):"
```

#### Quick Commands (pre-defined versions)
```bash
# Quick development builds
make quick-build        # Builds version 0.1.0
make quick-test         # Tests version 0.1.0
make quick-beta         # Builds version 0.1.0b1

# Quick publishing
make quick-publish-test # Publishes 0.1.0b1 to TestPyPI
make quick-publish      # Publishes 0.1.0 to PyPI
```

#### Development Setup
```bash
# Set up development environment
make install        # Install in development mode
make install-dev    # Install with development dependencies
make dev-setup      # Complete development setup and test

# Other useful commands
make help           # Show all available commands
make clean          # Clean build artifacts
```

### Manual Building (Alternative)

If you prefer to use the build script directly:

```bash
# Build with specific version
python build.py --version 0.1.0 --build

# Build beta version
python build.py --version 0.1.0b1 --build
```

### Testing
```bash
# Test installation
python build.py --version 0.1.0 --test

# Test specific module installations
python -c "from flotorch.sdk.llm import FlotorchLLM; print('SDK works!')"
python -c "from flotorch.adk.agent import FlotorchADKAgent; print('ADK works!')"
```

### Publishing
```bash
# Publish to TestPyPI
python build.py --version 0.1.0b1 --publish-test

# Publish to PyPI
python build.py --version 0.1.0 --publish
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/flotorch/flotorch-python/issues)
- **Documentation**: [docs.flotorch.com](https://docs.flotorch.com)
- **Discussions**: [GitHub Discussions](https://github.com/flotorch/flotorch-python/discussions)
