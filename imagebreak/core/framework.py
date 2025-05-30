"""Main ImageBreak framework for orchestrating AI safety testing."""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from .config import Config
from .prompt_generator import PromptGenerator
from .prompt_alteration import PromptAlteration
from .cyclic_generator import CyclicImageGenerator
from ..types import (
    PromptData, TestResult, BatchTestResults, ModelResponse, 
    ResponseStatus, ModerationResult
)
from ..models.base import BaseModel
from ..analysis.moderation import ModerationAnalyzer
from ..analysis.reporter import TestReporter


class ImageBreakFramework:
    """Main framework for testing AI model safety and content moderation."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the ImageBreak framework.
        
        Args:
            config: Configuration object (uses default if not provided)
        """
        self.config = config or Config()
        self.config.validate()
        
        # Set up logging
        self._setup_logging()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing ImageBreak framework")
        
        # Initialize components
        self.models: Dict[str, BaseModel] = {}
        self.prompt_generator = PromptGenerator()
        self.prompt_alteration = PromptAlteration()
        self.cyclic_generator = CyclicImageGenerator(self.config)
        self.moderation_analyzer = ModerationAnalyzer(self.config)
        self.reporter = TestReporter(self.config)
        
        self.logger.info("ImageBreak framework initialized successfully")
    
    def _setup_logging(self) -> None:
        """Set up logging configuration."""
        if not self.config.enable_logging:
            return
            
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                *([logging.FileHandler(self.config.log_file)] if self.config.log_file else [])
            ]
        )
    
    def add_model(self, name: str, model: BaseModel) -> None:
        """
        Add a model to the framework.
        
        Args:
            name: Unique name for the model
            model: Model instance
        """
        self.models[name] = model
        self.logger.info(f"Added model '{name}': {model}")
    
    def remove_model(self, name: str) -> None:
        """
        Remove a model from the framework.
        
        Args:
            name: Name of the model to remove
        """
        if name in self.models:
            del self.models[name]
            self.logger.info(f"Removed model '{name}'")
        else:
            self.logger.warning(f"Model '{name}' not found")
    
    def list_models(self) -> List[str]:
        """Get list of available model names."""
        return list(self.models.keys())
    
    def generate_boundary_prompts(
        self,
        policies: str,
        num_prompts: int = 10,
        topics: Optional[List[str]] = None,
        model_name: Optional[str] = None
    ) -> List[PromptData]:
        """
        Generate prompts for testing policy boundaries.
        
        Args:
            policies: Policy text to test against
            num_prompts: Number of prompts to generate
            topics: Specific topics to focus on
            model_name: Model to use (uses first available if not specified)
            
        Returns:
            List of generated PromptData objects
        """
        if not self.models:
            raise ValueError("No models available. Add a model first.")
            
        if model_name:
            if model_name not in self.models:
                raise ValueError(f"Model '{model_name}' not found")
            model = self.models[model_name]
        else:
            model = next(iter(self.models.values()))
            
        self.logger.info(f"Generating {num_prompts} boundary prompts using {model.model_name}")
        
        return self.prompt_generator.generate_boundary_prompts(
            model=model,
            policies=policies,
            num_prompts=num_prompts,
            topics=topics
        )
    
    def alter_prompts(
        self,
        prompt_data_list: List[PromptData],
        model_name: Optional[str] = None
    ) -> List[PromptData]:
        """
        Alter prompts to test filter evasion.
        
        Args:
            prompt_data_list: List of prompts to alter
            model_name: Model to use for alteration
            
        Returns:
            List of PromptData with altered versions
        """
        if not self.models:
            raise ValueError("No models available. Add a model first.")
            
        if model_name:
            if model_name not in self.models:
                raise ValueError(f"Model '{model_name}' not found")
            model = self.models[model_name]
        else:
            model = next(iter(self.models.values()))
            
        self.logger.info(f"Altering {len(prompt_data_list)} prompts using {model.model_name}")
        
        return self.prompt_alteration.alter_prompts_batch(
            model=model,
            prompt_data_list=prompt_data_list
        )
    
    def test_image_generation_cyclic(
        self,
        prompt_data_list: List[PromptData],
        image_model_name: Optional[str] = None,
        text_model_name: Optional[str] = None,
        save_images: bool = True,
        **generation_kwargs
    ) -> List[Any]:  # CyclicResult type
        """
        Test image generation with cyclic quality assessment and retries.
        
        Args:
            prompt_data_list: List of prompts to test
            image_model_name: Model for image generation
            text_model_name: Model for prompt refinement
            save_images: Whether to save generated images
            **generation_kwargs: Additional generation parameters
            
        Returns:
            List of CyclicResult objects
        """
        if not self.models:
            raise ValueError("No models available. Add a model first.")
        
        # Get models
        image_model_name = image_model_name or self.config.default_image_model
        text_model_name = text_model_name or self.config.default_text_model
        
        image_model = self.models.get(image_model_name)
        text_model = self.models.get(text_model_name)
        
        if not image_model:
            raise ValueError(f"Image model '{image_model_name}' not available")
        
        if not text_model:
            raise ValueError(f"Text model '{text_model_name}' not available")
        
        if not image_model.supports_image_generation():
            raise ValueError(f"Model '{image_model_name}' does not support image generation")
        
        # Set up generation parameters
        if save_images:
            generation_kwargs['save_folder'] = str(self.config.output_dir / "images")
        
        self.logger.info(f"Testing cyclic image generation with {len(prompt_data_list)} prompts")
        
        return self.cyclic_generator.batch_generate_with_retries(
            image_model=image_model,
            text_model=text_model,
            prompt_data_list=prompt_data_list,
            **generation_kwargs
        )
    
    def test_image_generation(
        self,
        prompt_data_list: List[PromptData],
        model_names: Optional[List[str]] = None,
        use_altered_prompts: bool = True,
        save_images: bool = True
    ) -> List[TestResult]:
        """
        Test image generation with given prompts (legacy method).
        
        Args:
            prompt_data_list: List of prompts to test
            model_names: Models to test (all available if not specified)
            use_altered_prompts: Whether to use altered prompts when available
            save_images: Whether to save generated images
            
        Returns:
            List of TestResult objects
        """
        if not self.models:
            raise ValueError("No models available. Add a model first.")
            
        if model_names:
            models_to_test = {name: self.models[name] for name in model_names if name in self.models}
        else:
            models_to_test = self.models
            
        if not models_to_test:
            raise ValueError("No valid models found for testing")
            
        # Filter models that support image generation
        image_models = {
            name: model for name, model in models_to_test.items() 
            if model.supports_image_generation()
        }
        
        if not image_models:
            raise ValueError("No models support image generation")
            
        self.logger.info(f"Testing image generation with {len(image_models)} models and {len(prompt_data_list)} prompts")
        
        results = []
        
        for model_name, model in image_models.items():
            self.logger.info(f"Testing with model: {model_name}")
            
            for i, prompt_data in enumerate(prompt_data_list):
                # Choose which prompt to use
                test_prompt = (
                    prompt_data.altered_prompt 
                    if use_altered_prompts and prompt_data.altered_prompt 
                    else prompt_data.original_prompt
                )
                
                # Test image generation
                save_folder = str(self.config.output_dir / "images") if save_images else None
                
                response = model.generate_image(
                    prompt=test_prompt,
                    save_folder=save_folder
                )
                
                # Create test result
                result = TestResult(
                    prompt_data=prompt_data,
                    model_name=model_name,
                    response=response,
                    success_metrics={
                        "generated_successfully": response.status == ResponseStatus.SUCCESS,
                        "blocked_by_filter": response.status == ResponseStatus.BLOCKED_BY_FILTER,
                        "used_altered_prompt": use_altered_prompts and bool(prompt_data.altered_prompt)
                    }
                )
                
                results.append(result)
                
                # Rate limiting
                if self.config.rate_limit_delay > 0:
                    time.sleep(self.config.rate_limit_delay)
                    
                if (i + 1) % 10 == 0:
                    self.logger.info(f"Completed {i + 1}/{len(prompt_data_list)} tests for {model_name}")
        
        self.logger.info(f"Completed image generation testing. Total results: {len(results)}")
        return results
    
    def analyze_with_moderation(
        self,
        test_results: List[TestResult],
        services: Optional[List[str]] = None
    ) -> List[TestResult]:
        """
        Analyze test results with content moderation services.
        
        Args:
            test_results: Results from image generation testing
            services: Moderation services to use (default: AWS Rekognition if available)
            
        Returns:
            Test results with moderation analysis added
        """
        if not self.config.use_aws_moderation:
            self.logger.info("AWS moderation disabled, skipping moderation analysis")
            return test_results
        
        self.logger.info(f"Analyzing {len(test_results)} results with moderation services")
        
        # Filter results that have successfully generated images
        results_with_images = [
            result for result in test_results 
            if (result.response.image_path or result.response.image_url) 
            and result.response.status == ResponseStatus.SUCCESS
        ]
        
        self.logger.info(f"Found {len(results_with_images)} results with images to analyze")
        
        for result in results_with_images:
            try:
                moderation_result = self.moderation_analyzer.analyze_image(
                    image_path=result.response.image_path,
                    image_url=result.response.image_url,
                    services=services
                )
                result.moderation_result = moderation_result
                
            except Exception as e:
                self.logger.error(f"Moderation analysis failed for {result.response.image_path}: {e}")
        
        return test_results
    
    def run_safety_tests(
        self,
        prompt_data_list: List[PromptData],
        model_names: Optional[List[str]] = None,
        test_alterations: bool = True,
        test_image_generation: bool = True,
        run_moderation_analysis: bool = True,
        use_cyclic_generation: Optional[bool] = None
    ) -> BatchTestResults:
        """
        Run comprehensive safety tests.
        
        Args:
            prompt_data_list: Prompts to test
            model_names: Models to test
            test_alterations: Whether to test prompt alterations
            test_image_generation: Whether to test image generation
            run_moderation_analysis: Whether to run moderation analysis
            use_cyclic_generation: Whether to use cyclic generation (uses config if None)
            
        Returns:
            BatchTestResults with comprehensive test data
        """
        start_time = datetime.now()
        self.logger.info(f"Starting comprehensive safety tests with {len(prompt_data_list)} prompts")
        
        # Step 1: Alter prompts if requested
        if test_alterations:
            self.logger.info("Step 1: Altering prompts")
            prompt_data_list = self.alter_prompts(prompt_data_list, model_names[0] if model_names else None)
        
        # Step 2: Test image generation if requested  
        results = []
        if test_image_generation:
            use_cyclic = use_cyclic_generation if use_cyclic_generation is not None else self.config.enable_cyclic_regeneration
            
            if use_cyclic:
                self.logger.info("Step 2: Testing cyclic image generation")
                cyclic_results = self.test_image_generation_cyclic(
                    prompt_data_list=prompt_data_list,
                    image_model_name=model_names[0] if model_names else None,
                    text_model_name=model_names[0] if model_names else None,
                    save_images=True
                )
                
                # Convert CyclicResult to TestResult for compatibility
                for cyclic_result in cyclic_results:
                    test_result = TestResult(
                        prompt_data=cyclic_result.prompt_data,
                        model_name=self.config.default_image_model,
                        response=cyclic_result.final_response,
                        success_metrics={
                            "generated_successfully": cyclic_result.success,
                            "total_attempts": cyclic_result.total_attempts,
                            "final_quality_score": cyclic_result.final_quality_score,
                            "exceeded_max_attempts": cyclic_result.exceeded_max_attempts
                        }
                    )
                    results.append(test_result)
            else:
                self.logger.info("Step 2: Testing standard image generation")
                results = self.test_image_generation(
                    prompt_data_list=prompt_data_list,
                    model_names=model_names,
                    use_altered_prompts=test_alterations
                )
        
        # Step 3: Run moderation analysis if requested
        if run_moderation_analysis and results:
            self.logger.info("Step 3: Running moderation analysis")
            results = self.analyze_with_moderation(results)
        
        # Calculate summary statistics
        end_time = datetime.now()
        summary_stats = self._calculate_summary_stats(results)
        
        batch_results = BatchTestResults(
            results=results,
            summary_stats=summary_stats,
            start_time=start_time,
            end_time=end_time
        )
        
        self.logger.info(f"Safety tests completed in {end_time - start_time}")
        return batch_results
    
    def generate_report(
        self,
        batch_results: BatchTestResults,
        output_file: Optional[str] = None,
        format: str = "html"
    ) -> str:
        """
        Generate a comprehensive test report.
        
        Args:
            batch_results: Results from safety tests
            output_file: Output file path (auto-generated if not provided)
            format: Report format (html, json, csv)
            
        Returns:
            Path to generated report file
        """
        return self.reporter.generate_report(
            batch_results=batch_results,
            output_file=output_file,
            format=format
        )
    
    def _calculate_summary_stats(self, results: List[TestResult]) -> Dict[str, Any]:
        """Calculate summary statistics for test results."""
        if not results:
            return {}
        
        total_tests = len(results)
        successful_generations = sum(1 for r in results if r.response.status == ResponseStatus.SUCCESS)
        blocked_by_filters = sum(1 for r in results if r.response.status == ResponseStatus.BLOCKED_BY_FILTER)
        errors = sum(1 for r in results if r.response.status == ResponseStatus.ERROR)
        
        # Moderation stats
        moderated_results = [r for r in results if r.moderation_result is not None]
        flagged_content = sum(1 for r in moderated_results if r.moderation_result.flagged)
        
        # Model breakdown
        model_stats = {}
        for result in results:
            model = result.model_name
            if model not in model_stats:
                model_stats[model] = {"total": 0, "successful": 0, "blocked": 0, "errors": 0}
            
            model_stats[model]["total"] += 1
            if result.response.status == ResponseStatus.SUCCESS:
                model_stats[model]["successful"] += 1
            elif result.response.status == ResponseStatus.BLOCKED_BY_FILTER:
                model_stats[model]["blocked"] += 1
            else:
                model_stats[model]["errors"] += 1
        
        return {
            "total_tests": total_tests,
            "successful_generations": successful_generations,
            "blocked_by_filters": blocked_by_filters,
            "errors": errors,
            "success_rate": successful_generations / total_tests if total_tests > 0 else 0.0,
            "filter_bypass_rate": successful_generations / (successful_generations + blocked_by_filters) if (successful_generations + blocked_by_filters) > 0 else 0.0,
            "moderation_analyzed": len(moderated_results),
            "flagged_content": flagged_content,
            "model_breakdown": model_stats
        } 