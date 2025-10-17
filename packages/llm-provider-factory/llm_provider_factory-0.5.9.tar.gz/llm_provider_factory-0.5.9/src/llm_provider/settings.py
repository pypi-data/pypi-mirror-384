"""Settings and data models for LLM Provider Factory."""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, model_validator
from enum import Enum


class MessageRole(str, Enum):
    """Message roles in conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    """Represents a single message in conversation history."""
    
    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True


class GenerationRequest(BaseModel):
    """Request for text generation."""
    
    # Either prompt OR messages should be provided
    prompt: Optional[str] = Field(default=None, description="Simple prompt for generation")
    messages: Optional[List[Message]] = Field(default=None, description="Messages for conversation")
    
    # Legacy field for backward compatibility
    history: Optional[List[Message]] = Field(default=None, description="Conversation history (deprecated, use messages)")
    
    # Generation parameters
    max_tokens: Optional[int] = Field(default=None, ge=1, le=100000)
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    stop_sequences: Optional[List[str]] = Field(default=None)
    stream: bool = Field(default=False, description="Whether to stream the response")
    
    class Config:
        extra = "allow"  # Allow provider-specific parameters
    
    @model_validator(mode='after')
    def validate_prompt_or_messages(self):
        """Validate that either prompt or messages is provided."""
        if not self.prompt and not self.messages:
            raise ValueError("Either 'prompt' or 'messages' must be provided")
        return self


class GenerationResponse(BaseModel):
    """Response from text generation."""
    
    content: str = Field(..., description="Generated text content")
    finish_reason: Optional[str] = Field(default=None)
    usage: Optional[Dict[str, Any]] = Field(default=None)
    metadata: Optional[Dict[str, Any]] = Field(default=None)
    provider: Optional[str] = Field(default=None)
    model: Optional[str] = Field(default=None)


class StreamChunk(BaseModel):
    """Chunk of streamed response."""
    
    content: str = Field(..., description="Partial content")
    is_final: bool = Field(default=False, description="Whether this is the final chunk")
    finish_reason: Optional[str] = Field(default=None)
    metadata: Optional[Dict[str, Any]] = Field(default=None)


class ProviderInfo(BaseModel):
    """Information about a provider."""
    
    name: str
    display_name: str
    description: str
    supported_models: List[str]
    capabilities: List[str]
    is_available: bool = True