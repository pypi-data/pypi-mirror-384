import os
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel

from rhesis.sdk.client import Client
from rhesis.sdk.models.base import BaseLLM

DEFAULT_MODEL_NAME = "rhesis-llm-v1"
API_ENDPOINT = "services/generate/content"


class RhesisLLM(BaseLLM):
    """Service for interacting with the LLM API endpoints."""

    def __init__(
        self, model_name: str = DEFAULT_MODEL_NAME, api_key=None, base_url=None, **kwargs
    ) -> None:
        """
        RhesisLLMService: Rhesis LLM Provider

        This class provides an interface to the Rhesis family of large language models via
        the Rhesis API.

        Args:
            model_name (str): The name of the Rhesis model to use (default: "rhesis-llm-v1").
            api_key (str, optional): API key for Rhesis. If not provided, will use RHESIS_API_KEY
                from environment.
            base_url (str, optional): Base URL for the Rhesis API. If not provided, will use
            RHESIS_BASE_URL from environment.
            **kwargs: Additional parameters passed to the underlying client.

        Usage:
            >>> llm = RhesisLLM(model_name="rhesis-llm-v1")
            >>> result = llm.generate("Tell me a joke.")
            >>> print(result)

        If a Pydantic schema is provided to `generate`, the response will be validated and returned
        as a dict.

        Raises:
            ValueError: If the API key is not set.
        """
        self.api_key = api_key or os.getenv("RHESIS_API_KEY")
        self.base_url = base_url or os.getenv("RHESIS_BASE_URL")

        if self.api_key is None:
            raise ValueError("RHESIS_API_KEY is not set")

        super().__init__(model_name, **kwargs)

    def load_model(self) -> Any:
        self.client = Client(api_key=self.api_key, base_url=self.base_url)
        self.headers = {
            "Authorization": f"Bearer {self.client.api_key}",
            "Content-Type": "application/json",
        }
        return self

    def generate(self, prompt: str, schema: Optional[BaseModel] = None, **kwargs: Any) -> Any:
        """Run a chat completion using the API, and return the response."""
        try:
            # Before sending the request, we need to convert the Pydantic schema to a JSON schema
            if schema:
                schema = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema.__name__,
                        "schema": schema.model_json_schema(),
                        "strict": True,
                    },
                }

            response = self.create_completion(
                prompt=prompt,
                schema=schema,
                **kwargs,
            )

            return response

        except (requests.exceptions.HTTPError, KeyError, IndexError) as e:
            # Log the error and return an appropriate message
            print(f"Error occurred while running the prompt: {e}")
            if schema:
                return {"error": "An error occurred while processing the request."}

            return "An error occurred while processing the request."

    def create_completion(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        schema: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Create a chat completion using the API.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate (increased default for larger responses)
            **kwargs: Additional parameters to pass to the API

        Returns:
            Dict[str, Any]: The raw response from the API

        Raises:
            requests.exceptions.HTTPError: If the API request fails
            ValueError: If the response cannot be parsed
        """
        request_data = {
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "schema": schema,
            **kwargs,
        }

        response = requests.post(
            self.client.get_url(API_ENDPOINT),
            headers=self.headers,
            json=request_data,
        )

        response.raise_for_status()
        result: Dict[str, Any] = response.json()
        return result
