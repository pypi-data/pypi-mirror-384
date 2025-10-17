from openai import OpenAI

from davidkhala.ai.openai import Client


class NativeClient(Client):
    def __init__(self, api_key, base_url=None):
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

