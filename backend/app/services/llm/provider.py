"""
LLM provider factory for different model providers
"""
from typing import AsyncIterator, Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.config import settings
from app.core.model_registry import ModelRegistry
from app.models.user_keys import UserAPIKeys


class LLMProvider:
    """Factory for creating LLM instances based on provider"""

    @staticmethod
    def create_llm(
        model_id: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        streaming: bool = True,
        user_keys: Optional[UserAPIKeys] = None
    ) -> BaseChatModel:
        """
        Create LLM instance based on model ID

        Args:
            model_id: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            streaming: Enable streaming
            user_keys: Optional user-provided API keys (priority over server keys)

        Returns:
            Configured LLM instance
        """

        if not ModelRegistry.is_model_available(model_id, user_keys):
            raise ValueError(f"Model {model_id} is not available. Check API key.")

        provider = ModelRegistry.get_provider(model_id)
        env_key = ModelRegistry.get_env_key(model_id)

        # Get API key with user keys taking priority
        api_key = ModelRegistry._get_api_key(env_key, user_keys)

        if provider == "OpenAI":
            return ChatOpenAI(
                model=model_id,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=streaming,
                api_key=api_key
            )

        elif provider == "Anthropic":
            return ChatAnthropic(
                model=model_id,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=streaming,
                api_key=api_key
            )

        elif provider == "Google":
            return ChatGoogleGenerativeAI(
                model=model_id,
                temperature=temperature,
                max_output_tokens=max_tokens,
                streaming=streaming,
                google_api_key=api_key
            )

        elif provider == "HuggingFace":
            # HuggingFace uses endpoint wrapped in ChatHuggingFace for chat support
            llm = HuggingFaceEndpoint(
                repo_id=model_id,
                temperature=temperature,
                max_new_tokens=max_tokens,
                huggingfacehub_api_token=api_key,
            )
            # Wrap in ChatHuggingFace to properly handle chat messages
            return ChatHuggingFace(llm=llm)

        else:
            raise ValueError(f"Unknown provider: {provider}")

    @staticmethod
    async def stream_llm_response(
        llm: BaseChatModel,
        messages: list,
    ) -> AsyncIterator[str]:
        """Stream LLM response"""
        async for chunk in llm.astream(messages):
            if hasattr(chunk, 'content'):
                yield chunk.content
            else:
                yield str(chunk)

    @staticmethod
    def format_messages(messages: list) -> list:
        """Convert message dicts to LangChain message objects"""
        lc_messages = []

        for msg in messages:
            role = msg.get("role") if isinstance(msg, dict) else msg.role
            content = msg.get("content") if isinstance(msg, dict) else msg.content

            if role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            elif role == "system":
                lc_messages.append(SystemMessage(content=content))

        return lc_messages
