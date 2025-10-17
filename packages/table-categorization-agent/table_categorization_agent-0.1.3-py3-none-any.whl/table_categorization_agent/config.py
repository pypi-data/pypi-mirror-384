"""
Configuration for Table Categorization Agent

Centralized configuration management using sfn_blueprint.
"""


from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict




class TableCategorizationConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',              
        env_file_encoding='utf-8',
        case_sensitive=False,         
        extra='ignore'               
    )

    table_ai_provider: str = Field(default="openai", description="AI provider to use")
    table_model: str = Field(default="gpt-4o", description="AI model to use")
    table_temperature: float = Field(default=0.3, ge=0.0, le=2.0, description="AI model temperature")
    table_max_tokens: int = Field(default=4000, ge=100, le=8000, description="Maximum tokens for AI response")
