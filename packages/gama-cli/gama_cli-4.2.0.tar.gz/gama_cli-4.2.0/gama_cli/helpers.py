from typing import List, Dict
from dataclasses import dataclass
import click
import os
from pathlib import Path
import subprocess
import yaml
import platform
from python_on_whales.utils import ValidPath
from python_on_whales.docker_client import DockerClient
import pkg_resources


@dataclass
class ServiceInstanceInfo:
    """Information about a service's running state and instance ownership"""

    is_running: bool
    is_same_instance: bool
    container_name: str = ""


def get_project_root() -> Path:
    current_file_dir = Path(__file__).parent
    return current_file_dir.parent.parent.parent


def make_dir_set_permission(path: Path, permission=0o777) -> Path:
    """Make a directory and set the permissions"""
    os.makedirs(path, mode=permission, exist_ok=True)
    path.chmod(permission)
    # If this errors then the current user does not have permission to set the permissions
    # This probably means the directory already exists
    return path


def get_gama_version():
    """GAMA version is latest if it is a dev version otherwise it is the CLI version"""
    version = pkg_resources.require("gama-cli")[0].version
    if version == "0.0.0":
        version = "latest"
    return version


def is_dev_version():
    if os.environ.get("GAMA_CLI_DEV_MODE") == "false":
        return False

    if os.environ.get("GAMA_CLI_DEV_MODE") == "true":
        return True
    return pkg_resources.require("gama_cli")[0].version == "0.0.0"


def docker_compose_path(path: str) -> Path:
    current_file_dir = Path(__file__).parent
    return current_file_dir / "docker" / path


def check_directory_ownership(path: Path) -> bool:
    stat = path.stat()
    return stat.st_uid == os.getuid() and stat.st_gid == os.getgid()


def get_docker_file_args(files: List[str]):
    return "-f " + " -f ".join(files)


def get_args_str(args: List[str]):
    return " ".join(args)


def call(command: str, abort=True, env=None):
    click.echo(click.style(f"Running: {command}", fg="blue"))
    if env:
        env = {**os.environ, **env}

    prj_root = get_project_root()
    error = subprocess.call(command, shell=True, executable="/bin/bash", cwd=prj_root, env=env)
    if error and abort:
        raise click.ClickException("Failed")


def get_arch():
    arch = platform.machine()
    if arch == "x86_64":
        return "amd64"
    elif arch == "aarch64":
        return "arm64"
    else:
        print(f"Unsupported arch: {arch}")
        exit(1)


def docker_bake(version: str, compose_files: List[ValidPath], push: bool, services: List[str]):
    compose_args: list[str] = []
    for f in compose_files:
        compose_args.append(f"--file {f}")

    # Load the compose config
    file_args = " ".join(compose_args)
    command_get_config = f"docker compose {file_args} config"
    print("Running command: ", command_get_config)
    config = subprocess.run(
        command_get_config, shell=True, check=True, cwd=get_project_root(), capture_output=True
    )
    config = config.stdout.decode("utf-8")
    config = yaml.safe_load(config)

    # Create the bake command args
    bake_args = compose_args
    bake_args.append(
        "--provenance=false"
    )  # this allows us to create a multi-arch manifest at a later stage

    # Get the arch
    arch = get_arch()

    # Get all services we should build and set their tags and arch
    services_actual: list[str] = []
    for service, service_config in config["services"].items():
        if "image" in service_config and "build" in service_config:
            # If we have a list of services to build, only build those
            if len(services) == 0 or service in services:
                image = service_config["image"]
                image = image.split(":")[0]
                bake_args.append(f"--set {service}.platform=linux/{arch}")
                bake_args.append(f"--set {service}.tags={image}:{version}-{arch}")
                bake_args.append(f"--set {service}.tags={image}:latest-{arch}")
                services_actual.append(service)

    # Add other args
    if push:
        bake_args.append("--push")

    print(f"Baking services: {', '.join(services_actual)}...")
    bake_command = " ".join(
        [
            "docker buildx bake",
            " ".join(bake_args),
            " ".join(services_actual),
        ]
    )

    print("Running bake command: ", bake_command)
    subprocess.run(
        bake_command,
        shell=True,
        check=True,
        cwd=get_project_root(),
    )


