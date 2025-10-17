from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class SchemaDescriptionConfig(BaseSettings):
    """Configuration settings for the Table Description Agent."""

    # AI Provider Configuration
    model_config = SettingsConfigDict(
        env_file='.env',              
        env_file_encoding='utf-8',
        case_sensitive=False,         
        extra='ignore'               
    )
    ai_provider_schema_description: str = Field(default="openai", description="AI provider to use")
    model_name_schema_description: str = Field(default="gpt-4o", description="AI model to use")
    temperature_schema_description: float = Field(default=0.3, ge=0.0, le=2.0, description="AI model temperature")
    max_tokens_schema_description: int = Field(default=4000, ge=100, le=8000, description="Maximum tokens for AI response")

