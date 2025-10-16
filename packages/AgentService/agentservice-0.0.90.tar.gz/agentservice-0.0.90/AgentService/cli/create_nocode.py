
import AgentService
from AgentService.utils.checkers import is_project, is_project_name
from AgentService.utils.templates import process_template

from shutil import ignore_patterns, copytree
import os
import click

import string


PROJECT_TEMPLATES = (
    ("agent.cfg", ),
)


IGNORE = ignore_patterns('*.pyc', '__pycache__', '.svn')


@click.group()
def group():
    pass


@group.command('create_nocode', help="Command that creates nocode AgentService project")
@click.argument('project_name', type=str)
def create_project_nocode(project_name):
    current_path = os.getcwd()
    templates_dir = os.path.join(AgentService.__path__[0], "templates", "project_nocode")
    project_dir = os.path.join(current_path, project_name)

    if is_project(current_path):
        return print(
            {"status": "err", "description": f"Error: AgentService project has already created in {current_path}"}
        )

    if os.path.isdir(project_name):
        return print(
            {"status": "err", "description": f"Error: directory with name {project_name} already exists in {project_dir}"}
        )

    if not is_project_name(project_name):
        return print(
            {"status": "err", "description": "Error: AgentService project names must begin with a letter and contain only letters, numbers and underscores"}
        )

    copytree(templates_dir, project_dir, ignore=IGNORE)

    for paths in PROJECT_TEMPLATES:
        file_path = os.path.join(
            project_dir,
            string.Template(os.path.join(*paths)).substitute(project_name=project_name)
        )
        process_template(file_path, project_name=project_name)

    return print(
        {"status": "ok", "description": f"AgentService project with name {project_name} has been created in {project_dir}"}
    )
