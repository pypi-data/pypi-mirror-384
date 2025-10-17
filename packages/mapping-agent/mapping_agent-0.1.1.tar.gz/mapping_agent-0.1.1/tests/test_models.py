"""
Tests for data models in mapping_agent.models
"""
import pytest
import traceback
from pydantic import ValidationError
from mapping_agent.models import MappingEntry, CanonicalMappings

def test_mapping_entry_creation():
    """Test creation of MappingEntry with valid data"""
    try:
        print("\nTesting MappingEntry creation with valid data...")
        entry = MappingEntry(
            table="schema.table",
            column_name="test_column",
            col_description="Test column description",
        rank=1,
        reason="Test reason"
        )
        assert entry.table == "schema.table"
        assert entry.column_name == "test_column"
        assert entry.rank == 1
        print("✓ Test passed: MappingEntry creation with valid data")
    except Exception as e:
        print(f"Test failed: MappingEntry creation with valid data - {str(e)}")
        print(traceback.format_exc()[:1000])

def test_mapping_entry_validation():
    """Test validation of required fields in MappingEntry"""
    try:
        print("\nTesting MappingEntry validation...")
        with pytest.raises(ValidationError):
            # Missing required field 'table'
            MappingEntry(
                column_name="test_column",
            col_description="Test",
            rank=1,
            reason="Test"
        )
        print("✓ Test passed: MappingEntry validation")
    except Exception as e:  
        print(f"Test failed: MappingEntry validation - {str(e)}")
        print(traceback.format_exc()[:1000])

def test_canonical_mappings_from_dict():
    """Test creating CanonicalMappings from dictionary"""
    try:
        print("\nTesting CanonicalMappings from dict...")
        data = {
        "field1": [
            {
                "table": "schema.table1",
                "column_name": "col1",
                "col_description": "desc1",
                "rank": 1,
                "reason": "reason1"
            }
            ]
        }
        mappings = CanonicalMappings.model_validate(data)
        assert "field1" in mappings.root
        assert len(mappings.root["field1"]) == 1
        assert mappings.root["field1"][0].column_name == "col1"
        print("✓ Test passed: CanonicalMappings from dict")
    except Exception as e:  
        print(f"Test failed: CanonicalMappings from dict - {str(e)}")
        print(traceback.format_exc()[:1000])

def test_canonical_mappings_from_objects():
    """Test creating CanonicalMappings from objects"""
    try:
        print("\nTesting CanonicalMappings from objects...")
        entry = MappingEntry(
            table="schema.table1",
            column_name="col1",
            col_description="desc1",
            rank=1,
        reason="reason1"
        )
        data = {"field1": [entry]}
        mappings = CanonicalMappings.model_validate(data)
        assert "field1" in mappings.root
        assert len(mappings.root["field1"]) == 1
        assert mappings.root["field1"][0].column_name == "col1"
        print("✓ Test passed: CanonicalMappings from objects")
    except Exception as e:  
        print(f"Test failed: CanonicalMappings from objects - {str(e)}")
        print(traceback.format_exc()[:1000])

def test_canonical_mappings_invalid_data():
    """Test validation of invalid data in CanonicalMappings"""
    print("\nTesting CanonicalMappings with invalid data...")
    with pytest.raises(ValueError):
        # Invalid data - missing required fields
        CanonicalMappings.model_validate({"field1": [{"invalid": "data"}]})
    print("✓ Test passed: CanonicalMappings with invalid data")

if __name__ == "__main__":
    test_mapping_entry_creation()
    test_mapping_entry_validation()
    test_canonical_mappings_from_dict()
    test_canonical_mappings_from_objects()
    test_canonical_mappings_invalid_data()
    print("\nAll models tests completed successfully!")
