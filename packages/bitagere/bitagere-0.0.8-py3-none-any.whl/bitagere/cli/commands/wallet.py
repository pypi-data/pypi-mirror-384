import click
import getpass  # For passphrase prompts not handled by click directly if needed


# ANSI escape codes for colors
class Colors:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"  # Resets color
    BOLD = "\033[1m"


@click.group("wallet")
def wallet_cmds():
    """Manage wallets (encrypted)"""
    pass


@wallet_cmds.command("create")
@click.option(
    "--name",
    "-n",
    prompt=f"{Colors.BLUE}Enter a name for the new wallet{Colors.ENDC}",
    help="Name of the wallet.",
)
@click.option(
    "--overwrite",
    "-o",
    is_flag=True,
    help="Overwrite if wallet with the same name exists.",
)
def create_wallet(name: str, overwrite: bool):
    """Creates a new wallet, encrypts it with a passphrase, and shows the mnemonic."""
    from bitagere.wallet.wallet import Wallet
    import sys

    click.echo(
        f"{Colors.BLUE}Attempting to create wallet: {Colors.BOLD}{name}{Colors.ENDC}"
    )

    if Wallet.wallet_exists(name) and not overwrite:
        click.echo(
            f"{Colors.RED}Wallet '{Colors.BOLD}{name}{Colors.ENDC}' already exists. Use --overwrite to replace it.{Colors.ENDC}"
        )
        sys.exit(1)

    if Wallet.wallet_exists(name) and overwrite:
        if not click.confirm(
            f"{Colors.YELLOW}Wallet '{Colors.BOLD}{name}{Colors.ENDC}' already exists. Overwrite?{Colors.ENDC}",
            abort=False,
        ):
            click.echo("Wallet creation aborted by user.")
            sys.exit(0)  # User chose not to overwrite, not an error
        click.echo(
            f"{Colors.BLUE}Overwriting existing wallet: {Colors.BOLD}{name}{Colors.ENDC}"
        )

    # Generate wallet object and mnemonic first
    wallet_obj, mnemonic = Wallet.create_new_wallet(
        name, overwrite=overwrite
    )  # overwrite here is for internal logic if any, actual file check is above

    if not wallet_obj or not mnemonic:
        # This case should ideally be caught by Wallet.wallet_exists check if it's due to pre-existence without overwrite.
        # If it's another error from Wallet.create_new_wallet (e.g., key generation failure):
        click.echo(
            f"{Colors.RED}Failed to initialize wallet '{Colors.BOLD}{name}{Colors.ENDC}'. An internal error occurred.{Colors.ENDC}"
        )
        sys.exit(1)

    # Now prompt for passphrase and save
    try:
        passphrase = click.prompt(
            f"{Colors.BLUE}Enter passphrase to encrypt wallet '{Colors.BOLD}{name}{Colors.ENDC}'{Colors.ENDC}",
            hide_input=True,
            confirmation_prompt=True,
        )
    except click.exceptions.Abort:
        click.echo(
            f"\n{Colors.YELLOW}Passphrase entry aborted. Wallet '{name}' was not saved.{Colors.ENDC}"
        )
        click.echo(
            f"{Colors.YELLOW}{Colors.BOLD}IMPORTANT: The mnemonic for the unsaved wallet was:{Colors.ENDC}"
        )
        click.echo(f"  {Colors.BOLD}{Colors.GREEN}{mnemonic}{Colors.ENDC}")
        click.echo(
            f"{Colors.YELLOW}You can use the 'wallet import' command with this mnemonic if you wish to save it later.{Colors.ENDC}"
        )
        sys.exit(1)

    if wallet_obj.save(
        passphrase, overwrite=overwrite
    ):  # Pass overwrite to save method
        click.echo(
            f"{Colors.GREEN}Wallet '{Colors.BOLD}{wallet_obj.name}{Colors.ENDC}' created and encrypted successfully.{Colors.ENDC}"
        )
        click.echo(f"  Address: {Colors.BOLD}{wallet_obj.get_address()}{Colors.ENDC}")
        click.echo(
            f"{Colors.YELLOW}{Colors.BOLD}IMPORTANT: Store this mnemonic phrase in a secure place.{Colors.ENDC}"
        )
        click.echo(
            f"{Colors.YELLOW}It is the only way to recover your wallet if you forget the passphrase for this specific encrypted file:{Colors.ENDC}"
        )
        click.echo(f"  Mnemonic: {Colors.BOLD}{Colors.GREEN}{mnemonic}{Colors.ENDC}")
    else:
        # This condition implies wallet_obj.save() returned False.
        # This could be due to file already existing and overwrite=False (though we check Wallet.wallet_exists above),
        # or an actual saving error.
        click.echo(
            f"{Colors.RED}Failed to save wallet '{Colors.BOLD}{name}{Colors.ENDC}'.{Colors.ENDC}"
        )
        if Wallet.wallet_exists(name) and not overwrite:
            click.echo(
                f"{Colors.RED}It seems the wallet file was created by another process between generation and saving, and overwrite was not specified.{Colors.ENDC}"
            )
        click.echo(
            f"{Colors.YELLOW}{Colors.BOLD}IMPORTANT: The mnemonic for the unsaved wallet was:{Colors.ENDC}"
        )
        click.echo(f"  {Colors.BOLD}{Colors.GREEN}{mnemonic}{Colors.ENDC}")
        click.echo(
            f"{Colors.YELLOW}You can use the 'wallet import' command with this mnemonic if you wish to save it later.{Colors.ENDC}"
        )
        sys.exit(1)


