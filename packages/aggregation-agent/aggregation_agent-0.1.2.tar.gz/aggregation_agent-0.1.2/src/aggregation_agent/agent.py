"""
Aggregation Agent - Suggests and implements data aggregation strategies.
"""

import datetime
import json
import logging
import re
from copy import deepcopy
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import tiktoken
from pandas.api.types import (
    is_bool_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
    is_string_dtype,
)
from sfn_blueprint import SFNAgent, SFNAIHandler, SFNDataLoader

from .config import (
    BOOLEAN_DATA_TYPES,
    DATETIME_DATA_TYPES,
    DEFAULT_BOOLEAN_AGGREGATIONS,
    DEFAULT_DATETIME_AGGREGATIONS,
    DEFAULT_NUMERIC_AGGREGATIONS,
    DEFAULT_TEXT_AGGREGATIONS,
    NUMERICAL_DATA_TYPES,
    AggregationConfig,
)
from .constants import (
    format_golden_wizard_aggregation_suggestion_prompt,
    format_group_by_columns_prompt_golden_wizard,
    format_other_wizard_aggregation_suggestion_prompt,
    format_other_wizard_group_by_columns,
)

logger = logging.getLogger(__name__)


class AggregationAgent(SFNAgent):
    """
    Agent for suggesting optimal aggregation methods for features.

    This agent analyzes table schema and field mappings to suggest
    appropriate aggregation methods for each feature when grouping data.
    """

    def __init__(self, config: Optional[AggregationConfig] = None):
        """
        Initialize the Aggregation Agent.

        Args:
            model_name: Name of the model to use
        """
        super().__init__(name="Aggregation Advisor", role="Data Aggregation Advisor")
        self.config = config or AggregationConfig()
        self.ai_handler = SFNAIHandler()
        self.data_loader = SFNDataLoader()
        self.token = tiktoken.encoding_for_model("gpt-4o-mini")

        # Define allowed aggregation methods per data type
        self.allowed_methods = {
            "TEXT": ["Unique Count", "Mode", "Last Value"],
            "NUMERICAL": ["Min", "Max", "Sum", "Mean", "Median", "Mode", "Last Value"],
            "DATETIME": ["Max", "Min"],
            "BOOLEAN": ["Mode", "Last Value"],
        }

    # def suggest_aggregation_methods(
    #     self,
    #     table_schema: Dict[str, Any],
    #     field_mappings: Dict[str, str],
    #     problem_type: str,
    #     group_by_fields: List[str],
    #     additional_context: Dict[str, Any] = None,
    # ) -> Dict[str, List[Dict[str, Any]]]:
    #     """
    #     Suggest aggregation methods for features based on their data types and the problem context.

    #     Args:
    #         table_schema: Schema of the table with field types
    #         field_mappings: Mappings of fields to standard names
    #         problem_type: Type of problem (regression, classification, etc.)
    #         group_by_fields: Fields that will be used for grouping
    #         additional_context: Additional context about the problem (optional)

    #     Returns:
    #         Dictionary with suggested aggregation methods for each field, where each field
    #         can have multiple suggested methods
    #     """
    #     logger.info("Suggesting aggregation methods")

    #     # Create prompt for LLM using constants
    #     prompt = format_aggregation_suggestion_prompt(
    #         table_schema=table_schema,
    #         field_mappings=field_mappings,
    #         problem_type=problem_type,
    #         group_by_fields=group_by_fields,
    #         additional_context=additional_context,
    #     )

    #     # Make the LLM call
    #     logger.info("Sending aggregation method suggestion prompt to LLM")
    #     response = self.llm_agent.generate_text(prompt, max_tokens=1000)

    #     # Parse the JSON response
    #     try:
    #         # Extract JSON content if it's embedded in other text
    #         json_content = response
    #         if "{" in response and "}" in response:
    #             start_idx = response.find("{")
    #             end_idx = response.rfind("}") + 1
    #             json_content = response[start_idx:end_idx]

    #         suggestions = json.loads(json_content)
    #         logger.info(
    #             f"Successfully parsed aggregation method suggestions from LLM response"
    #         )
    #         return suggestions
    #     except Exception as e:
    #         logger.error(f"Error parsing LLM response: {str(e)}")
    #         logger.error(f"Raw response: {response}")
    #         return {}

    def validate_aggregation_methods(
        self, suggestions: Dict[str, List[Dict[str, str]]], table_schema: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Validate the suggested aggregation methods against allowed methods for each data type.

        Args:
            suggestions: Dictionary of suggested aggregation methods (lists per field)
            table_schema: Schema of the table with field types

        Returns:
            Dictionary with validated aggregation methods
        """
        logger.info("Validating aggregation method suggestions")

        validated_suggestions = {}

        # Map schema types to our data type categories
        type_mapping = {
            "int": "NUMERICAL",
            "float": "NUMERICAL",
            "numeric": "NUMERICAL",
            "number": "NUMERICAL",
            "integer": "NUMERICAL",
            "double": "NUMERICAL",
            "decimal": "NUMERICAL",
            "text": "TEXT",
            "string": "TEXT",
            "varchar": "TEXT",
            "char": "TEXT",
            "date": "DATETIME",
            "datetime": "DATETIME",
            "timestamp": "DATETIME",
            "time": "DATETIME",
            "boolean": "BOOLEAN",
            "bool": "BOOLEAN",
        }

        for field, field_suggestions in suggestions.items():
            # Get the field's data type from schema
            field_type = table_schema.get(field, {}).get("type", "").lower()
            data_type_category = type_mapping.get(
                field_type, "TEXT"
            )  # Default to TEXT if unknown

            # Initialize validated suggestions for this field
            validated_suggestions[field] = []

            # Process each suggested method for this field
            for suggestion in field_suggestions:
                method = suggestion.get("method", "")

                # Check if the method is allowed for this data type
                if method in self.allowed_methods.get(data_type_category, []):
                    # Method is valid, keep it
                    valid_suggestion = suggestion.copy()
                    valid_suggestion["data_type"] = data_type_category
                    validated_suggestions[field].append(valid_suggestion)
                else:
                    # Method is not valid, log warning
                    logger.warning(
                        f"Invalid aggregation method '{method}' for field '{field}' with type '{data_type_category}'"
                    )

            # If no valid methods were found, add a default method
            if not validated_suggestions[field]:
                if self.allowed_methods.get(data_type_category, []):
                    default_method = self.allowed_methods[data_type_category][0]
                    validated_suggestions[field].append(
                        {
                            "method": default_method,
                            "explanation": f"Default {default_method} aggregation for {data_type_category} type.",
                            "data_type": data_type_category,
                        }
                    )

        # Check for missing fields in the suggestions
        for field, field_info in table_schema.items():
            if field not in suggestions and field not in validated_suggestions:
                field_type = field_info.get("type", "").lower()
                data_type_category = type_mapping.get(field_type, "TEXT")

                if self.allowed_methods.get(data_type_category, []):
                    default_method = self.allowed_methods[data_type_category][0]
                    validated_suggestions[field] = [
                        {
                            "method": default_method,
                            "explanation": f"Default {default_method} aggregation for {data_type_category} type.",
                            "data_type": data_type_category,
                        }
                    ]

        logger.info(
            f"Validated aggregation method suggestions for {len(validated_suggestions)} fields"
        )
        return validated_suggestions

    def _get_dataframe_metadata(self, df: pd.DataFrame) -> Dict[str, Any]:
        df = df.convert_dtypes()

        meta_data = {"table_info": {"row_count": len(df)}, "table_columns_info": {}}

        for col in df.columns:
            col_info = {}
            col_series = df[col]

            col_info["data_type"] = str(col_series.dtype)

            null_percentage = float(col_series.isnull().sum() / len(df) * 100)
            col_info["null_percentage"] = round(null_percentage, 2)

            if null_percentage >= 99:
                col_info["distinct_count"] = 0
                col_info["freq/top5"] = []
                col_info["min/max_value"] = []
                col_info["date_distribution"] = []
            else:
                try:
                    distinct_count = int(col_series.nunique())
                except TypeError:
                    distinct_count = int(col_series.astype(str).nunique())
                col_info["distinct_count"] = distinct_count

                try:
                    freq_top5 = list(col_series.value_counts().head(5).items())
                except TypeError:
                    freq_top5 = list(
                        col_series.astype(str).value_counts().head(5).items()
                    )
                col_info["freq/top5"] = freq_top5

                try:
                    min_val, max_val = col_series.min(), col_series.max()
                    col_info["min/max_value"] = [(min_val, max_val)]
                except:  # noqa: E722
                    col_info["min/max_value"] = []

                date_distribution = []
                if (
                    col_series.dtype == "object"
                    or "datetime" in str(col_series.dtype).lower()
                ):
                    try:
                        date_series = pd.to_datetime(
                            col_series, errors="coerce", format="%Y-%m-%d"
                        )
                        valid_dates = date_series.dropna()

                        if len(valid_dates) > 0:
                            date_counts = (
                                valid_dates.dt.date.value_counts().sort_index()
                            )
                            date_distribution = [
                                (date, count) for date, count in date_counts.items()
                            ]
                    except:  # noqa: E722
                        pass

                col_info["date_distribution"] = date_distribution

            meta_data["table_columns_info"][col] = col_info

        return meta_data

    def json_converter(self, obj):
        """Custom JSON serializer for objects not serializable by default json code."""
        if isinstance(obj, (datetime.datetime, datetime.date, pd.Timestamp)):
            return obj.isoformat()
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    def _get_group_by_field(
        self,
        business_domain: str,
        business_domain_description: str,
        column_descriptions: dict,
        entity_description: dict,
        mappings: dict,
        table_category,
        df=None,
        sample_data=None,
        metadata=None,
        use_case=None,
    ):
        logger.info("Sending group by method suggestion prompt to LLM")

        try:
            if isinstance(df, pd.DataFrame) and not df.empty:
                meta_data = self._get_dataframe_metadata(df)
                meta_data = json.dumps(meta_data, indent=4, default=str)

                # Clean and sample data
                clean_df = df.dropna()
                sample_size = min(len(clean_df), 7)
                if sample_size > 0:
                    sample = clean_df.sample(n=sample_size, random_state=42)
                    sample_json = sample.to_json(
                        orient="records", indent=4, date_format="iso"
                    )
                else:
                    sample_json = "[]"
                    logger.warning("No data available after cleaning DataFrame")
            else:
                meta_data = metadata
                sample_json = sample_data

            # Build business domain context
            business_domain_context = (
                f"{business_domain} : {business_domain_description}"
            )

            column_text = json.dumps(column_descriptions, indent=4)
            entity_text = json.dumps(entity_description, indent=4)
            mappings_text = json.dumps(mappings, indent=4)

            if use_case:
                system_prompt, user_prompt = format_other_wizard_group_by_columns(
                    use_case=use_case,
                    business_domain=business_domain_context,
                    entity_description=entity_text,
                    column_descriptions=column_text,
                    sample_data=sample_json,
                    meta_data=meta_data,
                    mappings=mappings_text,
                )
            else:
                system_prompt, user_prompt = (
                    format_group_by_columns_prompt_golden_wizard(
                        sample_data=sample_json,
                        meta_data=meta_data,
                        mappings=mappings_text,
                        business_domain=business_domain_context,
                        table_category=table_category,
                        entity_description=entity_text,
                    )
                )

            print("Group By User Prompt: ", user_prompt)
            response, cost = self.ai_handler.route_to(
                self.config.group_by_ai_provider,
                configuration={
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature,
                },
                model=self.config.group_by_model,
            )

            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]  # Remove ```json
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]

            return json.loads(clean_response), cost
        except Exception as e:
            logger.error(f"Error in LLM suggestion phase: {str(e)}")
            return []

    def _clean_json_string(self, json_string, data_df, dtype_dict):
        logger.info("cleaning json string...")

        json_match = re.search(
            r"```(?:json)?\s*(\{.*?\})\s*```", json_string, re.DOTALL
        )

        if json_match:
            json_string = json_match.group(1)
        else:
            json_match = re.search(r"^\s*(\{.*\})\s*$", json_string, re.DOTALL)
            if json_match:
                json_string = json_match.group(1)
            else:
                json_string = json_string.strip()

        # Strip leading and trailing whitespace
        json_string = json_string.strip()

        if json_string.startswith("```json"):
            json_string = json_string[7:-3]

        # Check if the cleaned string represents a valid JSON dictionary
        try:
            cleaned_dict = json.loads(json_string)
            if not isinstance(cleaned_dict, dict):
                raise ValueError("Not a valid JSON dictionary")
        except (ValueError, json.decoder.JSONDecodeError):
            raise ValueError("Not a valid JSON dictionary")

        # Check if there are any keys in the cleaned dictionary
        if len(cleaned_dict) == 0:
            logger.info(" Cleaned JSON is empty..")
        else:
            logger.info(
                f" Number of columns present in cleaned JSON are {len(cleaned_dict)}"
            )

        # Check if keys are present in DataFrame columns
        missing_columns = []
        for key in cleaned_dict.keys():
            if key not in data_df.columns:
                missing_columns.append(key)

        if missing_columns:
            logger.info(
                " Warning: The following keys from the cleaned JSON dictionary are not present as columns in the DataFrame:"
            )
            logger.info(f" {missing_columns}'")
        else:
            logger.info("All columns identified.")

        for column, methods in list(cleaned_dict.items()):
            if isinstance(methods, list):
                data_type = dtype_dict.get(column)

                if data_type in self.allowed_methods:
                    allowed_methods = self.allowed_methods[data_type]

                    valid_methods = [
                        method
                        for method in methods
                        if method["method"] in allowed_methods
                    ]

                    if valid_methods:
                        if len(valid_methods) != len(methods):
                            logger.info(
                                f"Invalid methods removed for column '{column}': {[method['method'] for method in methods if method['method'] not in allowed_methods]}"
                            )

                        cleaned_dict[column] = valid_methods
                    else:
                        logger.info(
                            f"No valid methods for column '{column}', removing column"
                        )
                        del cleaned_dict[column]
                else:
                    logger.info(
                        f"Data type '{data_type}' is not allowed, removing column '{column}'"
                    )
                    del cleaned_dict[column]
            else:
                logger.info(
                    f"Methods for column '{column}' are not a list, removing column"
                )

                del cleaned_dict[column]

        return cleaned_dict if cleaned_dict else None

    def format_response(self, cleaned_json, op_col_dtypes):
        data = dict()

        for op_cod in op_col_dtypes:
            op_col, op_dtype = op_cod["column_name"], op_cod["data_type"]

            op_dtype = op_dtype.lower() if op_dtype else None
            if op_dtype in NUMERICAL_DATA_TYPES:
                curr_agg = deepcopy(DEFAULT_NUMERIC_AGGREGATIONS)
            elif op_dtype in DATETIME_DATA_TYPES:
                curr_agg = deepcopy(DEFAULT_DATETIME_AGGREGATIONS)
            elif op_dtype in BOOLEAN_DATA_TYPES:
                curr_agg = deepcopy(DEFAULT_BOOLEAN_AGGREGATIONS)
            else:
                curr_agg = deepcopy(DEFAULT_TEXT_AGGREGATIONS)
            agg_sugg = cleaned_json.get(op_col.lower(), [])

            for agg in agg_sugg:
                cagg = agg.get("method").lower().replace(" ", "_")
                curr_agg[cagg]["checked"] = True
                curr_agg[cagg]["explanation"] = agg.get("explanation")

            # Add missing explanations as empty strings
            for agg_detail in curr_agg.values():
                if "explanation" not in agg_detail:
                    agg_detail["explanation"] = ""

            obj = {
                "datatype": op_dtype,
                "aggregations": list(curr_agg.values()),
            }

            data[op_col] = obj
        return data

    def get_column_category(self, dtype) -> str:
        if is_bool_dtype(dtype):
            return "BOOLEAN"
        elif is_numeric_dtype(dtype):
            return "NUMERICAL"
        elif is_datetime64_any_dtype(dtype):
            return "DATETIME"
        elif is_string_dtype(dtype) or is_object_dtype(dtype):
            return "TEXT"
        else:
            # Fallback for other dtypes like 'category', 'timedelta'
            return "TEXT"

    def suggest_aggregation_methods(
        self,
        data_df,
        column_text_describe_dict,
        group_by_columns,
        use_case=None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Suggest aggregation methods for features based on their data types and the problem context.
        """
        logger.info("Suggesting aggregation methods")

        try:

            for col in column_text_describe_dict.keys():
                if col not in data_df.columns:
                    logger.info(
                        f"Key '{col}' in column_text_describe_dict but not found as a column in data_df."
                    )

            for col in group_by_columns:
                if col not in data_df.columns:
                    raise ValueError(f"Group by column '{col}' not found in data_df.")

            df_inferred = data_df.convert_dtypes()
            feature_dtype_dict = {}

            for column_name, dtype in df_inferred.dtypes.items():
                convert_dtype = self.get_column_category(dtype)
                feature_dtype_dict[column_name] = convert_dtype

            if len(data_df) == len(data_df.groupby(group_by_columns)):
                logger.info(
                    "Only one record per group. Returning appropriate aggregation for all features."
                )

                default_methods = {
                    "TEXT": {
                        "method": "Last Value",
                        "explanation": "With only one record per group, Last Value returns the single available value.",
                    },
                    "NUMERICAL": {
                        "method": "Sum",
                        "explanation": "With only one record per group, Sum returns the single available value.",
                    },
                    "DATETIME": {
                        "method": "Max",
                        "explanation": "With only one record per group, max returns the single available value.",
                    },
                    "BOOLEAN": {
                        "method": "Mode",
                        "explanation": "With only one record per group, mode returns the single available value.",
                    },
                }

                aggregation_suggestion = {}

                for col in data_df.columns:
                    if col in group_by_columns:
                        continue

                    col_type = feature_dtype_dict[col]
                    method_info = default_methods[col_type]
                    aggregation_suggestion[col] = [method_info]

                return aggregation_suggestion, {}

            clean_df = data_df.dropna()
            sample = clean_df.sample(n=min(len(clean_df), 10), random_state=42)
            sample_json = sample.to_json(orient="records", indent=4, date_format="iso")

            df_describe_dict = data_df.describe().to_json(
                orient="records", indent=4, date_format="iso"
            )

            total_token = (
                len(self.token.encode(str(sample_json)))
                + len(self.token.encode(str(df_describe_dict)))
                + len(self.token.encode(str(column_text_describe_dict)))
                + len(self.token.encode(str(feature_dtype_dict)))
            )

            if total_token > 11000:
                removed_cols = data_df.columns[-25:]
                data_df = data_df.iloc[:, :-25]

                for col in removed_cols:
                    if col in column_text_describe_dict:
                        logger.info(
                            f"removing the respective {col} from the describe dict."
                        )

                        del column_text_describe_dict[col]
                    if col in feature_dtype_dict:
                        logger.info(
                            f"removing the respective {col} from the dtype dict."
                        )

                        del feature_dtype_dict[col]

                sample = clean_df.sample(n=min(len(clean_df), 5), random_state=42)

                sample_json = sample.to_json(
                    orient="records", indent=4, date_format="iso"
                )

                df_describe_dict = data_df.describe().to_json(
                    orient="records", indent=4, date_format="iso"
                )

            if use_case:
                system_prompt, user_prompt = (
                    format_other_wizard_aggregation_suggestion_prompt(
                        group_by_columns=group_by_columns,
                        use_case=use_case,
                        feature_dtype_dict=json.dumps(feature_dtype_dict, indent=4),
                        column_text_describe_dict=json.dumps(
                            column_text_describe_dict, indent=4
                        ),
                        df_describe_dict=df_describe_dict,
                        sample_data_dict=sample_json,
                    )
                )
            else:
                system_prompt, user_prompt = (
                    format_golden_wizard_aggregation_suggestion_prompt(
                        feature_dtype_dict=json.dumps(feature_dtype_dict, indent=4),
                        df_describe_dict=df_describe_dict,
                        sample_data_dict=sample_json,
                        column_text_describe_dict=json.dumps(
                            column_text_describe_dict, indent=4
                        ),
                    )
                )

            print("Aggregation User Prompt: ", user_prompt)
            cost_summary = {}

            for _ in range(3):
                response, cost = self.ai_handler.route_to(
                    self.config.aggregation_ai_provider,
                    configuration={
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "max_tokens": self.config.max_tokens,
                        "temperature": self.config.temperature,
                    },
                    model=self.config.aggregation_model,
                )

                cost_summary = {
                    k: cost.get(k, 0) + cost_summary.get(k, 0)
                    for k in set(cost) | set(cost_summary)
                }

                generated_texts = response.strip()

                cleaned_json = self._clean_json_string(
                    generated_texts, data_df, feature_dtype_dict
                )

                logger.info(
                    "Successfully parsed aggregation method suggestions from LLM response"
                )

                if cleaned_json and len(cleaned_json) > 4:
                    all_same = (
                        len(
                            set(
                                tuple(tuple(d.items()) for d in v)
                                for v in cleaned_json.values()
                            )
                        )
                        == 1
                    )

                    if not all_same:
                        return cleaned_json, cost_summary
                    else:
                        logger.warning(
                            "All suggested aggregation methods are the same. Trying again."
                        )
                elif cleaned_json and len(cleaned_json) <= 4:
                    logger.info(
                        "Output has fewer than 5 features. Returning the output."
                    )
                    return cleaned_json, cost_summary
                else:
                    logger.warning("Output does not meet the criteria. Trying again.")

            logger.warning(
                "Output check limit reached 3 iterations. Returning the last output."
            )

            return cleaned_json, cost_summary
        except Exception as e:
            logger.error(f"Error in LLM suggestion phase: {str(e)}")
            return {}, {}

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an aggregation task based on the provided task data.
        This method provides a standard interface for the orchestrator.

        Args:
            task_data: Dictionary containing task information
                - file: File path or data source
                - problem_context: Context about the aggregation task
                - domain_schema: Optional domain schema path

        Returns:
            Dictionary with execution results
        """

        # try:
        #     # Extract parameters from task_data
        #     data_file = task_data.get("file")
        #     problem_context = task_data.get("problem_context", "Data aggregation task")
        #     domain_schema = task_data.get("domain_schema")

        #     logger.info(f"Executing aggregation task: {problem_context}")

        #     # Extract and analyze context for intelligent decision making
        #     context_info = None
        #     context_recommendations = None
        #     try:
        #         context_info = extract_context_info(task_data)
        #         if context_info:
        #             logger.info(f"Context extracted for domain: {context_info.domain}")
        #             validation_result = validate_context(
        #                 context_info, ["domain", "workflow_goal", "data_sensitivity"]
        #             )
        #             if not validation_result["is_valid"]:
        #                 logger.warning(
        #                     f"Context validation issues: {validation_result['recommendations']}"
        #                 )
        #             context_recommendations = get_context_recommendations(
        #                 context_info, "aggregation_agent"
        #             )
        #             logger.info(
        #                 f"Generated {len(context_recommendations.data_processing)} data processing recommendations"
        #             )
        #             log_context_usage(
        #                 context_info,
        #                 "aggregation_agent",
        #                 ["domain", "workflow_goal", "compliance_requirements"],
        #             )
        #     except Exception as e:
        #         logger.warning(
        #             f"Context analysis failed, proceeding with basic execution: {e}"
        #         )

        #         # For now, return a placeholder response since we need actual data files
        #         # In a real scenario, you would load the data and perform aggregation analysis

        #         # Save results to workflow storage if available
        #         try:
        #             # Check if we have workflow storage information
        #             if (
        #                 "workflow_storage_path" in task_data
        #                 or "workflow_id" in task_data
        #             ):
        #                 from sfn_blueprint import WorkflowStorageManager

        #                 # Determine workflow storage path
        #                 workflow_storage_path = task_data.get(
        #                     "workflow_storage_path", "outputs/workflows"
        #                 )
        #                 workflow_id = task_data.get("workflow_id", "unknown")

        #                 # Initialize storage manager
        #                 storage_manager = WorkflowStorageManager(
        #                     workflow_storage_path, workflow_id
        #                 )

        #                 # Create a summary DataFrame for storage
        #                 import pandas as pd
        #                 from datetime import datetime

        #                 aggregation_summary = pd.DataFrame(
        #                     [
        #                         {
        #                             "task_type": "aggregation_analysis",
        #                             "status": "completed",
        #                             "problem_context": problem_context,
        #                             "execution_time": datetime.now().isoformat(),
        #                         }
        #                     ]
        #                 )

        #                 # Prepare metadata with context information
        #                 metadata = {
        #                     "aggregation_analysis": {
        #                         "task_type": "aggregation_analysis",
        #                         "status": "completed",
        #                         "problem_context": problem_context,
        #                     },
        #                     "recommendations": [
        #                         "Analyze data types for appropriate aggregation methods",
        #                         "Identify key metrics for patient outcomes analysis",
        #                         "Consider temporal aggregation for time-series data",
        #                         "Apply statistical aggregations for numerical fields",
        #                     ],
        #                     "execution_time": datetime.now().isoformat(),
        #                     "agent_name": "aggregation_agent",
        #                     "step_name": "data_aggregation",
        #                     "execution_timestamp": datetime.now().isoformat(),
        #                     "data_type": "DataFrame",
        #                     "storage_backend": "file",
        #                     "data_shape": [1, 4],
        #                     "data_columns": [
        #                         "task_type",
        #                         "status",
        #                         "problem_context",
        #                         "execution_time",
        #                     ],
        #                     "data_types": {
        #                         "task_type": "object",
        #                         "status": "object",
        #                         "problem_context": "object",
        #                         "execution_time": "object",
        #                     },
        #                     "storage_format": "csv",
        #                     "storage_reason": "Optimal format for 1 rows, 4 columns",
        #                 }

        #                 # Add context information if available
        #                 if context_info:
        #                     metadata["context_info"] = {
        #                         "domain": context_info.domain,
        #                         "workflow_goal": context_info.workflow_goal,
        #                         "data_sensitivity": context_info.data_sensitivity,
        #                         "compliance_requirements": context_info.compliance_requirements,
        #                         "context_quality_score": (
        #                             validation_result["quality_score"]
        #                             if "validation_result" in locals()
        #                             else 0.0
        #                         ),
        #                     }

        #                 # Add AI recommendations if available
        #                 if context_recommendations:
        #                     metadata["ai_recommendations"] = {
        #                         "data_processing": context_recommendations.data_processing,
        #                         "quality_checks": context_recommendations.quality_checks,
        #                         "optimization_strategies": context_recommendations.optimization_strategies,
        #                         "compliance_measures": context_recommendations.compliance_measures,
        #                     }

        #                 # Save the aggregation analysis results
        #                 storage_result = storage_manager.save_agent_result(
        #                     agent_name="aggregation_agent",
        #                     step_name="data_aggregation",
        #                     data=aggregation_summary,
        #                     metadata=metadata,
        #                 )

        #                 logger.info(
        #                     f"Aggregation analysis results saved to workflow storage: {storage_result['files']}"
        #                 )

        #         except ImportError:
        #             logger.warning(
        #                 "WorkflowStorageManager not available, skipping workflow storage"
        #             )
        #         except Exception as e:
        #             logger.warning(f"Failed to save to workflow storage: {e}")

        #         # Convert response to orchestrator format with context information
        #         return {
        #             "success": True,
        #             "result": {
        #                 "message": f"Aggregation analysis task completed: {problem_context}",
        #                 "task_type": "aggregation_analysis",
        #                 "status": "completed",
        #                 "recommendations": [
        #                     "Analyze data types for appropriate aggregation methods",
        #                     "Identify key metrics for patient outcomes analysis",
        #                     "Consider temporal aggregation for time-series data",
        #                     "Apply statistical aggregations for numerical fields",
        #                 ],
        #                 "execution_time": "completed",
        #                 "context_analysis": {
        #                     "domain": (
        #                         context_info.domain if context_info else "unknown"
        #                     ),
        #                     "workflow_goal": (
        #                         context_info.workflow_goal
        #                         if context_info
        #                         else "unknown"
        #                     ),
        #                     "context_quality_score": (
        #                         validation_result["quality_score"]
        #                         if context_info and "validation_result" in locals()
        #                         else 0.0
        #                     ),
        #                 },
        #                 "ai_recommendations": {
        #                     "data_processing": (
        #                         context_recommendations.data_processing
        #                         if context_recommendations
        #                         else []
        #                     ),
        #                     "quality_checks": (
        #                         context_recommendations.quality_checks
        #                         if context_recommendations
        #                         else []
        #                     ),
        #                     "optimization_strategies": (
        #                         context_recommendations.optimization_strategies
        #                         if context_recommendations
        #                         else []
        #                     ),
        #                     "compliance_measures": (
        #                         context_recommendations.compliance_measures
        #                         if context_recommendations
        #                         else []
        #                     ),
        #                 },
        #             },
        #             "agent": "aggregation_agent",
        #         }

        # except Exception as e:
        #     logger.error(f"Task execution failed: {e}")
        #     return {
        #         "success": False,
        #         "error": f"Task execution failed: {str(e)}",
        #         "agent": "aggregation_agent",
        #     }

        try:
            data_source = task_data["file"]
            domain_name = task_data["domain_name"]
            domain_description = task_data["domain_description"]
            column_describe: dict = task_data["column_description"]
            entity_description: dict = task_data["entity_description"]
            mappings: dict = task_data["mappings"]
            table_category = task_data["table_category"]
            use_case = task_data.get("use_case")

            df = self.data_loader.execute_task(SimpleNamespace(path=data_source))

            group_by_columns, cost_summary_group = self._get_group_by_field(
                df=df,
                business_domain=domain_name,
                business_domain_description=domain_description,
                column_descriptions=column_describe,
                entity_description=entity_description,
                mappings=mappings,
                use_case=use_case,
                table_category=table_category,
            )

            if not group_by_columns:
                logger.error("No group by column suggested by LLM.")
                raise ValueError("No valid group by column found.")

            aggregation_suggestion, cost_summary_aggregation = (
                self.suggest_aggregation_methods(
                    df,
                    column_text_describe_dict=column_describe,
                    group_by_columns=group_by_columns,
                    use_case=use_case,
                )
            )

            if not aggregation_suggestion:
                logger.error("No aggregation suggestions generated by LLM.")
                raise RuntimeError("Failed to get aggregation suggestions from LLM.")

            if "workflow_storage_path" in task_data or "workflow_id" in task_data:
                try:
                    from sfn_blueprint import WorkflowStorageManager

                    storage_manager = WorkflowStorageManager(
                        task_data.get("workflow_storage_path", "outputs/workflows"),
                        task_data.get("workflow_id", "unknown"),
                    )
                    storage_result = storage_manager.save_agent_result(
                        agent_name=self.__class__.__name__,
                        step_name="aggregation_suggestion",
                        data={
                            "aggregation_suggestions": aggregation_suggestion,
                            "groupby_columns": group_by_columns,
                            "cost_summary_group": cost_summary_group,
                            "cost_summary_aggregation": cost_summary_aggregation,
                        },
                        metadata={
                            "domain_name": domain_name,
                            "domain_description": domain_description,
                            "column_text_describe_dict": column_describe,
                            "group_by_columns": group_by_columns,
                            "entity_description": entity_description,
                            "mappings": mappings,
                            "use_case": use_case,
                        },
                    )
                    logger.info(
                        f"Aggregation suggestions saved to workflow storage: {storage_result.get('files')}"
                    )
                except ImportError:
                    logger.warning("WorkflowStorageManager not available, skipping.")
                except Exception as e:
                    logger.warning(f"Failed to save to workflow storage: {e}")

            return {
                "success": True,
                "result": {
                    "aggregation_suggestions": aggregation_suggestion,
                    "groupby_columns": group_by_columns,
                    "cost_summary_group": cost_summary_group,
                    "cost_summary_aggregation": cost_summary_aggregation,
                    "message": "Aggregation methods suggested and validated successfully.",
                },
                "agent": self.__class__.__name__,
            }
        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Task execution failed: {str(e)}",
                "agent": self.__class__.__name__,
            }
    
    def __call__(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.execute_task(task_data)