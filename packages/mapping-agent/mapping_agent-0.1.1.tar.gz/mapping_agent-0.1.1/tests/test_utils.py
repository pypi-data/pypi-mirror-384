"""
Tests for utility functions in mapping_agent.utils
"""
import pytest
import json
import traceback
from unittest.mock import MagicMock, patch
from mapping_agent.utils import clean_llm_output, process_mappings

def test_clean_llm_output_basic():
    """Test cleaning of LLM output with markdown code blocks"""
    try:
        print("\nTesting clean_llm_output with markdown code blocks...")
        raw = """```json
        {"key": "value"}
        ```"""
        cleaned = clean_llm_output(raw)
        assert '```' not in cleaned
        assert 'key' in cleaned
        print("✓ Test passed: clean_llm_output with markdown code blocks")
    except Exception as e:
        print(f"Test failed: clean_llm_output with markdown code blocks - {str(e)}")
        print(traceback.format_exc()[:1000])

def test_clean_llm_output_json_block():
    """Test cleaning of LLM output with JSON code blocks"""
    try:
        print("\nTesting clean_llm_output with JSON code blocks...")
        raw = """```json
        {"key": "value"}
        ```"""
        cleaned = clean_llm_output(raw)
        assert '```' not in cleaned
        assert 'key' in cleaned
        print("✓ Test passed: clean_llm_output with JSON code blocks")
    except Exception as e:
        print(f"Test failed: clean_llm_output with JSON code blocks - {str(e)}")
        print(traceback.format_exc()[:1000])

def test_clean_llm_output_no_blocks():
    """Test cleaning of LLM output without any code blocks"""
    try:
        print("\nTesting clean_llm_output without code blocks...")
        raw = '{"key": "value"}'
        cleaned = clean_llm_output(raw)
        assert cleaned == raw
        print("✓ Test passed: clean_llm_output without code blocks")
    except Exception as e:
        print(f"Test failed: clean_llm_output without code blocks - {str(e)}")
        print(traceback.format_exc()[:1000])

def test_process_mappings_basic():
    """Test processing of mappings with basic input"""
    try:
        print("\nTesting process_mappings with basic input...")
        canonical_fields = [{"name": "test_field"}]
        entity_name = "test_entity"
        sf_columns = [
            {
                "table": "schema.table",
                "name": "test_column",
                "schema": "schema",
                "description": "test description"
            }
        ]
        all_mappings = {
            "test_field": [
                {
                    "table": "schema.table",
                    "column_name": "test_column",
                    "col_description": "test description",
                    "rank": 1,
                    "reason": "test reason"
                }
            ]
        }

        result = process_mappings(canonical_fields, entity_name, sf_columns, all_mappings)
        
        assert entity_name in result
        assert "test_field" in result[entity_name]
        assert len(result[entity_name]["test_field"]) == 1
        assert result[entity_name]["test_field"][0]["column_name"] == "test_column"
        print("✓ Test passed: process_mappings with basic input")
    except Exception as e:
        print(f"Test failed: process_mappings with basic input - {str(e)}")
        print(traceback.format_exc()[:1000])

def test_process_mappings_duplicate_prevention():
    """Test that duplicate mappings are prevented"""
    try:
        print("\nTesting process_mappings duplicate prevention...")
        canonical_fields = [{"name": "test_field"}]
        entity_name = "test_entity"
        sf_columns = [
            {
                "table": "schema.table",
                "name": "test_column",
                "schema": "schema",
                "description": "test description"
            }
        ]
        all_mappings = {
            "test_field": [
                {
                    "table": "schema.table",
                    "column_name": "test_column",
                "col_description": "test description",
                "rank": 1,
                "reason": "test reason"
            },
            {
                "table": "schema.table",
                "column_name": "test_column",  # Duplicate
                "col_description": "test description",
                "rank": 2,
                "reason": "test reason 2"
            }
        ]
        }
    
        result = process_mappings(canonical_fields, entity_name, sf_columns, all_mappings)
        assert len(result[entity_name]["test_field"]) == 1  # Should be deduplicated
        print("✓ Test passed: process_mappings duplicate prevention")
    except Exception as e:
        print(f"Test failed: process_mappings duplicate prevention - {str(e)}")
        print(traceback.format_exc()[:1000])

def test_process_mappings_no_matches():
    """Test processing when no matches are found"""
    try:
        print("\nTesting process_mappings with no matches...")
        canonical_fields = [{"name": "non_existent_field"}]
        entity_name = "test_entity"
        sf_columns = [
            {
                "table": "schema.table",
                "name": "test_column",
                "schema": "schema",
                "description": "test description"
            }
        ]
        all_mappings = {}
    
        result = process_mappings(canonical_fields, entity_name, sf_columns, all_mappings)
        assert entity_name in result
        assert "non_existent_field" in result[entity_name]
        assert len(result[entity_name]["non_existent_field"]) == 0
        print("✓ Test passed: process_mappings with no matches")
    except Exception as e:
        print(f"Test failed: process_mappings with no matches - {str(e)}")
        print(traceback.format_exc()[:1000])

if __name__ == "__main__":
    test_clean_llm_output_basic()
    test_clean_llm_output_json_block()
    test_clean_llm_output_no_blocks()
    test_process_mappings_basic()
    test_process_mappings_duplicate_prevention()
    test_process_mappings_no_matches()
    print("\nAll utils tests completed successfully!")
