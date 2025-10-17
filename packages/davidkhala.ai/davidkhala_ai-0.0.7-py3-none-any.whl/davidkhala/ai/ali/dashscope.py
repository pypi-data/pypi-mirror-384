from enum import Enum
from http import HTTPStatus
from typing import List

from dashscope import Generation, TextEmbedding
from dashscope.api_entities.dashscope_response import DashScopeAPIResponse

from davidkhala.ai.model import AbstractClient


class ModelEnum(str, Enum):
    BAILIAN = Generation.Models.bailian_v1
    DOLLY = Generation.Models.dolly_12b_v2
    TURBO = Generation.Models.qwen_turbo
    PLUS = Generation.Models.qwen_plus
    MAX = Generation.Models.qwen_max
    EMBED = TextEmbedding.Models.text_embedding_v4


class API(AbstractClient):
    """
    Unsupported to use international base_url "https://dashscope-intl.aliyuncs.com"
    """

    model: ModelEnum

    def __init__(self, api_key):
        self.api_key = api_key

    def as_embeddings(self, model=ModelEnum.EMBED):
        super().as_embeddings(model)

    @staticmethod
    def _on_response(response:DashScopeAPIResponse):
        if response.status_code == HTTPStatus.OK:
            return response.output
        else:
            raise Exception(response)


    def chat(self, user_prompt: str, **kwargs):

        if not self.messages:
            kwargs['prompt'] = user_prompt
        else:
            kwargs['messages'] = [
                *self.messages,
                {
                    "role": "user",
                    'content': user_prompt
                }
            ]
        # prompt 和 messages 是互斥的参数：如果你使用了 messages，就不要再传 prompt
        r = Generation.call(
            self.model,
            api_key=self.api_key,
            **kwargs
        )
        return API._on_response(r)

    def encode(self, *_input: str)-> List[List[float]]:
        r= TextEmbedding.call(
            self.model,list(_input),
            api_key= self.api_key,
        )
        r = API._on_response(r)

        return [item['embedding'] for item in r['embeddings']]