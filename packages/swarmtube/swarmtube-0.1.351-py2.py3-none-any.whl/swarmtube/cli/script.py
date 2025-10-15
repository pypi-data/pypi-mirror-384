# import re
# import os
# import yaml

import click

# from swarmtube.helpers import *
from swarmtube.cli.main import main, CONTEXT_SETTINGS
from swarmtube.cli.config import config

from swarmtube.definitions import DEFAULT_LANGUAGE, UID_TYPE

# TODO: include any logic from module core
# Examples
# from swarmtube.models import *
# from swarmtube.logic import Tagger
# from syncmodels.storage import Storage

# Import local scripts models
from swarmtube.models.script import SwarmtubeScript as Item
from swarmtube.models.script import SwarmtubeScriptRequest as Request
from swarmtube.models.script import SwarmtubeScriptResponse as Response

# ---------------------------------------------------------
# Dynamic Loading Interface / EP Exposure
# ---------------------------------------------------------
TAG = "Scripts"
DESCRIPTION = "Scripts CLI API"
API_ORDER = 10

# ---------------------------------------------------------
# Loggers
# ---------------------------------------------------------

from agptools.logs import logger

log = logger(__name__)


# ---------------------------------------------------------
# Script CLI port implementation
# ---------------------------------------------------------
@main.group(context_settings=CONTEXT_SETTINGS)
@click.pass_obj
def script(env):
    """subcommands for managing scripts for swarmtube"""
    # banner("User", env.__dict__)


submodule = script


@submodule.command()
@click.option("--path", default=None)
@click.pass_obj
def create(env, path):
    """Create a new script for swarmtube"""
    # force config loading
    config.callback()

    # TODO: implement


@submodule.command()
@click.pass_obj
def read(env):
    """Find and list existing scripts for swarmtube"""
    # force config loading
    config.callback()

    # TODO: implement


@submodule.command()
@click.pass_obj
def update(env):
    """Update and existing scripts for swarmtube"""
    # force config loading
    config.callback()

    # TODO: implement


@submodule.command()
@click.pass_obj
def delete(env):
    """Delete an existing scripts for swarmtube"""
    # force config loading
    config.callback()

    # TODO: implement
