"""
Evaluation module for comparing transcriptions with ground truth
"""

import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

from batch_processor import BatchProcessingResult, TranscriptionResult


@dataclass
class EvaluationMetrics:
    """Metrics for evaluating transcription accuracy"""
    total_images: int
    successful_transcriptions: int
    failed_transcriptions: int
    images_with_ground_truth: int
    average_processing_time: float
    total_processing_time: float


class TranscriptionEvaluator:
    """Evaluate transcription results against ground truth"""
    
    def __init__(self):
        pass
    
    def calculate_metrics(self, batch_result: BatchProcessingResult) -> EvaluationMetrics:
        """Calculate evaluation metrics from batch results"""
        successful = batch_result.successful
        failed = batch_result.failed
        with_gt = sum(1 for r in batch_result.results if r.ground_truth is not None)
        
        processing_times = [r.processing_time for r in batch_result.results if r.processing_time]
        avg_time = sum(processing_times) / len(processing_times) if processing_times else 0.0
        
        return EvaluationMetrics(
            total_images=batch_result.total_images,
            successful_transcriptions=successful,
            failed_transcriptions=failed,
            images_with_ground_truth=with_gt,
            average_processing_time=avg_time,
            total_processing_time=batch_result.processing_time
        )
    
    def print_summary(self, batch_result: BatchProcessingResult, metrics: EvaluationMetrics):
        """Print a summary of the batch processing results"""
        print("\n" + "="*70)
        print("BATCH PROCESSING SUMMARY")
        print("="*70)
        print(f"Total images processed: {metrics.total_images}")
        print(f"Successful transcriptions: {metrics.successful_transcriptions}")
        print(f"Failed transcriptions: {metrics.failed_transcriptions}")
        print(f"Images with ground truth: {metrics.images_with_ground_truth}")
        print(f"Average processing time: {metrics.average_processing_time:.2f}s")
        print(f"Total processing time: {metrics.total_processing_time:.2f}s")
        print("="*70)
        
        if metrics.failed_transcriptions > 0:
            print("\nFailed images:")
            for result in batch_result.results:
                if result.error:
                    print(f"  - {Path(result.image_path).name}: {result.error}")
    
    def save_detailed_report(
        self,
        batch_result: BatchProcessingResult,
        metrics: EvaluationMetrics,
        output_path: str
    ):
        """Save a detailed evaluation report"""
        # Calculate detailed metrics
        detailed_metrics = self.calculate_detailed_metrics(batch_result)
        
        # Build comparison results
        comparison_results = []
        for r in batch_result.results:
            result_entry = {
                "image": Path(r.image_path).name,
                "image_path": r.image_path,
                "transcription": r.transcription,
                "extracted_data": r.extracted_data,
                "ground_truth": r.ground_truth,
                "processing_time": r.processing_time,
                "error": r.error,
                "has_ground_truth": r.ground_truth is not None
            }
            
            # Add comparison if ground truth exists
            if r.ground_truth and r.transcription:
                comparison = self.compare_with_ground_truth(
                    r.transcription,
                    r.ground_truth,
                    r.extracted_data
                )
                result_entry["comparison"] = comparison
            
            comparison_results.append(result_entry)
        
        report = {
            "summary": {
                "total_images": metrics.total_images,
                "successful_transcriptions": metrics.successful_transcriptions,
                "failed_transcriptions": metrics.failed_transcriptions,
                "images_with_ground_truth": metrics.images_with_ground_truth,
                "average_processing_time": metrics.average_processing_time,
                "total_processing_time": metrics.total_processing_time,
                "overall_accuracy": detailed_metrics["overall_accuracy"],
                "total_comparisons": detailed_metrics["total_comparisons"]
            },
            "field_statistics": detailed_metrics["field_statistics"],
            "results": comparison_results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"Detailed report saved to: {output_path}")
        
        # Print field-level statistics
        if detailed_metrics["field_statistics"]:
            print("\nField-Level Accuracy:")
            print("-" * 70)
            for field, stats in detailed_metrics["field_statistics"].items():
                print(f"{field}:")
                print(f"  Exact Match Rate: {stats.get('exact_match_rate', 0):.1%}")
                print(f"  Partial Match Rate: {stats.get('partial_match_rate', 0):.1%}")
                print(f"  No Match Rate: {stats.get('no_match_rate', 0):.1%}")
            print(f"\nOverall Accuracy: {detailed_metrics['overall_accuracy']:.1%}")
            print("=" * 70)
    
    def compare_with_ground_truth(self, transcription: str, ground_truth: Dict, extracted_data: Optional[Dict] = None) -> Dict:
        """
        Compare transcription with ground truth using improved metrics
        
        Args:
            transcription: The transcribed text (may be JSON string or plain text)
            ground_truth: Ground truth dictionary
            extracted_data: Optional pre-parsed structured data
        
        Returns:
            Dictionary with detailed comparison results
        """
        import json
        import re
        
        comparison = {
            "transcription": transcription,
            "ground_truth": ground_truth,
            "extracted_data": {},
            "matches": {},
            "field_accuracy": {},
            "overall_accuracy": 0.0
        }
        
        # Try to parse transcription as JSON if extracted_data not provided
        if extracted_data is None:
            if isinstance(transcription, str):
                try:
                    # Try parsing as JSON
                    if transcription.strip().startswith('{'):
                        extracted_data = json.loads(transcription)
                    # Try extracting JSON from markdown code blocks
                    elif "```json" in transcription:
                        json_match = re.search(r'```json\s*(\{.*?\})\s*```', transcription, re.DOTALL)
                        if json_match:
                            extracted_data = json.loads(json_match.group(1))
                    elif "```" in transcription:
                        json_match = re.search(r'```\s*(\{.*?\})\s*```', transcription, re.DOTALL)
                        if json_match:
                            extracted_data = json.loads(json_match.group(1))
                except:
                    pass
        else:
            extracted_data = extracted_data
        
        comparison["extracted_data"] = extracted_data
        
        # If ground truth is structured (like JSON with fields)
        if isinstance(ground_truth, dict):
            matches = {}
            field_scores = {}
            
            for key, expected_value in ground_truth.items():
                if not isinstance(expected_value, str):
                    expected_value = str(expected_value)
                
                # Try to get extracted value
                extracted_value = None
                if extracted_data and key in extracted_data:
                    extracted_value = extracted_data[key]
                    if extracted_value is None:
                        extracted_value = ""
                    else:
                        extracted_value = str(extracted_value).strip()
                
                # If not found in structured data, search in raw transcription
                if extracted_value is None or extracted_value == "":
                    transcription_lower = transcription.lower()
                    expected_lower = expected_value.lower()
                    # Check if expected value appears in transcription
                    found_in_text = expected_lower in transcription_lower
                    matches[key] = {
                        "expected": expected_value,
                        "extracted": None,
                        "found_in_text": found_in_text,
                        "exact_match": False,
                        "partial_match": found_in_text
                    }
                    field_scores[key] = 1.0 if found_in_text else 0.0
                else:
                    # Compare extracted value with expected
                    expected_clean = expected_value.strip().lower()
                    extracted_clean = extracted_value.strip().lower()
                    
                    exact_match = expected_clean == extracted_clean
                    
                    # Partial match: check if key parts match
                    partial_match = False
                    if not exact_match:
                        # For dates, check if numbers match
                        if key == "date":
                            expected_nums = re.findall(r'\d+', expected_value)
                            extracted_nums = re.findall(r'\d+', extracted_value)
                            partial_match = set(expected_nums) == set(extracted_nums)
                        # For totals, check if numbers match (ignore currency symbols)
                        elif key == "total":
                            expected_num = re.search(r'[\d.]+', expected_value)
                            extracted_num = re.search(r'[\d.]+', extracted_value)
                            if expected_num and extracted_num:
                                partial_match = expected_num.group() == extracted_num.group()
                        # For text fields, check if significant words match
                        else:
                            expected_words = set(re.findall(r'\w+', expected_clean))
                            extracted_words = set(re.findall(r'\w+', extracted_clean))
                            if expected_words and extracted_words:
                                overlap = len(expected_words & extracted_words) / len(expected_words)
                                partial_match = overlap >= 0.7
                    
                    matches[key] = {
                        "expected": expected_value,
                        "extracted": extracted_value,
                        "found_in_text": None,
                        "exact_match": exact_match,
                        "partial_match": partial_match or exact_match
                    }
                    
                    # Score: 1.0 for exact, 0.7 for partial, 0.0 for no match
                    if exact_match:
                        field_scores[key] = 1.0
                    elif partial_match:
                        field_scores[key] = 0.7
                    else:
                        field_scores[key] = 0.0
            
            comparison["matches"] = matches
            comparison["field_accuracy"] = field_scores
            
            # Calculate overall accuracy
            if field_scores:
                comparison["overall_accuracy"] = sum(field_scores.values()) / len(field_scores)
        
        return comparison
    
    def calculate_detailed_metrics(self, batch_result: BatchProcessingResult) -> Dict:
        """Calculate detailed field-level accuracy metrics"""
        field_stats = {}
        all_comparisons = []
        
        for result in batch_result.results:
            if result.ground_truth and result.transcription:
                comparison = self.compare_with_ground_truth(
                    result.transcription, 
                    result.ground_truth,
                    result.extracted_data
                )
                all_comparisons.append(comparison)
                
                # Aggregate field statistics
                for field, match_data in comparison.get("matches", {}).items():
                    if field not in field_stats:
                        field_stats[field] = {
                            "total": 0,
                            "exact_matches": 0,
                            "partial_matches": 0,
                            "no_matches": 0
                        }
                    
                    field_stats[field]["total"] += 1
                    if match_data.get("exact_match"):
                        field_stats[field]["exact_matches"] += 1
                    elif match_data.get("partial_match"):
                        field_stats[field]["partial_matches"] += 1
                    else:
                        field_stats[field]["no_matches"] += 1
        
        # Calculate percentages
        for field in field_stats:
            total = field_stats[field]["total"]
            if total > 0:
                field_stats[field]["exact_match_rate"] = field_stats[field]["exact_matches"] / total
                field_stats[field]["partial_match_rate"] = field_stats[field]["partial_matches"] / total
                field_stats[field]["no_match_rate"] = field_stats[field]["no_matches"] / total
        
        # Calculate overall accuracy
        if all_comparisons:
            overall_accuracy = sum(c.get("overall_accuracy", 0) for c in all_comparisons) / len(all_comparisons)
        else:
            overall_accuracy = 0.0
        
        return {
            "field_statistics": field_stats,
            "overall_accuracy": overall_accuracy,
            "total_comparisons": len(all_comparisons)
        }

