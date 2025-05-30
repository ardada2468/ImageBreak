"""Content moderation analysis for ImageBreak framework."""

import os
import logging
from typing import List, Dict, Any, Optional
import requests

from ..types import ModerationResult
from ..core.config import Config


class ModerationAnalyzer:
    """Analyzes content using various moderation services."""
    
    def __init__(self, config: Config):
        """
        Initialize the moderation analyzer.
        
        Args:
            config: Configuration object with API credentials
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize AWS client if credentials are available
        self.aws_rekognition = None
        if config.aws_access_key_id and config.aws_secret_access_key:
            try:
                import boto3
                self.aws_rekognition = boto3.client(
                    'rekognition',
                    aws_access_key_id=config.aws_access_key_id,
                    aws_secret_access_key=config.aws_secret_access_key,
                    region_name=config.aws_region
                )
                self.logger.info("AWS Rekognition client initialized")
            except ImportError:
                self.logger.warning("boto3 not installed, AWS Rekognition unavailable")
            except Exception as e:
                self.logger.error(f"Failed to initialize AWS Rekognition: {e}")
    
    def analyze_image(
        self,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        services: Optional[List[str]] = None
    ) -> ModerationResult:
        """
        Analyze an image with content moderation services.
        
        Args:
            image_path: Local path to image file
            image_url: URL of image to analyze
            services: List of services to use (default: all available)
            
        Returns:
            ModerationResult with analysis results
        """
        if not image_path and not image_url:
            raise ValueError("Either image_path or image_url must be provided")
        
        # Default to all available services
        if services is None:
            services = self.get_available_services()
        
        # Use image_path if available, otherwise download from URL
        local_image_path = image_path
        if not local_image_path and image_url:
            local_image_path = self._download_image(image_url)
        
        if not local_image_path:
            raise ValueError("Could not obtain image for analysis")
        
        result = ModerationResult(image_path=local_image_path)
        
        # Run analysis with requested services
        for service in services:
            try:
                if service.lower() == "aws_rekognition" and self.aws_rekognition:
                    self._analyze_with_aws_rekognition(local_image_path, result)
                else:
                    self.logger.warning(f"Service '{service}' not available or not implemented")
            except Exception as e:
                self.logger.error(f"Error analyzing with {service}: {e}")
        
        # Determine if content should be flagged based on labels
        result.flagged = self._determine_flagged_status(result)
        
        return result
    
    def _analyze_with_aws_rekognition(
        self, 
        image_path: str, 
        result: ModerationResult
    ) -> None:
        """
        Analyze image with AWS Rekognition.
        
        Args:
            image_path: Path to image file
            result: ModerationResult to update
        """
        try:
            with open(image_path, 'rb') as image_file:
                image_bytes = image_file.read()
            
            response = self.aws_rekognition.detect_moderation_labels(
                Image={'Bytes': image_bytes},
                MinConfidence=35  # Configurable threshold
            )
            
            # Process moderation labels
            for label in response.get('ModerationLabels', []):
                label_data = {
                    'label': label['Name'],
                    'confidence': label['Confidence'],
                    'parent_label': label.get('ParentName'),
                    'service': 'aws_rekognition'
                }
                result.labels.append(label_data)
                result.confidence_scores[label['Name']] = label['Confidence']
            
            result.service = 'aws_rekognition'
            self.logger.info(f"AWS Rekognition found {len(response.get('ModerationLabels', []))} moderation labels")
            
        except Exception as e:
            self.logger.error(f"AWS Rekognition analysis failed: {e}")
            raise
    
    def _download_image(self, image_url: str) -> Optional[str]:
        """
        Download image from URL to temporary file.
        
        Args:
            image_url: URL of image to download
            
        Returns:
            Path to downloaded image or None if failed
        """
        try:
            import tempfile
            import urllib.parse
            
            # Create temporary file
            _, ext = os.path.splitext(urllib.parse.urlparse(image_url).path)
            if not ext:
                ext = '.png'  # Default extension
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            temp_path = temp_file.name
            temp_file.close()
            
            # Download image
            response = requests.get(image_url, stream=True)
            response.raise_for_status()
            
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.logger.info(f"Downloaded image from {image_url} to {temp_path}")
            return temp_path
            
        except Exception as e:
            self.logger.error(f"Failed to download image from {image_url}: {e}")
            return None
    
    def _determine_flagged_status(self, result: ModerationResult) -> bool:
        """
        Determine if content should be flagged based on moderation labels.
        
        Args:
            result: ModerationResult with labels
            
        Returns:
            True if content should be flagged
        """
        # Define threshold and categories that should trigger flagging
        high_confidence_threshold = 80.0
        flagging_categories = [
            'Explicit Nudity', 'Graphic Violence', 'Hate Symbols',
            'Drugs', 'Smoking', 'Alcohol', 'Gambling', 'Violence'
        ]
        
        for label_data in result.labels:
            confidence = label_data.get('confidence', 0)
            label_name = label_data.get('label', '')
            parent_label = label_data.get('parent_label', '')
            
            # Flag if high confidence in concerning categories
            if confidence > high_confidence_threshold:
                if any(category.lower() in label_name.lower() for category in flagging_categories):
                    return True
                if parent_label and any(category.lower() in parent_label.lower() for category in flagging_categories):
                    return True
        
        return False
    
    def get_available_services(self) -> List[str]:
        """Get list of available moderation services."""
        services = []
        
        if self.aws_rekognition:
            services.append("aws_rekognition")
        
        return services
    
    def analyze_directory(
        self,
        directory_path: str,
        services: Optional[List[str]] = None
    ) -> List[ModerationResult]:
        """
        Analyze all images in a directory.
        
        Args:
            directory_path: Path to directory containing images
            services: Moderation services to use
            
        Returns:
            List of ModerationResult objects
        """
        if not os.path.exists(directory_path):
            raise ValueError(f"Directory does not exist: {directory_path}")
        
        # Find image files
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'}
        image_files = []
        
        for filename in os.listdir(directory_path):
            if any(filename.lower().endswith(ext) for ext in image_extensions):
                image_files.append(os.path.join(directory_path, filename))
        
        self.logger.info(f"Found {len(image_files)} images to analyze in {directory_path}")
        
        results = []
        for i, image_path in enumerate(image_files):
            try:
                result = self.analyze_image(image_path=image_path, services=services)
                results.append(result)
                
                if (i + 1) % 10 == 0:
                    self.logger.info(f"Analyzed {i + 1}/{len(image_files)} images")
                    
            except Exception as e:
                self.logger.error(f"Failed to analyze {image_path}: {e}")
        
        self.logger.info(f"Completed analysis of {len(results)} images")
        return results
    
    def get_moderation_statistics(
        self,
        results: List[ModerationResult]
    ) -> Dict[str, Any]:
        """
        Calculate statistics from moderation results.
        
        Args:
            results: List of ModerationResult objects
            
        Returns:
            Dictionary with moderation statistics
        """
        if not results:
            return {}
        
        total_images = len(results)
        flagged_images = sum(1 for r in results if r.flagged)
        
        # Label distribution
        label_counts = {}
        confidence_totals = {}
        
        for result in results:
            for label_data in result.labels:
                label = label_data.get('label', 'Unknown')
                confidence = label_data.get('confidence', 0)
                
                label_counts[label] = label_counts.get(label, 0) + 1
                confidence_totals[label] = confidence_totals.get(label, 0) + confidence
        
        # Calculate average confidences
        average_confidences = {
            label: confidence_totals[label] / label_counts[label]
            for label in label_counts
        }
        
        return {
            "total_images": total_images,
            "flagged_images": flagged_images,
            "flagged_rate": flagged_images / total_images,
            "clean_images": total_images - flagged_images,
            "clean_rate": (total_images - flagged_images) / total_images,
            "label_counts": label_counts,
            "average_confidences": average_confidences,
            "most_common_labels": sorted(label_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        } 