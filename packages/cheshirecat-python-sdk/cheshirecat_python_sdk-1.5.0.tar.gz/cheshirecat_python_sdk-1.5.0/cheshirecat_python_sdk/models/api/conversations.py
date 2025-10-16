from typing import List
from pydantic import BaseModel

from cheshirecat_python_sdk.models.api.nested.memories import ConversationHistoryItem


class ConversationHistoryDeleteOutput(BaseModel):
    deleted: bool


class ConversationHistoryOutput(BaseModel):
    history: List[ConversationHistoryItem]
