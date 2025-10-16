
from beanie import Document

from .meta import TimestampMixin
from .tool import Tool

from ..enums.agent import AgentResponseType


class AgentResponse(TimestampMixin, Document):
    type: AgentResponseType
    content: str | list[Tool]
