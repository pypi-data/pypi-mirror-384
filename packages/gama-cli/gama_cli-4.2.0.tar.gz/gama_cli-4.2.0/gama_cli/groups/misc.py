import click

from gama_cli.helpers import call, get_gama_version
import subprocess


@click.command(name="lint")
def lint():
    """Lints all the things"""
    call("pre-commit run --all")
    call("gama vessel lint-ui")


@click.command(name="test")
def test():
    """Tests all the things"""
    call("gama lint")
    # call("gama gs test")
    call("gama vessel test-ui")
    # call("gama vessel test-ros")


@click.command(name="test-e2e")
def test_e2e():
    """Brings up all containers and runs the e2e tests"""
    call("gama gs up")
    call("gama vessel up --mode stubs")
    call("gama vessel test-e2e")


@click.command(name="upgrade")
@click.option("--version", help="The version to upgrade to.")
def upgrade(version: str):
    """Upgrade GAMA CLI"""
    click.echo(f"Current version: {get_gama_version()}")
    result = click.prompt(
        "Are you sure you want to upgrade?", default="y", type=click.Choice(["y", "n"])
    )
    if result == "n":
        return

    if version:
        call(f"pip install --upgrade gama-cli=={version}")
    else:
        call("pip install --upgrade gama-cli")

    click.echo(click.style("Upgrade of GAMA CLI complete.", fg="green"))
    click.echo(
        click.style("Run `gama vessel install` or `gama gs install` to upgrade GAMA.", fg="green")
    )


@click.command(name="authenticate")
@click.option(
    "--username",
    help="The username to use for authentication.",
    required=True,
    prompt=True,
)
@click.option("--token", help="The token to use for authentication.", required=True, prompt=True)
def authenticate(username: str, token: str):
    """
    Authenticate with the GAMA package repository so that you can pull images.

    To get a username and token you'll need to contact a Greenroom Robotics employee.
    """
    call(f"echo {token} | docker login ghcr.io -u {username} --password-stdin")


@click.command(name="vcan")
@click.argument("action", type=click.Choice(["up", "down"]))
@click.option(
    "--devices", default=1, show_default=True, help="Number of vcan interfaces to create/remove."
)
def vcan(action: str, devices: int):
    vcan_setup(action, devices)


def vcan_setup(action: str, devices: int):
    """Start or stop the vcan0...vcanN interfaces"""
    if action == "up":
        call("sudo modprobe vcan")
        for i in range(devices):
            call(f"sudo ip link add dev vcan{i} type vcan")
            call(f"sudo ip link set up vcan{i}")
    elif action == "down":
        for i in range(devices):
            call(f"sudo ip link set down vcan{i}")
            call(f"sudo ip link delete vcan{i}")


# @click.command(name="pkg-versions")
# def pkg_versions():
#     """Get the versions of all GAMA packages"""

#     xmls = Path("projects").glob("**/package.xml")
#     for xml in xmls:
