# Traia Tools

**Traia Tools** is a collection of custom Python tools for [CrewAI](https://docs.crewai.com/) agents that specialize in Web3 and cryptocurrency trading strategies. This repository is structured as a Python package to be installed via `pip`, providing tools that integrate smoothly into CrewAI environments.

## Features
- **CoinGecko Quote Tool**: Fetch and process cryptocurrency price data from CoinGecko.

## Installation

1. Clone or download this repository.
2. Navigate to the `traia-tools` folder.
3. Install via `pip` (this will use the `pyproject.toml` file):
   ```bash
   pip install .
   ```

## Usage
After installation, you can import and use the tools directly in your code, such as:

```python
from traia_tools.tools import CoinGeckoQuoterTool

# Example usage
quoter = CoinGeckoQuoterTool()
quote = quoter.run("BTC")
print(quote)
```

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository.
2. Create a new branch for your changes.
3. Make your changes and commit them.
4. Push your changes to your fork.
5. Create a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
