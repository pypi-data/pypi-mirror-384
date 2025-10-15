# bitagere

This is the basic SDK used by development agere.

## Installation

You can install `bitagere` from PyPI using pip:

```bash
pip install bitagere
```

## `bitagere-cli` - Command Line Interface

This project also includes `bitagere-cli`, a powerful command-line tool for interacting with the BitAgere network and managing your wallets. When you install the `bitagere` package, `bitagere-cli` is automatically installed and ready to use.

Key features of `bitagere-cli` include:

- Wallet creation and management (create, list, show address, import).
- Querying chain information.
- Transferring funds.

For detailed instructions on how to use `bitagere-cli`, please refer to the [CLI README](./bitagere/cli/README.md).

To get a quick overview of available commands, you can always run:

```bash
bitagere-cli --help
```

## Development

We welcome contributions to `bitagere`! To get started with development, follow these steps:

### Prerequisites

- [Python](https://www.python.org/) >= 3.8
- [Poetry](https://python-poetry.org/) for dependency management and packaging.

### Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/GEBcore/bitagere.git
   cd bitagere
   ```

2. **Install dependencies:**

   Poetry will install all project dependencies, including development dependencies, into a virtual environment.

   ```bash
   poetry install
   ```

### Project Management with `pyproject.toml` and Poetry

This project uses `pyproject.toml` to define project metadata, dependencies, and build configurations, managed by Poetry.

- **Dependencies**: Project dependencies are listed under `[tool.poetry.dependencies]`, and development dependencies (like linters and testing tools) are under `[tool.poetry.group.dev.dependencies]`.
- **Scripts**: Console scripts are defined under `[tool.poetry.scripts]`.
- **Building**: To build the package (e.g., for distribution), use `poetry build`.
- **Running commands**: To run commands within the project's virtual environment, prefix them with `poetry run`. For example, `poetry run python your_script.py`.

### Logging

Bitagere exposes a helper to set up consistent logging across the SDK:

```python
from bitagere import configure_logging

configure_logging()
```

`configure_logging` accepts standard logging parameters so you can plug in custom handlers, formats, or levels before interacting with the SDK.

### Code Style & Formatting

This project uses [Black](https://github.com/psf/black) for code formatting. Before committing your changes, please format your code:

```bash
poetry run black .
```

Configuration for Black can be found in the `pyproject.toml` file under the `[tool.black]` section.

### Running Tests

To run the test suite using Python's built-in `unittest` module:

```bash
poetry run python -m unittest discover -s tests
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.
