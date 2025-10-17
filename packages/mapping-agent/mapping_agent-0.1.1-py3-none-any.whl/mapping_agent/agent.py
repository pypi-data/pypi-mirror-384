"""
Main MappingAgent class and workflow orchestration.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from pydantic import ValidationError
from .config import MappingAgentConfig
from .models import CanonicalMappings
from .constants import get_mapping_system_prompt, get_mapping_user_prompt
from .utils import clean_llm_output, process_mappings

import sfn_blueprint
from sfn_blueprint import SFNAIHandler, setup_logger

class MappingAgent:
    def __init__(self, config: Optional[MappingAgentConfig] = None):
        self.config = config or MappingAgentConfig()
        logger_result = setup_logger(__name__)
        self.logger = logger_result[0] if isinstance(logger_result, tuple) else logger_result
        self.ai_handler = SFNAIHandler()

    def run_workflow(self, 
                    canonical_fields: List[Dict[str, Any]], 
                    entity_desciption: str, 
                    table_columns: List[Dict[str, Any]]) -> Any:
        """
        Main workflow for mapping canonical fields to columns using LLM.
        """
        system_prompt = get_mapping_system_prompt()
        user_prompt = get_mapping_user_prompt(canonical_fields, entity_desciption, table_columns)

        llm_config = {
            "llm_provider": self.config.llm_provider,
            "model": self.config.model_name,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "top_p": self.config.top_p,
            "frequency_penalty": self.config.frequency_penalty,
            "presence_penalty": self.config.presence_penalty,
        }

        try:
            response, cost = self.ai_handler.route_to(
                llm_provider=llm_config["llm_provider"],
                configuration={
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": llm_config["temperature"],
                    "max_tokens": llm_config["max_tokens"]
                },
                model=llm_config["model"]
            )
            # self.logger.info(f"LLM response: {response}")
            print("type of response", type(response))
            print("cost", cost, type(cost))
            if isinstance(response, dict) and response.get("choices"):
                raw_output = response["choices"][0]["message"]["content"]
            else:
                raw_output = str(response)
            # Handle special no-mapping message
            if "I could not found suitable mappings for entity" in raw_output:
                return raw_output
            cleaned_json_str = clean_llm_output(raw_output)
            parsed_json = json.loads(cleaned_json_str)
            validated = CanonicalMappings.model_validate(parsed_json)
            self.logger.info("CanonicalMappings model validated.")
            return validated.root
        except (json.JSONDecodeError, ValidationError) as e:
            self.logger.error(f"Failed to parse/validate LLM response: {e}")
            self.logger.error(f"Raw output:\n{raw_output}")
            return {}

    def get_agent_name(self):
        return self.__class__.__name__
