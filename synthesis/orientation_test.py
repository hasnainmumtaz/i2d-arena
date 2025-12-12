"""
Orientation test module for testing LLM models' ability to detect image orientation
"""

import json
import re
import statistics
from dataclasses import dataclass, asdict
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image


@dataclass
class OrientationTestResult:
    """Result of a single orientation test"""
    image_path: str
    actual_rotation: int  # 0, 90, 180, or 270
    detected_rotation: Optional[int]  # Detected rotation angle
    model_name: str
    response: str  # Raw LLM response
    is_correct: bool
    processing_time: Optional[float] = None
    error: Optional[str] = None
    replication: int = 1  # Replication number (1, 2, 3, etc.)
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


@dataclass
class OrientationTestSummary:
    """Summary of orientation test results"""
    model_name: str
    total_tests: int
    correct_detections: int
    accuracy: float
    accuracy_by_rotation: Dict[int, Dict[str, float]]  # rotation -> {accuracy, count}
    consistency_score: Optional[float] = None  # For replications > 1
    mean_processing_time: Optional[float] = None
    total_input_tokens: Optional[int] = None
    total_output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    average_input_tokens: Optional[float] = None
    average_output_tokens: Optional[float] = None
    average_total_tokens: Optional[float] = None


@dataclass
class OrientationTestReport:
    """Complete orientation test report"""
    timestamp: str
    images_dir: str
    models_tested: List[str]
    replications: int
    total_images: int
    results: List[OrientationTestResult]
    summary: Dict[str, OrientationTestSummary]  # model_name -> summary
    overall_statistics: Dict


