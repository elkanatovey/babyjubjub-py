# Contributing to babyjubjub-py

Thank you for your interest in contributing to babyjubjub-py. This document provides guidelines for contributing to the project.

## Development Setup

### Prerequisites

- Rust 1.56 or later (install via [rustup](https://rustup.rs/))
- Python 3.8 or later
- Git

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/elkanatovey/babyjubjub-py.git
cd babyjubjub-py

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install maturin
pip install maturin

# Build the library in development mode
maturin develop

# Install development dependencies
pip install pytest
```

## Making Changes

### Code Style

- **Rust code**: Follow standard Rust formatting conventions. Run `cargo fmt` before committing.
- **Python code**: Follow PEP 8 style guide.

### Testing

Before submitting a pull request, ensure all tests pass:

```bash
# Run basic tests
python test_basic.py

# Run comprehensive test suite
pytest tests/ -v

# Run Rust tests
cargo test
```

### Adding New Features

1. Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Implement your changes in `src/lib.rs`

3. Add corresponding Python tests in `tests/`

4. Update documentation in README.md if needed

5. Ensure all tests pass

6. Submit a pull request with a clear description of changes

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update tests to cover new functionality
3. Ensure the CI pipeline passes
4. Request review from maintainers

## Reporting Issues

When reporting issues, please include:

- Operating system and version
- Python version
- Rust version
- Minimal reproducible example
- Expected vs actual behavior

## Performance Considerations

When contributing performance improvements:

- Include benchmarks showing the improvement
- Ensure correctness is maintained
- Consider cross-platform implications

## Documentation

- Document all public APIs
- Include usage examples for new features
- Update README.md for user-facing changes

## License

By contributing, you agree that your contributions will be licensed under the Apache-2.0 License.

