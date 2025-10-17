"""
Data models for the Mapping Agent.
"""
from typing import List, Dict, Any, Union, TypeVar
from pydantic import BaseModel, RootModel, ValidationError, Field

T = TypeVar('T', bound='MappingEntry')

class MappingEntry(BaseModel):
    """Represents a single mapping entry."""
    table: str = Field(..., description="Name of the table")
    column_name: str = Field(..., description="Name of the column")
    col_description: str = Field(..., description="Description of the column")
    rank: int = Field(..., ge=1, description="Ranking of this mapping")
    reason: str = Field(..., description="Reason for this mapping")

# Type alias for the mapping dictionary type
MappingDict = Dict[str, List[Union[Dict[str, Any], 'MappingEntry']]]

class CanonicalMappings(RootModel[Dict[str, List[MappingEntry]]]):
    """
    Container for multiple mapping entries, keyed by field name.
    
    This is a root model that represents a dictionary where:
    - Keys are field names (strings)
    - Values are lists of MappingEntry objects
    """
    root: Dict[str, List[MappingEntry]] = Field(
        default_factory=dict,
        description="Dictionary mapping field names to their mapping entries"
    )
    
    @classmethod
    def model_validate(cls, value: MappingDict) -> 'CanonicalMappings':
        """
        Validate and convert input data into a CanonicalMappings instance.
        
        Args:
            value: Dictionary where values are either MappingEntry objects or dicts
            
        Returns:
            Validated CanonicalMappings instance
            
        Raises:
            ValidationError: If the input data is invalid
        """
        if not isinstance(value, dict):
            raise ValueError("Input must be a dictionary")
            
        validated_entries: Dict[str, List[MappingEntry]] = {}
        
        for field_name, entries in value.items():
            if not isinstance(entries, list):
                raise ValueError(
                    f"Value for field '{field_name}' must be a list"
                )
                
            validated_entries[field_name] = []
            
            for i, entry in enumerate(entries, 1):
                try:
                    if isinstance(entry, MappingEntry):
                        validated_entries[field_name].append(entry)
                    elif isinstance(entry, dict):
                        try:
                            validated_entries[field_name].append(MappingEntry.model_validate(entry))
                        except ValidationError as ve:
                            # Convert Pydantic validation error to a more user-friendly message
                            error_msgs = []
                            for error in ve.errors():
                                field = ".".join(str(loc) for loc in error['loc'])
                                error_msgs.append(f"{field}: {error['msg']}")
                            error_msg = "; ".join(error_msgs)
                            raise ValueError(
                                f"Invalid mapping for field '{field_name}' at index {i-1}: {error_msg}"
                            ) from ve
                    else:
                        raise ValueError(f"Expected MappingEntry or dict, got {type(entry).__name__}")
                except ValueError as ve:
                    # Re-raise ValueError as is
                    raise ve
                except Exception as e:
                    # Catch any other exceptions and wrap them in a ValidationError
                    raise ValueError(
                        f"Unexpected error processing field '{field_name}' at index {i-1}: {str(e)}"
                    ) from e
        
        return cls(root=validated_entries)
    
    def __getitem__(self, key: str) -> List[MappingEntry]:
        """Enable dict-like access to mappings."""
        return self.root[key]
        
    def get(self, key: str, default: Any = None) -> List[MappingEntry]:
        """Get mappings for a field with an optional default value."""
        return self.root.get(key, default)
        
    def items(self):
        """Return key-value pairs of field names and their mappings."""
        return self.root.items()
        
    def keys(self):
        """Return field names."""
        return self.root.keys()
        
    def values(self):
        """Return all mapping entries."""
        return self.root.values()
        
    def __contains__(self, key: str) -> bool:
        """Check if a field exists in the mappings."""
        return key in self.root
