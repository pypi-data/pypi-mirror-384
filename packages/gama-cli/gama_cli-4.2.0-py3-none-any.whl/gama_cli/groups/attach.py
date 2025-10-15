import click

from gama_cli.helpers import call


@click.group(help="Attaches vscode to a running container")
def attach():
    pass


@click.command(name="vessel")
def vessel():
    """Attaches vscode to the vessel container"""
    container = b"gama_vessel".hex()
    path = "/home/ros/gama_vessel"
    call(f"code --folder-uri=vscode-remote://attached-container+{container}/{path}")


@click.command(name="gs")
def gs():
    """Attaches vscode to the gs container"""
    container = b"gama_gs".hex()
    path = "/home/ros/gama_gs"
    call(f"code --folder-uri=vscode-remote://attached-container+{container}/{path}")


@click.command(name="ui")
def ui():
    """Attaches vscode to the ui container"""
    container = b"gama_ui".hex()
    path = "/app"
    call(f"code --folder-uri=vscode-remote://attached-container+{container}/{path}")
