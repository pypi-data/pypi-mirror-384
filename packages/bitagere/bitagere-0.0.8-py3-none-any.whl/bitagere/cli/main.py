import click


@click.group()
def cli():
    """
    Bitagere Command Line Interface
    """
    pass


# Import command groups and individual commands
from .commands.wallet import wallet_cmds
from .commands.agere import agere_cmds  # Renamed from agere to agere_cmds
from .commands.chain import chain_info, balance, block_number, block_hash
from .commands.transfer import transfer_balance
from .commands.extrinsic import submit_extrinsic

# Add command groups
cli.add_command(wallet_cmds)
cli.add_command(agere_cmds)  # This is the placeholder agere group

# Add individual commands at the top level
cli.add_command(chain_info)
cli.add_command(balance)
cli.add_command(block_number)
cli.add_command(block_hash)
cli.add_command(transfer_balance)
cli.add_command(submit_extrinsic)


if __name__ == "__main__":
    cli()
