# bitagere-cli

`bitagere-cli` is a command-line interface tool for interacting with the BitAgere network and managing wallets.

## Installation

When you install the `bitagere` package, `bitagere-cli` is automatically installed and added to your system's PATH.

```bash
pip install bitagere
```

## Basic Usage

Once installed, you can use `bitagere-cli` from your terminal.

To see a list of available commands and options:

```bash
bitagere-cli --help
```

### Wallet Management

*   **Create a new wallet:**
    ```bash
    bitagere-cli wallet create <wallet_name>
    ```
*   **List existing wallets:**
    ```bash
    bitagere-cli wallet list
    ```
*   **Show wallet address:**
    ```bash
    bitagere-cli wallet show <wallet_name>
    ```
*   **Import a wallet from a mnemonic phrase:**
    ```bash
    bitagere-cli wallet import <wallet_name> "your mnemonic phrase here"
    ```

### Interacting with the Chain

*   **Get chain information:**
    ```bash
    bitagere-cli chain info
    ```
*   **Transfer funds:**
    ```bash
    bitagere-cli transfer <from_wallet> <to_address> <amount>
    ```

For more detailed information on specific commands, use the `--help` option with that command. For example:

```bash
bitagere-cli wallet create --help
```
