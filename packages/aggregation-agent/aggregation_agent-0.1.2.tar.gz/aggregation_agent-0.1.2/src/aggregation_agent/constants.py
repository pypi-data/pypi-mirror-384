"""
Prompt Constants for AggregationAgent

This file contains all prompts used by the AggregationAgent.
All prompts are centralized here for easy review and maintenance.

Prompt Types:
- PROMPT_TEMPLATE_*: Templates for dynamic content formatting
- SYSTEM_PROMPT_*: Role definitions and system instructions
"""

# =============================================================================
# PROMPT TEMPLATES
# =============================================================================

PROMPT_TEMPLATE_AGGREGATION_SUGGESTION = """
You are an expert data scientist specializing in feature aggregation.

I need you to suggest the most appropriate aggregation methods for each feature in a dataset
that will be grouped by certain fields. For each feature, suggest 1-3 different aggregation methods 
that would provide valuable information for the problem type.

Table Schema:
{table_schema}

Field Mappings (standard names):
{field_mappings}

Problem Type: {problem_type}

Group By Fields: {group_by_fields}

{additional_context_section}
For each field (except the group-by fields), suggest 1-3 aggregation methods that would be most 
informative for this problem type. Include a brief explanation of why each method is useful.

Available aggregation methods by data type:
- TEXT fields: Unique Count, Mode, Last Value
- NUMERICAL fields: Min, Max, Sum, Mean, Median, Mode, Last Value
- DATETIME fields: Min, Max
- BOOLEAN fields: Mode, Last Value

Return your suggestions as a JSON object where:
- Keys are the field names
- Values are arrays of objects, each containing:
    - "method": The suggested aggregation method
    - "explanation": Why this method is useful for this field and problem

Example response:
{{
    "purchase_amount": [
        {{
        "method": "Sum",
        "explanation": "Total purchase amount helps predict customer lifetime value"
        }},
        {{
        "method": "Mean",
        "explanation": "Average purchase amount indicates spending habits"
        }}
    ],
    "product_category": [
        {{
        "method": "Mode",
        "explanation": "Most common category shows customer preferences"
        }}
    ]
}}

Only include fields that should be aggregated (exclude group-by fields).
"""


PROMPT_TEMPLATE_GOLDEN_WIZARD_GROUP_BY_COLUMNS = """
You are an expert data analysis assistant designed to suggest most appropriate GROUP BY fields for a dataset.
Based on the following inputs, suggest the most appropriate GROUP BY fields:

1. Sample Data: {sample_data}
2. Statistical Metadata: {meta_data} (Contains count, unique values, mean, std, min, max, and percentiles for numeric columns)
3. Column Mappings: {mappings} (Note: This maps standard column names to actual input data column names)
4. Business Domain: {business_domain}
5. Table Entity: {table_category}
6. Entity Name and description: {entity_description}

Guidelines for suggesting group by fields:
1. Always include ID-like fields that appear to be unique identifiers (e.g., customer_id, account_id)
2. Include date fields if the data appears to be time series (e.g., transaction_date, created_at)
3. Include product_id or similar entity identifier fields if present.
4. Only include a categorical field if it is clearly meaningful and useful for aggregation for this specific entity. - Do NOT include fields that are merely descriptive, labels, or status-type fields. - If no categorical field is clearly relevant, do NOT include any categorical field.
5. Strictly select group by keys that are commonly used in this business domain, and leverage the entity description to choose fields that are meaningful for this specific entity.
    -Example: for Billing → ['billing_id', 'billing_date']; for Customer → ['customer_id', 'signup_date', 'region']."
6. Suggest the **smallest possible set of GROUP BY fields** (1 to 3 fields) that still result in meaningful aggregations.


IMPORTANT RULES:
1. ALWAYS use the actual input data column names from the sample data, NOT the standard column names
2. Use the column mappings to understand which input columns represent IDs, dates, or product identifiers
3. Only suggest columns that exist in the sample data
4. Do not suggest any columns that are not present in the input data
5. Use the statistical metadata to identify potential ID fields (high unique_count relative to count) and date fields (sequential min/max values)
6. Avoid suggesting continuous numeric fields or irrelevant categorical fields.
7. Always prioritize fields that are meaningful for the specific entity and consistent with the business domain.

Return ONLY a list of input data column names, nothing else.
Output must be in this exact format:
1.Example (valid):
["customer_id", "transaction_date"]

2.Example (valid, max 3 fields):
["billing_id", "billing_date", "product_id"]

3.Example (invalid, too many):
["customer_id", "transaction_date", "product_id", "region"]
"""

