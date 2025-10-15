import os
from typing import List, Optional
import click
import subprocess
from pathlib import Path

from gama_config.gama_vessel import (
    Variant,
    Network,
    Mode,
    DEFAULT_NAMESPACE_VESSEL,
    DEFAULT_VARIANT_CONFIGS_MAP,
    get_vessel_config_io,
    VariantVesselConfig,
)
from gama_cli.helpers import (
    call,
    docker_compose_path,
    get_project_root,
    docker_bake,
    docker_manifest,
    get_gama_version,
    maybe_ignore_build,
    maybe_ignore_prod,
    make_dir_set_permission,
    filter_services_to_start,
    has_service_running_on_other_instances,
)
from gama_cli.groups.misc import vcan_setup
from python_on_whales.docker_client import DockerClient
from python_on_whales.utils import ValidPath
from greenstream_config.types import Camera


DOCKER_VESSEL = docker_compose_path("vessel/docker-compose.yaml")
DOCKER_VESSEL_PROD = docker_compose_path("vessel/docker-compose.prod.yaml")
DOCKER_VESSEL_DEV = docker_compose_path("vessel/docker-compose.dev.yaml")
DOCKER_VESSEL_NETWORK_SHARED = docker_compose_path("vessel/docker-compose.network-shared.yaml")
DOCKER_VESSEL_NETWORK_HOST = docker_compose_path("vessel/docker-compose.network-host.yaml")

SERVICES = [
    "gama_ui",
    "gama_chart_tiler",
    "gama_chart_api",
    "gama_vessel",
    "gama_vessel_base",
    "gama_greenstream",
    "gama_docs",
]

SIMULATION_VCAN_VARIANTS = {
    Variant.MARS: 1,
}

# When starting multiple instances of GAMA, these services should only be started once
SHARED_SERVICES = []


def change_registry(image_with_registry: str, new_registry: str):
    # replace the leading part of the image with the new registry
    return new_registry + "/" + "/".join(image_with_registry.split("/")[1:])


def execute_command_on_seperate_registry(
    func: callable,
    host: str,
    service: Optional[str] = None,
    config_dir: str = "~/.config/greenroom",
):
    set_initial_env(config_dir)
    config = get_vessel_config_io().read()

    docker = DockerClient(
        compose_files=_get_compose_files(
            variant=config.variant,
        ),
        compose_project_directory=get_project_root(),
        compose_project_name=config.namespace_vessel,
    )
    images = docker.compose.config().services
    mapper = {}
    for service_name, service_config in images.items():
        if service and service_name != service:
            continue
        image = service_config.image
        if image:
            mapper[image] = change_registry(image, host)

    for service_name, service_config in images.items():
        if service and service_name != service:
            continue
        image = service_config.image
        if image:
            func(docker, image, mapper[image])


def tag_and_push(docker: DockerClient, local_image_tag: str, target_image_tag: str):
    docker.image.tag(local_image_tag, target_image_tag)
    docker.image.push(target_image_tag)


def pull_and_tag(docker: DockerClient, local_image_tag: str, target_image_tag: str):
    docker.image.pull(target_image_tag)
    docker.image.tag(target_image_tag, local_image_tag)


def set_initial_env(config_dir: str):
    os.environ["GAMA_CONFIG_DIR"] = config_dir

    if config_dir.startswith("/"):
        click.echo(
            click.style(
                "Warning: Using an absolute path requires the path to be accessible from the host and within the docker container.",
                fg="yellow",
            )
        )


