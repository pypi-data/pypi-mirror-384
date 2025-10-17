"""
Integration tests for the MappingAgent class
"""
import pytest
import traceback
from unittest.mock import MagicMock, patch
from mapping_agent.agent import MappingAgent
from mapping_agent.models import CanonicalMappings, MappingEntry

def test_agent_initialization():
    """Test that the agent initializes correctly"""
    try:
        print("\n\nTesting agent initialization...")
        agent = MappingAgent()
        assert agent is not None
        assert agent.config is not None
        assert agent.logger is not None
        print("✓ Test passed: agent initialization")
    except Exception as e:
        print(f"Test failed: agent initialization: {e}")
        print(traceback.format_exc()[:1000])

@patch('mapping_agent.agent.SFNAIHandler')
def test_run_workflow_success(mock_ai_handler):
    """Test successful execution of the run_workflow method"""
    try:
        print("\n\nTesting run_workflow with successful execution...")
        # Setup mock response with the structure the agent expects
        mock_response = {
            "choices": [{
                "message": {
                    "content": '{"field1": [{"table": "schema.table1", "column_name": "col1", "col_description": "desc1", "rank": 1, "reason": "test"}]}'
                }
            }]
        }
        mock_ai_handler.return_value.chat.return_value = mock_response
        
        # Initialize agent with mock
        agent = MappingAgent()
        agent.ai_handler = mock_ai_handler.return_value
        
        # Test data
        canonical_fields = [{
            "name": "field1",
            "description": "Test field 1",
            "data_type": "string"
        }]
        entity_name = "test_entity"
        table_columns = [{
            "table": "schema.table1", 
            "name": "col1", 
            "description": "desc1"
        }]
        
        # Execute
        result = agent.run_workflow(canonical_fields, entity_name, table_columns)
        
        # Verify
        print(result)
        assert result is not None, "Result should not be None"
        assert "field1" in result, "Result should contain 'field1' key"
        assert len(result["field1"]) > 0, "Field1 should have at least one mapping"
        assert result["field1"][0].column_name == "col1", "Column name should be 'col1'"
        print("✓ Test passed: run_workflow with successful execution")
    except Exception as e:
        print(f"Test failed: run_workflow with successful execution: {e}")
        print(traceback.format_exc()[:1000])

@patch('mapping_agent.agent.SFNAIHandler')
def test_run_workflow_no_mappings(mock_ai_handler):
    """Test handling of no mappings found scenario"""
    try:
        print("\n\nTesting run_workflow with no mappings found...")
        # Setup mock to return no suitable mappings message
        mock_response = {
            "choices": [{
                "message": {
                    "content": 'I could not found suitable mappings for entity test_entity'
                }
            }]
        }
        mock_ai_handler.return_value.chat.return_value = mock_response
    
        agent = MappingAgent()
        agent.ai_handler = mock_ai_handler.return_value
    
        # Provide properly formatted test data
        canonical_fields = [{
            'name': 'test_field',
            'description': 'Test field description',
            'data_type': 'string'
        }]
        table_columns = [{
            'table': 'test_schema.test_table',
            'name': 'test_column',
            'description': 'Test column description'
        }]
    
        result = agent.run_workflow(canonical_fields, "test_entity", table_columns)
        assert isinstance(result, str), "Expected a string response when no mappings found"
        assert "could not found suitable mappings" in result.lower()
        print("✓ Test passed: run_workflow with no mappings found")
    except Exception as e:
        print(f"Test failed: run_workflow with no mappings found: {e}")
        print(traceback.format_exc()[:1000])

@patch('mapping_agent.agent.SFNAIHandler')
def test_run_workflow_invalid_json(mock_ai_handler):        
    """Test handling of invalid JSON response from LLM"""
    try:
        print("\n\nTesting run_workflow with invalid JSON response...")
        # Setup mock to return invalid JSON
        mock_response = {
            "choices": [{
                "message": {
                    "content": 'invalid json'
                }
            }]
        }
        mock_ai_handler.return_value.chat.return_value = mock_response
    
        agent = MappingAgent()
        agent.ai_handler = mock_ai_handler.return_value
    
        # Provide properly formatted test data
        canonical_fields = [{
            'name': 'test_field',
            'description': 'Test field',
            'data_type': 'string'
        }]
        table_columns = [{
            'table': 'test_schema.test_table',
            'name': 'test_column',
            'description': 'Test column'
        }]
    
        result = agent.run_workflow(canonical_fields, "test_entity", table_columns)
        assert result == {}, "Expected empty dict for invalid JSON response"
        print("✓ Test passed: run_workflow with invalid JSON response")
    except Exception as e:
        print(f"Test failed: run_workflow with invalid JSON response: {e}")
        print(traceback.format_exc()[:1000])

def test_get_agent_name():
    """Test the get_agent_name method"""
    try:    
        print("\n\nTesting get_agent_name...")
        agent = MappingAgent()
        assert agent.get_agent_name() == "MappingAgent"
        print("✓ Test passed: get_agent_name")
    except Exception as e:
        print(f"Test failed: get_agent_name: {e}")
        print(traceback.format_exc()[:1000])

if __name__ == "__main__":
    test_agent_initialization()
    test_run_workflow_success()
    test_run_workflow_no_mappings()
    test_run_workflow_invalid_json()
    test_get_agent_name()
    print("\nAll agent integration tests completed successfully!")
