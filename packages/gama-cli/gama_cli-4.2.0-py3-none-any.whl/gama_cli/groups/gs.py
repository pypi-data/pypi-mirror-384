from typing import List, Optional
import click
import os

from gama_config.gama_gs import (
    Network,
    Mode,
    LogLevel,
    DEFAULT_NAMESPACE_GROUNDSTATION,
    get_gs_config_io,
    GamaGsConfig,
)
from gama_cli.helpers import (
    docker_compose_path,
    get_project_root,
    docker_bake,
    maybe_ignore_build,
    maybe_ignore_prod,
    get_gama_version,
)

from python_on_whales.docker_client import DockerClient
from python_on_whales.utils import ValidPath


def set_initial_env(config_dir: str):
    os.environ["GAMA_CONFIG_DIR"] = config_dir

    if config_dir.startswith("/"):
        click.echo(
            click.style(
                "Warning: Using an absolute path requires the path to be accessible from the host and within the docker container.",
                fg="yellow",
            )
        )


def set_env(config: GamaGsConfig):
    """Set environment variables needed by docker compose files"""
    # Set to be empty if using the default namespace groundstation
    os.environ["GAMA_CONTAINER_PREFIX"] = (
        ""
        if config.namespace_groundstation == DEFAULT_NAMESPACE_GROUNDSTATION
        else f"{config.namespace_groundstation}_"
    )
    # Set other environment variables that docker commands need
    os.environ["GAMA_NAMESPACE_VESSEL"] = config.namespace_vessel
    os.environ["GAMA_NAMESPACE_GROUNDSTATION"] = config.namespace_groundstation


# Reusable option decorator for config_dir
config_dir_option = click.option(
    "-c",
    "--config-dir",
    type=str,
    default="~/.config/greenroom",
    help="The directory where the gama config is stored. Resolved relative to: ~/.config/greenroom",
)

DOCKER_GS = docker_compose_path("./gs/docker-compose.yaml")
DOCKER_GS_PROD = docker_compose_path("./gs/docker-compose.prod.yaml")
DOCKER_GS_DEV = docker_compose_path("./gs/docker-compose.dev.yaml")
DOCKER_GS_NETWORK_SHARED = docker_compose_path("./gs/docker-compose.network-shared.yaml")
DOCKER_GS_NETWORK_HOST = docker_compose_path("./gs/docker-compose.network-host.yaml")

GS_SERVICES = ["gama_gs", "gama_ui"]


def _get_compose_files(network: Network = Network.SHARED, prod: bool = False) -> List[ValidPath]:
    compose_files: List[ValidPath] = [DOCKER_GS]

    if not prod:
        compose_files.append(DOCKER_GS_DEV)
    if prod:
        compose_files.append(DOCKER_GS_PROD)
    if network == Network.SHARED:
        compose_files.append(DOCKER_GS_NETWORK_SHARED)
    if network == Network.HOST:
        compose_files.append(DOCKER_GS_NETWORK_HOST)

    return compose_files


def _get_compose_profiles(ui: bool) -> List[str]:
    profiles = []
    if ui:
        profiles.append("ui")
    return profiles


def log_config(config: GamaGsConfig):
    click.echo(click.style("[+] GAMA GS Config:", fg="green"))
    click.echo(click.style(f" ⠿ Path: {get_gs_config_io().get_path()}", fg="white"))
    for attr, value in config.__dict__.items():
        click.echo(
            click.style(f" ⠿ {attr}: ".ljust(35), fg="white") + click.style(str(value), fg="green")
        )


@click.group(help="Commands for the ground-station")
def gs():
    pass


@click.command(name="up")
@click.option(
    "--build",
    type=bool,
    default=False,
    help="Should we rebuild the docker containers? Default: False",
)
@click.argument("args", nargs=-1)
@config_dir_option
def up(
    build: bool,
    args: List[str],
    config_dir: str = "~/.config/greenroom",
):
    """Starts the ground-station"""
    dev_mode = os.environ["GAMA_CLI_DEV_MODE"] == "true"

    set_initial_env(config_dir)
    config = get_gs_config_io().read()
    set_env(config)
    build = maybe_ignore_build(dev_mode, build)
    prod = maybe_ignore_prod(dev_mode, config.prod)

    gama_gs_command = "platform ros launch gama_gs_bringup gs.launch.py"
    if not prod:
        gama_gs_command += " --watch --build"

    os.environ["GAMA_VERSION"] = get_gama_version()
    os.environ["GAMA_GS_CONFIG"] = get_gs_config_io().serialise(config)
    os.environ["GAMA_GS_COMMAND"] = gama_gs_command
    os.environ["ROS_DOMAIN_ID"] = (
        str(config.discovery.ros_domain_id) if config.discovery.type == "simple" else "0"
    )
    os.environ["RMW_IMPLEMENTATION"] = (
        "rmw_zenoh_cpp" if config.discovery.type == "zenoh" else "rmw_fastrtps_cpp"
    )
    os.environ["GAMA_VESSEL_HOST"] = (
        config.discovery.discovery_server_ip
        if config.discovery.type == "fastdds" or config.discovery.type == "zenoh"
        else "localhost"
    )
    os.environ["GAMA_NAMESPACE_VESSEL"] = config.namespace_vessel
    os.environ["GAMA_NAMESPACE_GROUNDSTATION"] = config.namespace_groundstation

    log_config(config)

    docker = DockerClient(
        compose_files=_get_compose_files(network=config.network, prod=prod),
        compose_project_directory=get_project_root(),
        compose_profiles=_get_compose_profiles(config.ui),
        compose_project_name=config.namespace_groundstation,
    )
    docker.compose.up(detach=True, build=build)


