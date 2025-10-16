from typing import Literal, Dict

from cheshirecat_python_sdk.endpoints.base import AbstractEndpoint
from cheshirecat_python_sdk.models.api.conversations import ConversationHistoryOutput, ConversationHistoryDeleteOutput
from cheshirecat_python_sdk.models.dtos import Why
from cheshirecat_python_sdk.utils import deserialize


class ConversationEndpoint(AbstractEndpoint):
    def __init__(self, client: "CheshireCatClient"):
        super().__init__(client)
        self.prefix = "/conversation"

    def get_conversation_history(self, agent_id: str, user_id: str, chat_id: str) -> ConversationHistoryOutput:
        """
        This endpoint returns the conversation history.
        :param agent_id: The agent ID.
        :param user_id: The user ID to filter the conversation history.
        :param chat_id: The chat ID to filter the conversation history.
        :return: ConversationHistoryOutput, a list of conversation history entries.
        """
        return self.get(
            self.format_url(chat_id),
            agent_id,
            user_id=user_id,
            output_class=ConversationHistoryOutput,
        )

    def get_conversation_histories(self, agent_id: str, user_id: str) -> Dict[str, ConversationHistoryOutput]:
        """
        This endpoint returns the conversation histories.
        :param agent_id: The agent ID.
        :param user_id: The user ID to filter the conversation history.
        :return: ConversationHistoryOutput, a list of conversation history entries.
        """
        response = self.get_http_client(agent_id, user_id).get(self.prefix)
        response.raise_for_status()

        result = {}
        for key, item in response.json():
            result[key] = deserialize(item, ConversationHistoryOutput)
        return result

    def delete_conversation_history(self, agent_id: str, user_id: str, chat_id: str) -> ConversationHistoryDeleteOutput:
        """
        This endpoint deletes the conversation history.
        :param agent_id: The agent ID.
        :param user_id: The user ID to filter the conversation history.
        :param chat_id: The chat ID to filter the conversation history.
        :return: ConversationHistoryDeleteOutput, a message indicating the number of conversation history entries deleted.
        """
        return self.delete(
            self.format_url(chat_id),
            agent_id,
            output_class=ConversationHistoryDeleteOutput,
            user_id=user_id,
        )

    def post_conversation_history(
        self,
        who: Literal["user", "assistant"],
        text: str,
        agent_id: str,
        user_id: str,
        chat_id: str,
        image: str | bytes | None = None,
        why: Why | None = None,
    ) -> ConversationHistoryOutput:
        """
        This endpoint creates a new element in the conversation history.
        :param who: The role of the user in the conversation.
        :param text: The text of the conversation history entry.
        :param agent_id: The agent ID.
        :param user_id: The user ID to filter the conversation history.
        :param chat_id: The chat ID to filter the conversation history.
        :param image: The image of the conversation history entry.
        :param why: The reason for the conversation history entry.
        :return: ConversationHistoryOutput, the conversation history entry created.
        """
        payload = {
            "who": who,
            "text": text,
        }
        if image:
            payload["image"] = image
        if why:
            payload["why"] = why.model_dump()

        return self.post_json(
            self.format_url(chat_id),
            agent_id,
            output_class=ConversationHistoryOutput,
            payload=payload,
            user_id=user_id,
        )
