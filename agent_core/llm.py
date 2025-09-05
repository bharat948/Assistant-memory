from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI

class LLM:
    def __init__(self, model: str, temperature: float = 0.7, max_tokens: int = 4000, tools: Optional[List[Dict[str, Any]]] = None, system_instruction: Optional[str] = None):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.tools = tools
        self.system_instruction = system_instruction
        self.client = AsyncOpenAI()

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        processed_messages = []
        if self.system_instruction:
            processed_messages.append({"role": "system", "content": self.system_instruction})

        for message in messages:
            if 'content' in message and message['content'] is None:
                message['content'] = ""
            processed_messages.append(message)

        chat_completion_args = {
            "model": self.model,
            "messages": processed_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

        if self.tools:
            chat_completion_args["tools"] = self.tools

        response = await self.client.chat.completions.create(**chat_completion_args)
        print("LLM Response:", response)
        return response.choices[0].message.content or ""
