import runpy
from typing import Union, Literal, List

from openai import OpenAI, AsyncOpenAI

from davidkhala.ai.model import AbstractClient


class Client(AbstractClient):
    client: OpenAI
    encoding_format: Literal["float", "base64"] = "float"
    n = 1

    def connect(self):
        self.client.models.list()

    def encode(self, *_input: str) -> List[List[float]]:
        response = self.client.embeddings.create(
            model=self.model,
            input=list(_input),
            encoding_format=self.encoding_format
        )
        return [item.embedding for item in response.data]

    def chat(self, *user_prompt):

        messages = [
            *self.messages,
        ]
        for prompt in user_prompt:
            message = {
                "role": "user"
            }
            if type(prompt) == str:
                message['content'] = prompt
            elif type(prompt) == dict:
                message['content'] = [
                    {"type": "text", "text": prompt['text']},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": prompt['image_url'],
                        }
                    },
                ]
            messages.append(message)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            n=self.n
        )
        contents = [choice.message.content for choice in response.choices]
        assert len(contents) == self.n
        return contents

    def disconnect(self):
        self.client.close()


def with_opik(instance: Union[OpenAI, AsyncOpenAI]):
    from opik.integrations.openai import track_openai
    runpy.run_path('../opik.py')
    return track_openai(instance)
