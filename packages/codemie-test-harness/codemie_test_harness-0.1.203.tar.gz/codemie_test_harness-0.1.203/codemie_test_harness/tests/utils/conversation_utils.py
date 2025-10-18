import requests

from codemie_test_harness.tests.utils.base_utils import BaseUtils


class ConversationUtils(BaseUtils):
    def list_conversations(self):
        return self.client.conversations.list()

    def get_conversation_by_assistant_id(self, assistant_id: str):
        return self.client.conversations.list_by_assistant_id(assistant_id)

    def get_conversation_by_id(self, conversation_id: str) -> requests.Response:
        return self.client.conversations.get_conversation(conversation_id)

    def delete_conversation(self, conversation_id: str) -> requests.Response:
        return self.client.conversations.delete(conversation_id)
