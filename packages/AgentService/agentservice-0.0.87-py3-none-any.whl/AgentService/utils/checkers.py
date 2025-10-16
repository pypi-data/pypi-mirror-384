
import os
import re


def is_project_name(project_name: str) -> bool:
    return not re.search(r'^[_a-zA-Z]\w*$', project_name) is None


def is_project(project_path: os.PathLike) -> bool:
    return os.path.isfile(os.path.join(project_path, "agent.cfg"))
