
import pytest
from aggregation_agent.models import (
    AggregationMethod,
    AggregationSuggestion,
    DataType,
    AggregationResult,
    FieldMapping,
    TableSchema,
)


def test_aggregation_suggestion():
    suggestion = AggregationSuggestion(
        field_name="purchase_amount",
        field_type=DataType.NUMERICAL,
        suggested_methods=[AggregationMethod.SUM, AggregationMethod.MEAN],
        confidence_score=0.9,
        reasoning="Test reasoning",
        expected_impact="Test impact",
    )
    assert suggestion.is_high_confidence(threshold=0.8)
    assert not suggestion.is_high_confidence(threshold=0.95)
    assert suggestion.get_methods_summary() == "Sum, Mean"


def test_aggregation_result():
    suggestions = [
        AggregationSuggestion(
            field_name="purchase_amount",
            field_type=DataType.NUMERICAL,
            suggested_methods=[AggregationMethod.SUM],
            confidence_score=0.9,
            reasoning="",
            expected_impact="",
        ),
        AggregationSuggestion(
            field_name="product_category",
            field_type=DataType.CATEGORICAL,
            suggested_methods=[],
            confidence_score=0.5,
            reasoning="",
            expected_impact="",
        ),
    ]
    result = AggregationResult(
        table_name="sales",
        suggestions=suggestions,
        total_fields=0,  # This will be recalculated
        suggested_fields=0,  # This will be recalculated
        high_confidence_suggestions=0,  # This will be recalculated
        validation_summary={"validated": 0, "failed": 0, "pending": 2},
        recommendations=[],
    )
    assert result.total_fields == 2
    assert result.suggested_fields == 1
    assert result.high_confidence_suggestions == 1
    assert result.overall_confidence == (0.9 + 0.5) / 2

    stats = result.get_suggestions_stats()
    assert stats["total_fields"] == 2
    assert stats["suggested_fields"] == 1
    assert stats["suggestion_coverage"] == 0.5
    assert stats["high_confidence_rate"] == 0.5
    assert stats["overall_confidence"] == 0.7
    assert stats["validation_passed"] == 0
    assert stats["validation_failed"] == 0
    assert stats["validation_pending"] == 2


def test_table_schema():
    fields = [
        FieldMapping(
            original_name="cust_id",
            standard_name="customer_id",
            data_type=DataType.NUMERICAL,
        ),
        FieldMapping(
            original_name="email",
            standard_name="email_address",
            data_type=DataType.TEXT,
        ),
    ]
    schema = TableSchema(
        table_name="customers", fields=fields, primary_key="customer_id"
    )

    assert schema.get_field_by_name("cust_id").standard_name == "customer_id"
    assert schema.get_field_by_name("customer_id").original_name == "cust_id"
    assert schema.get_field_by_name("non_existent") is None

    numerical_fields = schema.get_fields_by_type(DataType.NUMERICAL)
    assert len(numerical_fields) == 1
    assert numerical_fields[0].standard_name == "customer_id"

    text_fields = schema.get_fields_by_type(DataType.TEXT)
    assert len(text_fields) == 1
    assert text_fields[0].standard_name == "email_address"

    assert len(schema.get_fields_by_type(DataType.DATETIME)) == 0