@click.command(name="down")
@click.argument("args", nargs=-1)
@config_dir_option
def down(args: List[str], config_dir: str = "~/.config/greenroom"):
    """Stops the ground-station"""
    set_initial_env(config_dir)
    config = get_gs_config_io().read()
    set_env(config)

    docker = DockerClient(
        compose_files=_get_compose_files(),
        compose_project_directory=get_project_root(),
        compose_profiles=_get_compose_profiles(True),
        compose_project_name=config.namespace_groundstation,
    )
    docker.compose.down()


@click.command(name="install")
@config_dir_option
def install(config_dir: str = "~/.config/greenroom"):  # type: ignore
    """Install GAMA on a gs"""
    set_initial_env(config_dir)
    config = get_gs_config_io().read()
    set_env(config)
    os.environ["GAMA_VERSION"] = get_gama_version()
    docker = DockerClient(
        compose_files=_get_compose_files(),
        compose_project_directory=get_project_root(),
        compose_profiles=_get_compose_profiles(config.ui),
        compose_project_name=config.namespace_groundstation,
    )
    try:
        docker.compose.pull()
    except Exception:
        click.echo(
            click.style(
                "Failed to pull GAMA files. Have you ran `gama authenticate` ?",
                fg="yellow",
            )
        )


@click.command(name="configure")
@click.option("--default", is_flag=True, help="Use default values")
@config_dir_option
def configure(default: bool, config_dir: str = "~/.config/greenroom"):  # type: ignore
    """Configure GAMA Ground Station"""
    set_initial_env(config_dir)

    if default:
        config = GamaGsConfig()
        get_gs_config_io().write(config)
        return

    # Check if the file exists
    if os.path.exists(get_gs_config_io().get_path()):
        click.echo(
            click.style(
                f"GAMA Ground Station config already exists: {get_gs_config_io().get_path()}",
                fg="yellow",
            )
        )
        result = click.prompt(
            "Do you want to overwrite it?", default="y", type=click.Choice(["y", "n"])
        )
        if result == "n":
            return

    try:
        config_current = get_gs_config_io().read()
    except Exception:
        config_current = GamaGsConfig()

    config = GamaGsConfig(
        namespace_vessel=click.prompt("Namespace Vessel", default=config_current.namespace_vessel),
        namespace_groundstation=click.prompt(
            "Namespace Groundstation", default=config_current.namespace_groundstation
        ),
        mode=click.prompt(
            "Mode", type=click.Choice([mode.value for mode in Mode]), default=config_current.mode
        ),
        network=click.prompt(
            "Network",
            type=click.Choice([network.value for network in Network]),
            default=config_current.network,
        ),
        prod=click.prompt("Prod", type=bool, default=config_current.prod),
        log_level=click.prompt(
            "Log Level",
            type=click.Choice([log_level.value for log_level in LogLevel]),
            default=config_current.log_level,
        ),
    )
    get_gs_config_io().write(config)


@click.command(name="build")
@click.option("--pull", is_flag=True, help="Pull the latest images")
@config_dir_option
def build(pull: bool = False, config_dir: str = "~/.config/greenroom"):
    """Builds the ground-station"""
    set_initial_env(config_dir)
    config = get_gs_config_io().read()
    set_env(config)
    docker = DockerClient(
        compose_files=_get_compose_files(),
        compose_project_directory=get_project_root(),
        compose_profiles=_get_compose_profiles(config.ui),
        compose_project_name=config.namespace_groundstation,
    )
    docker.compose.build(pull=pull)


@click.command(name="bake")
@click.option(
    "--version",
    type=str,
    required=True,
    help="The version to bake. Default: latest",
)
@click.option(
    "--push",
    type=bool,
    default=False,
    is_flag=True,
    help="Should we push the images to the registry? Default: False",
)
@click.argument("services", nargs=-1)
def bake(version: str, push: bool, services: List[str]):  # type: ignore
    """Bakes the gs docker containers"""
    compose_files = _get_compose_files()
    docker_bake(
        version=version,
        services=services,
        push=push,
        compose_files=compose_files,
    )


@click.command(name="test")
@config_dir_option
def test(config_dir: str = "~/.config/greenroom"):
    """Tests the ground-station"""
    set_initial_env(config_dir)
    config = get_gs_config_io().read()
    set_env(config)
    docker = DockerClient(
        compose_files=_get_compose_files(),
        compose_project_directory=get_project_root(),
        compose_profiles=_get_compose_profiles(config.ui),
        compose_project_name=config.namespace_groundstation,
    )
    docker.compose.run("gama_gs", list("platform ros test".split(" ")))


@click.command(name="config")
@config_dir_option
def config(config_dir: str = "~/.config/greenroom"):  # type: ignore
    """Read Config"""
    set_initial_env(config_dir)
    config = get_gs_config_io().read()
    log_config(config)
