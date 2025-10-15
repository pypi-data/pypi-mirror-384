"""
Configuration management for the Enrichment Agent.
"""
import os
from typing import Dict, Any, Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import Field

class EnrichmentConfig(BaseSettings):
    """Configuration for the Enrichment Agent."""
    model_name: str = Field(default="gpt-4.1-mini", description="LLM model to use for enrichment decisions (auto = let system choose)")
    model_api_key: Optional[str] = Field(default=None, description="API key for the LLM model")
    model_temperature: float = Field(default=0.1, description="Temperature for LLM responses")
    model_max_tokens: int = Field(default=2000, description="Maximum tokens for LLM responses")
    ai_provider: str = Field(default="openai", description="AI provider to use (openai, anthropic, cortex)")
    ai_task_type: str = Field(default="feature_suggestions_generator", description="Task type for AI requests")
    max_rows_per_batch: int = Field(default=10000, description="Maximum rows to process in one batch")
    enable_parallel_processing: bool = Field(default=True, description="Enable parallel data processing")
    enrichment_strategy: str = Field(default="auto", description="Enrichment strategy: auto, conservative, aggressive")
    output_format: str = Field(default="csv", description="Output format: csv, xlsx, json, parquet")
    include_enrichment_report: bool = Field(default=True, description="Include detailed enrichment report")
    backup_original_data: bool = Field(default=True, description="Backup original data before enrichment")
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    enable_console_logging: bool = Field(default=True, description="Enable console logging")
    cache_enabled: bool = Field(default=True, description="Enable caching for repeated operations")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    class Config:
        env_prefix = "ENRICHMENT_AGENT_"
        env_file = ".env"
        case_sensitive = False
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_environment_variables()
    def _load_environment_variables(self):
        if not self.model_api_key:
            self.model_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ENRICHMENT_AGENT_MODEL_API_KEY")
        for field_name, field_info in self.__class__.model_fields.items():
            env_var = f"ENRICHMENT_AGENT_{field_name.upper()}"
            if env_var not in os.environ:
                continue
            value = os.environ[env_var]
            field_type = field_info.annotation
            try:
                if field_type == bool:
                    if isinstance(value, str):
                        value = value.lower() in ('true', 'yes', '1')
                elif field_type == int:
                    value = int(value)
                elif field_type == float:
                    value = float(value)
                elif field_type == str:
                    value = str(value)
                setattr(self, field_name, value)
            except (ValueError, TypeError) as e:
                import logging
                logging.warning(
                    f"Failed to set {field_name} from environment variable {env_var}. "
                    f"Expected type {field_type}, got value: {value}. Error: {str(e)}"
                )
    def get_model_config(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "api_key": self.model_api_key,
            "temperature": self.model_temperature,
            "max_tokens": self.model_max_tokens,
        }
    def get_enrichment_config(self) -> Dict[str, Any]:
        return {
            "max_rows_per_batch": self.max_rows_per_batch,
            "enable_parallel_processing": self.enable_parallel_processing,
            "enrichment_strategy": self.enrichment_strategy,
        }
    def get_output_config(self) -> Dict[str, Any]:
        return {
            "output_format": self.output_format,
            "include_enrichment_report": self.include_enrichment_report,
            "backup_original_data": self.backup_original_data,
        }
def get_config() -> EnrichmentConfig:
    """Get the default configuration instance."""
    return EnrichmentConfig()
def get_config_from_env() -> EnrichmentConfig:
    """Get configuration from environment variables."""
    return EnrichmentConfig()
