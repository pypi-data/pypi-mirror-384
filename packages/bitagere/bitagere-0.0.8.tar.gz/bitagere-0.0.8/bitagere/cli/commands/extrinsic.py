import click


@click.group("extrinsic")
def extrinsic_cmds():
    """Submit extrinsics to the Substrate network"""
    pass


@extrinsic_cmds.command("submit")
@click.option("--wallet", required=True, help="Name of the wallet to use for signing.")
@click.option("--module", required=True, help="Substrate module name (e.g., Balances).")
@click.option("--call", required=True, help="Substrate call name (e.g., transfer).")
@click.argument("params", nargs=-1)
def submit_extrinsic(wallet: str, module: str, call: str, params: tuple):
    """
    Submits a generic extrinsic.
    Example: bitagere-cli extrinsic submit --wallet mywallet --module Balances --call transfer DestAddress Amount
    """
    click.echo(
        f"CLI: Submitting extrinsic from wallet '{wallet}' (not implemented yet)."
    )
    click.echo(f"Module: {module}, Call: {call}, Params: {params}")
