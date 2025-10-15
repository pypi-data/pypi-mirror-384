import click
import json
from bitagere.substrate.interface import AgereInterface
import getpass

NETWORK_URLS = {
    "local": "ws://127.0.0.1:9944",
    "signet": "wss://signet.geb.network/ws",
    # "mainnet": "wss://your-mainnet-node.com/ws", # Example for future mainnet
}


# Helper functions for colored output
def print_success(message):
    click.echo(click.style(message, fg="green"))


def print_error(message):
    click.echo(click.style(message, fg="red"))


def print_info(message):
    click.echo(click.style(message, fg="blue"))  # Or 'yellow' or 'cyan'


def _resolve_node_url(network_name: str, custom_url: str | None = None) -> str:
    if custom_url:
        print_info(f"Using custom node URL: {custom_url}")
        return custom_url

    url = NETWORK_URLS.get(network_name)
    if not url:
        # Should not happen if click.Choice is used correctly, but as a safeguard:
        print_error(f"Unknown network: {network_name}. Defaulting to 'local'.")
        return NETWORK_URLS["local"]

    print_info(f"Using '{network_name}' network URL: {url}")
    return url


def _get_passphrase(passphrase: str | None = None) -> str:
    if not passphrase:
        try:
            passphrase = getpass.getpass("Enter passphrase for wallet: ")
        except Exception as e:
            print_error(f"Failed to get passphrase: {e}")
            raise click.Abort()
    return passphrase


@click.group("agere")
def agere_cmds():
    """Placeholder for Agere-specific commands. Currently, all subcommands have been moved."""
    # If in the future, Agere-specific commands are added (e.g., interacting with a unique Agere pallet),
    # they would be defined here.
    # For now, this group might appear empty or show a help message indicating that
    # common operations like transfer, balance, etc., are now top-level.
    print_info(
        "Agere-specific commands will be listed here. Common operations are now top-level."
    )
    pass


# To keep the `agere` command group in `main.py` functional without errors if no subcommands are added here yet:
# You could add a simple placeholder command or ensure the group itself provides useful help.
@agere_cmds.command("info")
def agere_info():
    """Displays information about the Agere module or its CLI group."""
    click.echo("This is the command group for Agere-specific interactions.")
    click.echo(
        "General commands like transfer, balance, submit-extrinsic, chain-info, etc., have been moved to the top level or other groups."
    )
    click.echo(
        "Future commands specific to unique Agere pallet functionalities will be added here."
    )


@agere_cmds.command("submit-extrinsic")
@click.option(
    "--network",
    type=click.Choice(list(NETWORK_URLS.keys())),
    default="signet",
    show_default=True,
    help="Named network to use when --node-url is not provided.",
)
@click.option(
    "--node-url",
    type=str,
    default=None,
    help="Custom node websocket URL. Overrides the selected network.",
)
@click.option("--wallet-name", required=True, help="Wallet name used for signing.")
@click.option(
    "--passphrase",
    default=None,
    help="Wallet passphrase. If omitted you will be prompted securely.",
)
@click.option("--module", "module_name", required=True, help="Target pallet/module name.")
@click.option("--call", "call_function", required=True, help="Call/function name.")
@click.option(
    "--params",
    default="{}",
    help="JSON string containing call parameters.",
)
def submit_extrinsic(network, node_url, wallet_name, passphrase, module_name, call_function, params):
    """Submit a signed extrinsic via the Agere interface."""

    resolved_url = _resolve_node_url(network, node_url)

    try:
        params_dict = json.loads(params) if params else {}
    except json.JSONDecodeError as exc:
        print_error(f"Invalid JSON for --params: {exc}")
        raise click.ClickException("Invalid JSON provided for --params.") from exc

    interface = AgereInterface(node_url=resolved_url)
    try:
        result = interface.submit_signed_extrinsic(
            wallet_name=wallet_name,
            module=module_name,
            call_function=call_function,
            params=params_dict,
            passphrase=_get_passphrase(passphrase),
        )

        if not result:
            print_error("Extrinsic submission failed.")
            raise click.ClickException("Extrinsic submission failed.")

        print_success(f"Extrinsic submitted successfully. Hash: {result}")
    except click.ClickException:
        raise
    except Exception as exc:
        print_error(f"Extrinsic submission failed: {exc}")
        raise click.ClickException(str(exc)) from exc
    finally:
        try:
            interface.close()
        except Exception:
            pass


@agere_cmds.command("get-balance")
@click.option(
    "--network",
    type=click.Choice(list(NETWORK_URLS.keys())),
    default="signet",
    show_default=True,
    help="Named network to use when --node-url is not provided.",
)
@click.option(
    "--node-url",
    type=str,
    default=None,
    help="Custom node websocket URL. Overrides the selected network.",
)
@click.option("--address", required=True, help="SS58 address to query.")
def get_balance(network, node_url, address):
    """Retrieve the free balance for the provided address."""

    resolved_url = _resolve_node_url(network, node_url)
    interface = AgereInterface(node_url=resolved_url)
    try:
        balance = interface.get_account_balance(address)
        if balance is None:
            print_error("Failed to retrieve balance for the provided address.")
            raise click.ClickException("Failed to retrieve balance.")

        print_success(f"Balance for {address}: {balance}")
    except click.ClickException:
        raise
    except Exception as exc:
        print_error(f"Failed to retrieve balance: {exc}")
        raise click.ClickException(str(exc)) from exc
    finally:
        try:
            interface.close()
        except Exception:
            pass


if __name__ == "__main__":
    agere_cmds()
