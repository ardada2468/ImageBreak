"""Cyclic image generation with quality assessment and retry logic."""

import logging
import time
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

from ..types import PromptData, ModelResponse, ResponseStatus, TestResult
from ..models.base import BaseModel
from ..models.huggingface_model import HuggingFaceImageAnalyzer


@dataclass
class GenerationAttempt:
    """Data structure for tracking generation attempts."""
    attempt_number: int
    prompt_used: str
    response: ModelResponse
    quality_score: Optional[float] = None
    analysis_result: Optional[Dict[str, Any]] = None
    timestamp: Optional[float] = None


@dataclass
class CyclicResult:
    """Result from cyclic generation process."""
    prompt_data: PromptData
    final_response: ModelResponse
    attempts: List[GenerationAttempt]
    success: bool
    total_attempts: int
    final_quality_score: Optional[float]
    exceeded_max_attempts: bool


class CyclicImageGenerator:
    """
    Cyclic image generator that retries generation if quality is insufficient.
    Uses HuggingFace image analysis to assess quality and decide on retries.
    """
    
    def __init__(
        self,
        config,
        image_analyzer: Optional[HuggingFaceImageAnalyzer] = None,
        max_attempts: Optional[int] = None,
        quality_threshold: Optional[float] = None
    ):
        """
        Initialize cyclic generator.
        
        Args:
            config: Configuration object
            image_analyzer: HuggingFace image analyzer (will create default if None)
            max_attempts: Maximum retry attempts (uses config if None)
            quality_threshold: Quality threshold for acceptance (uses config if None)
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize image analyzer
        if image_analyzer:
            self.image_analyzer = image_analyzer
        else:
            try:
                self.image_analyzer = HuggingFaceImageAnalyzer(
                    model_name="Salesforce/blip2-opt-2.7b"
                )
                self.logger.info("Initialized default BLIP-2 image analyzer")
            except Exception as e:
                self.logger.warning(f"Failed to initialize image analyzer: {e}")
                self.image_analyzer = None
        
        self.max_attempts = max_attempts or config.max_retry_attempts
        self.quality_threshold = quality_threshold or config.quality_threshold
        self.enabled = config.enable_cyclic_regeneration
        
        self.logger.info(f"Cyclic generation: enabled={self.enabled}, "
                        f"max_attempts={self.max_attempts}, "
                        f"quality_threshold={self.quality_threshold}")
    
    def generate_with_retries(
        self,
        image_model: BaseModel,
        text_model: BaseModel,
        prompt_data: PromptData,
        **generation_kwargs
    ) -> CyclicResult:
        """
        Generate image with quality-based retries.
        
        Args:
            image_model: Model for image generation
            text_model: Model for prompt refinement
            prompt_data: Original prompt data
            **generation_kwargs: Additional arguments for image generation
            
        Returns:
            CyclicResult with generation details
        """
        if not self.enabled:
            # If cyclic generation is disabled, just do one attempt
            response = image_model.generate_image(
                prompt=prompt_data.altered_prompt or prompt_data.original_prompt,
                **generation_kwargs
            )
            
            return CyclicResult(
                prompt_data=prompt_data,
                final_response=response,
                attempts=[GenerationAttempt(
                    attempt_number=1,
                    prompt_used=prompt_data.altered_prompt or prompt_data.original_prompt,
                    response=response,
                    timestamp=time.time()
                )],
                success=response.status == ResponseStatus.SUCCESS,
                total_attempts=1,
                final_quality_score=None,
                exceeded_max_attempts=False
            )
        
        attempts = []
        current_prompt = prompt_data.altered_prompt or prompt_data.original_prompt
        
        for attempt_num in range(1, self.max_attempts + 1):
            self.logger.info(f"Generation attempt {attempt_num}/{self.max_attempts}")
            
            # Generate image
            response = image_model.generate_image(
                prompt=current_prompt,
                **generation_kwargs
            )
            
            attempt = GenerationAttempt(
                attempt_number=attempt_num,
                prompt_used=current_prompt,
                response=response,
                timestamp=time.time()
            )
            
            # If generation failed, record and continue
            if response.status != ResponseStatus.SUCCESS:
                attempts.append(attempt)
                error_msg = response.error_message or "Unknown error"
                self.logger.warning(f"Attempt {attempt_num} failed: {error_msg}")
                
                # Check for content policy violations and provide specific feedback
                if "content policy" in error_msg.lower() or "image_generation_user_error" in error_msg:
                    self.logger.info(f"Content policy violation detected on attempt {attempt_num}")
                    
                    # If we have more attempts, try to refine the prompt to be more acceptable
                    if attempt_num < self.max_attempts:
                        self.logger.info("Attempting to create content-policy compliant version")
                        current_prompt = self._refine_prompt_for_policy(text_model, current_prompt)
                
                # If blocked by filter, try to refine prompt (for other blocking types)
                elif (response.status == ResponseStatus.BLOCKED_BY_FILTER and 
                    attempt_num < self.max_attempts):
                    current_prompt = self._refine_prompt(text_model, current_prompt)
                
                continue
            
            # Analyze image quality if analyzer is available
            quality_score = None
            analysis_result = None
            
            # Check if this was a sanitized prompt vs original
            prompt_type = None
            if hasattr(response, 'metadata') and response.metadata:
                prompt_type = response.metadata.get('prompt_type', 'unknown')
            elif hasattr(response, 'content') and isinstance(response.content, dict):
                prompt_type = response.content.get('prompt_type', 'unknown')
            
            if prompt_type:
                self.logger.info(f"Successfully generated image using {prompt_type} prompt")
            
            if self.image_analyzer and (response.image_path or response.image_url):
                try:
                    analysis_response = self.image_analyzer.analyze_image(
                        image_path=response.image_path,
                        image_url=response.image_url,
                        prompt=self.config.image_analysis_system_instruction,
                        original_prompt=prompt_data.original_prompt
                    )
                    
                    if analysis_response.status == ResponseStatus.SUCCESS:
                        analysis_result = analysis_response.content
                        quality_score = analysis_result.get('quality_score', 0.5)
                        
                        self.logger.info(f"Image quality score: {quality_score:.2f}")
                        
                except Exception as e:
                    self.logger.error(f"Image analysis failed: {e}")
                    quality_score = 0.5  # Default score
            
            attempt.quality_score = quality_score
            attempt.analysis_result = analysis_result
            attempts.append(attempt)
            
            # Check if quality meets threshold
            if quality_score is None or quality_score >= self.quality_threshold:
                self.logger.info(f"Quality threshold met on attempt {attempt_num}")
                return CyclicResult(
                    prompt_data=prompt_data,
                    final_response=response,
                    attempts=attempts,
                    success=True,
                    total_attempts=attempt_num,
                    final_quality_score=quality_score,
                    exceeded_max_attempts=False
                )
            
            # If quality is insufficient and we have more attempts, refine prompt
            if attempt_num < self.max_attempts:
                self.logger.info(f"Quality below threshold ({quality_score:.2f} < {self.quality_threshold}), refining prompt")
                
                # Create feedback for prompt refinement
                feedback = self._create_quality_feedback(analysis_result, quality_score)
                current_prompt = self._refine_prompt_with_feedback(
                    text_model, current_prompt, feedback
                )
            
            # Rate limiting between attempts
            if self.config.rate_limit_delay > 0:
                time.sleep(self.config.rate_limit_delay)
        
        # All attempts exhausted
        final_response = attempts[-1].response if attempts else ModelResponse(
            status=ResponseStatus.ERROR,
            error_message="No successful generations"
        )
        
        return CyclicResult(
            prompt_data=prompt_data,
            final_response=final_response,
            attempts=attempts,
            success=False,
            total_attempts=len(attempts),
            final_quality_score=attempts[-1].quality_score if attempts else None,
            exceeded_max_attempts=True
        )
    
    def _refine_prompt(self, text_model: BaseModel, current_prompt: str) -> str:
        """
        Refine prompt using the text model's alteration method.
        
        Args:
            text_model: Model for prompt refinement
            current_prompt: Current prompt to refine
            
        Returns:
            Refined prompt
        """
        try:
            if hasattr(text_model, 'generate_alternate_prompt'):
                response = text_model.generate_alternate_prompt(current_prompt)
                
                if response.status == ResponseStatus.SUCCESS:
                    if isinstance(response.content, dict):
                        refined = response.content.get('altered_prompt', current_prompt)
                    else:
                        # Try to parse JSON
                        try:
                            import json
                            data = json.loads(response.content)
                            refined = data.get('altered_prompt', current_prompt)
                        except:
                            refined = current_prompt
                    
                    self.logger.info("Prompt refined for next attempt")
                    return refined
                    
        except Exception as e:
            self.logger.error(f"Prompt refinement failed: {e}")
        
        return current_prompt
    
    def _refine_prompt_for_policy(self, text_model: BaseModel, current_prompt: str) -> str:
        """
        Refine prompt specifically to address content policy violations.
        
        Args:
            text_model: Model for prompt refinement
            current_prompt: Current prompt that violated policy
            
        Returns:
            Policy-compliant refined prompt
        """
        try:
            policy_refinement_prompt = f"""
            The following prompt was rejected by OpenAI's content policy: "{current_prompt}"
            
            Please rewrite this prompt to be compliant with content policies while maintaining the artistic intent. 
            Focus on:
            1. Removing any explicit, violent, or inappropriate content
            2. Maintaining the artistic style and composition
            3. Making it suitable for general audiences
            4. Keeping the creative vision intact
            
            Format your response as JSON: {{"refined_prompt": "your_policy_compliant_prompt_here"}}
            """
            
            response = text_model.generate_text(
                prompt=policy_refinement_prompt,
                system_prompt="You are a content moderator helping to create safe, artistic prompts for image generation that comply with platform policies.",
                format_as_json=True
            )
            
            if response.status == ResponseStatus.SUCCESS:
                if isinstance(response.content, dict):
                    refined = response.content.get('refined_prompt', current_prompt)
                else:
                    try:
                        import json
                        data = json.loads(response.content)
                        refined = data.get('refined_prompt', current_prompt)
                    except:
                        refined = current_prompt
                
                self.logger.info(f"Prompt refined for policy compliance: '{current_prompt}' -> '{refined}'")
                return refined
                
        except Exception as e:
            self.logger.error(f"Policy-compliant prompt refinement failed: {e}")
        
        # Fallback: basic sanitization
        return self._basic_policy_sanitization(current_prompt)
    
    def _basic_policy_sanitization(self, prompt: str) -> str:
        """Basic fallback sanitization for policy compliance."""
        import re
        
        # Remove problematic terms
        problematic_words = [
            r'\b(explicit|graphic|violent|gore|blood|nude|naked|sexual|nsfw|adult)\b',
            r'\b(inappropriate|harmful|disturbing|offensive|vulgar)\b',
            r'\b(depicting|showing|containing)\s+(violence|blood|gore|explicit)',
        ]
        
        sanitized = prompt
        for pattern in problematic_words:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        # Clean up and add positive artistic terms
        sanitized = ' '.join(sanitized.split())
        
        if len(sanitized.strip()) < 10:
            sanitized = "An artistic composition with creative visual elements, professionally rendered"
        else:
            sanitized += ", artistic style, professional quality"
        
        return sanitized
    
    def _create_quality_feedback(
        self, 
        analysis_result: Optional[Dict[str, Any]], 
        quality_score: float
    ) -> str:
        """
        Create feedback message based on image analysis.
        
        Args:
            analysis_result: Result from image analysis
            quality_score: Quality score
            
        Returns:
            Feedback string for prompt refinement
        """
        if not analysis_result:
            return f"Image quality score was {quality_score:.2f}, which is below the threshold. Please improve the prompt for better quality."
        
        description = analysis_result.get('description', '')
        
        feedback_parts = [
            f"Image quality score: {quality_score:.2f} (below threshold {self.quality_threshold})",
            f"Image analysis: {description}"
        ]
        
        # Add specific suggestions based on analysis
        if 'blurry' in description.lower() or 'unclear' in description.lower():
            feedback_parts.append("Suggestion: Add terms for clarity and sharpness")
        
        if 'dark' in description.lower():
            feedback_parts.append("Suggestion: Add lighting specifications")
        
        if 'low-quality' in description.lower():
            feedback_parts.append("Suggestion: Add quality and detail specifications")
        
        return ". ".join(feedback_parts)
    
    def _refine_prompt_with_feedback(
        self, 
        text_model: BaseModel, 
        current_prompt: str, 
        feedback: str
    ) -> str:
        """
        Refine prompt with specific quality feedback.
        
        Args:
            text_model: Model for prompt refinement
            current_prompt: Current prompt
            feedback: Quality feedback
            
        Returns:
            Refined prompt
        """
        try:
            refinement_prompt = (
                f"Original prompt: {current_prompt}\n\n"
                f"Quality feedback: {feedback}\n\n"
                "Please refine the prompt to address the quality issues while maintaining "
                "the original intent. Focus on improving image clarity, detail, and overall quality. "
                "Format your response as JSON: {\"refined_prompt\": \"your_improved_prompt_here\"}"
            )
            
            response = text_model.generate_text(
                prompt=refinement_prompt,
                system_prompt="You are an expert at refining image generation prompts to improve quality.",
                format_as_json=True
            )
            
            if response.status == ResponseStatus.SUCCESS:
                if isinstance(response.content, dict):
                    refined = response.content.get('refined_prompt', current_prompt)
                else:
                    try:
                        import json
                        data = json.loads(response.content)
                        refined = data.get('refined_prompt', current_prompt)
                    except:
                        refined = current_prompt
                
                self.logger.info("Prompt refined with quality feedback")
                return refined
                
        except Exception as e:
            self.logger.error(f"Feedback-based refinement failed: {e}")
        
        return current_prompt
    
    def batch_generate_with_retries(
        self,
        image_model: BaseModel,
        text_model: BaseModel,
        prompt_data_list: List[PromptData],
        **generation_kwargs
    ) -> List[CyclicResult]:
        """
        Generate images for multiple prompts with retries.
        
        Args:
            image_model: Model for image generation
            text_model: Model for prompt refinement
            prompt_data_list: List of prompts to process
            **generation_kwargs: Additional arguments for image generation
            
        Returns:
            List of CyclicResult objects
        """
        results = []
        
        for i, prompt_data in enumerate(prompt_data_list):
            self.logger.info(f"Processing prompt {i+1}/{len(prompt_data_list)}")
            
            try:
                result = self.generate_with_retries(
                    image_model=image_model,
                    text_model=text_model,
                    prompt_data=prompt_data,
                    **generation_kwargs
                )
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Failed to process prompt {i+1}: {e}")
                # Create error result
                error_result = CyclicResult(
                    prompt_data=prompt_data,
                    final_response=ModelResponse(
                        status=ResponseStatus.ERROR,
                        error_message=str(e)
                    ),
                    attempts=[],
                    success=False,
                    total_attempts=0,
                    final_quality_score=None,
                    exceeded_max_attempts=False
                )
                results.append(error_result)
        
        return results 