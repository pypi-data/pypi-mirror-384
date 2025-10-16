
import configparser
import json
import os
import importlib

from AgentService.utils.singleton import SingletonMeta
from AgentService.agent import Agent


class Config(metaclass=SingletonMeta):
    project_name: str

    log_level: str
    log_path: str

    agent: Agent

    def __init__(self, project_path):
        config_path = os.path.join(project_path, "agent.cfg")
        config = configparser.ConfigParser()
        config.read(config_path)

        self.agent_data = None
        self.is_nocode = False

        if os.path.isfile("agent.json"):
            self.agent_data = json.load(open("agent.json", "r"))
            self.is_nocode = True

        self.openai_key = os.getenv("openai_key")
        self.db_name = os.getenv("db_name", default="AgentService")
        self.db_uri = os.getenv("db_uri")

        self.project_name = config["project"]["name"]

        self.agent_path = config["project"]["agent_source"]
        self.tools_path = config["project"]["tools_source"]

        if not self.is_nocode:
            importlib.import_module(self.agent_path)
            importlib.import_module(self.tools_path)

        self.app_host = config["app"]["host"]
        self.app_port = int(config["app"]["port"])

        self.log_level = config["logging"]["level"]
        self.log_path = config["logging"]["path"]

        self.agent = None

    def set_agent(self, agent: Agent):
        self.agent = agent
