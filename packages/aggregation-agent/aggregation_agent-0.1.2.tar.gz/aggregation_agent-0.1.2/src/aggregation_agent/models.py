"""
Data models for the Aggregation Agent

This module contains the core data structures used by the Aggregation Agent
for representing aggregation methods, suggestions, and results.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from enum import Enum


class AggregationMethod(str, Enum):
    """Supported aggregation methods"""
    # Text aggregations
    UNIQUE_COUNT = "Unique Count"
    MODE = "Mode"
    LAST_VALUE = "Last Value"
    
    # Numerical aggregations
    MIN = "Min"
    MAX = "Max"
    SUM = "Sum"
    MEAN = "Mean"
    MEDIAN = "Median"
    
    # Datetime aggregations
    EARLIEST = "Earliest"
    LATEST = "Latest"
    
    # Boolean aggregations
    MOST_FREQUENT = "Most Frequent"


class DataType(str, Enum):
    """Supported data types for aggregation"""
    TEXT = "TEXT"
    NUMERICAL = "NUMERICAL"
    DATETIME = "DATETIME"
    BOOLEAN = "BOOLEAN"
    CATEGORICAL = "CATEGORICAL"


@dataclass
class AggregationSuggestion:
    """Represents a suggested aggregation method for a field"""
    field_name: str
    field_type: DataType
    suggested_methods: List[AggregationMethod]
    confidence_score: float
    reasoning: str
    expected_impact: str
    validation_status: str = "pending"  # "pending", "validated", "failed"
    
    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if suggestion has high confidence"""
        return self.confidence_score >= threshold
    
    def get_methods_summary(self) -> str:
        """Get summary of suggested methods"""
        return ", ".join([method.value for method in self.suggested_methods])


@dataclass
class AggregationResult:
    """Result of aggregation method suggestions"""
    table_name: str
    suggestions: List[AggregationSuggestion]
    total_fields: int
    suggested_fields: int
    high_confidence_suggestions: int
    validation_summary: Dict[str, int]
    recommendations: List[str]
    overall_confidence: float = 0.0
    
    def __post_init__(self):
        """Calculate derived fields"""
        self.total_fields = len(self.suggestions)
        self.suggested_fields = sum(1 for s in self.suggestions if s.suggested_methods)
        self.high_confidence_suggestions = sum(1 for s in self.suggestions if s.is_high_confidence())
        
        # Calculate overall confidence
        if self.total_fields > 0:
            self.overall_confidence = sum(s.confidence_score for s in self.suggestions) / self.total_fields
    
    def get_suggestions_stats(self) -> Dict[str, Any]:
        """Get suggestions statistics"""
        return {
            "total_fields": self.total_fields,
            "suggested_fields": self.suggested_fields,
            "suggestion_coverage": self.suggested_fields / self.total_fields if self.total_fields > 0 else 0,
            "high_confidence_rate": self.high_confidence_suggestions / self.total_fields if self.total_fields > 0 else 0,
            "overall_confidence": self.overall_confidence,
            "validation_passed": self.validation_summary.get("validated", 0),
            "validation_failed": self.validation_summary.get("failed", 0),
            "validation_pending": self.validation_summary.get("pending", 0)
        }


@dataclass
class FieldMapping:
    """Represents a field mapping to standard names"""
    original_name: str
    standard_name: str
    data_type: DataType
    description: str = ""
    confidence: float = 1.0


@dataclass
class TableSchema:
    """Represents a table schema with field information"""
    table_name: str
    fields: List[FieldMapping]
    primary_key: Optional[str] = None
    foreign_keys: List[str] = None
    
    def __post_init__(self):
        if self.foreign_keys is None:
            self.foreign_keys = []
    
    def get_field_by_name(self, field_name: str) -> Optional[FieldMapping]:
        """Get field by name"""
        for field in self.fields:
            if field.original_name == field_name or field.standard_name == field_name:
                return field
        return None
    
    def get_fields_by_type(self, data_type: DataType) -> List[FieldMapping]:
        """Get all fields of a specific type"""
        return [field for field in self.fields if field.data_type == data_type]
