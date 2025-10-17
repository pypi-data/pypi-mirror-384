"""
Utility classes for the Enrichment Agent.
"""
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from .models import FeatureSuggestion, DataFrameProfile, DataFrameColumnStats

import json
import traceback

class FeatureProfiler:
    """Profiles features and data for enrichment."""
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    def profile(self, df: pd.DataFrame, sample_size: int = 5) -> Dict[str, Any]:
        return {
            "columns": list(df.columns),
            "data_types": df.dtypes.astype(str).to_dict(),
            "sample_data": df.head(sample_size).to_dict(orient="list"),
            "sample_str": df.head(sample_size).to_string(index=False),
            "shape": df.shape
        }

def extract_sample_data_feature_engineering(df: pd.DataFrame, sample_rows: int = 5) -> dict:
    """Extract sample data from a DataFrame for enrichment prompt input."""
    sample = df.head(sample_rows)
    return {col: sample[col].tolist() for col in sample.columns}

def validate_llm_json_output_feature_engineering(llm_response: str):
    """
    Validate and parse an LLM response expected to be a JSON object or array.
    Handles various response formats and provides detailed error messages.
    Returns a list of FeatureSuggestion objects.
    """
    if not llm_response or not isinstance(llm_response, str):
        raise ValueError("LLM response must be a non-empty string")

    try:
        # Clean the response
        # print("llm_response", llm_response, type(llm_response))
        cleaned = llm_response.strip()
        cleaned = cleaned.replace('\\"', '"')
        
        # Remove markdown code blocks if present
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:].strip()
        elif cleaned.startswith('```'):
            cleaned = cleaned[3:].strip()
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3].strip()
            
        
        # print("cleaned", cleaned, type(cleaned))
        # Try to parse as JSON
        parsed = json.loads(cleaned)
        
        # Convert parsed JSON to FeatureSuggestion objects
        suggestions = []
        if isinstance(parsed, dict):
            # Handle dictionary format like {"suggestion_1": {...}, "suggestion_2": {...}}
            for key, value in parsed.items():
                if isinstance(value, dict):
                    # Create FeatureSuggestion from dictionary
                    feature_name = value.get('feature_name', key)
                    sql_query = value.get('sql_query', value.get('transformation', ''))
                    explanation = value.get('explanation', '')
                    
                    suggestion = FeatureSuggestion(
                        feature_name=feature_name,
                        transformation=sql_query,
                        explanation=explanation
                    )
                    suggestions.append(suggestion)
                else:
                    # Handle case where value is just a string
                    suggestion = FeatureSuggestion(
                        feature_name=key,
                        transformation=str(value),
                        explanation=f"Feature suggestion: {value}"
                    )
                    suggestions.append(suggestion)
        elif isinstance(parsed, list):
            # Handle list format
            for i, item in enumerate(parsed):
                if isinstance(item, dict):
                    feature_name = item.get('feature_name', f'suggestion_{i+1}')
                    sql_query = item.get('sql_query', item.get('transformation', ''))
                    explanation = item.get('explanation', '')
                    
                    suggestion = FeatureSuggestion(
                        feature_name=feature_name,
                        transformation=sql_query,
                        explanation=explanation
                    )
                    suggestions.append(suggestion)
                else:
                    # Handle case where item is just a string
                    suggestion = FeatureSuggestion(
                        feature_name=f'suggestion_{i+1}',
                        transformation=str(item),
                        explanation=f"Feature suggestion: {item}"
                    )
                    suggestions.append(suggestion)
        
        return suggestions
            
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON: {str(e)}\nResponse content: {cleaned[:200]}..."
        raise ValueError(error_msg) from e

class EnrichmentValidator:
    """Validates enriched data and provides quality assessment."""
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    def validate_enriched_data(self, enriched_df: pd.DataFrame, original_profile: Dict[str, Any]) -> Dict[str, Any]:
        new_cols = set(enriched_df.columns) - set(original_profile["columns"])
        return {
            "new_features_count": len(new_cols),
            "new_features": list(new_cols),
            "enriched_shape": enriched_df.shape
        }

