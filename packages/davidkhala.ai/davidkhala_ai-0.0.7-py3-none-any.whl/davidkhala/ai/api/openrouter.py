import time

import requests
from davidkhala.utils.http_request import default_on_response
from requests import Response

from davidkhala.ai.api import API


class OpenRouter(API):
    @property
    def free_models(self) -> list[str]:
        return list(
            map(lambda model: model['id'],
                filter(lambda model: model['id'].endswith(':free'), self.list_models())
                )
        )

    @staticmethod
    def on_response(response: requests.Response):
        r = default_on_response(response)
        # openrouter special error on response.ok
        err = r.get('error')
        if err:
            derived_response = Response()
            derived_response.status_code = err['code']
            derived_response.reason = err['message']
            derived_response.metadata = err.get("metadata")

            derived_response.raise_for_status()
        return r

    def __init__(self, api_key: str, *models: str, **kwargs):

        super().__init__(api_key, 'https://openrouter.ai/api')

        if 'leaderboard' in kwargs and type(kwargs['leaderboard']) is dict:
            self._.options["headers"]["HTTP-Referer"] = kwargs['leaderboard'][
                'url']  # Site URL for rankings on openrouter.ai.
            self._.options["headers"]["X-Title"] = kwargs['leaderboard'][
                'name']  # Site title for rankings on openrouter.ai.
        self.models = models

        self._.on_response = OpenRouter.on_response

    def chat(self, *user_prompt: str, **kwargs):
        if self.models:
            kwargs["models"] = self.models
        else:
            kwargs["model"] = self.model

        try:
            r = super().chat(*user_prompt, **kwargs)
        except requests.HTTPError as e:
            if e.response.status_code == 429 and kwargs.get('retry'):
                time.sleep(1)
                return self.chat(*user_prompt, **kwargs)
            else: raise
        if self.models:
            assert r['model'] in self.models
        return r
