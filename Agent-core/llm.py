# app/core/llm.py
from typing import List, Dict, Any,Optional
from openai import AsyncOpenAI

class LLM:
    def __init__(self, model: str, temperature: float = 0.7, max_tokens: int = 4000, tools: Optional[List[Dict[str, Any]]] = None, system_instruction: Optional[str] = None):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.tools = tools
        self.system_instruction = system_instruction

        # Initialize OpenAI client (reads OPENAI_API_KEY from env)
        self.client = AsyncOpenAI()

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        messages: [{"role": "system"|"user"|"assistant", "content": "..."}]
        """
        # Ensure all message content is a string, handling potential None values
        processed_messages = []
        if self.system_instruction:
            processed_messages.append({"role": "system", "content": self.system_instruction})

        for message in messages:
            if 'content' in message and message['content'] is None:
                message['content'] = ""  # Replace None with an empty string
            processed_messages.append(message)

        # Prepare arguments for chat completion
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
        # OpenAI's message.content can be None if the model chooses to output a tool_call or function_call
        # In such cases, we should return an empty string or handle it appropriately.
        # For this fix, we'll return an empty string if content is None.
        return response.choices[0].message.content or ""
