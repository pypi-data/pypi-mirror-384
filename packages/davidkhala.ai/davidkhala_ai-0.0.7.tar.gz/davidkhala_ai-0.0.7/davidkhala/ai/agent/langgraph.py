from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent


class Agent:

    def __init__(self, model, instruction, *tools):
        self.agent = create_react_agent(
            model=model,
            tools=tools,
            prompt=instruction
        )

    def invoke(self, content):
        return self.agent.invoke({"messages": [{"role": "user", "content": content}]})['messages'][-1]


class OpenRouterModel:
    def __init__(self, api_key, leaderboard: dict = None):
        self.api_key = api_key

        if leaderboard:
            self.headers = {
                "HTTP-Referer": leaderboard['url'],
                "X-Title": leaderboard['name'],
            }

    def init_chat_model(self, model):
        """https://openrouter.ai/docs/community/lang-chain"""
        return ChatOpenAI(
            base_url='https://openrouter.ai/api/v1',
            model=model,
            api_key=self.api_key,
            default_headers=getattr(self, "headers", None)
        )