PROMPT_TEMPLATE_OTHER_WIZARD_GROUP_BY_COLUMNS = """
You are an expert data analysis assistant designed to suggest most appropriate GROUP BY fields for a dataset.
Based on the following inputs, suggest the most appropriate GROUP BY fields:

1. Use Case and Description: {use_case}
2. Modelling Approach:
3. Business Domain and it's description: {business_domain}
4. Entity Name and description: {entity_description}
5. Column names and Descriptions: {column_descriptions}
6. Sample Data (first 10 rows): {sample_data}
7. Statistical Metadata: {meta_data} (Contains row count, distinct count, null fraction, mean, std, min, max, etc. for numeric columns)
8. Column Mappings: {mappings} (Note: This maps standard column names to actual input data column names)

### Decision Process:
1. **Granularity Check**
    - Determine current dataset granularity from metadata + sample.
    - Infer target granularity from use case, description, and modelling approach.
    - If dataset granularity **matches use case granularity** → Return: `"No aggregation required; dataset is already at target granularity."`
    - If dataset granularity is **finer than use case granularity** → Proceed with groupby fields suggestions.

2. **Guidelines for suggesting group by fields: (when aggregation is required)**
    - When suggesting groupby fields, consider the use case description to identify which column(s) are relevant for the target metric. Only include those columns that are meaningful to the use case.
    - Always include ID-like fields that appear to be unique identifiers (e.g., customer_id, account_id)
    - Include date fields if time-based grouping is required (e.g., transaction_date → month).
    - Include entity/product identifiers if relevant.
    - Only include categorical fields if they are clearly meaningful for the business entity. -Do NOT include fields that are merely descriptive, labels, or status-type fields. - If no categorical field is clearly relevant, do NOT include any categorical field.
    - Strictly use the **minimum number of fields** (1 - 3) that produce meaningful aggregations.
    - Always use actual column names from the sample data.

IMPORTANT RULES:
1. ALWAYS use the actual input data column names from the sample data, NOT the standard column names
2. Use the column mappings to understand which input columns represent IDs, dates, or product identifiers
3. Only suggest columns that exist in the sample data
4. Do not suggest any columns that are not present in the input data
5. Use the statistical metadata to identify potential ID fields (high unique_count relative to count) and date fields (sequential min/max values)
6. Avoid suggesting continuous numeric fields or irrelevant categorical fields.
7. Always prioritize fields that are meaningful for the specific entity and consistent with the business domain.
8. Ensure selected fields are meaningful for aggregation and **can serve as potential join keys in future**.

Return ONLY a list of input data column names, nothing else.
Output must be in this exact format:
1.Example (valid):
["customer_id", "transaction_date"]

2.Example (valid, max 3 fields):
["billing_id", "billing_date", "product_id"]

3.Example (invalid, too many):
["customer_id", "transaction_date", "product_id", "region"]
"""

SYSTEM_PROMPT_GROUP_BY_COLUMNS_WIZARD = "You are an expert data analysis assistant that outputs only JSON arrays of GROUP BY field names for aggregation. Select the appropriate GROUP BY fields that are meaningful for the entity, relevant to the business domain, and follow all user-specified rules."

SYSTEM_PROMPT_WIZARD_AGGREGATION_SUGGESTION = (
    "You are a helpful assistant designed to output JSON."
)

