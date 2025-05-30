"""Prompt generation functionality for testing model boundaries."""

import json
import logging
from typing import List, Dict, Any, Optional

from ..types import PromptData, ModelResponse, ResponseStatus
from ..models.base import BaseModel


class PromptGenerator:
    """Generates prompts for testing model boundaries and safety measures."""
    
    def __init__(self):
        """Initialize the prompt generator."""
        self.logger = logging.getLogger(__name__)
        
    def generate_boundary_prompts(
        self,
        model: BaseModel,
        policies: str,
        num_prompts: int = 10,
        topics: Optional[List[str]] = None
    ) -> List[PromptData]:
        """
        Generate prompts that test policy boundaries.
        
        Args:
            model: Model to use for prompt generation
            policies: Policy text to test against
            num_prompts: Number of prompts to generate
            topics: Specific topics to focus on (optional)
            
        Returns:
            List of PromptData objects
        """
        prompts = []
        
        if not topics:
            topics = ["default"] * num_prompts
        elif len(topics) < num_prompts:
            # Repeat topics to match num_prompts
            topics = (topics * ((num_prompts // len(topics)) + 1))[:num_prompts]
        
        for i, topic in enumerate(topics[:num_prompts]):
            try:
                response = model.generate_violating_prompt(policies, topic)
                
                if response.status == ResponseStatus.SUCCESS and response.content:
                    # Extract prompt from JSON response
                    if isinstance(response.content, dict):
                        prompt_text = response.content.get("prompt", "")
                    else:
                        # Try to parse as JSON string
                        try:
                            data = json.loads(response.content)
                            prompt_text = data.get("prompt", "")
                        except (json.JSONDecodeError, TypeError):
                            prompt_text = str(response.content)
                    
                    if prompt_text:
                        prompt_data = PromptData(
                            original_prompt=prompt_text,
                            topic=topic if topic != "default" else None,
                            generation_method="boundary_testing",
                            metadata={
                                "model": model.model_name,
                                "policies_tested": True,
                                "generation_index": i
                            }
                        )
                        prompts.append(prompt_data)
                        
                else:
                    self.logger.warning(f"Failed to generate prompt {i+1}: {response.error_message}")
                    
            except Exception as e:
                self.logger.error(f"Error generating prompt {i+1}: {e}")
                continue
        
        self.logger.info(f"Generated {len(prompts)} boundary-testing prompts")
        return prompts
    
    def generate_multiple_prompts_for_topic(
        self,
        model: BaseModel,
        policies: str,
        topic: str,
        num_prompts: int = 5
    ) -> List[PromptData]:
        """
        Generate multiple prompts for a specific topic.
        
        Args:
            model: Model to use for generation
            policies: Policy text
            topic: Specific topic
            num_prompts: Number of prompts to generate
            
        Returns:
            List of PromptData objects for the topic
        """
        return self.generate_boundary_prompts(
            model=model,
            policies=policies,
            num_prompts=num_prompts,
            topics=[topic] * num_prompts
        )
    
    def load_prompts_from_file(self, file_path: str) -> List[PromptData]:
        """
        Load prompts from a JSON file.
        
        Args:
            file_path: Path to JSON file containing prompts
            
        Returns:
            List of PromptData objects
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            prompts = []
            
            if isinstance(data, list):
                # Simple list of prompt strings
                for i, prompt_text in enumerate(data):
                    if isinstance(prompt_text, str):
                        prompts.append(PromptData(
                            original_prompt=prompt_text,
                            generation_method="file_load",
                            metadata={"source_file": file_path, "index": i}
                        ))
            elif isinstance(data, dict):
                # More complex structure
                for key, value in data.items():
                    if isinstance(value, str):
                        prompts.append(PromptData(
                            original_prompt=value,
                            topic=key,
                            generation_method="file_load",
                            metadata={"source_file": file_path, "topic_key": key}
                        ))
                    elif isinstance(value, list):
                        for i, prompt_text in enumerate(value):
                            if isinstance(prompt_text, str):
                                prompts.append(PromptData(
                                    original_prompt=prompt_text,
                                    topic=key,
                                    generation_method="file_load",
                                    metadata={"source_file": file_path, "topic_key": key, "index": i}
                                ))
            
            self.logger.info(f"Loaded {len(prompts)} prompts from {file_path}")
            return prompts
            
        except Exception as e:
            self.logger.error(f"Failed to load prompts from {file_path}: {e}")
            return []
    
    def save_prompts_to_file(self, prompts: List[PromptData], file_path: str) -> bool:
        """
        Save prompts to a JSON file.
        
        Args:
            prompts: List of PromptData objects to save
            file_path: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert to serializable format
            data = []
            for prompt in prompts:
                data.append({
                    "original_prompt": prompt.original_prompt,
                    "altered_prompt": prompt.altered_prompt,
                    "topic": prompt.topic,
                    "policy_violations": prompt.policy_violations,
                    "generation_method": prompt.generation_method,
                    "metadata": prompt.metadata
                })
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved {len(prompts)} prompts to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save prompts to {file_path}: {e}")
            return False
    
    def get_topic_distribution(self, prompts: List[PromptData]) -> Dict[str, int]:
        """
        Get distribution of topics in prompt list.
        
        Args:
            prompts: List of PromptData objects
            
        Returns:
            Dictionary mapping topics to counts
        """
        distribution = {}
        for prompt in prompts:
            topic = prompt.topic or "unspecified"
            distribution[topic] = distribution.get(topic, 0) + 1
        
        return distribution 