from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sfn_blueprint import MODEL_CONFIG

# Centralized AI Provider configuration
DEFAULT_AI_PROVIDER = "openai"
DEFAULT_AI_TASK_TYPE = "suggestions_generator"

# Use centralized sfn_blueprint configuration
MODEL_CONFIG["aggregation_suggestions"] = {
    "model": "gpt-4o-mini",  # Will be overridden by sfn_blueprint centralized config
    "temperature": 0.3,
    "max_tokens": 1000,
    "n": 1,
    "stop": None,
}

MODEL_CONFIG["column_mapping"] = {
    "model": "gpt-4o-mini",  # Will be overridden by sfn_blueprint centralized config
    "temperature": 0.3,
    "max_tokens": 500,
    "n": 1,
    "stop": None,
}


class AggregationConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    aggregation_ai_provider: str = Field(
        default="openai", description="AI provider to use"
    )
    aggregation_model: str = Field(default="gpt-4o", description="AI model to use")
    temperature: float = Field(
        default=0.3, ge=0.0, le=2.0, description="AI model temperature"
    )
    max_tokens: int = Field(
        default=4000, ge=100, le=8000, description="Maximum tokens for AI response"
    )
    group_by_model: str = Field(
        default="gpt-4o", description="AI model for column mapping"
    )
    group_by_ai_provider: str = Field(
        default="openai", description="AI provider for column mapping"
    )


NUMERICAL_DATA_TYPES = [
    "bigint",
    "bigserial",
    "byteint",
    "decimal",
    "double precision",
    "double",
    "float",
    "float4",
    "float64",
    "float8",
    "int",
    "int4",
    "int64",
    "int8",
    "integer",
    "number",
    "numeric",
    "real",
    "serial",
    "smallint",
    "smallserial",
]


DEFAULT_NUMERIC_AGGREGATIONS = {
    "min": {"name": "min", "enabled": True, "checked": False, "mandatory": False},
    "max": {"name": "max", "enabled": True, "checked": False, "mandatory": False},
    "unique_count": {
        "name": "unique_count",
        "enabled": False,
        "checked": False,
        "mandatory": False,
    },
    "sum": {"name": "sum", "enabled": True, "checked": False, "mandatory": False},
    "mean": {"name": "mean", "enabled": True, "checked": False, "mandatory": False},
    "median": {"name": "median", "enabled": True, "checked": False, "mandatory": False},
    "mode": {"name": "mode", "enabled": True, "checked": False, "mandatory": False},
    "last_value": {
        "name": "last_value",
        "enabled": True,
        "checked": False,
        "mandatory": False,
    },
    "pivot": {"name": "pivot", "enabled": False, "checked": False, "mandatory": False},
}

DATETIME_DATA_TYPES = [
    "timestamp without time zone",
    "timestamp with time zone",
    "date",
    "time",
    "timestamp",
    "time without time zone",
    "time with time zone",
    "interval",
]

DEFAULT_DATETIME_AGGREGATIONS = {
    "min": {"name": "min", "enabled": True, "checked": False, "mandatory": False},
    "max": {"name": "max", "enabled": True, "checked": False, "mandatory": False},
    "unique_count": {
        "name": "unique_count",
        "enabled": False,
        "checked": False,
        "mandatory": False,
    },
    "sum": {"name": "sum", "enabled": False, "checked": False, "mandatory": False},
    "mean": {"name": "mean", "enabled": False, "checked": False, "mandatory": False},
    "median": {
        "name": "median",
        "enabled": False,
        "checked": False,
        "mandatory": False,
    },
    "mode": {"name": "mode", "enabled": False, "checked": False, "mandatory": False},
    "last_value": {
        "name": "last_value",
        "enabled": False,
        "checked": False,
        "mandatory": False,
    },
    "pivot": {"name": "pivot", "enabled": False, "checked": False, "mandatory": False},
}

BOOLEAN_DATA_TYPES = ["boolean", "bool"]

DEFAULT_BOOLEAN_AGGREGATIONS = {
    "min": {"name": "min", "enabled": False, "checked": False, "mandatory": False},
    "max": {"name": "max", "enabled": False, "checked": False, "mandatory": False},
    "unique_count": {
        "name": "unique_count",
        "enabled": False,
        "checked": False,
        "mandatory": False,
    },
    "sum": {"name": "sum", "enabled": False, "checked": False, "mandatory": False},
    "mean": {"name": "mean", "enabled": False, "checked": False, "mandatory": False},
    "median": {
        "name": "median",
        "enabled": False,
        "checked": False,
        "mandatory": False,
    },
    "mode": {"name": "mode", "enabled": True, "checked": False, "mandatory": False},
    "last_value": {
        "name": "last_value",
        "enabled": True,
        "checked": False,
        "mandatory": False,
    },
    "pivot": {"name": "pivot", "enabled": False, "checked": False, "mandatory": False},
}


DEFAULT_TEXT_AGGREGATIONS = {
    "min": {"name": "min", "enabled": False, "checked": False, "mandatory": False},
    "max": {"name": "max", "enabled": False, "checked": False, "mandatory": False},
    "unique_count": {
        "name": "unique_count",
        "enabled": True,
        "checked": False,
        "mandatory": False,
    },
    "sum": {"name": "sum", "enabled": False, "checked": False, "mandatory": False},
    "mean": {"name": "mean", "enabled": False, "checked": False, "mandatory": False},
    "median": {
        "name": "median",
        "enabled": False,
        "checked": False,
        "mandatory": False,
    },
    "mode": {"name": "mode", "enabled": True, "checked": False, "mandatory": False},
    "last_value": {
        "name": "last_value",
        "enabled": True,
        "checked": False,
        "mandatory": False,
    },
    "pivot": {"name": "pivot", "enabled": True, "checked": False, "mandatory": False},
}
