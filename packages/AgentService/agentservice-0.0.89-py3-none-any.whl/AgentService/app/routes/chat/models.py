
from typing import Optional, Dict, List
from pydantic import BaseModel, Field

from AgentService.types import AgentResponse, ChatToolState, ToolAnswer
from AgentService.enums.response import ResposneStatus


class SendMessageRequest(BaseModel):
    chat_id: str
    text: Optional[str] = None
    context: Dict = Field(default_factory=dict)
    tool_answers: List[ToolAnswer] = Field(default_factory=list)


class SendMessageResponse(BaseModel):
    data: Optional[AgentResponse] = None
    description: Optional[str] = None
    status: ResposneStatus


class GetStatesRequest(BaseModel):
    chat_id: str


class GetStatesResponse(BaseModel):
    data: list[ChatToolState] = Field(default_factory=list)
    description: Optional[str] = None
    status: ResposneStatus
