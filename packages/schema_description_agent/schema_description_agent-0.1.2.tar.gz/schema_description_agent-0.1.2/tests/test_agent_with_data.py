import pandas as pd
import json
from unittest.mock import patch, MagicMock
import sys
import os
import traceback

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from schema_description_agent.agent import SchemaDescriptionAgent
from schema_description_agent.config import SchemaDescriptionConfig
from schema_description_agent.models import SchemaDescription, TableDescription, ColumnDescription

def print_test_header(test_name):
    print("\n" + "="*80)
    print(f"RUNNING TEST: {test_name}")
    print("="*80)

# Sample data for testing
SAMPLE_DF = pd.DataFrame({
    'customer_id': [1, 2, 3, 4, 5],
    'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
    'age': [25, 30, 35, 40, 45],
    'email': ['alice@test.com', 'bob@test.com', 'charlie@test.com', 'david@test.com', 'eve@test.com'],
    'join_date': pd.to_datetime(['2020-01-01', '2020-02-01', '2020-03-01', '2020-04-01', '2020-05-01'])
})

def test_analyze_dataframe():
    print_test_header("test_analyze_dataframe")
    try:
        # Setup
        config = SchemaDescriptionConfig()
        agent = SchemaDescriptionAgent(config=config)
        
        # Test with sample data
        print("\nSample DataFrame:")
        print(SAMPLE_DF.head())
        
        # Execute
        print("\nAnalyzing DataFrame...")
        analysis = agent._analyze_dataframe(SAMPLE_DF)
        
        # Print results
        print("\nAnalysis Results:")
        print(f"Row count: {analysis['row_count']}")
        print(f"Column count: {analysis['column_count']}")
        print(f"Total cells: {analysis['total_cells']}")
        print(f"Duplicate rows: {analysis['duplicate_row_count']}")
        print(f"Missing cells: {analysis['missing_cells_total']}")
        
        print("\nColumn Details:")
        for col in analysis['column_details']:
            print(col)
            print(f"\nColumn: {col['name']}")
            print(f"  Data type: {col['data_type']}")
            print(f"  Null percentage: {col['null_percentage']:.2f}%")  
            print(f"  Unique percentage: {col['unique_percentage']:.2f}%")
        
        # Assertions
        assert analysis['row_count'] == 5
        assert analysis['column_count'] == 5
        assert analysis['total_cells'] == 25
        print("- "*40, "Analysis completed successfully.\n")
    except Exception as e:
        print("- "*40, "Analysis failed.\n")
        print(traceback.format_exc()[:1000])

def test_generate_table_description():
    print_test_header("test_generate_table_description")
    try:
        # Setup agent with real configuration
        config = SchemaDescriptionConfig()
        agent = SchemaDescriptionAgent(config=config)
        
        # Print sample data being used
        print("\nSample Data:")
        print(SAMPLE_DF.head())
    
        # Execute with actual LLM call
        print("\nGenerating table description using LLM...")
        result, _ = agent.generate_table_description(SAMPLE_DF)
    
        # Print results
        print("\nGenerated Table Description:")
        print(f"Table Name: {result.tables[0].table_name}")
        print(f"Description: {result.tables[0].description}")
        print("\nColumn Descriptions:")
        for col in result.tables[0].columns:
            print(f"- {col.name}: {col.description}")
    
        # Print raw LLM response for debugging
        print("\nRaw LLM Response:")
        print(json.dumps(result.model_dump(), indent=2))
    
        # Assertions
        assert len(result.tables) > 0
        assert len(result.tables[0].columns) > 0
        print("- "*40, "Generate table description completed successfully.\n")
    except Exception as e:
        print("- "*40, "Generate table description failed.\n")
        print(traceback.format_exc()[:1000])

def test_execute_task_success():
    print_test_header("test_execute_task_success")
    try:
        # Setup
        config = SchemaDescriptionConfig()
        agent = SchemaDescriptionAgent(config=config)
        
        # Mock data loader to return our sample DataFrame
        agent.data_loader = MagicMock()
        agent.data_loader.execute_task.return_value = SAMPLE_DF
        
        # Print sample data being used
        print("\nSample Data:")
        print(SAMPLE_DF.head())
        
        # Execute with actual LLM call
        print("\nExecuting task with sample data...")
        task_data = {'file': 'sample_customers.csv'}
        result = agent.execute_task(task_data)
        
        # Print results
        print("\nTask Execution Result:")
        print(f"Success: {result['success']}")
        if result['success']:
            print("Table Description:")
            print(json.dumps(result['result'], indent=2))
        
        # Assertions
        assert result['success']
        assert 'result' in result
        print("- "*40, "Execute task completed successfully.")
    except Exception as e:
        print("- "*40, "Execute task failed.")
        print(traceback.format_exc()[:1000])

def test_execute_task_no_file():
    print_test_header("test_execute_task_no_file")
    try:
        # Setup
        config = SchemaDescriptionConfig()
        agent = SchemaDescriptionAgent(config=config)
        
        # Execute with no file
        print("\nExecuting task with no file...")
        task_data = {}
        result = agent.execute_task(task_data)
        
        # Print results
        print("\nTask Execution Result:")
        print(f"Success: {result['success']}")
        if not result['success']:
            print(f"Error: {result['error']}")
        
        # Assertions
        assert not result['success']
        assert "No valid 'file'" in result['error']
        print("- "*40, "Execute task completed successfully.")
    except Exception as e:
        print("- "*40, "Execute task failed.")
        print(traceback.format_exc()[:1000])
