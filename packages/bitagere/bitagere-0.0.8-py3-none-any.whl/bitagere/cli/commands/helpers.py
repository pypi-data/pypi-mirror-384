# filepath: /home/hacpy/GEB/bitagere/bitagere/cli/commands/helpers.py
import click
import getpass

NETWORK_URLS = {
    "local": "ws://127.0.0.1:9944",
    "signet": "wss://signet.geb.network/ws",
    # "mainnet": "wss://your-mainnet-node.com/ws", # Example for future mainnet
}


def print_success(message):
    click.echo(click.style(message, fg="green"))


def print_error(message):
    click.echo(click.style(message, fg="red"))


def print_info(message):
    click.echo(click.style(message, fg="blue"))


def _resolve_node_url(network_name: str, custom_url: str = None) -> str:
    if custom_url:
        print_info(f"Using custom node URL: {custom_url}")
        return custom_url

    url = NETWORK_URLS.get(network_name)
    if not url:
        print_error(f"Unknown network: {network_name}. Defaulting to 'local'.")
        return NETWORK_URLS["local"]

    print_info(f"Using '{network_name}' network URL: {url}")
    return url


def _get_passphrase(passphrase: str = None) -> str:
    if not passphrase:
        try:
            passphrase = getpass.getpass("Enter passphrase for wallet: ")
        except Exception as e:
            print_error(f"Failed to get passphrase: {e}")
            raise click.Abort()
    if (
        not passphrase
    ):  # Check if passphrase is still empty (e.g. user just pressed enter)
        print_error("Passphrase cannot be empty.")
        raise click.Abort()
    return passphrase
