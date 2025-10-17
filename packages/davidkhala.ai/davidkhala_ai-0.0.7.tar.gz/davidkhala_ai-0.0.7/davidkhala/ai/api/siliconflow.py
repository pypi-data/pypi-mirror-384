from davidkhala.ai.api import API


class SiliconFlow(API):
    @property
    def free_models(self) -> list[str]:
        """
        Cannot be lively fetched by list_models
        """
        return [
            # chat section
            'THUDM/GLM-4.1V-9B-Thinking'
            'THUDM/GLM-Z1-9B-0414'
            'THUDM/GLM-4-9B-0414'
            'THUDM/glm-4-9b-chat'
            'Qwen/Qwen3-8B'
            'Qwen/Qwen2.5-7B-Instruct'
            'Qwen/Qwen2.5-Coder-7B-Instruct'
            'internlm/internlm2_5-7b-chat'
            'deepseek-ai/DeepSeek-R1-0528-Qwen3-8B',
            'deepseek-ai/DeepSeek-R1-Distill-Qwen-7B',
            # embedding and reranker
            'BAAI/bge-m3'
            'BAAI/bge-reranker-v2-m3'
            'BAAI/bge-large-zh-v1.5'
            'BAAI/bge-large-en-v1.5'
            'netease-youdao/bce-reranker-base_v1'
            'netease-youdao/bce-embedding-base_v1'
            # Audio
            'FunAudioLLM/SenseVoiceSmall'
            # image
            'Kwai-Kolors/Kolors'
        ]

    def __init__(self, api_key: str):
        super().__init__(api_key, 'https://api.siliconflow.cn')
        self._.options['timeout'] = 50
    def chat(self, *user_prompt: str, **kwargs):
        kwargs['model'] = self.model
        return super().chat(*user_prompt, **kwargs)