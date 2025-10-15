import gama_cli.groups.attach as attach
import gama_cli.groups.docker as docker
import gama_cli.groups.git as git
import gama_cli.groups.gs as gs
import gama_cli.groups.misc as misc
import gama_cli.groups.vessel as vessel
import gama_cli.groups.setup as setup
from gama_cli.helpers import is_dev_version, get_gama_version
from gama_cli.banner import get_banner
import click
import os


def cli():
    dev_mode = is_dev_version()
    version = get_gama_version()
    mode = "Developer" if dev_mode else "User"
    banner = get_banner(mode, version)

    os.environ["GAMA_CLI_DEV_MODE"] = "true" if dev_mode else "false"

    @click.group(help=banner)
    def gama_cli():
        pass

    gama_cli.add_command(misc.authenticate)
    gama_cli.add_command(misc.upgrade)

    gama_cli.add_command(vessel.vessel)
    vessel.vessel.add_command(vessel.up)
    vessel.vessel.add_command(vessel.down)
    vessel.vessel.add_command(vessel.configure)
    vessel.vessel.add_command(vessel.config)
    vessel.vessel.add_command(vessel.install)
    vessel.vessel.add_command(vessel.pull_local)

    gama_cli.add_command(gs.gs)
    gs.gs.add_command(gs.up)
    gs.gs.add_command(gs.down)
    gs.gs.add_command(gs.configure)
    gs.gs.add_command(gs.config)
    gs.gs.add_command(gs.install)

    if dev_mode:
        gama_cli.add_command(misc.test)
        gama_cli.add_command(misc.test_e2e)
        gama_cli.add_command(misc.lint)

        gama_cli.add_command(attach.attach)
        attach.attach.add_command(attach.vessel)
        attach.attach.add_command(attach.ui)
        attach.attach.add_command(attach.gs)

        gama_cli.add_command(docker.docker)
        docker.docker.add_command(docker.clearlogs)
        docker.docker.add_command(docker.registry)
        docker.docker.add_command(docker.list_registry)

        gama_cli.add_command(git.git)
        git.git.add_command(git.pull)

        gama_cli.add_command(setup.setup)
        setup.setup.add_command(setup.secrets)

        vessel.vessel.add_command(vessel.build)
        vessel.vessel.add_command(vessel.bake)
        vessel.vessel.add_command(vessel.manifest)
        vessel.vessel.add_command(vessel.test)
        vessel.vessel.add_command(vessel.push_local)
        vessel.vessel.add_command(vessel.type_generate)
        vessel.vessel.add_command(vessel.test_ui)
        vessel.vessel.add_command(vessel.test_e2e)
        vessel.vessel.add_command(vessel.test_ros)
        vessel.vessel.add_command(vessel.test_variant)
        vessel.vessel.add_command(vessel.test_scenarios)
        vessel.vessel.add_command(misc.vcan)

        gs.gs.add_command(gs.build)
        gs.gs.add_command(gs.bake)
        gs.gs.add_command(gs.test)

    gama_cli()


if __name__ == "__main__":
    cli()
