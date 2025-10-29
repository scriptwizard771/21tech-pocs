from enum import Enum
from langchain_openai import ChatOpenAI

# Optional import for Ollama - only needed if using Ollama models
try:
    from langchain_ollama import ChatOllama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    ChatOllama = None


class LLMsEnum(Enum):
    """Enum class for LLM names."""

    GEMMA = "gemma"
    LLAMA3 = "llama3"
    GPT4O = "gpt-4o"
    GPT4O_MINI = "gpt-4o-mini"
    DEEP_SEEK_CLOUD = "deep-seek-cloud"
    TGI = "tgi"

    @classmethod
    def validate_llm(cls, llm_name: str):
        """Validates if the provided LLM name is in the enum."""
        if llm_name not in cls._value2member_map_:
            raise ValueError(f"Invalid LLM name: {llm_name}")
        return True


class LLMFactory:
    """Factory class to create LLM instances dynamically."""

    _llms_mapping = {
        LLMsEnum.GEMMA.value: "_create_ollama_llm",
        LLMsEnum.LLAMA3.value: "_create_ollama_llm",
        LLMsEnum.GPT4O.value: "_create_gpt_llm",
        LLMsEnum.GPT4O_MINI.value: "_create_gpt_llm",
        LLMsEnum.DEEP_SEEK_CLOUD.value: "_create_gpt_llm",
        LLMsEnum.TGI.value: "_create_gpt_llm",
    }

    def get_llm(
        self,
        llm_name: str,
        temperature: float = 0.1,
        max_tokens: int = None,
        timeout: int = 60,
        max_retries: int = 5,
        **kwargs,
    ):
        """Creates an LLM instance based on the provided name and parameters."""
        LLMsEnum.validate_llm(llm_name)  # Ensures the LLM name is valid

        llm_creator = getattr(self, self._llms_mapping[llm_name])
        return llm_creator(
            llm_name=llm_name,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            max_retries=max_retries,
            **kwargs,
        )

    @staticmethod
    def _create_ollama_llm(
        llm_name: str,
        temperature: float,
        max_tokens: int,
        timeout: int,
        max_retries: int,
        **kwargs,
    ):
        if not OLLAMA_AVAILABLE:
            raise ImportError(
                f"langchain_ollama is not installed. Please install it to use {llm_name} models: "
                "pip install langchain-ollama"
            )
        return ChatOllama(
            model=llm_name,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            max_retries=max_retries,
            **kwargs,
        )

    @staticmethod
    def _create_gpt_llm(
        llm_name: str,
        temperature: float,
        max_tokens: int,
        timeout: int,
        max_retries: int,
        **kwargs,
    ):
        return ChatOpenAI(
            model=llm_name,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            max_retries=max_retries,
            **kwargs,
        )
