import click


def get_banner(mode: str, version: str):
    return "\n".join(
        [
            "\b",
            click.style("      ___           ___           ___           ___       ", bg="green")
            + click.style("       ___           ___              ", bg="yellow"),
            click.style(r"     /\  \         /\  \         /\__\         /\  \      ", bg="green")
            + click.style(r"      /\  \         /\__\      ___    ", bg="yellow"),
            click.style(r"    /::\  \       /::\  \       /::|  |       /::\  \     ", bg="green")
            + click.style(r"     /::\  \       /:/  /     /\  \   ", bg="yellow"),
            click.style(r"   /:/\:\  \     /:/\:\  \     /:|:|  |      /:/\:\  \    ", bg="green")
            + click.style(r"    /:/\:\  \     /:/  /      \:\  \  ", bg="yellow"),
            click.style(r"  /:/  \:\  \   /::\~\:\  \   /:/|:|__|__   /::\~\:\  \   ", bg="green")
            + click.style(r"   /:/  \:\  \   /:/  /       /::\__\ ", bg="yellow"),
            click.style(r" /:/__/_\:\__\ /:/\:\ \:\__\ /:/ |::::\__\ /:/\:\ \:\__\  ", bg="green")
            + click.style(r"  /:/__/ \:\__\ /:/__/     __/:/\/__/ ", bg="yellow"),
            click.style(r" \:\  /\ \/__/ \/__\:\/:/  / \/__/~~/:/  / \/__\:\/:/  /  ", bg="green")
            + click.style(r"  \:\  \  \/__/ \:\  \    /\/:/  /    ", bg="yellow"),
            click.style(r"  \:\ \:\__\        \::/  /        /:/  /       \::/  /   ", bg="green")
            + click.style(r"   \:\  \        \:\  \   \::/__/     ", bg="yellow"),
            click.style(r"   \:\/:/  /        /:/  /        /:/  /        /:/  /    ", bg="green")
            + click.style(r"    \:\  \        \:\  \   \:\__\     ", bg="yellow"),
            click.style(r"    \::/  /        /:/  /        /:/  /        /:/  /     ", bg="green")
            + click.style(r"     \:\__\        \:\__\   \/__/     ", bg="yellow"),
            click.style(r"     \/__/         \/__/         \/__/         \/__/      ", bg="green")
            + click.style(r"      \/__/         \/__/             ", bg="yellow"),
            click.style("                                                          ", bg="green")
            + click.style("                                      ", bg="yellow"),
            "\b",
            "Mode: "
            + click.style(mode, fg="green")
            + " - Version: "
            + click.style(version, fg="yellow"),
            "Powered by: " + click.style("Greenroom Robotics", fg="green"),
        ]
    )
