import pytest
import pandas as pd
import json
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from schema_description_agent.agent import SchemaDescriptionAgent
from schema_description_agent.config import SchemaDescriptionConfig
from schema_description_agent.models import SchemaDescription, TableDescription, ColumnDescription

@pytest.fixture
def mock_ai_handler():
    return MagicMock()

@pytest.fixture
def mock_data_loader():
    return MagicMock()

@pytest.fixture
def agent_instance(mock_ai_handler, mock_data_loader):
    with patch('schema_description_agent.agent.SFNAIHandler', return_value=mock_ai_handler):
        with patch('schema_description_agent.agent.SFNDataLoader', return_value=mock_data_loader):
            config = SchemaDescriptionConfig()
            agent = SchemaDescriptionAgent(config=config)
            yield agent

def test_analyze_dataframe(agent_instance):
    data = {'col1': [1, 2, 3], 'col2': ['A', 'B', 'A']}
    df = pd.DataFrame(data)
    analysis = agent_instance._analyze_dataframe(df)
    
    assert analysis['row_count'] == 3
    assert analysis['column_count'] == 2
    assert analysis['total_cells'] == 6
    assert analysis['duplicate_row_count'] == 0
    assert analysis['missing_cells_total'] == 0
    assert len(analysis['column_details']) == 2
    assert analysis['column_details'][0]['name'] == 'col1'
    assert analysis['column_details'][1]['name'] == 'col2'

def test_generate_table_description(agent_instance):
    mock_response = {
        "tables": [{
            "table_name": "test_table",
            "description": "A test table.",
            "columns": [{"name": "col1", "description": "Column 1."}]
        }]
    }
    agent_instance.ai_handler.route_to.return_value = (json.dumps(mock_response), {"cost": 0.01})
    
    data = {'col1': [1, 2, 3]}
    df = pd.DataFrame(data)
    
    result, _ = agent_instance.generate_table_description(df, metadata=None, table_name=None, schema=None)
    
    assert result.tables is not None
    assert len(result.tables) == 1
    assert result.tables[0].table_name == "test_table"

def test_execute_task_success(agent_instance):
    mock_df = pd.DataFrame({'col1': [1, 2, 3]})
    agent_instance.data_loader.execute_task.return_value = mock_df
    
    mock_description = SchemaDescription(
        tables=[
            TableDescription(
                table_name="test_table",
                description="A test table.",
                columns=[ColumnDescription(name="col1", description="Column 1.")]
            )
        ]
    )

    with patch.object(agent_instance, 'generate_table_description', return_value=(mock_description, {"cost": 0.01})) as mock_generate:
        task_data = {'file': 'dummy_path.csv'}
        result = agent_instance.execute_task(task_data)
        
        assert result['success']
        assert 'result' in result
        assert result['result']['table description'] == mock_description.model_dump()

def test_execute_task_no_file(agent_instance):
    task_data = {}
    result = agent_instance.execute_task(task_data)
    
    assert not result['success']
    assert result['error'] == "No valid 'file' provided in task data."

def test_execute_task_load_fail(agent_instance):
    agent_instance.data_loader.execute_task.return_value = None
    
    task_data = {'file': 'dummy_path.csv'}
    result = agent_instance.execute_task(task_data)
    
    assert not result['success']
    assert result['error'] == "Failed to load DataFrame from file."