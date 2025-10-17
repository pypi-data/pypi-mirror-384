"""
Kronos Labs API Client
"""

import json
from typing import List, Dict, Optional, Iterator, Union
import requests

from .exceptions import APIError, AuthenticationError
from .models import ChatCompletion, ChatCompletionChunk


class ChatCompletions:
    """Chat completions API"""
    
    def __init__(self, client: 'KronosLabs'):
        self._client = client
    
    def create(
        self,
        prompt: str,
        messages: Optional[List[Dict[str, str]]] = None,
        model: str = "hyperion",
        temperature: float = 0.7,
        is_stream: bool = False,
        tool: bool = False,
        **kwargs
    ) -> Union[ChatCompletion, Iterator[ChatCompletionChunk]]:
        """
        Create a chat completion.
        
        Args:
            prompt: The prompt text to send to the model
            messages: Optional list of message dicts with 'role' and 'content' keys
            model: Model to use - either "hyperion" or "hermes" (default: "hyperion")
            temperature: Controls randomness in the response (0.0-2.0)
            is_stream: Enable streaming responses
            tool: Enable tool usage
            **kwargs: Additional parameters to pass to the API
        
        Returns:
            ChatCompletion object if is_stream=False, otherwise an iterator of ChatCompletionChunk objects
        """
        # Validate model
        valid_models = ["hyperion", "hermes"]
        if model not in valid_models:
            raise ValueError(f"Invalid model '{model}'. Must be one of: {', '.join(valid_models)}")
        
        if model == "hyperion" and tool:
            raise ValueError(f"Model '{model}'. Does not have tool calling.")
        
        if messages is None:
            messages = []

        if model == "hyperion":
            payload = {
                "messages": messages,
                "prompt": prompt,
                "temperature": temperature,
                "is_stream": is_stream,
                "tool": tool,
                **kwargs
            }

        else:
            payload = {
                "messages": messages,
                "prompt": prompt,
                "temperature": temperature,
                "is_stream": is_stream,
                "tool": tool,
                **kwargs
            }
        
        if is_stream:
            return self._stream_completion(payload, model)
        else:
            return self._create_completion(payload, model)
    
    def _create_completion(self, payload: dict, model: str) -> ChatCompletion:
        """Create a non-streaming chat completion"""
        response = self._client._post(f"/api/chat/{model}", json=payload)
        return ChatCompletion.from_dict(response)
    
    def _stream_completion(self, payload: dict, model: str) -> Iterator[ChatCompletionChunk]:
        """Create a streaming chat completion"""
        response = self._client._post_stream(f"/api/chat/{model}", json=payload)
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                
                # Skip empty lines and the [DONE] message
                if not line_str.strip() or line_str.strip() == "data: [DONE]":
                    continue
                
                # Remove 'data: ' prefix
                if line_str.startswith("data: "):
                    line_str = line_str[6:]
                
                try:
                    chunk_data = json.loads(line_str)
                    yield ChatCompletionChunk.from_dict(chunk_data)
                except json.JSONDecodeError:
                    continue


class Chat:
    """Chat API"""
    
    def __init__(self, client: 'KronosLabs'):
        self.completions = ChatCompletions(client)


class KronosLabs:
    """
    Kronos Labs API Client
    
    Example:
        >>> client = KronosLabs(api_key="your-api-key")
        >>> response = client.chat.completions.create(
        ...     prompt="Hello, how are you?",
        ...     model="hyperion",  # or "hermes"
        ...     temperature=0.7
        ... )
        >>> print(response.choices[0].message.content)
    """
    
    BASE_URL = "https://kronoslabs.org"
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """
        Initialize the Kronos Labs client.
        
        Args:
            api_key: Your Kronos Labs API key
            base_url: Optional custom base URL (defaults to https://kronoslabs.org)
        """
        if not api_key:
            raise AuthenticationError("API key is required")
        
        self.api_key = api_key
        self.base_url = base_url or self.BASE_URL
        self.chat = Chat(self)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        return {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
    
    def _post(self, endpoint: str, **kwargs) -> dict:
        """
        Make a POST request to the API.
        
        Args:
            endpoint: API endpoint path
            **kwargs: Additional arguments to pass to requests.post
        
        Returns:
            Response JSON as dict
        
        Raises:
            AuthenticationError: If authentication fails
            APIError: If API returns an error
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        try:
            response = requests.post(url, headers=headers, **kwargs)
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            
            if response.status_code != 200:
                error_message = f"API request failed with status {response.status_code}"
                try:
                    error_data = response.json()
                    error_message = error_data.get("error", error_message)
                except:
                    pass
                raise APIError(error_message, status_code=response.status_code, response=response)
            
            return response.json()
        
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")
    
    def _post_stream(self, endpoint: str, **kwargs):
        """
        Make a streaming POST request to the API.
        
        Args:
            endpoint: API endpoint path
            **kwargs: Additional arguments to pass to requests.post
        
        Returns:
            Response object with streaming enabled
        
        Raises:
            AuthenticationError: If authentication fails
            APIError: If API returns an error
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        try:
            response = requests.post(url, headers=headers, stream=True, **kwargs)
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            
            if response.status_code != 200:
                error_message = f"API request failed with status {response.status_code}"
                try:
                    error_data = response.json()
                    error_message = error_data.get("error", error_message)
                except:
                    pass
                raise APIError(error_message, status_code=response.status_code, response=response)
            
            return response
        
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")
