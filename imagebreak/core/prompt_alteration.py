"""Prompt alteration functionality for testing filter evasion."""

import json
import logging
from typing import List, Dict, Any, Optional

from ..types import PromptData, ModelResponse, ResponseStatus
from ..models.base import BaseModel


class PromptAlteration:
    """Alters prompts to test content filter evasion (for research purposes)."""
    
    def __init__(self):
        """Initialize the prompt alteration system."""
        self.logger = logging.getLogger(__name__)
        
    def alter_prompt(
        self,
        model: BaseModel,
        prompt_data: PromptData
    ) -> PromptData:
        """
        Generate an altered version of a prompt to test filter evasion.
        
        Args:
            model: Model to use for prompt alteration
            prompt_data: Original prompt data
            
        Returns:
            PromptData with altered_prompt field populated
        """
        try:
            response = model.generate_alternate_prompt(prompt_data.original_prompt)
            
            if response.status == ResponseStatus.SUCCESS and response.content:
                # Extract altered prompt from response
                altered_prompt = self._extract_altered_prompt(response.content)
                
                if altered_prompt:
                    # Update the prompt data with the altered version
                    prompt_data.altered_prompt = altered_prompt
                    prompt_data.metadata["alteration_successful"] = True
                    prompt_data.metadata["alteration_model"] = model.model_name
                else:
                    self.logger.warning("Failed to extract altered prompt from response")
                    prompt_data.metadata["alteration_successful"] = False
                    prompt_data.metadata["alteration_error"] = "Failed to extract prompt"
                    
            else:
                self.logger.warning(f"Prompt alteration failed: {response.error_message}")
                prompt_data.metadata["alteration_successful"] = False
                prompt_data.metadata["alteration_error"] = response.error_message
                
        except Exception as e:
            self.logger.error(f"Error during prompt alteration: {e}")
            prompt_data.metadata["alteration_successful"] = False
            prompt_data.metadata["alteration_error"] = str(e)
            
        return prompt_data
    
    def alter_prompts_batch(
        self,
        model: BaseModel,
        prompt_data_list: List[PromptData]
    ) -> List[PromptData]:
        """
        Alter multiple prompts in batch.
        
        Args:
            model: Model to use for prompt alteration
            prompt_data_list: List of original prompt data
            
        Returns:
            List of PromptData with altered_prompt fields populated
        """
        altered_prompts = []
        
        for i, prompt_data in enumerate(prompt_data_list):
            try:
                altered_prompt = self.alter_prompt(model, prompt_data)
                altered_prompts.append(altered_prompt)
                
                if (i + 1) % 10 == 0:
                    self.logger.info(f"Processed {i + 1}/{len(prompt_data_list)} prompt alterations")
                    
            except Exception as e:
                self.logger.error(f"Error altering prompt {i}: {e}")
                # Add the original prompt data with error metadata
                prompt_data.metadata["alteration_successful"] = False
                prompt_data.metadata["alteration_error"] = str(e)
                altered_prompts.append(prompt_data)
        
        successful_alterations = sum(1 for p in altered_prompts if p.metadata.get("alteration_successful", False))
        self.logger.info(f"Successfully altered {successful_alterations}/{len(prompt_data_list)} prompts")
        
        return altered_prompts
    
    def _extract_altered_prompt(self, content: Any) -> Optional[str]:
        """
        Extract the altered prompt from model response content.
        
        Args:
            content: Response content (could be dict, string, etc.)
            
        Returns:
            Extracted prompt string or None
        """
        try:
            if isinstance(content, dict):
                # Look for common keys
                for key in ["altered_prompt", "prompt", "modified_prompt", "refined_prompt"]:
                    if key in content:
                        return content[key]
                        
                # If no standard key found, try the first string value
                for value in content.values():
                    if isinstance(value, str) and len(value) > 10:  # Reasonable prompt length
                        return value
                        
            elif isinstance(content, str):
                # Try to parse as JSON first
                try:
                    data = json.loads(content)
                    return self._extract_altered_prompt(data)
                except json.JSONDecodeError:
                    # Return as-is if it's not JSON
                    return content if len(content) > 10 else None
                    
        except Exception as e:
            self.logger.error(f"Error extracting altered prompt: {e}")
            
        return None
    
    def create_alteration_mapping(
        self,
        prompt_data_list: List[PromptData]
    ) -> Dict[str, str]:
        """
        Create a mapping from altered prompts to original prompts.
        
        Args:
            prompt_data_list: List of prompt data with alterations
            
        Returns:
            Dictionary mapping altered prompts to original prompts
        """
        mapping = {}
        
        for prompt_data in prompt_data_list:
            if prompt_data.altered_prompt:
                mapping[prompt_data.altered_prompt] = prompt_data.original_prompt
                
        return mapping
    
    def get_alteration_success_rate(
        self,
        prompt_data_list: List[PromptData]
    ) -> float:
        """
        Calculate the success rate of prompt alterations.
        
        Args:
            prompt_data_list: List of prompt data
            
        Returns:
            Success rate as a float between 0 and 1
        """
        if not prompt_data_list:
            return 0.0
            
        successful = sum(1 for p in prompt_data_list if p.metadata.get("alteration_successful", False))
        return successful / len(prompt_data_list)
    
    def get_alteration_statistics(
        self,
        prompt_data_list: List[PromptData]
    ) -> Dict[str, Any]:
        """
        Get detailed statistics about prompt alterations.
        
        Args:
            prompt_data_list: List of prompt data
            
        Returns:
            Dictionary with alteration statistics
        """
        total = len(prompt_data_list)
        successful = sum(1 for p in prompt_data_list if p.metadata.get("alteration_successful", False))
        failed = total - successful
        
        # Analyze failure reasons
        failure_reasons = {}
        for prompt_data in prompt_data_list:
            if not prompt_data.metadata.get("alteration_successful", False):
                error = prompt_data.metadata.get("alteration_error", "Unknown error")
                failure_reasons[error] = failure_reasons.get(error, 0) + 1
        
        return {
            "total_prompts": total,
            "successful_alterations": successful,
            "failed_alterations": failed,
            "success_rate": successful / total if total > 0 else 0.0,
            "failure_rate": failed / total if total > 0 else 0.0,
            "failure_reasons": failure_reasons
        } 