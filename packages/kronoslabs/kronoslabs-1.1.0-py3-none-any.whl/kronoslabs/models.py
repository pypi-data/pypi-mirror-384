"""
Data models for API responses
"""

from typing import Optional, Dict, List, Any


class Message:
    """Chat message"""
    
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Message':
        return cls(
            role=data.get("role", ""),
            content=data.get("content", "")
        )
    
    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content
        }


class Delta:
    """Delta object for streaming responses"""
    
    def __init__(self, role: Optional[str] = None, content: Optional[str] = None):
        self.role = role
        self.content = content
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Delta':
        return cls(
            role=data.get("role"),
            content=data.get("content")
        )


class Choice:
    """Choice object in chat completion response"""
    
    def __init__(
        self,
        index: int,
        message: Optional[Message] = None,
        finish_reason: Optional[str] = None
    ):
        self.index = index
        self.message = message
        self.finish_reason = finish_reason
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Choice':
        message = None
        if "message" in data:
            message = Message.from_dict(data["message"])
        
        return cls(
            index=data.get("index", 0),
            message=message,
            finish_reason=data.get("finish_reason")
        )


class StreamChoice:
    """Choice object in streaming chat completion response"""
    
    def __init__(
        self,
        index: int,
        delta: Delta,
        finish_reason: Optional[str] = None
    ):
        self.index = index
        self.delta = delta
        self.finish_reason = finish_reason
    
    @classmethod
    def from_dict(cls, data: dict) -> 'StreamChoice':
        delta = Delta.from_dict(data.get("delta", {}))
        
        return cls(
            index=data.get("index", 0),
            delta=delta,
            finish_reason=data.get("finish_reason")
        )


class Usage:
    """Token usage information"""
    
    def __init__(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int
    ):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Usage':
        return cls(
            prompt_tokens=data.get("prompt_tokens", 0),
            completion_tokens=data.get("completion_tokens", 0),
            total_tokens=data.get("total_tokens", 0)
        )


class ChatCompletion:
    """Chat completion response"""
    
    def __init__(
        self,
        id: str,
        object: str,
        created: int,
        model: str,
        choices: List[Choice],
        usage: Optional[Usage] = None
    ):
        self.id = id
        self.object = object
        self.created = created
        self.model = model
        self.choices = choices
        self.usage = usage
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ChatCompletion':
        choices = [Choice.from_dict(choice) for choice in data.get("choices", [])]
        usage = None
        if "usage" in data:
            usage = Usage.from_dict(data["usage"])
        
        return cls(
            id=data.get("id", ""),
            object=data.get("object", ""),
            created=data.get("created", 0),
            model=data.get("model", ""),
            choices=choices,
            usage=usage
        )


class ChatCompletionChunk:
    """Streaming chat completion chunk"""
    
    def __init__(
        self,
        id: str,
        object: str,
        created: int,
        model: str,
        choices: List[StreamChoice]
    ):
        self.id = id
        self.object = object
        self.created = created
        self.model = model
        self.choices = choices
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ChatCompletionChunk':
        choices = [StreamChoice.from_dict(choice) for choice in data.get("choices", [])]
        
        return cls(
            id=data.get("id", ""),
            object=data.get("object", ""),
            created=data.get("created", 0),
            model=data.get("model", ""),
            choices=choices
        )
