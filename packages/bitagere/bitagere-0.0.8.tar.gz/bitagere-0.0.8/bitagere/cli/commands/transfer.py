# filepath: /home/hacpy/GEB/bitagere/bitagere/cli/commands/transfer.py
import click
import getpass
from bitagere.substrate.interface import AgereInterface
from .helpers import (
    print_success,
    print_error,
    print_info,
    _resolve_node_url,
    _get_passphrase,
    NETWORK_URLS,
)


@click.command("transfer")
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
    "--wallet-name",
    "-w",
    required=True,
    help="Name of the wallet to sign the transfer with.",
)
@click.option(
    "--passphrase",
    "-p",
    help="Passphrase for the wallet. If not provided, you will be prompted.",
    default=None,
)
@click.option(
    "--to",
    "-t",
    "destination_address",
    required=True,
    help="The SS58 address of the recipient.",
)
@click.option(
    "--amount",
    "-a",
    required=True,
    type=click.FLOAT,
    help="Amount to transfer (in token units, e.g., 1.0). Will be converted to Planck.",
)
@click.option(
    "--decimals",
    "-d",
    default=12,
    show_default=True,
    type=int,
    help="Number of decimal places for the token.",
)
@click.option(
    "--wait-for-inclusion/--no-wait-for-inclusion",
    "-inc/-no-inc",
    default=True,
    show_default=True,
    help="Wait for the extrinsic to be included in a block.",
)
@click.option(
    "--wait-for-finalization/--no-wait-for-finalization",
    "-fin/-no-fin",
    default=False,
    show_default=True,
    help="Wait for the extrinsic to be finalized.",
)
def transfer_balance(
    network,
    node_url,
    wallet_name,
    passphrase,
    destination_address,
    amount,
    decimals,
    wait_for_inclusion,
    wait_for_finalization,
):
    """Performs a balance transfer to a destination address."""
    final_node_url = _resolve_node_url(network, node_url)

    print_info(f"Attempting transfer:")
    print_info(f"  Node URL: {final_node_url}")
    print_info(f"  From Wallet: {wallet_name}")
    print_info(f"  To Address: {destination_address}")
    print_info(f"  Amount: {amount/1e8} GEB ")
    print_info(f"  Wait for inclusion: {wait_for_inclusion}")
    print_info(f"  Wait for finalization: {wait_for_finalization}")

    actual_passphrase = _get_passphrase(passphrase)
    if not actual_passphrase:
        return

    interface = None
    try:
        interface = AgereInterface(node_url=final_node_url)
        result = interface.transfer(
            wallet_name=wallet_name,
            passphrase=actual_passphrase,
            destination_address=destination_address,
            amount=amount,
            wait_for_inclusion=wait_for_inclusion,
            wait_for_finalization=wait_for_finalization,
        )

        if result:
            if result.startswith("0x") and len(result) == 66:
                print_success(f"Transfer submitted successfully. Hash: {result}")
            else:
                print_error(f"Transfer submission failed: {result}")
        else:
            print_error(
                "Transfer submission failed. No hash or error message returned."
            )
    except ConnectionError as e:
        print_error(f"Connection Error during transfer: {e}")
    except Exception as e:
        print_error(f"An unexpected error occurred during transfer: {e}")
    finally:
        if interface:
            interface.close()
