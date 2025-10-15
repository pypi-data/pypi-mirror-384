# filepath: /home/hacpy/GEB/bitagere/bitagere/cli/commands/chain.py
import click
from bitagere.substrate.interface import AgereInterface
from .helpers import (
    print_success,
    print_error,
    print_info,
    _resolve_node_url,
    NETWORK_URLS,
)


@click.command("chain-info")
@click.option(
    "--network",
    "-net",
    type=click.Choice(NETWORK_URLS.keys(), case_sensitive=False),
    default="signet",
    show_default=True,
    help="Predefined network name.",
)
@click.option(
    "--node-url",
    "-url",
    help="Custom Substrate node WebSocket URL (overrides --network selection).",
)
def chain_info(network, node_url):
    """
    Retrieves and displays basic information about the connected Substrate chain.
    """
    final_node_url = _resolve_node_url(network, node_url)
    print_info(f"Attempting to retrieve chain info from: {final_node_url}")

    try:
        with AgereInterface(node_url=final_node_url) as interface:
            info = interface.get_chain_info()
            if info:
                print_success("Successfully retrieved chain information:")
                print_info(f"  Chain Name: {info.get('chain', 'N/A')}")
                print_info(f"  Node Name: {info.get('node_name', 'N/A')}")
                print_info(f"  Node Version: {info.get('node_version', 'N/A')}")
                print_info(f"  Spec Version: {info.get('spec_version', 'N/A')}")
            else:
                print_error(
                    "Failed to retrieve chain information. Interface returned None."
                )
    except ConnectionError as e:
        print_error(f"Connection Error: {e}")
    except Exception as e:
        print_error(f"An unexpected error occurred: {e}")


@click.command("balance")
@click.option(
    "--network",
    "-net",
    type=click.Choice(NETWORK_URLS.keys(), case_sensitive=False),
    default="signet",
    show_default=True,
    help="Predefined network name.",
)
@click.option(
    "--node-url",
    "-url",
    help="Custom Substrate node WebSocket URL (overrides --network selection).",
)
@click.option(
    "--address", "-addr", required=True, help="The SS58 address to query balance for."
)
def balance(network, node_url, address):
    """Retrieves the account free balance for a given SS58 address, formatted in GEB."""
    final_node_url = _resolve_node_url(network, node_url)
    print_info(
        f"Attempting to retrieve balance for address: {address} from node: {final_node_url}"
    )
    try:
        with AgereInterface(node_url=final_node_url) as interface:
            # get_account_balance now returns int | None (the free balance in smallest unit)
            free_balance_smallest_unit = interface.get_account_balance(address)

            if free_balance_smallest_unit is not None:
                # GEB token has 8 decimal places of precision. 1 GEB = 10^8 smallest units.
                geb_conversion_factor = 10**8

                geb_balance = free_balance_smallest_unit / geb_conversion_factor
                formatted_balance = f"{geb_balance:.8f}"  # Format to 8 decimal places

                print_success(f"Free balance for {address}: {formatted_balance} GEB")
            else:
                print_error(
                    f"Failed to retrieve balance for {address}. Interface returned None."
                )
    except ConnectionError as e:
        print_error(f"Connection Error: {e}")
    except Exception as e:
        print_error(f"An unexpected error occurred while getting balance: {e}")


@click.command("block-number")
@click.option(
    "--network",
    "-net",
    type=click.Choice(NETWORK_URLS.keys(), case_sensitive=False),
    default="signet",
    show_default=True,
    help="Predefined network name.",
)
@click.option(
    "--node-url",
    "-url",
    help="Custom Substrate node WebSocket URL (overrides --network selection).",
)
def block_number(network, node_url):
    """Retrieves the current block number (height) of the chain."""
    final_node_url = _resolve_node_url(network, node_url)
    print_info(f"Attempting to retrieve current block number from: {final_node_url}")
    try:
        with AgereInterface(node_url=final_node_url) as interface:
            current_block_number = interface.get_current_block_number()
            if current_block_number is not None:
                print_success(f"Current block number: {current_block_number}")
            else:
                print_error("Failed to retrieve current block number.")
    except ConnectionError as e:
        print_error(f"Connection Error: {e}")
    except Exception as e:
        print_error(f"An unexpected error occurred while getting block number: {e}")


@click.command("block-hash")
@click.option(
    "--network",
    "-net",
    type=click.Choice(NETWORK_URLS.keys(), case_sensitive=False),
    default="signet",
    show_default=True,
    help="Predefined network name.",
)
@click.option(
    "--node-url",
    "-url",
    help="Custom Substrate node WebSocket URL (overrides --network selection).",
)
@click.option(
    "--block-number",
    "-bn",
    type=int,
    default=None,
    help="The block number to get hash for (default: latest).",
)
def block_hash(network, node_url, block_number):
    """Retrieves the hash of a specific block, or the latest block."""
    final_node_url = _resolve_node_url(network, node_url)
    if block_number is None:
        print_info(f"Attempting to retrieve latest block hash from: {final_node_url}")
    else:
        print_info(
            f"Attempting to retrieve block hash for block {block_number} from: {final_node_url}"
        )
    try:
        with AgereInterface(node_url=final_node_url) as interface:
            hash_val = interface.get_block_hash(block_id=block_number)
            if hash_val:
                print_success(
                    f"Block hash{(f' for block {block_number}' if block_number else ' (latest)')}: {hash_val}"
                )
            else:
                print_error(
                    f"Failed to retrieve block hash{(f' for block {block_number}' if block_number else ' (latest)')}."
                )
    except ConnectionError as e:
        print_error(f"Connection Error: {e}")
    except Exception as e:
        print_error(f"An unexpected error occurred while getting block hash: {e}")