@wallet_cmds.command("import")
@click.option(
    "--name",
    "-n",
    prompt=f"{Colors.BLUE}Enter a name for the imported wallet{Colors.ENDC}",
    help="Name for the wallet.",
)
@click.option(
    "--mnemonic",
    "-m",
    prompt=f"{Colors.BLUE}Enter your mnemonic phrase{Colors.ENDC}",
    hide_input=True,
    help="The mnemonic phrase to import.",
)
@click.option(
    "--overwrite",
    "-o",
    is_flag=True,
    help="Overwrite if wallet with the same name exists.",
)
def import_wallet(name: str, mnemonic: str, overwrite: bool):
    """Imports a wallet from a mnemonic phrase and encrypts it with a passphrase."""
    from bitagere.wallet.wallet import Wallet  # Local import

    click.echo(
        f"{Colors.BLUE}Attempting to import wallet: {Colors.BOLD}{name}{Colors.ENDC}"
    )
    wallet = Wallet.import_wallet_from_mnemonic(name, mnemonic, overwrite=overwrite)

    if wallet:
        click.echo(
            f"{Colors.GREEN}Wallet '{Colors.BOLD}{wallet.name}{Colors.ENDC}' imported and encrypted successfully.{Colors.ENDC}"
        )
        click.echo(f"  Address: {Colors.BOLD}{wallet.get_address()}{Colors.ENDC}")
    else:
        click.echo(
            f"{Colors.RED}Failed to import wallet '{Colors.BOLD}{name}{Colors.ENDC}'. Check for existing wallet or errors during passphrase entry/saving.{Colors.ENDC}"
        )


@wallet_cmds.command("list")
def list_wallets():
    """Lists all available (encrypted) wallet names."""
    from bitagere.wallet.wallet import Wallet  # Local import

    wallets = Wallet.list_wallets()
    if wallets:
        click.echo(f"{Colors.GREEN}Available wallets:{Colors.ENDC}")
        for wallet_name in wallets:
            click.echo(f"- {Colors.BOLD}{wallet_name}{Colors.ENDC}")
    else:
        click.echo(f"{Colors.YELLOW}No wallets found.{Colors.ENDC}")


@wallet_cmds.command("show")
@click.argument("name", type=str)
def show_wallet(name: str):
    """Shows details for a specific wallet (address, public key) after prompting for passphrase."""
    from bitagere.wallet.wallet import Wallet  # Local import

    # Note: getpass doesn't support colored prompts directly in a simple way.
    # The prompt from getpass will be standard terminal color.
    passphrase = getpass.getpass(f"Enter passphrase to decrypt wallet '{name}': ")
    wallet = Wallet.load(name, passphrase)

    if wallet:
        click.echo(
            f"{Colors.GREEN}Details for wallet: '{Colors.BOLD}{wallet.name}{Colors.ENDC}'{Colors.ENDC}"
        )
        click.echo(f"  Address: {Colors.BOLD}{wallet.get_address()}{Colors.ENDC}")
        click.echo(f"  Public Key: {Colors.BOLD}{wallet.get_public_key()}{Colors.ENDC}")
        click.echo(
            f"  {Colors.YELLOW}Mnemonic: Not available in encrypted wallet file. It was shown at creation/import time.{Colors.ENDC}"
        )
    else:
        click.echo(
            f"{Colors.RED}Wallet '{Colors.BOLD}{name}{Colors.ENDC}' not found or passphrase incorrect.{Colors.ENDC}"
        )
