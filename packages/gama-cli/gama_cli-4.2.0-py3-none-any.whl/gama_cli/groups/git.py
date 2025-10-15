import click

from gama_cli.helpers import call


@click.group(help="Git convenience commands")
def git():
    pass


@click.command(name="pull")
def pull():
    """Pulls this repo and all submodules"""
    call("git pull --recurse-submodules=yes")