PROMPT_TEMPLATE_GOLDEN_WIZARD_AGGREGATION_SUGGESTION = """You are designed to recommend aggregation methods to a set of
features present in the dataset and provide explanations for each suggestion.
The suggestions and explanations will be based on four key factors:
1. Data types of the features.
2. Sample data.
3. Statistical summary of the numeric columns.
4. Column descriptions.

Make sure to remove these fields in the output JSON as these fields will be used for grouping and thus do not need aggregation suggestions.

Exemption : Always suggest 'Unique Count' aggregation for **ID-like columns** irrespective of considering datatype or any statistics. ID-like columns typically include those that have "ID" (e.g., accountid, customer_id, productID). These columns are typically used to uniquely identify entities, and counting distinct values is the most meaningful aggregation for such columns.
**ID RECOGNITION HINT**
To ensure consistency, apply the following logic to determine ID-like columns:
    - Any column name that contains "ID", "Id", or "id" (case-insensitive).
ID-like columns uniquely identify entities, and counting distinct values provides key insights.

***AGGREGATION SUGGESTION AND EXPLANATIONS***
*1. Understand data types from the feature_dtype_dict dictionary: {feature_dtype_dict}
    - If Dtype is TEXT, suggest aggregation methods from ['Unique Count','Mode','Last Value'].
    - If Dtype is NUMERICAL, suggest aggregation methods from ['Min','Max','Sum','Mean','Median','Mode','Last Value'].
    - If Dtype is DATETIME, suggest aggregation methods from ['Max', 'Min'].
    - If Dtype is BOOLEAN, suggest aggregation methods from ['Mode','Last Value'].

*2. Understand distributions of the numerical fields from describe_dict: {df_describe_dict},
and feature names and their sample values from {sample_data_dict},
and textual descriptions from column_text_describe_dict: {column_text_describe_dict},

**NOTE**
* Suggest methods like "Min" or "Max" when you think aggregating on extremes of the values can be a useful feature.
* To capture the central tendency of a feature, suggest "Median" when data is skewed; otherwise, suggest "Mean" when data is normally distributed.
* Do not suggest the same set of aggregation methods for every feature.
* For TEXT data types, suggest 'Last Value' only when aggregating the last value can be useful for model understanding.
* Consider one feature at a time while suggesting. Avoid suggesting the same set of aggregation methods for features of the same datatype.
* Provide concise, precise, and assertive explanations in the present tense. Avoid using redundant words and ensure the explanation fits a hover-over text style.

**NOTE**
1. NEVER suggest the exact same set of aggregation methods for all features in the output.
2. Try to suggest aggregation methods for as many features as possible, both numerical and non-numerical.
3. Restrict suggestions to 2-3 methods per feature at most.
4. NEVER change the output format. Keys should be feature names, and values should be a list of dictionaries containing aggregation methods and explanations.
5. consider suggesting 'Unique Count' for other columns also where the it may offer meaningful insights.
6. You are to respond **ONLY in valid JSON format** strictly.
**EXAMPLE OUTPUT FORMAT**
{{
    "Feature1": [
        {{"method": "Mean", "explanation": "Explanation for suggesting Mean"}},
        {{"method": "Median", "explanation": "Explanation for suggesting Median"}}
    ],
    "Feature2": [
        {{"method": "Last Value", "explanation": "Explanation for suggesting Last Value"}}
    ]
}}
"""

PROMPT_TEMPLATE_OTHER_WIZARD_AGGREGATION_SUGGESTION = """You are designed to recommend aggregation methods to a set of
features present in the dataset and provide explanations for each suggestion.
The suggestions and explanations will be based on four key factors:
1.GroupBy Fields (These fields define the dataset's grain and must NEVER be aggregated.): {group_by_columns}
2. Use Case and Description {use_case}
3. Modelling Approach
4. Column names and description. {column_text_describe_dict}
5. Data types of the features. {feature_dtype_dict}
6. Sample data (first 10 rows). {sample_data_dict}
7. Statistical summary of the numeric columns. {df_describe_dict}

***AGGREGATION SUGGESTION AND EXPLANATIONS***
1. **Never suggest aggregation for the provided GroupBy fields.**
2. **Always suggest 'Unique Count' for ID-like columns** (any name containing "ID", "Id", or "id"), 
regardless of data type or statistics.

3. Suggest aggregation methods according to data type:
        - If Dtype is TEXT, suggest aggregation methods from ['Unique Count','Mode','Last Value'].
        - If Dtype is NUMERICAL, suggest aggregation methods from ['Min','Max','Sum','Mean','Median','Mode','Last Value'].
        - If Dtype is DATETIME, suggest aggregation methods from ['Max', 'Min'].
        - If Dtype is BOOLEAN, suggest aggregation methods from ['Mode','Last Value'].

4.  Use case & modelling approach guidance:
    - Classification/Regression → focus on summarizing entity-level behavior (Mean, Median, Unique Count).
    - Clustering/Segmentation → capture variation/diversity (Mean, Std, Unique Count).
    - Time Series Forecasting → highlight temporal trends/extremes (Sum, Min, Max).
    - Anomaly Detection → highlight deviations/outliers (Max, Min, Unique Count).

**NOTE**
* Suggest methods like "Min" or "Max" when you think aggregating on extremes of the values can be a useful feature.
* To capture the central tendency of a feature, suggest "Median" when data is skewed; otherwise, suggest "Mean" when data is normally distributed.
* Do not suggest the same set of aggregation methods for every feature.
* For TEXT data types, suggest 'Last Value' only when aggregating the last value can be useful for model understanding.
* Consider one feature at a time while suggesting. Avoid suggesting the same set of aggregation methods for features of the same datatype.
* Provide concise, precise, and assertive explanations in the present tense. Avoid using redundant words and ensure the explanation fits a hover-over text style.

**Important**
1. NEVER suggest the exact same set of aggregation methods for all features in the output.
2. Try to suggest aggregation methods for as many features as possible, both numerical and non-numerical.
3. Restrict suggestions to 2-3 methods per feature at most.
4. NEVER change the output format. Keys should be feature names, and values should be a list of dictionaries containing aggregation methods and explanations.
5. consider suggesting 'Unique Count' for other columns also where the it may offer meaningful insights.
6. You are to respond **ONLY in valid JSON format** strictly.
**EXAMPLE OUTPUT FORMAT**
{{
    "Feature1": [
        {{"method": "Mean", "explanation": "Explanation for suggesting Mean"}},
        {{"method": "Median", "explanation": "Explanation for suggesting Median"}}
    ],
    "Feature2": [
        {{"method": "Last Value", "explanation": "Explanation for suggesting Last Value"}}
        ...
    ]
    ...
}}
"""
# =============================================================================
# PROMPT FORMATTING FUNCTIONS
# =============================================================================


