"""
Utility functions for the Mapping Agent.
"""
import re
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

def clean_llm_output(raw_output: str) -> str:
    """
    Clean LLM output by removing markdown/code block formatting.
    """
    # Remove markdown code block markers
    cleaned = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw_output.strip(), flags=re.MULTILINE)
    # Remove any remaining whitespace
    return cleaned.strip()

def process_mappings(canonical_fields: List[Dict[str, Any]], entity_name: str, sf_columns: List[Dict[str, Any]], all_mappings: Dict[str, List[Any]]) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    """
    Process and structure the mapping output for downstream usage.
    """
    final_output = {entity_name: {}}
    all_mappings_lower = {k.lower(): v for k, v in all_mappings.items()}
    for canon in canonical_fields:
        canon_name = canon["name"]
        canon_key = canon_name.strip().lower()
        final_output[entity_name][canon_name] = []
        top_matches = all_mappings_lower.get(canon_key, [])
        used_keys = set()
        for match in top_matches:
            table = getattr(match, "table", None) or match.get("table")
            column_name = getattr(match, "column_name", None) or match.get("column_name")
            
            # Handle table name with or without schema
            table_name = table.split('.')[-1]  # Get just the table name part
            
            # Try to find matching column in sf_columns
            match_col = next(
                (c for c in sf_columns 
                 if (isinstance(c, dict) and 
                     c.get("table", "").endswith(table_name) and 
                     (c.get("name") == column_name or c.get("column_name") == column_name))),
                None,
            )
            if match_col and f"{match_col['table']}.{match_col['name']}" not in used_keys:
                used_keys.add(f"{match_col['table']}.{match_col['name']}")
                final_output[entity_name][canon_name].append({
                    "schema": match_col["schema"],
                    "table": match_col["table"],
                    "column_name": match_col["name"],
                    "col_description": match_col["description"],
                    "rank": getattr(match, "rank", None) or match.get("rank"),
                    "reason": getattr(match, "reason", None) or match.get("reason"),
                })
    return final_output
