
import fastapi
from beanie.operators import And

from AgentService.config import Config

from AgentService.types.chat import ChatToolState, Chat
from AgentService.enums.chat import ChatToolStateStatus

from .models import (
    SendMessageRequest, SendMessageResponse,
    GetStatesRequest, GetStatesResponse
)


chat_router = fastapi.APIRouter(prefix="/chat")


@chat_router.post("")
async def send_message(request: SendMessageRequest) -> SendMessageResponse:
    agent = Config().agent

    response = await agent.answer(
        chat_id=request.chat_id,
        text=request.text,
        context=request.context,
        tool_answers=list(map(lambda x: x.dict(), request.tool_answers))
    )

    return SendMessageResponse(
        data=response,
        status="ok"
    )


@chat_router.get("states")
async def get_states() -> GetStatesResponse:
    states = await ChatToolState.find_all().to_list()

    return GetStatesResponse(
        data=states,
        status="ok"
    )


@chat_router.get("state")
async def get_state(request: GetStatesRequest) -> GetStatesResponse:
    chat = await Chat.find_one(Chat.chat_id == request.chat_id)

    if not chat:
        return GetStatesResponse(
            description=f"Can't find such chat {request.chat_id}",
            status="error"
        )

    states = await ChatToolState.find_many(
        And(
            ChatToolState.chat_id == chat.id,
            ChatToolState.status == ChatToolStateStatus.in_progress
        )
    ).to_list()

    return GetStatesResponse(
        data=states,
        status="ok"
    )
