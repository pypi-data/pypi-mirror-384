"""
Data models for the Enrichment Agent.
"""
import os
from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field


class EnrichmentConfig(BaseModel):
    """Configuration for the Enrichment Agent."""
    llm_provider: str = Field(os.getenv("LLM_PROVIDER", "openai"), description="LLM provider to use")
    model_name: str = Field(os.getenv("LLM_MODEL", "gpt-4.1-mini"), description="AI model to use")
    api_key: str = Field(os.getenv("LLM_API_KEY", ""), description="API key for LLM provider")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level for the agent"
    )


class DataFrameColumnStats(BaseModel):
    """Model for storing statistics about a DataFrame column."""
    column_name: str = Field(..., description="Name of the column")
    data_type: str | None = Field(None, description="Data type of the column")
    null_count: int | None = Field(None, description="Number of null values")
    unique_count: int | None = Field(None, description="Number of unique values")
    mean: float | None = Field(None, description="Mean value (for numeric columns)")
    std: float | None = Field(None, description="Standard deviation (for numeric columns)")
    min_val: Any | None = Field(None, description="Minimum value")
    max_val: Any | None = Field(None, description="Maximum value")
    top_values: dict[Any, int] | None = Field(None, description="Most common values and their counts")

class DataFrameProfile(TypedDict):
    """Type definition for DataFrame profile information."""
    sample_rows: str
    columns: list[str]
    data_types: dict[str, str]
    computed_stats: dict[str, DataFrameColumnStats]  # Updated to use DataFrameColumnStats
    identical_column_pairs: list[tuple]
    shape: tuple[int, int]
    missing_values: dict[str, int]
    unique_counts: dict[str, int]

class FeatureSuggestion(BaseModel):
    """Model for a single feature suggestion."""
    feature_name: str = Field(..., description="Name of the new feature")
    transformation: str = Field(..., description="Python code for the feature transformation")
    explanation: str = Field(..., description="Explanation of the feature")

# class EnrichmentOperation(BaseModel):
#     """Model for individual enrichment operations."""
#     operation_id: str = Field(..., description="Unique identifier for the operation")
#     operation_type: str = Field(..., description="Type of enrichment operation")
#     description: str = Field(..., description="Description of what the operation does")
#     parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters used for the operation")
#     status: str = Field(default="pending", description="Status: pending, completed, failed")
#     start_time: Optional[datetime] = Field(default=None, description="When the operation started")
#     end_time: Optional[datetime] = Field(default=None, description="When the operation completed")

class EnrichmentReport(BaseModel):
    """Model for enrichment operation reports."""
    report_id: str = Field(..., description="Unique identifier for the report")
    original_shape: Any = Field(..., description="Original data shape")
    enriched_shape: Any = Field(..., description="Enriched data shape")
    features_added: list[str] = Field(default_factory=list, description="Features added")
    execution_time: float | None = Field(default=None, description="Total execution time in seconds")

class EnrichmentResponse(BaseModel):
    """Response model for data enrichment operations."""
    success: bool = Field(..., description="Whether the enrichment operation was successful")
    suggestions: dict[str, Any] | None = Field(default=None, description="List of feature suggestions")
    message: str = Field(..., description="Human-readable message about the operation")
    errors: list[str] = Field(default_factory=list, description="List of errors if operation failed")

class EnrichmentRequest(BaseModel):
    """Request model for data enrichment operations."""
    data: Any = Field(..., description="Input data to be enriched (DataFrame, dict, or file path)")
    goal: str = Field(..., description="Enrichment goal or objective")
    enrichment_parameters: dict[str, Any] | None = Field(default_factory=dict, description="Optional enrichment parameters")
    data_source: str | None = Field(default=None, description="Source of the data")
    user_preferences: dict[str, Any] | None = Field(default_factory=dict, description="User-specific enrichment preferences")
    class Config:
        arbitrary_types_allowed = True

class EnrichmentParameters(BaseModel):
    """Model for enrichment operation parameters."""
    handle_missing_values: bool = Field(default=True, description="Whether to handle missing values in feature engineering")
    create_interactions: bool = Field(default=True, description="Whether to create feature interactions")
    create_polynomials: bool = Field(default=False, description="Whether to create polynomial features")
    create_bins: bool = Field(default=False, description="Whether to create binned features")
    custom_rules: list[dict[str, Any]] = Field(default_factory=list, description="Custom feature engineering rules")
    preserve_original: bool = Field(default=True, description="Whether to preserve original data")
    class Config:
        use_enum_values = True

