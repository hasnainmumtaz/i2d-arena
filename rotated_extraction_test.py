"""
Rotated extraction test module for testing LLM models' data extraction accuracy on rotated images
"""

import json
import statistics
from dataclasses import dataclass, asdict
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image
from batch_processor import TranscriptionResult
from evaluator import TranscriptionEvaluator


@dataclass
class RotatedExtractionResult:
    """Result of a single rotated extraction test"""
    image_path: str
    rotation_angle: int  # 0, 90, 180, or 270
    model_name: str
    transcription: str
    extracted_data: Optional[Dict] = None
    ground_truth: Optional[Dict] = None
    accuracy: Optional[float] = None  # Overall accuracy from comparison
    field_accuracy: Optional[Dict[str, float]] = None  # Per-field accuracy
    processing_time: Optional[float] = None
    error: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


@dataclass
class RotatedExtractionSummary:
    """Summary of rotated extraction test results"""
    model_name: str
    total_tests: int
    successful_extractions: int
    overall_accuracy: float  # Average accuracy across all rotations
    accuracy_by_rotation: Dict[int, Dict[str, float]]  # rotation -> {accuracy, count, successful}
    mean_processing_time: Optional[float] = None
    total_input_tokens: Optional[int] = None
    total_output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    average_input_tokens: Optional[float] = None
    average_output_tokens: Optional[float] = None
    average_total_tokens: Optional[float] = None


@dataclass
class RotatedExtractionReport:
    """Complete rotated extraction test report"""
    timestamp: str
    images_dir: str
    ground_truth_dir: Optional[str]
    models_tested: List[str]
    total_images: int
    results: List[RotatedExtractionResult]
    summary: Dict[str, RotatedExtractionSummary]  # model_name -> summary
    overall_statistics: Dict


