"""
Intelligent Data Enrichment Agent using LLM-driven approach.
"""

import logging
import traceback
import warnings
from typing import Any

import pandas as pd

warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)
pd.options.mode.chained_assignment = None

from sfn_blueprint import SFNAIHandler, setup_logger

from .constants import (
    format_feature_engineering_system_prompt,
    format_feature_engineering_user_prompt,
)
from .models import EnrichmentConfig, EnrichmentResponse, FeatureSuggestion
from .utils import (
    EnrichmentValidator,
    FeatureProfiler,
    extract_dataframe_profile,
    validate_llm_json_output_feature_engineering,
)


class EnrichmentAgent:
    """
    Intelligent agent for data enrichment and feature engineering using LLMs.
    """
    def __init__(self, model_name: str = "auto", config: EnrichmentConfig | None = None):
        # Initialize configuration
        self.llm_handler = SFNAIHandler()
        self.config = config if config else EnrichmentConfig()  # Use default config if none provided
        # Set up logging
        try:
            logger_result = setup_logger(__name__)
            self.logger = logger_result[0] if isinstance(logger_result, tuple) else logger_result
        except Exception as e:
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger(__name__)
            self.logger.info(f"Using fallback logging due to: {e}")
        
        # Set model and basic attributes
        self.model_name = self.config.model_name
        self.llm_provider = self.config.llm_provider
        self.agent_type = "enrichment_agent"
        self.logger.info(f"Enrichment Agent initialized with model: {self.model_name}")
        
        # Set log level from config
        logging.getLogger().setLevel(self.config.log_level)
        
        # Initialize components
        self.feature_profiler = FeatureProfiler()
        self.validator = EnrichmentValidator()
        # Initialize sfn-blueprint components with error handling

    def _parse_input_data(self, data: pd.DataFrame | dict[str, Any] | str) -> pd.DataFrame:
        if isinstance(data, pd.DataFrame):
            return data.copy()
        elif isinstance(data, dict):
            return pd.DataFrame(data)
        elif isinstance(data, str):
            return pd.read_csv(data)
        else:
            raise ValueError("Unsupported input data type.")

    def suggest_features(
        self,
        df: pd.DataFrame,
        user_prompt: str,
        system_prompt: str,
        profile: Any,
        parameters: dict[str, Any] | None = None
    ) -> list[FeatureSuggestion]:
        """
        Generate feature suggestions based on the input data and context.
        
        Args:
            df: Input DataFrame
            user_prompt: User's description of the task
            system_prompt: System instructions for feature generation
            profile: Data profile information
            parameters: Additional parameters for feature generation
            
        Returns:
            List of FeatureSuggestion objects
            
        Raises:
            ValueError: If no LLM handler is available or if feature generation fails
        """
        suggestions = []
        
        if not self.llm_handler:
            self.logger.warning("No LLM handler available, using default suggestions")
            # Return some default suggestions if no LLM handler is available
            return [
                FeatureSuggestion(
                    feature_name="feature_1",
                    transformation="df['feature_1'] = df['age'] * df['salary'] / 1000",
                    explanation="Created a new feature combining age and salary"
                )
            ]
            
        try:
            # Log the prompts being sent to the LLM
            self.logger.debug(f"System Prompt: {system_prompt[:200]}...")
            self.logger.debug(f"User Prompt: {user_prompt[:200]}...")
            
            # Call the LLM
            llm_result = self.llm_handler.route_to(
                self.llm_provider,
                configuration={
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.3,  # Lower temperature for more focused outputs
                    "max_tokens": 1000    # Limit response length
                },
                model=self.model_name
            )
            
            # Handle different response formats
            response = llm_result[0] if isinstance(llm_result, tuple) else llm_result
            
            if not response or not isinstance(response, str):
                raise ValueError("Received empty or invalid response from LLM")
                
            # Log the raw response for debugging
            self.logger.debug(f"LLM Response: {response[:200]}...")
            
            # Parse and validate the response
            suggestions = validate_llm_json_output_feature_engineering(response)
            
            if not suggestions:
                self.logger.warning("No valid feature suggestions were generated")
                return []
                
            self.logger.info(f"Successfully generated {len(suggestions)} feature suggestions")
            return suggestions
            
        except Exception as e:
            error_msg = f"Failed to generate feature suggestions: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg) from e

    def enrich_data(
        self,
        data: pd.DataFrame | dict[str, Any] | str,
        db_name: str = "database",
        schema: str = "public",
        table_name: str = "table",
        domain_metadata: dict[str, Any] | None = None,
        entity_metadata: dict[str, Any] | None = None,
        use_case: str | None = None,
        ml_approach: str | None = None,
        mode: str | None = None,
        sample_rows: int = 5,
        parameters: dict[str, Any] | None = None
    ) -> EnrichmentResponse:
        """
            Main entry point for data enrichment. Suggests and applies new features using all provided context.
        """
        try:
            df = self._parse_input_data(data)
            # print("\n** parsed data\n", df)
            profile = extract_dataframe_profile(df, sample_size=sample_rows)
            # print("\n** profile\n", profile)
            # Prepare all context for prompt
            system_prompt = format_feature_engineering_system_prompt()
            # print("\n** system_prompt\n", system_prompt)


            user_prompt = format_feature_engineering_user_prompt(
            db_name=db_name,
            schema=schema,
            table_name=table_name,
            use_case=use_case or "N/A",
            ml_approach=ml_approach or "N/A",
            domain_metadata=domain_metadata or {},
            entity_metadata=entity_metadata or {},
            column_names=profile["columns"],
            column_dtypes=profile["data_types"],
            computed_stats=profile["computed_stats"],
            sample_data=profile["sample_rows"],
            )
            # print("\n** user_prompt\n", user_prompt)
            
            # In production, call LLM here. For now, stub with demo suggestions.
            suggestions = self.suggest_features(
                df, user_prompt, system_prompt, profile, parameters
            )

            # Convert suggestions list to dict format as expected by the model
            suggestions_dict = {}
            if suggestions:
                for i, suggestion in enumerate(suggestions):
                    if hasattr(suggestion, '__dict__'):
                        suggestions_dict[f"suggestion_{i+1}"] = suggestion.__dict__
                    elif isinstance(suggestion, dict):
                        suggestions_dict[f"suggestion_{i+1}"] = suggestion
                    else:
                        # If it's a string or other type, wrap it in a basic structure
                        suggestions_dict[f"suggestion_{i+1}"] = {
                            "feature_name": f"suggestion_{i+1}",
                            "content": str(suggestion)
                        }
            
            return EnrichmentResponse(
                success=True,
                suggestions=suggestions_dict,
                message="Data enrichment completed successfully.",
                errors=[]
            )
        except Exception as e:
            self.logger.error(f"Failed to enrich data: {e}")
            print(traceback.format_exc()[:500])
            return EnrichmentResponse(
                success=False,
                suggestions=None,
                message="Data enrichment failed.",
                errors=[str(e)]
            )

    def __call__(self,
        data: pd.DataFrame | dict[str, Any] | str,
        db_name: str = "database",
        schema: str = "public",
        table_name: str = "table",
        domain_metadata: dict[str, Any] | None = None,
        entity_metadata: dict[str, Any] | None = None,
        use_case: str | None = None,
        ml_approach: str | None = None,
        mode: str | None = None,
        sample_rows: int = 5,
        parameters: dict[str, Any] | None = None
        ) -> EnrichmentResponse:
        """
        Main entry point for data enrichment. Suggests and applies new features using all provided context.
        """
        return self.enrich_data(data, db_name, schema, 
                                table_name, domain_metadata, 
                                entity_metadata, use_case, ml_approach, 
                                mode, sample_rows, parameters)