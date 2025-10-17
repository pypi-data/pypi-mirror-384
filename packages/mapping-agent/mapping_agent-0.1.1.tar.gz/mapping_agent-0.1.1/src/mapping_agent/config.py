"""
Configuration for the Mapping Agent.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os

class MappingAgentConfig(BaseSettings):
    """Configuration settings for the Mapping Agent."""
    llm_provider: str = Field(os.getenv("LLM_PROVIDER", "openai"), description="LLM provider to use")
    model_name: str = Field(os.getenv("LLM_MODEL", "gpt-4.1-mini"), description="AI model to use")
    api_key: str = Field(os.getenv("LLM_API_KEY", ""), description="API key for LLM provider")
    temperature: float = Field(default=0.3, ge=0, le=0.5, description="LLM temperature")
    max_tokens: int = Field(default=4000, ge=0, le=8000, description="Max tokens for LLM response")
    top_p: float = Field(default=1.0, ge=0, le=1, description="Top-p sampling parameter")
    frequency_penalty: float = Field(default=0.0, ge=0, le=1, description="Frequency penalty")
    presence_penalty: float = Field(default=0.0, ge=0, le=1, description="Presence penalty")

    class Config:
        env_prefix = "MAPPING_AGENT_"
        case_sensitive = False
