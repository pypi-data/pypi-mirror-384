# GAMA CLI

![GAMA CLI](./docs/gama_cli.png)

Publicly available on [PyPi](https://pypi.org/project/gama-cli/) for convenience but if you don't work at Greenroom Robotics, you probably don't want to use this.

## Install

* For development:
  * `pip install -e ./libs/gama_config`
  * `pip install -e ./tools/gama_cli`
* For production: `pip install gama-cli`
* You may also need to `export PATH=$PATH:~/.local/bin` if you don't have `~/.local/bin` in your path
* Install autocomplete:
  * bash: `echo 'eval "$(_GAMA_CLI_COMPLETE=bash_source gama)"' >> ~/.bashrc`
  * zsh: `echo 'eval "$(_GAMA_CLI_COMPLETE=zsh_source gama)"' >> ~/.zshrc` (this is much nicer)

## Usage

* `gama --help` to get help with the CLI

### Groundstation

Installing a GAMA on a groundstation is as simple as this:

* `mkdir ~/gama && cd ~/gama`
* `gama authenticate` to authenticate with the GAMA package registry
* `gama gs configure` to configure GAMA on a groundstation
* `gama gs install` to install GAMA on a groundstation
* `gama gs up` to start GAMA on a groundstation
* `gama gs down` to stop GAMA on a groundstation

### Vessel

Installing a GAMA on a vessel is as simple as this:

* `mkdir ~/gama && cd ~/gama`
* `gama authenticate` to authenticate with the GAMA package registry
* `gama vessel configure` to configure GAMA on a vessel
* `gama vessel install` to install GAMA on a vessel
* `gama vessel up` to start GAMA on a vessel
* `gama vessel down` to stop GAMA on a vessel

## Dev mode

GAMA CLI can be ran in dev mode. This will happen if it is installed with `pip install -e ./tools/gama_cli` or if the environment variable `GAMA_CLI_DEV_MODE` is set to `true`.