"""Test reporting functionality for ImageBreak framework."""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from ..types import BatchTestResults
from ..core.config import Config


class TestReporter:
    """Generates reports from test results."""
    
    def __init__(self, config: Config):
        """Initialize the test reporter."""
        self.config = config
    
    def generate_report(
        self,
        batch_results: BatchTestResults,
        output_file: Optional[str] = None,
        format: str = "html"
    ) -> str:
        """
        Generate a test report.
        
        Args:
            batch_results: Results to generate report for
            output_file: Output file path
            format: Report format (html, json, csv)
            
        Returns:
            Path to generated report file
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = str(self.config.output_dir / f"imagebreak_report_{timestamp}.{format}")
        
        if format.lower() == "json":
            return self._generate_json_report(batch_results, output_file)
        elif format.lower() == "csv":
            return self._generate_csv_report(batch_results, output_file)
        elif format.lower() == "html":
            return self._generate_html_report(batch_results, output_file)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_json_report(self, batch_results: BatchTestResults, output_file: str) -> str:
        """Generate JSON report."""
        # Convert to serializable format
        report_data = {
            "summary": batch_results.summary_stats,
            "test_info": {
                "start_time": batch_results.start_time.isoformat(),
                "end_time": batch_results.end_time.isoformat() if batch_results.end_time else None,
                "total_results": len(batch_results.results)
            },
            "results": []
        }
        
        for result in batch_results.results:
            result_data = {
                "prompt": {
                    "original": result.prompt_data.original_prompt,
                    "altered": result.prompt_data.altered_prompt,
                    "topic": result.prompt_data.topic
                },
                "model": result.model_name,
                "response": {
                    "status": result.response.status.value,
                    "error_message": result.response.error_message,
                    "image_path": result.response.image_path,
                    "image_url": result.response.image_url
                },
                "moderation": {
                    "flagged": result.moderation_result.flagged if result.moderation_result else None,
                    "labels": result.moderation_result.labels if result.moderation_result else []
                } if result.moderation_result else None,
                "metrics": result.success_metrics
            }
            report_data["results"].append(result_data)
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        return output_file
    
    def _generate_csv_report(self, batch_results: BatchTestResults, output_file: str) -> str:
        """Generate CSV report."""
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            header = [
                "model", "original_prompt", "altered_prompt", "topic", 
                "response_status", "generated_successfully", "blocked_by_filter",
                "image_path", "moderation_flagged", "moderation_labels"
            ]
            writer.writerow(header)
            
            # Data rows
            for result in batch_results.results:
                row = [
                    result.model_name,
                    result.prompt_data.original_prompt,
                    result.prompt_data.altered_prompt or "",
                    result.prompt_data.topic or "",
                    result.response.status.value,
                    result.success_metrics.get("generated_successfully", False),
                    result.success_metrics.get("blocked_by_filter", False),
                    result.response.image_path or "",
                    result.moderation_result.flagged if result.moderation_result else "",
                    "|".join([label.get("label", "") for label in result.moderation_result.labels]) if result.moderation_result else ""
                ]
                writer.writerow(row)
        
        return output_file
    
    def _generate_html_report(self, batch_results: BatchTestResults, output_file: str) -> str:
        """Generate HTML report."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ImageBreak Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .metric {{ display: inline-block; margin-right: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .success {{ color: green; }}
                .blocked {{ color: orange; }}
                .error {{ color: red; }}
                .flagged {{ background-color: #ffebee; }}
            </style>
        </head>
        <body>
            <h1>ImageBreak Safety Test Report</h1>
            
            <div class="summary">
                <h2>Test Summary</h2>
                <div class="metric"><strong>Total Tests:</strong> {batch_results.summary_stats.get('total_tests', 0)}</div>
                <div class="metric"><strong>Successful:</strong> {batch_results.summary_stats.get('successful_generations', 0)}</div>
                <div class="metric"><strong>Blocked:</strong> {batch_results.summary_stats.get('blocked_by_filters', 0)}</div>
                <div class="metric"><strong>Errors:</strong> {batch_results.summary_stats.get('errors', 0)}</div>
                <div class="metric"><strong>Success Rate:</strong> {batch_results.summary_stats.get('success_rate', 0):.1%}</div>
                <div class="metric"><strong>Filter Bypass Rate:</strong> {batch_results.summary_stats.get('filter_bypass_rate', 0):.1%}</div>
            </div>
            
            <h2>Detailed Results</h2>
            <table>
                <tr>
                    <th>Model</th>
                    <th>Prompt</th>
                    <th>Status</th>
                    <th>Moderation</th>
                    <th>Image</th>
                </tr>
        """
        
        for result in batch_results.results:
            status_class = "success" if result.response.status.value == 1 else "blocked" if result.response.status.value == 0 else "error"
            moderation_class = "flagged" if result.moderation_result and result.moderation_result.flagged else ""
            
            prompt_display = result.prompt_data.altered_prompt[:100] if result.prompt_data.altered_prompt else result.prompt_data.original_prompt[:100]
            if len(prompt_display) == 100:
                prompt_display += "..."
            
            moderation_info = ""
            if result.moderation_result:
                moderation_info = f"Flagged: {result.moderation_result.flagged}"
                if result.moderation_result.labels:
                    labels = [label.get("label", "") for label in result.moderation_result.labels[:3]]
                    moderation_info += f"<br>Labels: {', '.join(labels)}"
            
            image_info = ""
            if result.response.image_path:
                image_info = f"<a href='{result.response.image_path}'>View Image</a>"
            
            html_content += f"""
                <tr class="{moderation_class}">
                    <td>{result.model_name}</td>
                    <td>{prompt_display}</td>
                    <td class="{status_class}">{result.response.status.name}</td>
                    <td>{moderation_info}</td>
                    <td>{image_info}</td>
                </tr>
            """
        
        html_content += """
            </table>
        </body>
        </html>
        """
        
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        return output_file 