class OrientationTester:
    """Test LLM models' ability to detect image orientation"""
    
    # Rotation angles to test (clockwise)
    ROTATION_ANGLES = [0, 90, 180, 270]
    
    # Orientation detection prompt
    ORIENTATION_PROMPT = """What is the orientation of this image? Respond with one of:
- "0 degrees" or "upright" or "0°"
- "90 degrees" or "rotated clockwise" or "90°"
- "180 degrees" or "upside down" or "180°"
- "270 degrees" or "rotated counter-clockwise" or "270°"

Respond with only the angle value (0, 90, 180, or 270)."""
    
    def __init__(self, images_dir: str):
        """
        Initialize orientation tester
        
        Args:
            images_dir: Directory containing images to test
        """
        self.images_dir = Path(images_dir)
    
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
    
    def parse_orientation_response(self, response) -> Optional[int]:
        """
        Parse orientation angle from LLM response
        
        Args:
            response: LLM response (can be str, dict, or other type)
        
        Returns:
            Detected rotation angle (0, 90, 180, 270) or None if not found
        """
        # Convert response to string if it's not already
        if isinstance(response, dict):
            # If it's a dict, try to extract text content
            if 'content' in response:
                response = response['content']
            elif 'text' in response:
                response = response['text']
            else:
                # Convert entire dict to string
                response = str(response)
        elif not isinstance(response, str):
            response = str(response)
        
        response_lower = response.lower().strip()
        
        # Try to extract number directly
        # Look for patterns like "0", "90", "180", "270"
        number_patterns = [
            r'\b0\s*(?:degrees?|°|d|deg)\b',
            r'\b90\s*(?:degrees?|°|d|deg)\b',
            r'\b180\s*(?:degrees?|°|d|deg)\b',
            r'\b270\s*(?:degrees?|°|d|deg)\b',
            r'\b(?:0|zero)\b',
            r'\b(?:90|ninety)\b',
            r'\b(?:180|one\s*hundred\s*eighty)\b',
            r'\b(?:270|two\s*hundred\s*seventy)\b'
        ]
        
        for pattern in number_patterns:
            match = re.search(pattern, response_lower)
            if match:
                # Extract the number
                number_match = re.search(r'\b(\d+)\b', match.group())
                if number_match:
                    angle = int(number_match.group(1))
                    # Normalize to valid angles
                    if angle in [0, 90, 180, 270]:
                        return angle
                    # Handle 360 as 0
                    if angle == 360:
                        return 0
        
        # Try keyword matching
        if any(word in response_lower for word in ['upright', 'normal', '0', 'zero']):
            return 0
        if any(word in response_lower for word in ['90', 'ninety', 'clockwise', 'right']):
            return 90
        if any(word in response_lower for word in ['180', 'upside', 'down', 'inverted']):
            return 180
        if any(word in response_lower for word in ['270', 'counter', 'counter-clockwise', 'left']):
            return 270
        
        return None
    
    def test_single_orientation(
        self,
        image_path: Path,
        rotation_angle: int,
        transcriber,
        model_name: str,
        replication: int = 1
    ) -> OrientationTestResult:
        """
        Test orientation detection for a single image/rotation combination
        
        Args:
            image_path: Path to original image
            rotation_angle: Rotation angle to test (0, 90, 180, 270)
            transcriber: Transcriber instance
            model_name: Name of the model being tested
            replication: Replication number (for multiple runs)
        
        Returns:
            OrientationTestResult
        """
        import time
        
        start_time = time.time()
        
        try:
            # Rotate image in memory
            rotated_image_io = self.rotate_image(image_path, rotation_angle)
            
            # Encode rotated image to base64 for transcriber
            import base64
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
            
            # Test orientation detection using data URL
            # Try to use structured=False for OpenAI transcriber (defaults to True which returns dict)
            try:
                response = transcriber.transcribe(
                    image_data_url,
                    prompt=self.ORIENTATION_PROMPT,
                    structured=False
                )
            except TypeError:
                # Transcriber doesn't support structured parameter, use default
                response = transcriber.transcribe(
                    image_data_url,
                    prompt=self.ORIENTATION_PROMPT
                )
            
            # Parse response
            detected_angle = self.parse_orientation_response(response)
            
            # Check if correct
            is_correct = detected_angle == rotation_angle
            
            processing_time = time.time() - start_time
            
            # Get token usage from transcriber if available
            token_usage = getattr(transcriber, 'get_last_token_usage', lambda: {})()
            input_tokens = token_usage.get('input_tokens') if isinstance(token_usage, dict) else None
            output_tokens = token_usage.get('output_tokens') if isinstance(token_usage, dict) else None
            total_tokens = token_usage.get('total_tokens') if isinstance(token_usage, dict) else None
            
            return OrientationTestResult(
                image_path=str(image_path),
                actual_rotation=rotation_angle,
                detected_rotation=detected_angle,
                model_name=model_name,
                response=response if isinstance(response, str) else str(response),
                is_correct=is_correct,
                processing_time=processing_time,
                replication=replication,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens
            )
        
        except Exception as e:
            processing_time = time.time() - start_time
            return OrientationTestResult(
                image_path=str(image_path),
                actual_rotation=rotation_angle,
                detected_rotation=None,
                model_name=model_name,
                response="",
                is_correct=False,
                processing_time=processing_time,
                error=str(e),
                replication=replication,
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
        # Convert to set of string paths, then back to Path objects
        unique_files = list(set(str(f) for f in image_files))
        return sorted([Path(f) for f in unique_files])
    
    def test_batch(
        self,
        model_configs: List[Dict],
        max_images: Optional[int] = None,
        replications: int = 1,
        parallel: bool = True,
        max_workers: int = 10
    ) -> OrientationTestReport:
        """
        Test orientation detection for multiple images and models
        
        Args:
            model_configs: List of model configuration dicts
            max_images: Maximum number of images to test (None for all)
            replications: Number of times to test each image/rotation (for robustness)
        
        Returns:
            OrientationTestReport
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
        model_config_map = {}  # Map model_name to model_config for saving provider/model_identifier
        
        print(f"\n{'='*70}")
        print(f"ORIENTATION TEST")
        print(f"{'='*70}")
        print(f"Images to test: {len(image_files)}")
        print(f"Models: {len(model_configs)}")
        print(f"Rotations per image: {len(self.ROTATION_ANGLES)} ({self.ROTATION_ANGLES})")
        print(f"Replications per rotation: {replications}")
        total_tests = len(image_files) * len(model_configs) * len(self.ROTATION_ANGLES) * replications
        print(f"Total tests: {total_tests}")
        print(f"Processing mode: {'Parallel' if parallel and total_tests > 1 else 'Sequential'}")
        if parallel and total_tests > 1:
            print(f"Max workers: {max_workers}")
        print(f"{'='*70}\n")
        
        for model_config in model_configs:
            model_name = model_config.get('name', f"{model_config['provider']}_{model_config['model_name']}")
            model_names.append(model_name)
            model_config_map[model_name] = model_config  # Store config for later use
            
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
                    for rep in range(1, replications + 1):
                        test_tasks.append((image_path, rotation, model_name, rep))
            
            if parallel and len(test_tasks) > 1:
                # Parallel processing
                from concurrent.futures import ThreadPoolExecutor, as_completed
                print(f"Processing {len(test_tasks)} tests in parallel (max {max_workers} workers)...")
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Submit all tasks
                    future_to_task = {
                        executor.submit(
                            self.test_single_orientation,
                            image_path,
                            rotation,
                            transcriber,
                            model_name,
                            replication=rep
                        ): (image_path, rotation, rep, i)
                        for i, (image_path, rotation, model_name, rep) in enumerate(test_tasks, 1)
                    }
                    
                    # Process completed tasks
                    completed = 0
                    for future in as_completed(future_to_task):
                        completed += 1
                        image_path, rotation, rep, task_num = future_to_task[future]
                        try:
                            result = future.result()
                            results.append(result)
                            
                            status = "✓" if result.is_correct else "✗"
                            error_str = f" (Error: {result.error})" if result.error else ""
                            detected = f"{result.detected_rotation}°" if result.detected_rotation is not None else "None"
                            print(f"  [{completed}/{len(test_tasks)}] {image_path.name} - {rotation}° (rep {rep}): {status} "
                                  f"(detected: {detected}){error_str}")
                        except Exception as e:
                            print(f"  [{completed}/{len(test_tasks)}] {image_path.name} - {rotation}° (rep {rep}): Exception - {e}")
                            results.append(OrientationTestResult(
                                image_path=str(image_path),
                                actual_rotation=rotation,
                                detected_rotation=None,
                                model_name=model_name,
                                response="",
                                is_correct=False,
                                error=str(e),
                                replication=rep
                            ))
            else:
                # Sequential processing
                test_count = 0
                for image_path, rotation, model_name, rep in test_tasks:
                    test_count += 1
                    image_name = image_path.name
                    if test_count == 1 or (test_count - 1) % (len(self.ROTATION_ANGLES) * replications) == 0:
                        print(f"  Processing {image_name}...")
                    
                    result = self.test_single_orientation(
                        image_path,
                        rotation,
                        transcriber,
                        model_name,
                        replication=rep
                    )
                    results.append(result)
                    
                    status = "✓" if result.is_correct else "✗"
                    error_str = f" (Error: {result.error})" if result.error else ""
                    detected = f"{result.detected_rotation}°" if result.detected_rotation is not None else "None"
                    print(f"    [{test_count}/{len(test_tasks)}] Rotation {rotation}° (rep {rep}): {status} "
                          f"(detected: {detected}){error_str}")
        
        # Sort results to maintain consistent order (by model, image path, rotation, replication)
        results.sort(key=lambda x: (x.model_name, x.image_path, x.actual_rotation, x.replication))
        
        # Generate summary
        summary = self._calculate_summary(results, model_names, replications)
        
        # Overall statistics
        overall_stats = self._calculate_overall_statistics(results, model_names)
        
        report = OrientationTestReport(
            timestamp=datetime.now().isoformat(),
            images_dir=str(self.images_dir),
            models_tested=model_names,
            replications=replications,
            total_images=len(image_files),
            results=results,
            summary=summary,
            overall_statistics=overall_stats
        )
        
        # Return both report and model_config_map for saving provider/model_identifier
        return report, model_config_map
    
    def _calculate_summary(
        self,
        results: List[OrientationTestResult],
        model_names: List[str],
        replications: int
    ) -> Dict[str, OrientationTestSummary]:
        """Calculate summary statistics for each model"""
        summary = {}
        
        for model_name in model_names:
            model_results = [r for r in results if r.model_name == model_name]
            
            total_tests = len(model_results)
            correct = sum(1 for r in model_results if r.is_correct)
            accuracy = correct / total_tests if total_tests > 0 else 0.0
            
            # Accuracy by rotation
            accuracy_by_rotation = {}
            for rotation in self.ROTATION_ANGLES:
                rotation_results = [r for r in model_results if r.actual_rotation == rotation]
                if rotation_results:
                    rotation_correct = sum(1 for r in rotation_results if r.is_correct)
                    rotation_total = len(rotation_results)
                    rotation_accuracy = rotation_correct / rotation_total if rotation_total > 0 else 0.0
                    accuracy_by_rotation[rotation] = {
                        'accuracy': rotation_accuracy,
                        'count': rotation_total,
                        'correct': rotation_correct
                    }
            
            # Consistency score (for replications > 1)
            consistency_score = None
            if replications > 1:
                # For each image/rotation combination, check if all replications agree
                consistency_count = 0
                consistency_total = 0
                
                # Group by image and rotation
                from collections import defaultdict
                groups = defaultdict(list)
                for r in model_results:
                    key = (r.image_path, r.actual_rotation)
                    groups[key].append(r)
                
                for group_results in groups.values():
                    if len(group_results) == replications:
                        # Check if all detected the same angle
                        detected_angles = [r.detected_rotation for r in group_results if r.detected_rotation is not None]
                        if detected_angles:
                            if len(set(detected_angles)) == 1:
                                consistency_count += 1
                            consistency_total += 1
                
                if consistency_total > 0:
                    consistency_score = consistency_count / consistency_total
            
            # Mean processing time
            processing_times = [r.processing_time for r in model_results if r.processing_time]
            mean_time = statistics.mean(processing_times) if processing_times else None
            
            # Aggregate token usage
            total_input_tokens = sum(r.input_tokens for r in model_results if r.input_tokens is not None)
            total_output_tokens = sum(r.output_tokens for r in model_results if r.output_tokens is not None)
            total_tokens = sum(r.total_tokens for r in model_results if r.total_tokens is not None)
            
            # Calculate averages, filtering out None values
            input_token_values = [r.input_tokens for r in model_results if r.input_tokens is not None]
            output_token_values = [r.output_tokens for r in model_results if r.output_tokens is not None]
            total_token_values = [r.total_tokens for r in model_results if r.total_tokens is not None]
            
            avg_input_tokens = statistics.mean(input_token_values) if input_token_values else None
            avg_output_tokens = statistics.mean(output_token_values) if output_token_values else None
            avg_total_tokens = statistics.mean(total_token_values) if total_token_values else None
            
            summary[model_name] = OrientationTestSummary(
                model_name=model_name,
                total_tests=total_tests,
                correct_detections=correct,
                accuracy=accuracy,
                accuracy_by_rotation=accuracy_by_rotation,
                consistency_score=consistency_score,
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
        results: List[OrientationTestResult],
        model_names: List[str]
    ) -> Dict:
        """Calculate overall statistics across all models"""
        total_tests = len(results)
        total_correct = sum(1 for r in results if r.is_correct)
        overall_accuracy = total_correct / total_tests if total_tests > 0 else 0.0
        
        # Accuracy by rotation (across all models)
        accuracy_by_rotation = {}
        for rotation in self.ROTATION_ANGLES:
            rotation_results = [r for r in results if r.actual_rotation == rotation]
            if rotation_results:
                rotation_correct = sum(1 for r in rotation_results if r.is_correct)
                rotation_total = len(rotation_results)
                rotation_accuracy = rotation_correct / rotation_total if rotation_total > 0 else 0.0
                accuracy_by_rotation[rotation] = {
                    'accuracy': rotation_accuracy,
                    'count': rotation_total,
                    'correct': rotation_correct
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
            'total_correct': total_correct,
            'overall_accuracy': overall_accuracy,
            'accuracy_by_rotation': accuracy_by_rotation,
            'best_rotation': {'angle': best_rotation[0], 'accuracy': best_rotation[1]['accuracy']} if best_rotation else None,
            'worst_rotation': {'angle': worst_rotation[0], 'accuracy': worst_rotation[1]['accuracy']} if worst_rotation else None
        }
    
    def save_results(self, report: OrientationTestReport, output_path: str, model_config_map: Dict = None):
        """
        Save orientation test results to JSON file and individual model files
        
        Args:
            report: OrientationTestReport to save
            output_path: Path to output summary JSON file
            model_config_map: Optional dict mapping model_name to model_config (for provider/model_identifier)
        """
        # Save summary report
        output_data = {
            'timestamp': report.timestamp,
            'images_dir': report.images_dir,
            'models_tested': report.models_tested,
            'replications': report.replications,
            'total_images': report.total_images,
            'results': [asdict(r) for r in report.results],
            'summary': {
                model_name: {
                    'model_name': summary.model_name,
                    'total_tests': summary.total_tests,
                    'correct_detections': summary.correct_detections,
                    'accuracy': summary.accuracy,
                    'accuracy_by_rotation': summary.accuracy_by_rotation,
                    'consistency_score': summary.consistency_score,
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
        
        # Save individual model results to results/orientation
        results_dir = Path("results/orientation")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        for model_name in report.models_tested:
            summary = report.summary[model_name]
            model_results = [r for r in report.results if r.model_name == model_name]
            
            # Extract provider and model_identifier from config if available
            provider = None
            model_identifier = None
            if model_config_map and model_name in model_config_map:
                config = model_config_map[model_name]
                provider = config.get('provider')
                model_identifier = config.get('model_name')  # This is the actual model identifier
            
            model_data = {
                "model": model_name,
                "timestamp": report.timestamp,
                "provider": provider,
                "model_identifier": model_identifier,
                "summary": {
                    'total_tests': summary.total_tests,
                    'correct_detections': summary.correct_detections,
                    'accuracy': summary.accuracy,
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
    
    def print_summary(self, report: OrientationTestReport):
        """Print a formatted summary of the orientation test results"""
        print("\n" + "="*70)
        print("ORIENTATION TEST SUMMARY")
        print("="*70)
        print(f"Total images tested: {report.total_images}")
        print(f"Models tested: {', '.join(report.models_tested)}")
        print(f"Replications per test: {report.replications}")
        print(f"Total tests: {len(report.results)}")
        print("="*70)
        
        # Per-model summary
        print("\nPer-Model Results:")
        print("-" * 70)
        for model_name in report.models_tested:
            summary = report.summary[model_name]
            print(f"\n{model_name}:")
            print(f"  Total tests: {summary.total_tests}")
            print(f"  Correct detections: {summary.correct_detections}")
            print(f"  Overall accuracy: {summary.accuracy:.1%}")
            
            if summary.consistency_score is not None:
                print(f"  Consistency score: {summary.consistency_score:.1%}")
            
            if summary.mean_processing_time:
                print(f"  Mean processing time: {summary.mean_processing_time:.2f}s")
            
            print(f"  Accuracy by rotation:")
            for rotation in self.ROTATION_ANGLES:
                if rotation in summary.accuracy_by_rotation:
                    rot_stats = summary.accuracy_by_rotation[rotation]
                    print(f"    {rotation}°: {rot_stats['accuracy']:.1%} "
                          f"({rot_stats['correct']}/{rot_stats['count']})")
        
        # Overall statistics
        print("\n" + "="*70)
        print("Overall Statistics:")
        print("-" * 70)
        stats = report.overall_statistics
        print(f"Overall accuracy: {stats['overall_accuracy']:.1%}")
        print(f"Total tests: {stats['total_tests']}")
        print(f"Total correct: {stats['total_correct']}")
        
        if stats.get('best_rotation'):
            print(f"\nBest performing rotation: {stats['best_rotation']['angle']}° "
                  f"({stats['best_rotation']['accuracy']:.1%})")
        if stats.get('worst_rotation'):
            print(f"Most challenging rotation: {stats['worst_rotation']['angle']}° "
                  f"({stats['worst_rotation']['accuracy']:.1%})")
        
        print("="*70 + "\n")

