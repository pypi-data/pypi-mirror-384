import warnings

from openai import AzureOpenAI, OpenAI

from davidkhala.ai.openai import Client


class ModelDeploymentClient(Client):
    def __init__(self, key, deployment):
        self.client = AzureOpenAI(
            api_version="2024-12-01-preview",  # mandatory
            azure_endpoint=f"https://{deployment}.cognitiveservices.azure.com/",
            api_key=key,
        )


@warnings.deprecated("Azure Open AI is deprecated. Please migrate to Azure AI Foundry")
class OpenAIClient(Client):

    def __init__(self, api_key, project):
        self.client = OpenAI(
            base_url=f"https://{project}.openai.azure.com/openai/v1/",
            api_key=api_key,
        )

    def as_chat(self, model="gpt-oss-120b", sys_prompt: str = None):
        super().as_chat(model, sys_prompt)
