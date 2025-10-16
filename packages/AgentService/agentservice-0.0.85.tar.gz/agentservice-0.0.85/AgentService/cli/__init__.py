
from . import create
from . import start
from . import tool

import click
import os

from AgentService.utils.checkers import is_project
from AgentService.utils.logger import setup_logger
from AgentService.config import Config


__execute = click.CommandCollection(
    sources=[
        create.group
    ],
    help='Use "agent <command> -h/--help" to see more info about a command',
)

__execute_project = click.CommandCollection(
    sources=[
        tool.group,
        start.group
    ],
    help='Use "python3.11 manage.py <command> -h/--help" to see more info about a command',
)


def execute():
    __execute()


def execute_project():
    current_path = os.getcwd()
    if not is_project(current_path):
        print(f'Error: no AgentService project found in {current_path}')
        return

    config = Config(current_path)
    setup_logger(config.log_path, config.log_level)

    __execute_project()
