"""
Model comparison module for evaluating multiple LLM models
Compares performance of different models on the same set of images
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from batch_processor import BatchProcessor, BatchProcessingResult, TranscriptionResult
from evaluator import TranscriptionEvaluator, EvaluationMetrics
from image_transcriber import create_transcriber


@dataclass
class ModelComparisonResult:
    """Results of comparing multiple models"""
    models: List[str]
    comparison_data: Dict[str, BatchProcessingResult]
    timestamp: str
    images_dir: str
    ground_truth_dir: Optional[str]


class ModelComparator:
    """Compare performance of multiple models"""
    
    def __init__(self, images_dir: str, ground_truth_dir: Optional[str] = None):
        """
        Initialize model comparator
        
        Args:
            images_dir: Directory containing images to process
            ground_truth_dir: Optional directory containing ground truth files
        """
        self.images_dir = images_dir
        self.ground_truth_dir = ground_truth_dir
        self.evaluator = TranscriptionEvaluator()
    
    def compare_models(
        self,
        model_configs: List[Dict],
        prompt: Optional[str] = None,
        max_images: Optional[int] = None,
        save_individual_results: bool = True
    ) -> ModelComparisonResult:
        """
        Compare multiple models on the same set of images
        
        Args:
            model_configs: List of model configuration dicts, each containing:
                - 'name': Display name for the model
                - 'provider': Provider name (openai, anthropic, etc.)
                - 'model_name': Model name/ID
                - 'api_key': Optional API key
                - 'kwargs': Optional additional parameters
            prompt: Custom prompt for transcription
            max_images: Maximum number of images to process
            save_individual_results: Whether to save individual model results
        
        Returns:
            ModelComparisonResult with comparison data
        """
        comparison_data = {}
        model_names = []
        
        print(f"\n{'='*70}")
        print(f"MODEL COMPARISON")
        print(f"{'='*70}")
        print(f"Comparing {len(model_configs)} models on images from: {self.images_dir}")
        if self.ground_truth_dir:
            print(f"Ground truth directory: {self.ground_truth_dir}")
        print(f"{'='*70}\n")
        
        for i, config in enumerate(model_configs, 1):
            model_name = config.get('name', f"{config['provider']}_{config['model_name']}")
            model_names.append(model_name)
            
            print(f"\n[{i}/{len(model_configs)}] Processing with: {model_name}")
            print("-" * 70)
            
            # Create transcriber
            transcriber = create_transcriber(
                provider=config['provider'],
                model_name=config['model_name'],
                api_key=config.get('api_key'),
                **config.get('kwargs', {})
            )
            
            # Process batch
            processor = BatchProcessor(
                transcriber=transcriber,
                images_dir=self.images_dir,
                ground_truth_dir=self.ground_truth_dir
            )
            
            batch_result = processor.process_batch(
                prompt=prompt,
                max_images=max_images
            )
            
            comparison_data[model_name] = batch_result
            
            comparison_data[model_name] = batch_result
            
            # Individual results are now saved via save_comparison_results to results/comparison/
            # We skip saving to the main directory to avoid clutter
        
        return ModelComparisonResult(
            models=model_names,
            comparison_data=comparison_data,
            timestamp=datetime.now().isoformat(),
            images_dir=self.images_dir,
            ground_truth_dir=self.ground_truth_dir
        )
    
    def generate_comparison_report(
        self,
        comparison_result: ModelComparisonResult,
        output_path: str = "model_comparison_report.json"
    ):
        """Generate a detailed comparison report"""
        
        report = {
            "timestamp": comparison_result.timestamp,
            "images_dir": comparison_result.images_dir,
            "ground_truth_dir": comparison_result.ground_truth_dir,
            "models_compared": comparison_result.models,
            "summary": {},
            "per_model_metrics": {},
            "per_image_comparison": []
        }
        
        # Calculate metrics for each model
        for model_name in comparison_result.models:
            batch_result = comparison_result.comparison_data[model_name]
            metrics = self.evaluator.calculate_metrics(batch_result)
            detailed_metrics = self.evaluator.calculate_detailed_metrics(batch_result)
            
            report["per_model_metrics"][model_name] = {
                "total_images": metrics.total_images,
                "successful_transcriptions": metrics.successful_transcriptions,
                "failed_transcriptions": metrics.failed_transcriptions,
                "success_rate": metrics.successful_transcriptions / metrics.total_images if metrics.total_images > 0 else 0,
                "average_processing_time": metrics.average_processing_time,
                "total_processing_time": metrics.total_processing_time,
                "images_with_ground_truth": metrics.images_with_ground_truth,
                "overall_accuracy": detailed_metrics["overall_accuracy"],
                "field_statistics": detailed_metrics["field_statistics"]
            }
        
        # Per-image comparison
        if comparison_result.models:
            first_model = comparison_result.models[0]
            first_batch = comparison_result.comparison_data[first_model]
            
            for result in first_batch.results:
                image_name = Path(result.image_path).name
                image_comparison = {
                    "image": image_name,
                    "image_path": result.image_path,
                    "ground_truth": result.ground_truth,
                    "models": {}
                }
                
                for model_name in comparison_result.models:
                    batch_result = comparison_result.comparison_data[model_name]
                    # Find corresponding result for this image
                    matching_result = next(
                        (r for r in batch_result.results if Path(r.image_path).name == image_name),
                        None
                    )
                    
                    if matching_result:
                        model_data = {
                            "transcription": matching_result.transcription,
                            "extracted_data": matching_result.extracted_data,
                            "processing_time": matching_result.processing_time,
                            "error": matching_result.error,
                            "success": matching_result.error is None
                        }
                        
                        # Add comparison if ground truth exists
                        if result.ground_truth and matching_result.transcription:
                            comparison = self.evaluator.compare_with_ground_truth(
                                matching_result.transcription,
                                result.ground_truth,
                                matching_result.extracted_data
                            )
                            model_data["comparison"] = {
                                "overall_accuracy": comparison.get("overall_accuracy", 0),
                                "field_accuracy": comparison.get("field_accuracy", {})
                            }
                        
                        image_comparison["models"][model_name] = model_data
                
                report["per_image_comparison"].append(image_comparison)
        
        # Summary statistics
        if report["per_model_metrics"]:
            report["summary"] = {
                "best_success_rate": max(
                    m["success_rate"] for m in report["per_model_metrics"].values()
                ),
                "fastest_average_time": min(
                    m["average_processing_time"] for m in report["per_model_metrics"].values()
                ),
                "fastest_total_time": min(
                    m["total_processing_time"] for m in report["per_model_metrics"].values()
                ),
                "best_overall_accuracy": max(
                    m.get("overall_accuracy", 0) for m in report["per_model_metrics"].values()
                )
            }
        
        # Add accuracy comparison section
        report["accuracy_comparison"] = self._generate_accuracy_comparison(report["per_model_metrics"])
        
        # Save report
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\nComparison report saved to: {output_path}")
        return report
    
    def _generate_accuracy_comparison(self, per_model_metrics: Dict) -> Dict:
        """Generate accuracy comparison between models"""
        accuracy_comparison = {
            "overall_accuracy": {},
            "field_accuracy": {}
        }
        
        # Overall accuracy comparison
        for model_name, metrics in per_model_metrics.items():
            accuracy_comparison["overall_accuracy"][model_name] = metrics.get("overall_accuracy", 0.0)
        
        # Field-level accuracy comparison
        # Get all fields from first model
        first_model_metrics = next(iter(per_model_metrics.values()))
        field_stats = first_model_metrics.get("field_statistics", {})
        
        for field in field_stats.keys():
            accuracy_comparison["field_accuracy"][field] = {}
            for model_name, metrics in per_model_metrics.items():
                model_field_stats = metrics.get("field_statistics", {})
                if field in model_field_stats:
                    field_data = model_field_stats[field]
                    accuracy_comparison["field_accuracy"][field][model_name] = {
                        "exact_match_rate": field_data.get("exact_match_rate", 0),
                        "partial_match_rate": field_data.get("partial_match_rate", 0),
                        "no_match_rate": field_data.get("no_match_rate", 0),
                        "total": field_data.get("total", 0)
                    }
        
        return accuracy_comparison
    
    def print_comparison_summary(self, comparison_result: ModelComparisonResult):
        """Print a formatted comparison summary"""
        
        print("\n" + "="*70)
        print("AS-IS DATA EXTRACTION SUMMARY")
        print("="*70)
        
        # Calculate detailed metrics for all models
        model_metrics = {}
        for model_name in comparison_result.models:
            batch_result = comparison_result.comparison_data[model_name]
            basic_metrics = self.evaluator.calculate_metrics(batch_result)
            detailed_metrics = self.evaluator.calculate_detailed_metrics(batch_result)
            model_metrics[model_name] = {
                "basic": basic_metrics,
                "detailed": detailed_metrics
            }
        accuracy_data = []
        for model_name in comparison_result.models:
            overall_acc = model_metrics[model_name]["detailed"]["overall_accuracy"]
            accuracy_data.append((model_name, overall_acc))
        
        # Sort by accuracy (descending)
        accuracy_data.sort(key=lambda x: x[1], reverse=True)
        
        for model_name, accuracy in accuracy_data:
            print(f"{model_name:<30} {accuracy:.1%}")
        
        print("="*70)
        
        # Field-level accuracy comparison
        if accuracy_data and model_metrics[accuracy_data[0][0]]["detailed"]["field_statistics"]:
            print("\nField-Level Accuracy Comparison:")
            print("-" * 70)
            
            # Get all fields
            first_model = comparison_result.models[0]
            field_stats = model_metrics[first_model]["detailed"]["field_statistics"]
            
            for field in field_stats.keys():
                print(f"\n{field.upper()}:")
                field_data = []
                for model_name in comparison_result.models:
                    model_field_stats = model_metrics[model_name]["detailed"]["field_statistics"]
                    if field in model_field_stats:
                        exact_rate = model_field_stats[field].get("exact_match_rate", 0)
                        partial_rate = model_field_stats[field].get("partial_match_rate", 0)
                        total_rate = exact_rate + partial_rate
                        field_data.append((model_name, exact_rate, partial_rate, total_rate))
                
                # Sort by total accuracy (exact + partial)
                field_data.sort(key=lambda x: x[3], reverse=True)
                
                print(f"  {'Model':<28} {'Exact':<12} {'Partial':<12} {'Total':<12}")
                print("  " + "-" * 64)
                for model_name, exact, partial, total in field_data:
                    print(f"  {model_name:<28} {exact:<12.1%} {partial:<12.1%} {total:<12.1%}")
        
        print("\n" + "="*70)
        
        # Best performers
        if comparison_result.models:
            best_success = max(
                model_metrics.items(),
                key=lambda x: x[1]["basic"].successful_transcriptions / x[1]["basic"].total_images if x[1]["basic"].total_images > 0 else 0
            )
            fastest_avg = min(
                model_metrics.items(),
                key=lambda x: x[1]["basic"].average_processing_time
            )
            fastest_total = min(
                model_metrics.items(),
                key=lambda x: x[1]["basic"].total_processing_time
            )
            best_accuracy = max(
                model_metrics.items(),
                key=lambda x: x[1]["detailed"]["overall_accuracy"]
            )
            
            print(f"\nBest Success Rate: {best_success[0]} ({best_success[1]['basic'].successful_transcriptions}/{best_success[1]['basic'].total_images})")
            print(f"Best Overall Accuracy: {best_accuracy[0]} ({best_accuracy[1]['detailed']['overall_accuracy']:.1%})")
            print(f"Fastest Average Time: {fastest_avg[0]} ({fastest_avg[1]['basic'].average_processing_time:.2f}s)")
            print(f"Fastest Total Time: {fastest_total[0]} ({fastest_total[1]['basic'].total_processing_time:.2f}s)")
        
        print("="*70 + "\n")
    
    def save_comparison_results(
        self,
        comparison_result: ModelComparisonResult,
        output_dir: str = "results/comparison"
    ):
        """Save all comparison results to a directory"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save individual model results
        for model_name in comparison_result.models:
            batch_result = comparison_result.comparison_data[model_name]
            
            # Calculate metrics for this model
            metrics = self.evaluator.calculate_metrics(batch_result)
            detailed_metrics = self.evaluator.calculate_detailed_metrics(batch_result)
            
            filename = f"{model_name.replace(' ', '_').lower()}.json"
            filepath = output_path / filename
            
            output_data = {
                "model": model_name,
                "timestamp": batch_result.timestamp,
                "total_images": batch_result.total_images,
                "successful": batch_result.successful,
                "failed": batch_result.failed,
                "processing_time": batch_result.processing_time,
                "metrics": {
                    "success_rate": metrics.successful_transcriptions / metrics.total_images if metrics.total_images > 0 else 0,
                    "average_processing_time": metrics.average_processing_time,
                    "total_processing_time": metrics.total_processing_time,
                    "overall_accuracy": detailed_metrics["overall_accuracy"],
                    "field_statistics": detailed_metrics["field_statistics"]
                },
                "results": [
                    {
                        "image_path": r.image_path,
                        "transcription": r.transcription,
                        "ground_truth_path": r.ground_truth_path,
                        "ground_truth": r.ground_truth,
                        "processing_time": r.processing_time,
                        "error": r.error,
                        "input_tokens": r.input_tokens,
                        "output_tokens": r.output_tokens,
                        "total_tokens": r.total_tokens
                    }
                    for r in batch_result.results
                ]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nIndividual model results saved to: {output_dir}/")