def set_env(config: VariantVesselConfig):
    """Set environment variables needed by docker compose files"""
    # Set to be empty if using the default namespace vessel
    os.environ["GAMA_CONTAINER_PREFIX"] = (
        ""
        if config.namespace_vessel == DEFAULT_NAMESPACE_VESSEL
        else f"{config.namespace_vessel}_"
    )
    # Set other environment variables that docker commands need
    os.environ["GAMA_VARIANT"] = config.variant
    os.environ["GAMA_NAMESPACE_VESSEL"] = config.namespace_vessel
    os.environ["GAMA_NAMESPACE_GROUNDSTATION"] = config.namespace_groundstation
    os.environ["GAMA_DISPLAY_NAME"] = config.display_name
    # Ports
    os.environ["GAMA_UI_PORT"] = str(config.ports.ui)
    os.environ["GAMA_ENV_SERVER_PORT"] = str(config.ports.ui + 100)
    os.environ["GAMA_CHART_TILER_PORT"] = str(config.ports.chart_tiler)
    os.environ["GAMA_CHART_API_PORT"] = str(config.ports.chart_api)
    os.environ["GAMA_DOCS_PORT"] = str(config.ports.docs)
    os.environ["GAMA_MISSION_PLAN_RUNNER_PORT"] = str(config.ports.mission_plan_runner)
    os.environ["GAMA_GREENSTREAM_SIGNALLING_PORT"] = str(config.ports.greenstream_signalling)
    os.environ["GAMA_GREENSTREAM_UI_PORT"] = str(config.ports.greenstream_ui)
    os.environ["GAMA_TAPEDECK_PORT"] = str(config.ports.tapedeck)
    os.environ["GAMA_DATA_BRIDGE_PORT"] = str(config.ports.data_bridge)
    os.environ["GAMA_GS_DATA_BRIDGE_PORT"] = str(config.ports.gs_data_bridge)


def _get_compose_files(
    network: Network = Network.SHARED,
    variant: Variant = Variant.ARMIDALE,
    prod: bool = False,
) -> List[ValidPath]:
    compose_files: List[ValidPath] = [DOCKER_VESSEL]
    if not prod:
        compose_files.append(DOCKER_VESSEL_DEV)

    compose_files.append(
        docker_compose_path(f"vessel/docker-compose.variant.{variant.value}.yaml")
    )

    if network == Network.SHARED:
        compose_files.append(DOCKER_VESSEL_NETWORK_SHARED)
    if network == Network.HOST:
        compose_files.append(DOCKER_VESSEL_NETWORK_HOST)
    if prod:
        compose_files.append(DOCKER_VESSEL_PROD)

    return compose_files


def log_config(config: VariantVesselConfig):
    click.echo(click.style("[+] GAMA Vessel Config:", fg="green"))
    click.echo(click.style(f" ⠿ Path: {get_vessel_config_io().get_path()}", fg="white"))
    for attr, value in config.__dict__.items():
        click.echo(
            click.style(f" ⠿ {attr}: ".ljust(35), fg="white") + click.style(str(value), fg="green")
        )


# Reusable option decorator for config_dir
config_dir_option = click.option(
    "-c",
    "--config-dir",
    type=str,
    default="~/.config/greenroom",
    help="The directory where the gama config is stored. Resolved relative to: ~/.config/greenroom",
)


@click.group(help="Commands for the vessel")
def vessel():
    pass


@click.command(name="build")
@click.argument(
    "service",
    required=False,
    type=click.Choice(SERVICES),
)
@click.option("--pull", is_flag=True, help="Pull the latest images")
@click.argument("args", nargs=-1)
@config_dir_option
def build(service: str, args: List[str], pull: bool = False, config_dir: str = "~/.config/greenroom"):  # type: ignore
    """Build the vessel"""
    set_initial_env(config_dir)
    config = get_vessel_config_io().read()
    set_env(config)

    docker = DockerClient(
        compose_files=_get_compose_files(variant=config.variant, prod=False),
        compose_project_directory=get_project_root(),
        compose_project_name=config.namespace_vessel,
    )

    if service:
        docker.compose.build([service], pull=pull)
        return

    docker.compose.build(pull=pull)


@click.command(name="pull-local")
@click.option(
    "--host",
    "-h",
    type=str,
    required=True,
    help="The host to pull the images from, ie localhost:5555",
)
@click.argument(
    "service",
    required=False,
    type=click.Choice(SERVICES),
)
@config_dir_option
def pull_local(host: str, service: Optional[str] = None, config_dir: str = "~/.config/greenroom"):  # type: ignore
    execute_command_on_seperate_registry(pull_and_tag, host, service, config_dir)