def format_other_wizard_aggregation_suggestion_prompt(
    group_by_columns: str,
    use_case: str,
    column_text_describe_dict: str,
    feature_dtype_dict: str,
    sample_data_dict: str,
    df_describe_dict: str,
):
    user_prompt = PROMPT_TEMPLATE_OTHER_WIZARD_AGGREGATION_SUGGESTION.format(
        group_by_columns=group_by_columns,
        use_case=use_case,
        column_text_describe_dict=column_text_describe_dict,
        feature_dtype_dict=feature_dtype_dict,
        sample_data_dict=sample_data_dict,
        df_describe_dict=df_describe_dict,
    )
    return SYSTEM_PROMPT_WIZARD_AGGREGATION_SUGGESTION, user_prompt


def format_golden_wizard_aggregation_suggestion_prompt(
    feature_dtype_dict: str,
    df_describe_dict: str,
    sample_data_dict: str,
    column_text_describe_dict: str,
):
    user_prompt = PROMPT_TEMPLATE_GOLDEN_WIZARD_AGGREGATION_SUGGESTION.format(
        feature_dtype_dict=feature_dtype_dict,
        df_describe_dict=df_describe_dict,
        sample_data_dict=sample_data_dict,
        column_text_describe_dict=column_text_describe_dict,
    )
    return SYSTEM_PROMPT_WIZARD_AGGREGATION_SUGGESTION, user_prompt


def format_group_by_columns_prompt_golden_wizard(
    sample_data: str,
    meta_data: str,
    mappings: str,
    business_domain: str,
    table_category: str,
    entity_description: str,
):

    user_prompt = PROMPT_TEMPLATE_GOLDEN_WIZARD_GROUP_BY_COLUMNS.format(
        sample_data=sample_data,
        meta_data=meta_data,
        mappings=mappings,
        business_domain=business_domain,
        table_category=table_category,
        entity_description=entity_description,
    )
    return SYSTEM_PROMPT_GROUP_BY_COLUMNS_WIZARD, user_prompt


def format_other_wizard_group_by_columns(
    use_case: str,
    business_domain: str,
    entity_description: str,
    column_descriptions: str,
    sample_data: str,
    meta_data: str,
    mappings: str,
):
    user_prompt = PROMPT_TEMPLATE_OTHER_WIZARD_GROUP_BY_COLUMNS.format(
        use_case=use_case,
        business_domain=business_domain,
        entity_description=entity_description,
        column_descriptions=column_descriptions,
        sample_data=sample_data,
        meta_data=meta_data,
        mappings=mappings,
    )
    return SYSTEM_PROMPT_GROUP_BY_COLUMNS_WIZARD, user_prompt


def format_aggregation_suggestion_prompt(
    table_schema: dict,
    field_mappings: dict,
    problem_type: str,
    group_by_fields: list,
    additional_context: dict = None,
) -> str:
    """
    Format the aggregation suggestion prompt with the provided parameters.

    Args:
        table_schema: Schema of the table with field types
        field_mappings: Mappings of fields to standard names
        problem_type: Type of problem (regression, classification, etc.)
        group_by_fields: Fields that will be used for grouping
        additional_context: Additional context about the problem (optional)

    Returns:
        Formatted prompt string
    """
    import json

    # Format the additional context section
    additional_context_section = ""

    if additional_context:
        additional_context_section = f"""
Additional Context:
{json.dumps(additional_context, indent=2)}
"""

    return PROMPT_TEMPLATE_AGGREGATION_SUGGESTION.format(
        table_schema=json.dumps(table_schema, indent=2),
        field_mappings=json.dumps(field_mappings, indent=2),
        problem_type=problem_type,
        group_by_fields=", ".join(group_by_fields),
        additional_context_section=additional_context_section,
    )