def extract_dataframe_profile(df: pd.DataFrame, sample_size: int = 5) -> DataFrameProfile:
    """
    Extracts profile information from a pandas DataFrame including:
    - sample_rows (as string)
    - columns (list)
    - data_types (dict)
    - computed_stats (dict of DataFrameColumnStats)
    - identical_column_pairs (list of tuples)
    Handles errors gracefully, logs them, and returns a DataFrameProfile.
    """
    logger = logging.getLogger(__name__)
    error_log = []
    sample_rows = ''
    columns = []
    data_types = {}
    computed_stats = {}

    # Sample Rows
    try:
        sample_rows = df.head(sample_size).to_string()
    except Exception as e:
        logger.error(f"Failed to extract sample rows: {e}")
        error_log.append(f"sample_rows: {str(e)}")
        sample_rows = ''

    # Columns
    try:
        columns = list(df.columns)
    except Exception as e:
        logger.error(f"Failed to extract columns: {e}")
        error_log.append(f"columns: {str(e)}")
        columns = []

    # Data Types
    try:
        data_types = df.dtypes.astype(str).to_dict()
    except Exception as e:
        logger.error(f"Failed to extract data types: {e}")
        error_log.append(f"data_types: {str(e)}")
        data_types = {}

    # Computed Stats
    for col in columns:
        try:
            series = df[col]
            null_fraction = float(series.isnull().mean()) if series.size > 0 else None
            distinct_count = int(series.nunique(dropna=True))
            mean = float(series.mean()) if pd.api.types.is_numeric_dtype(series) else None
            std = float(series.std()) if pd.api.types.is_numeric_dtype(series) else None
            min_val = float(series.min()) if pd.api.types.is_numeric_dtype(series) else None
            max_val = float(series.max()) if pd.api.types.is_numeric_dtype(series) else None
            computed_stats[col] = DataFrameColumnStats(
                column_name=col,
                null_fraction=null_fraction,
                distinct_count=distinct_count,
                mean=mean,
                std=std,
                min_val=min_val,
                max_val=max_val
            )
        except Exception as e:
            logger.error(f"Failed to compute stats for column {col}: {e}")
            error_log.append(f"computed_stats[{col}]: {str(e)}")
            computed_stats[col] = DataFrameColumnStats(column_name=col)

    return DataFrameProfile(
        sample_rows=sample_rows,
        columns=columns,
        data_types=data_types,
        computed_stats=computed_stats,
        error_log=error_log
    )


# class CodeExecutor:
#     """Executes Python code for feature engineering."""
#     def execute(self, code: str, df: pd.DataFrame) -> Dict[str, Any]:
#         try:
#             exec(code, {"df": df})
#             return {"output": "success", "error": None}
#         except Exception as e:
#             return {"output": None, "error": str(e)}

# class LLMCodeValidator:
#     """Uses an LLM to validate and fix Python code for feature engineering."""
#     def __init__(self, executor: CodeExecutor, llm_client: str, model: str):
#         self.executor = executor
#         self.llm_client = llm_client
#         self.model = model
#     def run_with_validation(self, goal, df_head_str, code: str, user_prompt_template, system_prompt: Optional[str] = None, max_retries: int = 2) -> Dict[str, Any]:
#         current_code = code
#         for attempt in range(max_retries + 1):
#             result = self.executor.execute(current_code, pd.DataFrame())
#             if result["error"] is None:
#                 return result
#             if attempt >= max_retries:
#                 break
#             # Placeholder: In production, call LLM to fix code
#             current_code = code  # For now, do not change
#         return {"output": "", "error": f"Max retries exceeded. Last error: {result.get('error', 'Unknown')}", "locals": {}}