@click.command(name="push-local")
@click.option(
    "--host",
    "-h",
    type=str,
    required=True,
    help="The host  push the images to, ie localhost:5555",
    default="localhost:5555",
)
@click.argument(
    "service",
    required=False,
    type=click.Choice(SERVICES),
)
@config_dir_option
def push_local(host: str, service: Optional[str] = None, config_dir: str = "~/.config/greenroom"):  # type: ignore
    # pass the context to execute_command_on_seperate_registry
    execute_command_on_seperate_registry(tag_and_push, host, service, config_dir)


@click.command(name="bake")
@click.option(
    "--variant",
    type=click.Choice(Variant),  # type: ignore
    help="The variant to bake",
    default=Variant.ARMIDALE,
)
@click.option(
    "--version",
    type=str,
    default="latest",
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
def bake(variant: Variant, version: str, push: bool, services: List[str]):  # type: ignore
    """Bakes the vessel docker containers"""
    compose_files = _get_compose_files(variant=variant)
    docker_bake(
        version=version,
        services=services,
        push=push,
        compose_files=compose_files,
    )


@click.command(name="test-ui")
@config_dir_option
def test_ui(config_dir: str = "~/.config/greenroom"):  # type: ignore
    """Runs test for the ui"""
    set_initial_env(config_dir)
    config = get_vessel_config_io().read()
    set_env(config)
    docker = DockerClient(
        compose_files=_get_compose_files(),
        compose_project_directory=get_project_root(),
        compose_project_name=config.namespace_vessel,
    )
    docker.compose.run("gama_ui", ["npm", "run", "test"])


@click.command(name="test-ros")
@config_dir_option
def test_ros(config_dir: str = "~/.config/greenroom"):  # type: ignore
    """Runs test for the ros nodes"""
    set_initial_env(config_dir)
    config = get_vessel_config_io().read()
    set_env(config)
    docker = DockerClient(
        compose_files=_get_compose_files(),
        compose_project_directory=get_project_root(),
        compose_project_name=config.namespace_vessel,
    )
    docker.compose.run(
        "gama_vessel",
        ["platform", "ros", "test"],
    )


@click.command(name="test-scenarios")
@click.option(
    "--restart",
    type=bool,
    default=False,
    is_flag=True,
    help="Should we restart the containers? Default: False",
)
@click.option(
    "--sim-speed",
    type=float,
    default=25.0,
    help="What speed should the scenarios be run at? Default: 25",
)
@click.argument("name", required=False, type=str)
def test_scenarios(restart: bool, sim_speed: float, name: Optional[str]):
    """Runs the scenario tests"""

    raise Exception("This command is not supported yet")


@click.command(name="test-e2e")
def test_e2e():  # type: ignore
    """Runs UI e2e tests (assuming all the containers are up)"""
    call("cd ./projects/gama_ui && npm run test:e2e")


@click.command(name="test-variant")
@click.option("--missim", is_flag=True, help="Run missim waypoint test", default=False)
@click.option("--vcan", is_flag=True, help="Set up vcan interfaces", default=False)
@config_dir_option
def test_variant(missim: bool, vcan: bool, config_dir: str = "~/.config/greenroom"):  # type: ignore
    """Test that all variant nodes start successfully using pytest and launch_testing"""
    set_initial_env(config_dir)
    config = get_vessel_config_io().read()
    set_env(config)

    # Set up the same environment variables as the 'up' command
    os.environ["GAMA_VESSEL_CONFIG"] = get_vessel_config_io().serialise(config)
    os.environ["GAMA_VERSION"] = get_gama_version()
    os.environ["GAMA_VESSEL_HOST"] = (
        config.discovery.discovery_server_ip
        if config.discovery.type == "fastdds" or config.discovery.type == "zenoh"
        else "localhost"
    )
    os.environ["ROS_DOMAIN_ID"] = (
        str(config.discovery.ros_domain_id) if config.discovery.type == "simple" else "0"
    )
    os.environ["RMW_IMPLEMENTATION"] = (
        "rmw_zenoh_cpp" if config.discovery.type == "zenoh" else "rmw_fastrtps_cpp"
    )

    docker = DockerClient(
        compose_files=_get_compose_files(
            network=config.network,
            variant=config.variant,
            prod=False,
        ),
        compose_project_directory=get_project_root(),
        compose_project_name=config.namespace_vessel,
    )

    # Run pytest using the pytest_launch.py script inside the gama_vessel container
    click.echo(f"Running variant {config.variant} launch tests using pytest_launch.py script...")

    launch_script = "pytest_launch.py --missim" if missim else "pytest_launch.py"

    # If missim has been requested, then make sure there is a missim_core container running
    if missim:
        # Check if missim_core container is running
        try:
            running_containers = docker.container.list()
            missim_running = any(
                "missim_core" in container.name for container in running_containers
            )
            if not missim_running:
                click.echo(
                    click.style(
                        "✗ missim_core container is not running. Please start it first.", fg="red"
                    )
                )
                raise click.ClickException("missim_core container required for missim tests")
        except Exception as e:
            click.echo(click.style(f"✗ Failed to check for missim_core container: {e}", fg="red"))
            raise click.ClickException("Could not verify missim_core container status")

    try:
        if vcan and config.variant in SIMULATION_VCAN_VARIANTS:
            try:
                vcan_setup("up", SIMULATION_VCAN_VARIANTS[config.variant])
            except Exception as e:
                click.echo(
                    click.style(
                        f"✗ Failed to set up vcan interfaces, probably already configured: {e}",
                        fg="red",
                    )
                )

        docker.compose.run(
            "gama_vessel",
            [
                "bash",
                "-c",
                f"source ~/.profile && python3 /home/ros/gama_vessel/src/gama_bringup/scripts/{launch_script}",
            ],
            remove=True,
        )
        click.echo(click.style("✓ All variant tests passed!", fg="green"))
    except Exception as e:
        raise click.ClickException(f"Variant tests failed: {e}")


@click.command(name="test")
def test():  # type: ignore
    """Runs test for the all vessel code"""
    call("gama_cli vessel test-ui")
    call("gama_cli vessel test-ros")


@click.command(name="lint-ui")
@click.argument("args", nargs=-1)
@config_dir_option
def lint_ui(args: List[str], config_dir: str = "~/.config/greenroom"):  # type: ignore
    """Runs lints for the ui"""
    set_initial_env(config_dir)
    config = get_vessel_config_io().read()
    set_env(config)
    docker = DockerClient(
        compose_files=_get_compose_files(),
        compose_project_directory=get_project_root(),
        compose_project_name=config.namespace_vessel,
    )
    docker.compose.run("gama_ui", ["npm", "run", "lint", *args])


@click.command(name="type-generate")
@config_dir_option
def type_generate(config_dir: str = "~/.config/greenroom"):  # type: ignore
    """Generates typescript types & schemas for all ros messages"""
    click.echo(
        click.style("Generating typescript types & schemas for all ros messages", fg="green")
    )

    # check the version of node
    node_version = subprocess.run(["node", "--version"], stdout=subprocess.PIPE).stdout.decode(
        "utf-8"
    )
    if int(node_version.split(".")[0][1:]) < 20:
        click.echo(click.style("Node version less than 20, please upgrade", fg="red"))
        return

    set_initial_env(config_dir)
    config = get_vessel_config_io().read()
    set_env(config)
    docker = DockerClient(
        compose_files=_get_compose_files(
            network=config.network, variant=config.variant, prod=False
        ),
        compose_project_directory=get_project_root(),
        compose_project_name=config.namespace_vessel,
    )
    subprocess.run(["npm", "run", "generate"], cwd=get_project_root() / "projects/gama_ui")

    docker.compose.execute(
        "gama_vessel",
        [
            "bash",
            "-l",
            "-c",
            "python3 src/gama_packages/mission_plan_runner/mission_plan_runner/generate_schemas.py",
        ],
    )
    docker.compose.execute("gama_vessel", ["npx", "ros-typescript-generator"])


@click.command(name="up")
@click.option(
    "--build",
    type=bool,
    default=False,
    is_flag=True,
    help="Should we rebuild the docker containers? Default: False",
)
@click.option(
    "--nowatch",
    type=bool,
    default=False,
    is_flag=True,
    help="Should we prevent gama_vessel from watching for changes? Default: False",
)
@click.argument(
    "service",
    required=False,
    type=click.Choice(SERVICES),
)
@click.argument("args", nargs=-1)
@config_dir_option
def up(
    build: bool,
    nowatch: bool,
    service: str,
    args: List[str],
    config_dir: str = "~/.config/greenroom",
):
    """Starts the vessel"""
    dev_mode = os.environ["GAMA_CLI_DEV_MODE"] == "true"

    set_initial_env(config_dir)
    config = get_vessel_config_io().read()
    set_env(config)
    build = maybe_ignore_build(dev_mode, build)
    prod = maybe_ignore_prod(dev_mode, config.prod)
    log_config(config)

    if prod and build:
        raise click.UsageError("Cannot build in production mode. Run `gama vessel build` instead")

    # Make the log and chart tiles directories
    log_directory = Path(config.log_directory).expanduser()
    recording_directory = Path(config.recording_directory).expanduser()
    charts_dir = Path(config.charts_directory).expanduser()
    get_vessel_config_io().get_path().chmod(0o777)
    make_dir_set_permission(log_directory)
    make_dir_set_permission(recording_directory)
    make_dir_set_permission(charts_dir)

    # If charts_dir is empty, copy the default charts
    if not os.listdir(charts_dir):
        if dev_mode:
            default_charts_dir = Path(get_project_root()) / "data/charts"
            call(f"cp -r {default_charts_dir}/* {charts_dir}")
        else:
            raise click.UsageError(f"Charts are missing. Add some charts to {charts_dir}")

    docker = DockerClient(
        compose_files=_get_compose_files(
            network=config.network,
            variant=config.variant,
            prod=prod,
        ),
        compose_project_directory=get_project_root(),
        compose_project_name=config.namespace_vessel,
    )

    if prod:
        gama_vessel_command = "ros2 launch ./src/gama_bringup/launch/configure.launch.py"
    else:
        # build packages and watch for changes
        gama_vessel_command_args = "--build"
        if not nowatch:
            gama_vessel_command_args += " --watch"

        gama_vessel_command = f"platform ros run {gama_vessel_command_args} ros2 launch ./src/gama_bringup/launch/configure.launch.py"

    os.environ["GAMA_VESSEL_CONFIG"] = get_vessel_config_io().serialise(config)
    os.environ["GAMA_VERSION"] = get_gama_version()
    os.environ["GAMA_VESSEL_HOST"] = (
        config.discovery.discovery_server_ip
        if config.discovery.type == "fastdds" or config.discovery.type == "zenoh"
        else "localhost"
    )
    os.environ["GAMA_VESSEL_COMMAND"] = gama_vessel_command
    os.environ["GAMA_LOG_DIR"] = str(log_directory)
    os.environ["GAMA_RECORDING_DIR"] = str(recording_directory)
    os.environ["GAMA_CHARTS_DIR"] = str(charts_dir)
    os.environ["ROS_DOMAIN_ID"] = (
        str(config.discovery.ros_domain_id) if config.discovery.type == "simple" else "0"
    )
    os.environ["GAMA_RECORDINGS_DIR"] = str(recording_directory)
    os.environ["RMW_IMPLEMENTATION"] = (
        "rmw_zenoh_cpp" if config.discovery.type == "zenoh" else "rmw_fastrtps_cpp"
    )

    services = (
        [service]
        if service
        else [
            "gama_ui",
            "gama_chart_tiler",
            "gama_chart_api",
            "gama_vessel",
            "gama_greenstream",
            "gama_docs",
        ]
    )

    # Filter out shared services that are already running
    services_to_start, same_instance_services = filter_services_to_start(services, SHARED_SERVICES)

    if not services_to_start:
        click.echo(
            click.style(
                "All requested services are already running. Nothing to start.", fg="green"
            )
        )
        return

    docker.compose.up(
        services_to_start,
        detach=True,
        build=build,
    )


@click.command(name="down")
@click.argument("args", nargs=-1)
@config_dir_option
def down(args: List[str], config_dir: str = "~/.config/greenroom"):  # type: ignore
    """Stops the vessel"""
    set_initial_env(config_dir)
    config = get_vessel_config_io().read()
    set_env(config)
    docker = DockerClient(
        compose_files=_get_compose_files(),
        compose_project_directory=get_project_root(),
        compose_project_name=config.namespace_vessel,
    )
    # set timeout to 20 secs (default 10) to allow for graceful shutdown of rosbag et al
    docker.compose.down(timeout=20)


@click.command(name="install")
@click.option(
    "--variant",
    type=click.Choice(Variant),  # type: ignore
    help="Which variant of GAMA to install?",
)
@config_dir_option
def install(variant: Variant, config_dir: str = "~/.config/greenroom"):  # type: ignore
    """Install GAMA on a vessel"""
    set_initial_env(config_dir)
    config = get_vessel_config_io().read()
    set_env(config)
    variant = variant or config.variant
    os.environ["GAMA_VERSION"] = get_gama_version()
    docker = DockerClient(
        compose_files=_get_compose_files(variant=variant),
        compose_project_directory=get_project_root(),
        compose_project_name=config.namespace_vessel,
    )
    try:
        docker.compose.pull(
            [
                "gama_ui",
                "gama_chart_tiler",
                "gama_chart_api",
                "gama_vessel",
                "gama_greenstream",
                "gama_docs",
            ]
        )
    except Exception:
        click.echo(
            click.style(
                "Failed to pull GAMA files. Have you ran `gama authenticate` ?",
                fg="yellow",
            )
        )


@click.command(name="configure")
@click.option(
    "--variant",
    type=click.Choice(Variant),  # type: ignore
    help="The Variant",
    required=True,
    prompt="Which variant of GAMA to configure?",
)
@click.option(
    "--mode",
    type=click.Choice(Mode),  # type: ignore
    help="The Mode",
    required=True,
    prompt="Which mode to run in?",
)
@click.option(
    "--prod",
    type=bool,
    help="Whether to run in production mode",
    is_flag=True,
)
@click.option(
    "--skip-confirm",
    type=bool,
    help="Skip confirmation",
    is_flag=True,
)
@click.option(
    "--include-defaults",
    type=bool,
    help="Include default values in the generated config file",
    is_flag=True,
)
@config_dir_option
def configure(
    variant: Variant,
    mode: Mode,
    prod: bool,
    skip_confirm: bool,
    include_defaults: bool,
    config_dir: str = "~/.config/greenroom",
):
    """Configure GAMA Vessel"""
    set_initial_env(config_dir)
    config = DEFAULT_VARIANT_CONFIGS_MAP[variant]
    if mode is not None:
        config.mode = mode
    if prod is not None:
        config.prod = prod

    config.cameras = [
        Camera(
            name="bow",
            type="color",
            order=0,
            ptz=False,
        )
    ]

    # Check if the file exists
    if os.path.exists(get_vessel_config_io().get_path()):
        click.echo(
            click.style(
                f"GAMA Vessel config already exists: {get_vessel_config_io().get_path()}",
                fg="yellow",
            )
        )
        result = skip_confirm or click.prompt(
            "Do you want to overwrite it?", default="y", type=click.Choice(["y", "n"])
        )
        if result == "n":
            return

    get_vessel_config_io().write(config, include_defaults=include_defaults)


@click.command(name="config")
@config_dir_option
def config(config_dir: str = "~/.config/greenroom"):  # type: ignore
    """Read Config"""
    set_initial_env(config_dir)
    config = get_vessel_config_io().read()
    log_config(config)


@click.command(name="manifest")
@click.option(
    "--version",
    type=str,
    required=True,
    help="The version to create manifests for",
)
def manifest(version: str):  # type: ignore
    """Create and push multi-arch Docker manifests for vessel images"""
    # List of all vessel images that need manifests
    images = [
        "gama_ui",
        "gama_greenstream",
        "gama_gs",
        "gama_docs_austal_m_usv",
        "gama_docs_tenggara",
        "gama_docs_dmak",
        "gama_docs_mars",
        "gama_docs_fremantle",
        "gama_vessel_austal_m_usv",
        "gama_vessel_tenggara",
        "gama_vessel_dmak",
        "gama_vessel_mars",
        "gama_vessel_fremantle",
    ]

    # For now, only amd64 is supported. When arm64 support is added, pass ["amd64", "arm64"]
    docker_manifest(version=version, images=images, archs=["amd64"])
