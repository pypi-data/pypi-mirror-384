"""
StepFn Aggregation Agent Package

A modular, LLM-driven data aggregation agent that provides intelligent
aggregation strategies and column mapping recommendations.

Features:
- LLM-driven aggregation strategy selection
- Intelligent column mapping suggestions
- Centralized sfn_blueprint integration
- Configurable AI provider management
- Independent usage or orchestrator integration
"""

from .agent import AggregationAgent
from .column_mapping_agent import SFNColumnMappingAgent
from .config import DEFAULT_AI_PROVIDER, DEFAULT_AI_TASK_TYPE

__version__ = "0.1.0"
__author__ = "StepFn AI"
__email__ = "rajesh@stepfunction.ai"

__all__ = [
    "AggregationAgent",
    "SFNColumnMappingAgent", 
    "DEFAULT_AI_PROVIDER",
    "DEFAULT_AI_TASK_TYPE"
]
