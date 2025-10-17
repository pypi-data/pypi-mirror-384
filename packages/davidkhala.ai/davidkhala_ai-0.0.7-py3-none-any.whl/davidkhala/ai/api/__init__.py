import datetime
from abc import abstractmethod

from davidkhala.utils.http_request import Request

from davidkhala.ai.model import AbstractClient


class API(AbstractClient):
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url + '/v1'
        self._ = Request({"bearer": api_key})

    @property
    @abstractmethod
    def free_models(self) -> list[str]:
        ...

    def chat(self, *user_prompt: str, **kwargs):
        messages = [
            *self.messages,
            *[{
                "role": "user",
                "content": _
            } for _ in user_prompt],
        ]

        json = {
            "messages": messages,
            **kwargs,
        }

        response = self._.request(f"{self.base_url}/chat/completions", "POST", json=json)

        return {
            "data": list(map(lambda x: x['message']['content'], response['choices'])),
            "meta": {
                "usage": response['usage'],
                "created": datetime.datetime.fromtimestamp(response['created'])
            },
            'model': response['model'],
        }

    def list_models(self):
        response = self._.request(f"{self.base_url}/models", "GET")
        return response['data']
