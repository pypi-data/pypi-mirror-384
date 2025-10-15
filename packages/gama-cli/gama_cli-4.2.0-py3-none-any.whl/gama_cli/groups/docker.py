import click

from gama_cli.helpers import call
import requests


@click.group(help="Docker convenience methods")
def docker():
    pass


@click.command(name="clearlogs")
def clearlogs():  # type: ignore
    """Clears all the docker logs"""
    command = 'sudo sh -c "truncate -s 0 /var/lib/docker/containers/*/*-json.log"'
    call(command)


@click.command(name="registry")
@click.option("--port", type=int, default=5555)
@click.option("--persist", type=bool, default=True, is_flag=True)
@click.option("--restart", type=bool, default=False, is_flag=True)
@click.option("--clean-volume", type=bool, default=False, is_flag=True)
@click.argument("up_or_down", type=str)
def registry(port: int, persist: bool, restart: bool, clean_volume: bool, up_or_down: str):  # type: ignore
    """Starts the docker registry"""
    cmd = f"docker run -d -p {port}:5000"
    if persist:
        cmd += " --name registry -v /var/lib/registry:/var/lib/registry"
    if restart:
        cmd += " --restart=always"

    cmd += " registry:latest"
    if up_or_down == "up":
        call(cmd)
    elif up_or_down == "down":
        call("docker stop registry")
        call("docker rm registry")
        if clean_volume:
            call("sudo rm -rf /var/lib/registry")
    else:
        raise click.ClickException("Invalid command")


@click.command(name="list-registry")
@click.option("--host", type=str, default="localhost:5555")
def list_registry(host: str):  # type: ignore
    response = requests.get(f"http://{host}/v2/_catalog")
    if response.status_code == 200:
        repositories = response.json().get("repositories", [])
        click.echo(f"Repositories: {repositories}")
    else:
        click.echo(f"Failed to fetch repositories: {response.status_code}")
