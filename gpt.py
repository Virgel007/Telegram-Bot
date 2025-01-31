import httpx
import logging
from openai import OpenAI

LOGGER = logging.getLogger(__name__)


class ChatGptService:

    def __init__(self, token: str):
        token = "sk-proj-" + token[:3:-1] if token.startswith('gpt:') else token
        self.client = OpenAI(
            http_client=httpx.Client(proxy="http://18.199.183.77:49232"),
            api_key=token)
        self._message_list = []

    async def send_message_list(self) -> str:
        try:
            completion = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=self._message_list,
                max_tokens=3000,
                temperature=0.9)
            message = completion.choices[0].message
            self._message_list.append(message)
            return message.content
        except Exception as e:
            LOGGER.error("Error sending message list: %s", e)

    def set_prompt(self, prompt_text: str) -> None:
        self._message_list.clear()
        self._message_list.append({"role": "system", "content": prompt_text})

    async def add_message(self, message_text: str) -> str:
        self._message_list.append({"role": "user", "content": message_text})
        return await self.send_message_list()

    async def send_question(self, prompt_text: str, topic: str) -> str:
        self.set_prompt(prompt_text)
        if topic == "quiz_more":
            # Continue the dialog with the previous topic
            return await self.send_message_list()
        else:
            # Start a new dialog with the specified topic
            self._message_list.append({"role": "user", "content": f"{topic}?"})
            return await self.send_message_list()
