import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
import json  # <--- THIS LINE WAS MISSING
from aggregation_agent.agent import AggregationAgent
from aggregation_agent.config import AggregationConfig
from sfn_blueprint.utils.data_loader import SFNDataLoader

@pytest.fixture
def agent():
    """Fixture to create an AggregationAgent with a mock config."""
    # The patch ensures that when AggregationAgent is initialized,
    # its self.ai_handler becomes a mock instance.
    with patch('aggregation_agent.agent.SFNAIHandler'):
        config = AggregationConfig(
            aggregation_ai_provider="mock_provider",
            group_by_ai_provider="mock_provider",
            aggregation_model="mock_model",
            group_by_model="mock_model",
        )
        agent = AggregationAgent(config=config)
        yield agent
def test_get_column_category(agent):
    """Test the get_column_category method."""
    assert agent.get_column_category("int64") == "NUMERICAL"
    assert agent.get_column_category("float64") == "NUMERICAL"
    assert agent.get_column_category("datetime64[ns]") == "DATETIME"
    assert agent.get_column_category("bool") == "BOOLEAN"
    assert agent.get_column_category("object") == "TEXT"
    assert agent.get_column_category("category") == "TEXT"

def test_clean_json_string(agent):
    """Test the _clean_json_string method."""
    json_string = '```json\n{"key": [{"method": "Sum"}]}\n```'
    data_df = pd.DataFrame({'key': [1]})
    dtype_dict = {'key': 'NUMERICAL'}
    agent.allowed_methods['NUMERICAL'] = ['Sum'] # Ensure 'Sum' is an allowed method
    cleaned_json = agent._clean_json_string(json_string, data_df, dtype_dict)
    assert cleaned_json == {'key': [{'method': 'Sum'}]}

    # Test with invalid JSON
    with pytest.raises(ValueError):
        agent._clean_json_string("not a json string", data_df, dtype_dict)

def test_get_dataframe_metadata(agent):
    """Test the _get_dataframe_metadata method."""
    data = {
        'col1': [1, 2, 3, 4, 5],
        'col2': ['A', 'B', 'A', 'C', 'B'],
        'col3': [1.1, 2.2, 3.3, 4.4, 5.5],
        'col4': [True, False, True, True, False],
        'col5': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05'])
    }
    df = pd.DataFrame(data)
    metadata = agent._get_dataframe_metadata(df)

    assert metadata['table_info']['row_count'] == 5
    assert 'col1' in metadata['table_columns_info']
    assert metadata['table_columns_info']['col1']['data_type'] == 'Int64'
    assert metadata['table_columns_info']['col2']['distinct_count'] == 3



@patch.object(SFNDataLoader, 'execute_task')
def test_execute_task_no_groupby(mock_execute_task, agent):
    """Test execute_task when the LLM fails to suggest a group-by column."""
    mock_df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
    mock_execute_task.return_value = mock_df

    with patch('aggregation_agent.agent.SFNAIHandler') as mock_ai_handler:
        # Simulate LLM returning an empty list for group-by (as a JSON string)
        mock_ai_handler.return_value.route_to.return_value = (json.dumps([]), 0.1)

        task_data = {
            "file": "dummy.csv", "domain_name": "test", "domain_description": "test",
            "column_description": {}, "entity_description": {}, "mappings": {}, "table_category": "test"
        }

        result = agent.execute_task(task_data)
        assert not result['success']
        assert "Task execution failed: not enough values to unpack (expected 2, got 0)" in result['error']