def docker_manifest(
    version: str,
    images: List[str],
    archs: List[str] = ["amd64"],
    registry: str = "ghcr.io/greenroom-robotics",
):
    """Create and push multi-arch Docker manifests for a list of images

    Args:
        version: The version tag for the images
        images: List of image names (without registry)
        archs: List of architectures to include in the manifest (default: ["amd64"])
        registry: Docker registry URL (default: "ghcr.io/greenroom-robotics")
    """
    for image in images:
        # Create manifest for versioned tag
        versioned_tag = f"{registry}/{image}:{version}"
        versioned_arch_tags = [f"{registry}/{image}:{version}-{arch}" for arch in archs]

        click.echo(click.style(f"Creating manifest for {versioned_tag}", fg="blue"))
        manifest_create_cmd = (
            f"docker manifest create --amend {versioned_tag} {' '.join(versioned_arch_tags)}"
        )
        subprocess.run(manifest_create_cmd, shell=True, check=True, cwd=get_project_root())

        click.echo(click.style(f"Pushing manifest {versioned_tag}", fg="blue"))
        manifest_push_cmd = f"docker manifest push {versioned_tag}"
        subprocess.run(manifest_push_cmd, shell=True, check=True, cwd=get_project_root())

        # Create manifest for latest tag
        latest_tag = f"{registry}/{image}:latest"
        latest_arch_tags = [f"{registry}/{image}:latest-{arch}" for arch in archs]

        click.echo(click.style(f"Creating manifest for {latest_tag}", fg="blue"))
        manifest_create_cmd = (
            f"docker manifest create --amend {latest_tag} {' '.join(latest_arch_tags)}"
        )
        subprocess.run(manifest_create_cmd, shell=True, check=True, cwd=get_project_root())

        click.echo(click.style(f"Pushing manifest {latest_tag}", fg="blue"))
        manifest_push_cmd = f"docker manifest push {latest_tag}"
        subprocess.run(manifest_push_cmd, shell=True, check=True, cwd=get_project_root())

        click.echo(click.style(f"✓ Created manifests for {image}", fg="green"))


def maybe_ignore_build(dev_mode: bool, build: bool):
    """Force build false in non-dev mode"""
    if dev_mode:
        return build
    if build:
        click.echo(click.style("Ignoring --build flag in non-dev mode", fg="yellow"))
    return False


def maybe_ignore_prod(dev_mode: bool, prod: bool):
    """Force prod true in non-dev mode"""
    if dev_mode:
        return prod
    if prod is False:
        click.echo(click.style("Ignoring prod=false in non-dev mode", fg="yellow"))
    return True


def get_service_instance_info(services: List[str]) -> Dict[str, ServiceInstanceInfo]:
    """Get detailed information about which services are running and from which instance"""
    try:
        docker = DockerClient()
        running_containers = docker.ps()
        service_info = {}
        current_prefix = os.environ.get("GAMA_CONTAINER_PREFIX", "")

        for service in services:
            service_info[service] = ServiceInstanceInfo(
                is_running=False, is_same_instance=False, container_name=""
            )

            # Check for containers with names that match the service pattern
            for container in running_containers:
                container_name = container.name
                expected_name_with_prefix = current_prefix + service

                # Check if this container matches the service
                if (
                    container_name == service  # Direct match (no prefix)
                    or container_name == expected_name_with_prefix  # With current prefix
                    or container_name.endswith(f"_{service}")  # With any prefix
                ):
                    service_info[service] = ServiceInstanceInfo(
                        is_running=True,
                        is_same_instance=(container_name == expected_name_with_prefix),
                        container_name=container_name,
                    )
                    break

        return service_info
    except Exception:
        # If we can't check, assume none are running to avoid blocking startup
        return {service: ServiceInstanceInfo(False, False, "") for service in services}


def has_service_running_on_other_instances(service: str) -> bool:
    """Check if a service is running on any other GAMA instances (not this one)"""
    try:
        docker = DockerClient()
        running_containers = docker.ps()
        current_prefix = os.environ.get("GAMA_CONTAINER_PREFIX", "")
        expected_name_with_prefix = current_prefix + service

        for container in running_containers:
            container_name = container.name
            # Check if this container matches the service
            if (
                container_name == service  # Direct match (no prefix)
                or container_name == expected_name_with_prefix  # With current prefix
                or container_name.endswith(f"_{service}")  # With any prefix
            ):
                # If it's NOT from the same instance, we found one on another instance
                if container_name != expected_name_with_prefix:
                    return True
        return False
    except Exception:
        # If we can't check, assume none are running to avoid blocking startup
        return False


def filter_services_to_start(
    requested_services: List[str], shared_services: List[str]
) -> tuple[List[str], List[str]]:
    """
    Filter out shared services that are already running and display warnings.

    Returns:
        tuple: (services_to_start, same_instance_services)
    """
    service_info = get_service_instance_info(shared_services)
    services_to_start = []
    same_instance_services = []

    for service in requested_services:
        if service in shared_services:
            info = service_info.get(service)
            if info and info.is_running:
                if info.is_same_instance:
                    same_instance_services.append(service)
                    # Include same-instance services in services_to_start so Docker can restart them if needed
                    services_to_start.append(service)
                else:
                    click.echo(
                        click.style(
                            f"Warning: Skipping {service} - already running from another GAMA instance",
                            fg="yellow",
                        )
                    )
            else:
                services_to_start.append(service)
        else:
            services_to_start.append(service)

    return services_to_start, same_instance_services
