"""
LLM client implementations for the memory module.
"""
import json
import os
from dotenv import load_dotenv
from groq import Groq
from .logging_config import llm_logger, logger

class GroqLLMClient:
    """Real LLM client using Groq API."""
    def __init__(self, api_key: str = None, model: str = "openai/gpt-oss-20b", temperature: float = 0.7, max_tokens: int = 1024):
        load_dotenv()
        if api_key is None:
            api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found.")
        self.client = Groq(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def complete(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant providing concise JSON outputs."},
                {"role": "user", "content": prompt}
            ],
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content

    def chat_complete(self, messages: list, system_prompt: str = None) -> str:
        """Complete a chat conversation with proper message history"""
        chat_messages = []
        
        # Add system prompt if provided
        if system_prompt:
            chat_messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation messages
        chat_messages.extend(messages)
        
        response = self.client.chat.completions.create(
            messages=chat_messages,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content

    def stream_chat(self, messages: list, system_prompt: str = None):
        """Stream chat responses for real-time conversation"""
        chat_messages = []
        
        # Add system prompt if provided
        if system_prompt:
            chat_messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation messages
        chat_messages.extend(messages)
        
        stream = self.client.chat.completions.create(
            messages=chat_messages,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    def consolidate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a memory consolidation assistant providing concise JSON outputs."},
                {"role": "user", "content": prompt}
            ],
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        logger.info("LLM response received")
        logger.debug("LLM response preview: %s", response.choices[0].message.content)
        return response.choices[0].message.content

class MockLLMClient:
    """Mock LLM client for testing"""
    
    def __init__(self):
        self.call_count = 0
        llm_logger.info("MockLLMClient initialized")
    
    def complete(self, prompt: str) -> str:
        self.call_count += 1
        llm_logger.debug(f"MockLLM.complete() call #{self.call_count}")
        
        # Simulate different responses based on content
        if "Python" in prompt or "async" in prompt:
            tags = ["python", "async_programming", "learning", "concurrency"]
            collection = "learning_notes"
            summary = "Discussion about Python async/await patterns and coroutines."
            sentiment = "neutral"
            topics = ["python", "async", "programming"]
        elif "SQL" in prompt or "database" in prompt:
            tags = ["sql", "database", "query", "learning", "joins"]
            collection = "learning_notes"
            summary = "Explanation of SQL JOIN operations and query optimization."
            sentiment = "neutral"
            topics = ["sql", "database", "queries"]
        elif "?" in prompt:
            tags = ["question", "conversation", "help"]
            collection = "conversations"
            summary = "User asking a question."
            sentiment = "neutral"
            topics = ["question"]
        else:
            tags = ["general", "conversation", "chat"]
            collection = "conversations"
            summary = "General conversation exchange."
            sentiment = "neutral"
            topics = ["general"]
        
        response = {
            "tags": tags,
            "collection": collection,
            "metadata": {
                "key_entities": [],
                "sentiment": sentiment,
                "topics": topics
            },
            "importance": 0.6,
            "chunk_type": "chat",
            "summary": summary
        }
        
        llm_logger.debug(f"Generated response: {json.dumps(response, indent=2)}")
        return json.dumps(response)

    def chat_complete(self, messages: list, system_prompt: str = None) -> str:
        """Complete a chat conversation with proper message history"""
        self.call_count += 1
        llm_logger.debug(f"MockLLM.chat_complete() call #{self.call_count}")
        
        # Get the last user message for context
        last_user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_message = msg.get("content", "")
                break
        
        # Generate contextual responses based on conversation
        if "Python" in last_user_message or "async" in last_user_message:
            return "Python async/await is a powerful feature for handling asynchronous operations. It allows you to write concurrent code that can handle I/O operations efficiently without blocking the main thread. The `async` keyword defines a coroutine function, while `await` is used to wait for the result of an async operation."
        elif "SQL" in last_user_message or "database" in last_user_message:
            return "SQL JOINs are used to combine rows from two or more tables based on related columns. The most common types are INNER JOIN (returns matching records), LEFT JOIN (returns all records from left table), RIGHT JOIN (returns all records from right table), and FULL OUTER JOIN (returns all records when there's a match in either table)."
        elif "?" in last_user_message:
            return "I'd be happy to help you with that! Could you provide more details about what you'd like to know?"
        else:
            return "That's an interesting topic! I'm here to help you explore it further. What specific aspect would you like to discuss?"

    def stream_chat(self, messages: list, system_prompt: str = None):
        """Stream chat responses for real-time conversation"""
        self.call_count += 1
        llm_logger.debug(f"MockLLM.stream_chat() call #{self.call_count}")
        
        # Get the last user message for context
        last_user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_message = msg.get("content", "")
                break
        
        # Generate contextual responses based on conversation
        if "Python" in last_user_message or "async" in last_user_message:
            response_text = "Python async/await is a powerful feature for handling asynchronous operations. It allows you to write concurrent code that can handle I/O operations efficiently without blocking the main thread. The `async` keyword defines a coroutine function, while `await` is used to wait for the result of an async operation."
        elif "SQL" in last_user_message or "database" in last_user_message:
            response_text = "SQL JOINs are used to combine rows from two or more tables based on related columns. The most common types are INNER JOIN (returns matching records), LEFT JOIN (returns all records from left table), RIGHT JOIN (returns all records from right table), and FULL OUTER JOIN (returns all records when there's a match in either table)."
        elif "?" in last_user_message:
            response_text = "I'd be happy to help you with that! Could you provide more details about what you'd like to know?"
        else:
            response_text = "That's an interesting topic! I'm here to help you explore it further. What specific aspect would you like to discuss?"
        
        # Simulate streaming by yielding words
        words = response_text.split()
        for i, word in enumerate(words):
            if i == 0:
                yield word
            else:
                yield " " + word
    
    def consolidate(self, prompt: str) -> str:
        self.call_count += 1
        llm_logger.debug(f"MockLLM.consolidate() call #{self.call_count}")
        
        response = {
            "should_consolidate": True,
            "consolidated_summary": "Consolidated summary combining multiple related memory chunks about Python async programming concepts.",
            "tags": ["consolidated", "python", "async", "learning"],
            "importance": 0.85,
            "metadata": {
                "consolidation_prompt_length": len(prompt),
                "consolidation_reason": "Related Python async programming discussions"
            }
        }
        
        llm_logger.debug(f"Generated consolidation response")
        return json.dumps(response)
