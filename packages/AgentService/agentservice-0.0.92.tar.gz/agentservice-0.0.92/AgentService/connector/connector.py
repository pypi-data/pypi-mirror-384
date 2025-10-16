
import asyncio
import enum
import functools
import typing
import aiohttp

from loguru import logger

from .event import ToolEvent

from AgentService.types import (
    AgentResponse, Tool,
    ToolAnswer, ChatToolState
)

from AgentService.enums.tool import ToolResponse
from AgentService.enums.agent import AgentResponseType

from AgentService.app.routes.chat.models import SendMessageRequest


class AgentConnector:
    def __init__(
        self,
        endpoint: str,
        key: str = None
    ):

        self.log = logger.bind(classname=self.__class__.__name__)

        self.endpoint = endpoint[:-1] if endpoint.endswith("/") else endpoint
        self.key = key

        self.callbacks = {}

    def bind_tool_output(self, tool_name: str, function: typing.Callable):
        self.callbacks.update({tool_name: functools.partial(self.answer_tool, function=function)})
        self.log.debug(f"Binded callback -> {tool_name} -> {function}")

    async def add_to_storage(self, key: str, data: list[dict] | dict):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=f"{self.endpoint}/storage/add",
                json={
                    "key": key,
                    "data": data
                },
                raise_for_status=False
            ) as resp:

                self.log.debug(f"Got response -> {await resp.text()}")
                return await resp.json()

    async def remove_from_storage(self, key: str, data: list[dict] | dict):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=f"{self.endpoint}/storage/remove",
                json={
                    "key": key,
                    "data": data
                },
                raise_for_status=False
            ) as resp:

                self.log.debug(f"Got response -> {await resp.text()}")
                return await resp.json()

    async def update_storage(self, key: str, data: dict, new_data: dict):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=f"{self.endpoint}/storage/update",
                json={
                    "key": key,
                    "data": data,
                    "new_data": new_data
                },
                raise_for_status=False
            ) as resp:

                self.log.debug(f"Got response -> {await resp.text()}")
                return await resp.json()

    async def get_from_storage(self, key: str) -> list[dict]:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=f"{self.endpoint}/storage",
                json={
                    "key": key
                },
                raise_for_status=False
            ) as resp:

                self.log.debug(f"Got response -> {await resp.text()}")
                return await resp.json()

    async def answer_tool(self, event: ToolEvent, function: typing.Callable) -> ToolAnswer:
        try:
            response = await function(data=event.tool.arguments, chat_id=event.chat_id)

            if response in [None, ""]:
                response = "function returned nothing"

            elif isinstance(response, enum.Enum):
                response = response.value

            elif not isinstance(response, str):
                response = str(response)

            return ToolAnswer(
                tool_id=event.tool.tool_id,
                name=event.tool.name,
                text=response
            )

        except Exception as err:
            self.log.exception(err)

            return ToolAnswer(
                tool_id=event.tool.tool_id,
                name=event.tool.name,
                text="function returned nothing"
            )

    async def dispatch_event(self, event: ToolEvent):
        callback = self.callbacks.get(event.tool.name)

        if not callback:
            self.log.warning(f"Can't find callback function \"{event.tool.name}\" in {self.callbacks}")

            return ToolAnswer(
                tool_id=event.tool.tool_id,
                name=event.tool.name,
                text="function not binded"
            )

        while True:
            response: ToolAnswer = await callback(event=event)
            self.log.debug(f"Dispatching event -> {event} -> {callback} -> {response}")

            try:
                ToolResponse[response.text]

            except KeyError:
                break

            await asyncio.sleep(5)

        return response

    async def handle_tools(self, tools: list[Tool], chat_id) -> list[ToolAnswer]:
        tool_answers = [
            await self.dispatch_event(ToolEvent(tool_name=tool.name, tool=tool, chat_id=chat_id))
            for tool in tools
        ]

        return tool_answers

    async def request(self, request: SendMessageRequest) -> AgentResponse:
        self.log.debug(f"Sending request -> {request.to_dict()}")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=f"{self.endpoint}/chat",
                json=request.to_dict(),
                raise_for_status=False
            ) as resp:

                self.log.debug(f"Got response -> {await resp.text()}")

                response = await resp.json()
                agent_response = AgentResponse(**response["data"])

                return agent_response

    async def send(self, chat_id: str, text: str = None, context: dict = {}, tool_answers: list[ToolAnswer] = []) -> AgentResponse:
        agent_response = await self.request(SendMessageRequest(chat_id=chat_id, text=text, context=context, tool_answers=tool_answers))

        if agent_response.type == AgentResponseType.answer:
            return agent_response

        tool_answers = await self.handle_tools(agent_response.content, chat_id)

        return await self.send(chat_id, tool_answers=tool_answers)

    async def send_tool_states(self, tools: list[Tool], chat_id: str):
        tool_answers = await self.handle_tools(tools, chat_id)

        return await self.send(chat_id, tool_answers=tool_answers)

    async def request_tool_states(self) -> list[ChatToolState]:
        self.log.debug(f"Getting tool states")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=f"{self.endpoint}/chat/states",
                raise_for_status=False
            ) as resp:
                self.log.debug(f"Got response -> {await resp.text()}")

                response = await resp.json()
                tool_states = list(map(lambda x: ChatToolState(**x), response))

                return tool_states

    async def handle_tool_states(self):
        tool_states = await self.request_tool_states()
        tools_by_chat = {}

        for tool_state in tool_states:
            if tool_state.chat_id not in tools_by_chat:
                tools_by_chat[tool_state.chat_id] = []

            tools_by_chat[tool_state.chat_id].append(Tool(
                id=tool_state.tool_id,
                name=tool_state.name,
                arguments=tool_state.arguments
            ))

        return await asyncio.gather(*[
            self.send_tool_states(tools_by_chat[chat_id], chat_id=chat_id)
            for chat_id in tools_by_chat
        ])
