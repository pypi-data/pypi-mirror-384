"""Responses API - AI model response generation"""

from typing import Any, Dict, Iterator, List, Optional
import httpx
from .models import ModelResponse
from ._base_client import _raise_for_status


class ResponsesAPI:
    """Sync Responses API client"""

    def __init__(self, client: httpx.Client):
        self._client = client

    def create(
        self,
        model: str,
        inputs: List[Dict[str, Any]],
        stream: bool = False,
        organization_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        assistant_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """
        Create a model response

        Args:
            model: Model identifier (e.g., "gpt-4.1", "claude-3-5-sonnet")
            inputs: List of input messages
            stream: Whether to stream the response
            organization_id: Organization ID for billing
            thread_id: Thread ID to maintain conversation context
            assistant_id: Assistant ID to load preset configuration
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            tools: List of tools/functions the model can call
            response_format: Output format specification (e.g., {"type": "json_object"})
            **kwargs: Additional request parameters

        Returns:
            ModelResponse object with the AI's response

        Example:
            >>> client = FreddyClient(api_key="...")
            >>> response = client.responses.create(
            ...     model="gpt-4.1",
            ...     inputs=[{"role": "user", "texts": [{"text": "Hello!"}]}]
            ... )
            >>> print(response.output[0].content[0].text)
        """
        if stream:
            raise NotImplementedError("Streaming is not yet supported in sync client")

        payload: Dict[str, Any] = {
            "model": model,
            "inputs": inputs,
            "stream": stream,
            **kwargs,
        }

        if organization_id:
            payload["organizationId"] = organization_id
        if thread_id:
            payload["threadId"] = thread_id
        if assistant_id:
            payload["assistantId"] = assistant_id
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["maxTokens"] = max_tokens
        if tools:
            payload["tools"] = tools
        if response_format:
            payload["responseFormat"] = response_format

        response = self._client.post("/v1/model/response", json=payload)
        _raise_for_status(response)
        return ModelResponse(**response.json())


class AsyncResponsesAPI:
    """Async Responses API client"""

    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def create(
        self,
        model: str,
        inputs: List[Dict[str, Any]],
        stream: bool = False,
        organization_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        assistant_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """
        Create a model response (async)

        Args:
            model: Model identifier (e.g., "gpt-4.1", "claude-3-5-sonnet")
            inputs: List of input messages
            stream: Whether to stream the response
            organization_id: Organization ID for billing
            thread_id: Thread ID to maintain conversation context
            assistant_id: Assistant ID to load preset configuration
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            tools: List of tools/functions the model can call
            response_format: Output format specification
            **kwargs: Additional request parameters

        Returns:
            ModelResponse object with the AI's response

        Example:
            >>> async with AsyncFreddyClient(api_key="...") as client:
            ...     response = await client.responses.create(
            ...         model="gpt-4.1",
            ...         inputs=[{"role": "user", "texts": [{"text": "Hello!"}]}]
            ...     )
            ...     print(response.output[0].content[0].text)
        """
        if stream:
            raise NotImplementedError("Streaming is not yet supported in async client")

        payload: Dict[str, Any] = {
            "model": model,
            "inputs": inputs,
            "stream": stream,
            **kwargs,
        }

        if organization_id:
            payload["organizationId"] = organization_id
        if thread_id:
            payload["threadId"] = thread_id
        if assistant_id:
            payload["assistantId"] = assistant_id
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["maxTokens"] = max_tokens
        if tools:
            payload["tools"] = tools
        if response_format:
            payload["responseFormat"] = response_format

        response = await self._client.post("/v1/model/response", json=payload)
        _raise_for_status(response)
        return ModelResponse(**response.json())

