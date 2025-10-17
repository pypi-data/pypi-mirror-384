from abc import ABC
from typing import Optional, List


class AbstractClient(ABC):
    api_key: str
    base_url: str
    model: Optional[str]
    messages = []

    def as_chat(self, model: str, sys_prompt: str = None):
        self.model = model
        if sys_prompt is not None:
            self.messages = [{"role": "system", "content": sys_prompt}]

    def as_embeddings(self, model: str):
        self.model = model

    def chat(self, *user_prompt, **kwargs):
        ...

    def encode(self, *_input: str) -> List[List[float]]:
        ...
    def connect(self):
        ...

    def disconnect(self):
        ...
