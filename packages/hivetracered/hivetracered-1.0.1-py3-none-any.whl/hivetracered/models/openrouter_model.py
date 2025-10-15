from typing import List, Any, Optional, Union, Dict
from hivetracered.models.openai_model import OpenAIModel
from langchain_openai import ChatOpenAI
from hivetracered.models.langchain_model import LangchainModel
from dotenv import load_dotenv
import os
from typing import AsyncGenerator
import asyncio
from tqdm import tqdm

from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_core.runnables import RunnableLambda

load_dotenv(override=True)

class OpenRouterModel(LangchainModel):
    """
    OpenAI language model implementation using the LangChain integration.
    Provides a standardized interface to OpenAI's API with rate limiting support and 
    both synchronous and asynchronous processing capabilities.
    """
    
    def __init__(self, model: str = "nvidia/nemotron-nano-9b-v2", base_url = "https://openrouter.ai/api/v1", batch_size: int = 1, rpm: int = 300, api_key: str = None, max_retries: int = 3, **kwargs):

        """
        Initialize the OpenAI model client with the specified configuration.

        Args:
            model: OpenAI model identifier (e.g., "nvidia/nemotron-nano-9b-v2")
            base_url: OpenRouter API base URL
            batch_size: Number of requests to process in parallel
            rpm: Rate limit in requests per minute
            api_key: API key; defaults to OPENROUTER_API_KEY env var
            max_retries: Maximum number of retry attempts on transient errors (default: 3)
            **kwargs: Additional parameters to pass to the ChatOpenAI constructor
        """
        load_dotenv(override=True)

        # Get API key from environment if not provided
        if api_key is None:
            api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = base_url
        self.model_name = model
        self.max_retries = max_retries

        self.kwargs = kwargs or {}

        if not "temperature" in self.kwargs:
            self.kwargs["temperature"] = 0.000001

        self.batch_size = batch_size
        rate_limiter = InMemoryRateLimiter(
            requests_per_second=rpm / 60,
            check_every_n_seconds=0.1,
        )
        self.client = ChatOpenAI(model=model, rate_limiter=rate_limiter, base_url=base_url, openai_api_key=api_key, **self.kwargs)
        self.client = self._add_retry_policy(self.client)
    