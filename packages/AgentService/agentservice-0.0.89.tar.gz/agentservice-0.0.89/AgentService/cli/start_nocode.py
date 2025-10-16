
import json

import click
from loguru import logger as log

from AgentService.agent import Agent, AgentTool
from AgentService.config import Config
from AgentService.app import start_app
from AgentService.types import setup_database


@click.group()
def group():
    pass


@group.command('start', help="Command that starts AgentService project")
def start_project():
    log.info(f"Starting AgentService project")

    with open("agent.json", "r") as f:
        data = json.load(f)

    tools_raw = data.pop("tools", [])

    cls = type("Agent0", (Agent, ), data)
    agents = [cls]

    first_agent = agents[0]
    log.info(f"Found {len(agents)} agents. Using first one: {first_agent.__name__}")

    tools = []
    for i, tool_raw in enumerate(tools_raw):
        cls = type(f"{AgentTool.__name__}{i}", (AgentTool, ), tool_raw)
        tools.append(cls())

    log.info(f"Found {len(tools)} tools: {tools}")

    config = Config()

    agent = first_agent(
        openai_key=config.openai_key,
        tools=tools
    )
    config.set_agent(agent)

    start_app()