class RotatedExtractionTester:
    """Test LLM models' data extraction accuracy on rotated images"""
    
    # Rotation angles to test (clockwise)
    ROTATION_ANGLES = [0, 90, 180, 270]
    
    def __init__(self, images_dir: str, ground_truth_dir: Optional[str] = None):
        """
        Initialize rotated extraction tester
        
        Args:
            images_dir: Directory containing images to test
            ground_truth_dir: Optional directory containing ground truth files
        """
        self.images_dir = Path(images_dir)
        self.ground_truth_dir = Path(ground_truth_dir) if ground_truth_dir else None
        self.evaluator = TranscriptionEvaluator()
    
    def rotate_image(self, image_path: Path, angle: int) -> BytesIO:
        """
        Rotate image in memory and return as BytesIO object
        
        Args:
            image_path: Path to image file
            angle: Rotation angle in degrees (0, 90, 180, 270)
        
        Returns:
            BytesIO object containing rotated image
        """
        # Open and rotate image
        with Image.open(image_path) as img:
            # Rotate image (expand=True to avoid cropping)
            rotated = img.rotate(-angle, expand=True)  # Negative for clockwise
            
            # Save to BytesIO
            output = BytesIO()
            # Determine format from original file
            format = img.format or 'JPEG'
            rotated.save(output, format=format)
            output.seek(0)
            
            return output
    
    def load_ground_truth(self, image_path: Path) -> Optional[Dict]:
        """Load ground truth for an image file"""
        if not self.ground_truth_dir:
            return None
        
        # Get base name without extension
        base_name = image_path.stem
        
        # Try JSON first
        gt_path = self.ground_truth_dir / f"{base_name}.json"
        if gt_path.exists():
            try:
                with open(gt_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load ground truth from {gt_path}: {e}")
                return None
        
        # Try TXT as fallback
        gt_path = self.ground_truth_dir / f"{base_name}.txt"
        if gt_path.exists():
            try:
                with open(gt_path, 'r', encoding='utf-8') as f:
                    return {"text": f.read().strip()}
            except Exception as e:
                print(f"Warning: Could not load ground truth from {gt_path}: {e}")
                return None
        
        return None
    
    def test_single_rotation(
        self,
        image_path: Path,
        rotation_angle: int,
        transcriber,
        model_name: str,
        prompt: Optional[str] = None
    ) -> RotatedExtractionResult:
        """
        Test data extraction for a single image/rotation combination
        
        Args:
            image_path: Path to original image
            rotation_angle: Rotation angle to test (0, 90, 180, 270)
            transcriber: Transcriber instance
            model_name: Name of the model being tested
            prompt: Custom prompt for extraction
        
        Returns:
            RotatedExtractionResult
        """
        import time
        import base64
        
        start_time = time.time()
        ground_truth = self.load_ground_truth(image_path)
        
        try:
            # Rotate image in memory
            rotated_image_io = self.rotate_image(image_path, rotation_angle)
            
            # Encode rotated image to base64 for transcriber
            rotated_image_io.seek(0)
            image_data = rotated_image_io.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Determine MIME type from original file
            mime_type = "image/jpeg"
            if str(image_path).lower().endswith('.png'):
                mime_type = "image/png"
            elif str(image_path).lower().endswith('.webp'):
                mime_type = "image/webp"
            
            # Create data URL for transcriber
            image_data_url = f"data:{mime_type};base64,{base64_image}"
            
            # Use structured extraction if ground truth exists
            use_structured = ground_truth is not None
            
            # Extract data from rotated image
            if use_structured:
                # Try structured output
                try:
                    result = transcriber.transcribe(
                        image_data_url,
                        prompt=prompt,
                        structured=True
                    )
                    # If it's a dict, convert to JSON string for storage
                    if isinstance(result, dict):
                        extracted_data = result
                        transcription = json.dumps(result, ensure_ascii=False)
                    else:
                        transcription = result
                        extracted_data = None
                        # Try to parse as JSON
                        try:
                            if isinstance(transcription, str) and transcription.strip().startswith('{'):
                                extracted_data = json.loads(transcription)
                        except:
                            pass
                except TypeError:
                    # Fallback if structured parameter not supported
                    default_prompt = prompt or """Extract all information from this invoice/receipt image and return it as JSON with the following structure:
{
    "company": "Company name",
    "date": "Date in DD/MM/YYYY format",
    "address": "Full address",
    "total": "Total amount"
}

Be precise and extract the exact values as they appear in the image."""
                    transcription = transcriber.transcribe(
                        image_data_url,
                        prompt=default_prompt
                    )
                    extracted_data = None
                    # Try to parse as JSON
                    try:
                        if isinstance(transcription, str) and transcription.strip().startswith('{'):
                            extracted_data = json.loads(transcription)
                    except:
                        pass
            else:
                default_prompt = prompt or "Extract all information from this image and return it as structured JSON."
                transcription = transcriber.transcribe(
                    image_data_url,
                    prompt=default_prompt
                )
                extracted_data = None
                # Try to parse as JSON
                try:
                    if isinstance(transcription, str) and transcription.strip().startswith('{'):
                        extracted_data = json.loads(transcription)
                except:
                    pass
            
            processing_time = time.time() - start_time
            
            # Get token usage from transcriber if available
            token_usage = getattr(transcriber, 'get_last_token_usage', lambda: {})()
            input_tokens = token_usage.get('input_tokens') if isinstance(token_usage, dict) else None
            output_tokens = token_usage.get('output_tokens') if isinstance(token_usage, dict) else None
            total_tokens = token_usage.get('total_tokens') if isinstance(token_usage, dict) else None
            
            # Evaluate accuracy if ground truth exists
            accuracy = None
            field_accuracy = None
            if ground_truth and transcription:
                comparison = self.evaluator.compare_with_ground_truth(
                    transcription,
                    ground_truth,
                    extracted_data
                )
                accuracy = comparison.get("overall_accuracy", 0.0)
                field_accuracy = comparison.get("field_accuracy", {})
            
            return RotatedExtractionResult(
                image_path=str(image_path),
                rotation_angle=rotation_angle,
                model_name=model_name,
                transcription=transcription if isinstance(transcription, str) else json.dumps(transcription, ensure_ascii=False),
                extracted_data=extracted_data,
                ground_truth=ground_truth,
                accuracy=accuracy,
                field_accuracy=field_accuracy,
                processing_time=processing_time,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens
            )
        
        except Exception as e:
            processing_time = time.time() - start_time
            return RotatedExtractionResult(
                image_path=str(image_path),
                rotation_angle=rotation_angle,
                model_name=model_name,
                transcription="",
                extracted_data=None,
                ground_truth=ground_truth,
                accuracy=None,
                field_accuracy=None,
                processing_time=processing_time,
                error=str(e),
                input_tokens=None,
                output_tokens=None,
                total_tokens=None
            )
    
    def find_image_files(self, extensions: Tuple[str, ...] = ('.jpg', '.jpeg', '.png', '.webp')) -> List[Path]:
        """Find all image files in the images directory"""
        image_files = []
        for ext in extensions:
            image_files.extend(self.images_dir.glob(f"*{ext}"))
            image_files.extend(self.images_dir.glob(f"*{ext.upper()}"))
        # Remove duplicates (case-insensitive filesystems may return same files for .jpg and .JPG)
        unique_files = list(set(str(f) for f in image_files))
        return sorted([Path(f) for f in unique_files])
    
    def test_batch(
        self,
        model_configs: List[Dict],
        prompt: Optional[str] = None,
        max_images: Optional[int] = None,
        parallel: bool = True,
        max_workers: int = 10
    ) -> RotatedExtractionReport:
        """
        Test data extraction accuracy for multiple images and models at different rotations
        
        Args:
            model_configs: List of model configuration dicts
            prompt: Custom prompt for extraction
            max_images: Maximum number of images to test (None for all)
            parallel: If True, process tests in parallel
            max_workers: Number of parallel workers (if parallel=True)
        
        Returns:
            RotatedExtractionReport
        """
        from image_transcriber import create_transcriber
        
        # Find images
        image_files = self.find_image_files()
        if max_images:
            image_files = image_files[:max_images]
        
        if not image_files:
            raise ValueError(f"No images found in {self.images_dir}")
        
        results = []
        model_names = []
        
        print(f"\n{'='*70}")
        print(f"ROTATED EXTRACTION TEST")
        print(f"{'='*70}")
        print(f"Images to test: {len(image_files)}")
        print(f"Models: {len(model_configs)}")
        print(f"Rotations per image: {len(self.ROTATION_ANGLES)} ({self.ROTATION_ANGLES})")
        total_tests = len(image_files) * len(model_configs) * len(self.ROTATION_ANGLES)
        print(f"Total tests: {total_tests}")
        print(f"Processing mode: {'Parallel' if parallel and total_tests > 1 else 'Sequential'}")
        if parallel and total_tests > 1:
            print(f"Max workers: {max_workers}")
        print(f"{'='*70}\n")
        
        for model_config in model_configs:
            model_name = model_config.get('name', f"{model_config['provider']}_{model_config['model_name']}")
            model_names.append(model_name)
            
            print(f"\nTesting with: {model_name}")
            print("-" * 70)
            
            # Create transcriber
            transcriber = create_transcriber(
                provider=model_config['provider'],
                model_name=model_config['model_name'],
                api_key=model_config.get('api_key'),
                **model_config.get('kwargs', {})
            )
            
            # Prepare all test tasks
            test_tasks = []
            for image_path in image_files:
                for rotation in self.ROTATION_ANGLES:
                    test_tasks.append((image_path, rotation, model_name))
            
            if parallel and len(test_tasks) > 1:
                # Parallel processing
                from concurrent.futures import ThreadPoolExecutor, as_completed
                print(f"Processing {len(test_tasks)} tests in parallel (max {max_workers} workers)...")
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Submit all tasks
                    future_to_task = {
                        executor.submit(
                            self.test_single_rotation,
                            image_path,
                            rotation,
                            transcriber,
                            model_name,
                            prompt
                        ): (image_path, rotation, i)
                        for i, (image_path, rotation, model_name) in enumerate(test_tasks, 1)
                    }
                    
                    # Process completed tasks
                    completed = 0
                    for future in as_completed(future_to_task):
                        completed += 1
                        image_path, rotation, task_num = future_to_task[future]
                        try:
                            result = future.result()
                            results.append(result)
                            
                            status = "✓" if result.error is None else "✗"
                            accuracy_str = f" ({result.accuracy:.1%})" if result.accuracy is not None else ""
                            error_str = f" (Error: {result.error})" if result.error else ""
                            print(f"  [{completed}/{len(test_tasks)}] {image_path.name} - {rotation}°: {status}{accuracy_str}{error_str}")
                        except Exception as e:
                            print(f"  [{completed}/{len(test_tasks)}] {image_path.name} - {rotation}°: Exception - {e}")
                            results.append(RotatedExtractionResult(
                                image_path=str(image_path),
                                rotation_angle=rotation,
                                model_name=model_name,
                                transcription="",
                                extracted_data=None,
                                ground_truth=self.load_ground_truth(image_path),
                                accuracy=None,
                                field_accuracy=None,
                                error=str(e)
                            ))
            else:
                # Sequential processing
                test_count = 0
                for image_path, rotation, model_name in test_tasks:
                    test_count += 1
                    image_name = image_path.name
                    if test_count == 1 or (test_count - 1) % len(self.ROTATION_ANGLES) == 0:
                        print(f"  Processing {image_name}...")
                    
                    result = self.test_single_rotation(
                        image_path,
                        rotation,
                        transcriber,
                        model_name,
                        prompt
                    )
                    results.append(result)
                    
                    status = "✓" if result.error is None else "✗"
                    accuracy_str = f" ({result.accuracy:.1%})" if result.accuracy is not None else ""
                    error_str = f" (Error: {result.error})" if result.error else ""
                    print(f"    [{test_count}/{len(test_tasks)}] Rotation {rotation}°: {status}{accuracy_str}{error_str}")
        
        # Sort results to maintain consistent order (by model, image path, rotation)
        results.sort(key=lambda x: (x.model_name, x.image_path, x.rotation_angle))
        
        # Generate summary
        summary = self._calculate_summary(results, model_names)
        
        # Overall statistics
        overall_stats = self._calculate_overall_statistics(results, model_names)
        
        return RotatedExtractionReport(
            timestamp=datetime.now().isoformat(),
            images_dir=str(self.images_dir),
            ground_truth_dir=str(self.ground_truth_dir) if self.ground_truth_dir else None,
            models_tested=model_names,
            total_images=len(image_files),
            results=results,
            summary=summary,
            overall_statistics=overall_stats
        )
    
    def _calculate_summary(
        self,
        results: List[RotatedExtractionResult],
        model_names: List[str]
    ) -> Dict[str, RotatedExtractionSummary]:
        """Calculate summary statistics for each model"""
        summary = {}
        
        for model_name in model_names:
            model_results = [r for r in results if r.model_name == model_name]
            
            total_tests = len(model_results)
            successful = sum(1 for r in model_results if r.error is None)
            
            # Calculate overall accuracy (average of all rotation accuracies)
            accuracy_results = [r.accuracy for r in model_results if r.accuracy is not None]
            overall_accuracy = statistics.mean(accuracy_results) if accuracy_results else 0.0
            
            # Accuracy by rotation
            accuracy_by_rotation = {}
            for rotation in self.ROTATION_ANGLES:
                rotation_results = [r for r in model_results if r.rotation_angle == rotation]
                if rotation_results:
                    rotation_accuracy_results = [r.accuracy for r in rotation_results if r.accuracy is not None]
                    rotation_accuracy = statistics.mean(rotation_accuracy_results) if rotation_accuracy_results else 0.0
                    rotation_successful = sum(1 for r in rotation_results if r.error is None)
                    accuracy_by_rotation[rotation] = {
                        'accuracy': rotation_accuracy,
                        'count': len(rotation_results),
                        'successful': rotation_successful
                    }
            
            # Mean processing time
            processing_times = [r.processing_time for r in model_results if r.processing_time]
            mean_time = statistics.mean(processing_times) if processing_times else None
            
            # Aggregate token usage
            total_input_tokens = sum(r.input_tokens for r in model_results if r.input_tokens is not None)
            total_output_tokens = sum(r.output_tokens for r in model_results if r.output_tokens is not None)
            total_tokens = sum(r.total_tokens for r in model_results if r.total_tokens is not None)
            
            token_results = [r for r in model_results if r.total_tokens is not None]
            avg_input_tokens = statistics.mean([r.input_tokens for r in token_results]) if token_results else None
            avg_output_tokens = statistics.mean([r.output_tokens for r in token_results]) if token_results else None
            avg_total_tokens = statistics.mean([r.total_tokens for r in token_results]) if token_results else None
            
            summary[model_name] = RotatedExtractionSummary(
                model_name=model_name,
                total_tests=total_tests,
                successful_extractions=successful,
                overall_accuracy=overall_accuracy,
                accuracy_by_rotation=accuracy_by_rotation,
                mean_processing_time=mean_time,
                total_input_tokens=total_input_tokens if total_input_tokens > 0 else None,
                total_output_tokens=total_output_tokens if total_output_tokens > 0 else None,
                total_tokens=total_tokens if total_tokens > 0 else None,
                average_input_tokens=avg_input_tokens,
                average_output_tokens=avg_output_tokens,
                average_total_tokens=avg_total_tokens
            )
        
        return summary
    
    def _calculate_overall_statistics(
        self,
        results: List[RotatedExtractionResult],
        model_names: List[str]
    ) -> Dict:
        """Calculate overall statistics across all models"""
        total_tests = len(results)
        total_successful = sum(1 for r in results if r.error is None)
        
        # Overall accuracy (average across all tests with accuracy)
        accuracy_results = [r.accuracy for r in results if r.accuracy is not None]
        overall_accuracy = statistics.mean(accuracy_results) if accuracy_results else 0.0
        
        # Accuracy by rotation (across all models)
        accuracy_by_rotation = {}
        for rotation in self.ROTATION_ANGLES:
            rotation_results = [r for r in results if r.rotation_angle == rotation]
            if rotation_results:
                rotation_accuracy_results = [r.accuracy for r in rotation_results if r.accuracy is not None]
                rotation_accuracy = statistics.mean(rotation_accuracy_results) if rotation_accuracy_results else 0.0
                rotation_successful = sum(1 for r in rotation_results if r.error is None)
                accuracy_by_rotation[rotation] = {
                    'accuracy': rotation_accuracy,
                    'count': len(rotation_results),
                    'successful': rotation_successful
                }
        
        # Best and worst performing rotations
        if accuracy_by_rotation:
            best_rotation = max(accuracy_by_rotation.items(), key=lambda x: x[1]['accuracy'])
            worst_rotation = min(accuracy_by_rotation.items(), key=lambda x: x[1]['accuracy'])
        else:
            best_rotation = None
            worst_rotation = None
        
        return {
            'total_tests': total_tests,
            'total_successful': total_successful,
            'overall_accuracy': overall_accuracy,
            'accuracy_by_rotation': accuracy_by_rotation,
            'best_rotation': {'angle': best_rotation[0], 'accuracy': best_rotation[1]['accuracy']} if best_rotation else None,
            'worst_rotation': {'angle': worst_rotation[0], 'accuracy': worst_rotation[1]['accuracy']} if worst_rotation else None
        }
    
    def save_results(self, report: RotatedExtractionReport, output_path: str):
        """
        Save rotated extraction test results to JSON file and individual model files
        
        Args:
            report: RotatedExtractionReport to save
            output_path: Path to output summary JSON file
        """
        # Save summary report
        output_data = {
            'timestamp': report.timestamp,
            'images_dir': report.images_dir,
            'ground_truth_dir': report.ground_truth_dir,
            'models_tested': report.models_tested,
            'total_images': report.total_images,
            'results': [asdict(r) for r in report.results],
            'summary': {
                model_name: {
                    'model_name': summary.model_name,
                    'total_tests': summary.total_tests,
                    'successful_extractions': summary.successful_extractions,
                    'overall_accuracy': summary.overall_accuracy,
                    'accuracy_by_rotation': summary.accuracy_by_rotation,
                    'mean_processing_time': summary.mean_processing_time,
                    'total_input_tokens': summary.total_input_tokens,
                    'total_output_tokens': summary.total_output_tokens,
                    'total_tokens': summary.total_tokens,
                    'average_input_tokens': summary.average_input_tokens,
                    'average_output_tokens': summary.average_output_tokens,
                    'average_total_tokens': summary.average_total_tokens
                }
                for model_name, summary in report.summary.items()
            },
            'overall_statistics': report.overall_statistics
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nSummary results saved to: {output_path}")
        
        # Save individual model results to results/rotated_extraction
        results_dir = Path("results/rotated_extraction")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        for model_name in report.models_tested:
            summary = report.summary[model_name]
            model_results = [r for r in report.results if r.model_name == model_name]
            
            model_data = {
                "model": model_name,
                "timestamp": report.timestamp,
                "summary": {
                    'total_tests': summary.total_tests,
                    'successful_extractions': summary.successful_extractions,
                    'overall_accuracy': summary.overall_accuracy,
                    'accuracy_by_rotation': summary.accuracy_by_rotation,
                    'mean_processing_time': summary.mean_processing_time,
                    'total_input_tokens': summary.total_input_tokens,
                    'total_output_tokens': summary.total_output_tokens,
                    'total_tokens': summary.total_tokens,
                    'average_input_tokens': summary.average_input_tokens,
                    'average_output_tokens': summary.average_output_tokens,
                    'average_total_tokens': summary.average_total_tokens
                },
                "results": [asdict(r) for r in model_results]
            }
            
            filename = f"{model_name.replace(' ', '_').lower()}.json"
            filepath = results_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(model_data, f, indent=2, ensure_ascii=False)
                
        print(f"Individual model results saved to: {results_dir}/")
    
    def print_summary(self, report: RotatedExtractionReport):
        """Print a formatted summary of the rotated extraction test results"""
        print("\n" + "="*70)
        print("ROTATED EXTRACTION TEST SUMMARY")
        print("="*70)
        print(f"Total images tested: {report.total_images}")
        print(f"Models tested: {', '.join(report.models_tested)}")
        print(f"Total tests: {len(report.results)}")
        print("="*70)
        
        # Per-model summary
        print("\nPer-Model Results:")
        print("-" * 70)
        for model_name in report.models_tested:
            summary = report.summary[model_name]
            print(f"\n{model_name}:")
            print(f"  Total tests: {summary.total_tests}")
            print(f"  Successful extractions: {summary.successful_extractions}")
            print(f"  Overall accuracy: {summary.overall_accuracy:.1%}")
            
            if summary.mean_processing_time:
                print(f"  Mean processing time: {summary.mean_processing_time:.2f}s")
            
            print(f"  Accuracy by rotation:")
            for rotation in self.ROTATION_ANGLES:
                if rotation in summary.accuracy_by_rotation:
                    rot_stats = summary.accuracy_by_rotation[rotation]
                    print(f"    {rotation}°: {rot_stats['accuracy']:.1%} "
                          f"({rot_stats['successful']}/{rot_stats['count']})")
        
        # Overall statistics
        print("\n" + "="*70)
        print("Overall Statistics:")
        print("-" * 70)
        stats = report.overall_statistics
        print(f"Overall accuracy: {stats['overall_accuracy']:.1%}")
        print(f"Total tests: {stats['total_tests']}")
        print(f"Total successful: {stats['total_successful']}")
        
        if stats.get('best_rotation'):
            print(f"\nBest performing rotation: {stats['best_rotation']['angle']}° "
                  f"({stats['best_rotation']['accuracy']:.1%})")
        if stats.get('worst_rotation'):
            print(f"Most challenging rotation: {stats['worst_rotation']['angle']}° "
                  f"({stats['worst_rotation']['accuracy']:.1%})")
        
        print("="*70 + "\n")

