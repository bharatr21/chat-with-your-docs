"""
LLM provider factory for different model providers
"""

from collections.abc import AsyncIterator

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_openai import ChatOpenAI

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
        user_keys: UserAPIKeys | None = None,
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
        api_key = ModelRegistry._get_api_key(env_key, user_keys)

        # Provider factory with common parameters
        common_params = {
            "temperature": temperature,
            "streaming": streaming,
        }

        provider_factories = {
            "OpenAI": lambda: ChatOpenAI(
                model=model_id, max_tokens=max_tokens, api_key=api_key, **common_params
            ),
            "Anthropic": lambda: ChatAnthropic(
                model=model_id, max_tokens=max_tokens, api_key=api_key, **common_params
            ),
            "Google": lambda: ChatGoogleGenerativeAI(
                model=model_id,
                max_output_tokens=max_tokens,
                google_api_key=api_key,
                **common_params,
            ),
            "HuggingFace": lambda: ChatHuggingFace(
                llm=HuggingFaceEndpoint(
                    repo_id=model_id,
                    temperature=temperature,
                    max_new_tokens=max_tokens,
                    huggingfacehub_api_token=api_key,
                )
            ),
        }

        if provider not in provider_factories:
            raise ValueError(f"Unknown provider: {provider}")

        return provider_factories[provider]()

    @staticmethod
    async def stream_llm_response(
        llm: BaseChatModel,
        messages: list,
    ) -> AsyncIterator[str]:
        """Stream LLM response"""
        async for chunk in llm.astream(messages):
            if hasattr(chunk, "content"):
                if chunk.content is not None:
                    yield chunk.content
            else:
                yield str(chunk)

    @staticmethod
    def format_messages(messages: list) -> list:
        """Convert message dicts to LangChain message objects."""
        role_to_message_class = {
            "user": HumanMessage,
            "assistant": AIMessage,
            "system": SystemMessage,
        }

        lc_messages = []
        for msg in messages:
            role = msg.get("role") if isinstance(msg, dict) else msg.role
            content = msg.get("content") if isinstance(msg, dict) else msg.content

            message_class = role_to_message_class.get(role)
            if message_class:
                lc_messages.append(message_class(content=content))

        return lc_messages
