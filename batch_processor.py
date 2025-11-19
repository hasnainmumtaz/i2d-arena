"""
Batch processing module for image transcription
Handles processing multiple images and comparing with ground truth
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TranscriptionResult:
    """Result of a single image transcription"""
    image_path: str
    transcription: str
    ground_truth_path: Optional[str] = None
    ground_truth: Optional[Dict] = None
    extracted_data: Optional[Dict] = None  # Parsed structured data
    processing_time: Optional[float] = None
    error: Optional[str] = None


@dataclass
class BatchProcessingResult:
    """Results of batch processing"""
    results: List[TranscriptionResult]
    total_images: int
    successful: int
    failed: int
    processing_time: float
    timestamp: str


class BatchProcessor:
    """Process multiple images in batch"""
    
    def __init__(self, transcriber, images_dir: str, ground_truth_dir: Optional[str] = None):
        """
        Initialize batch processor
        
        Args:
            transcriber: Instance of ImageTranscriber (or subclass)
            images_dir: Directory containing images to process
            ground_truth_dir: Optional directory containing ground truth files
        """
        self.transcriber = transcriber
        self.images_dir = Path(images_dir)
        self.ground_truth_dir = Path(ground_truth_dir) if ground_truth_dir else None
    
    def find_image_files(self, extensions: Tuple[str, ...] = ('.jpg', '.jpeg', '.png', '.webp')) -> List[Path]:
        """Find all image files in the images directory"""
        image_files = []
        for ext in extensions:
            image_files.extend(self.images_dir.glob(f"*{ext}"))
            image_files.extend(self.images_dir.glob(f"*{ext.upper()}"))
        return sorted(image_files)
    
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
    
    def process_single_image(self, image_path: Path, prompt: str = None) -> TranscriptionResult:
        """Process a single image"""
        import time
        import json
        
        start_time = time.time()
        ground_truth = self.load_ground_truth(image_path)
        gt_path = None
        
        if ground_truth and self.ground_truth_dir:
            base_name = image_path.stem
            gt_path = str(self.ground_truth_dir / f"{base_name}.json")
        
        try:
            # Use structured extraction by default if ground truth exists
            use_structured = ground_truth is not None
            
            # Check if transcriber supports structured output
            if use_structured:
                # Try structured output
                try:
                    result = self.transcriber.transcribe(
                        str(image_path),
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
                    transcription = self.transcriber.transcribe(
                        str(image_path),
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
                default_prompt = prompt or "Transcribe or describe everything you see in this image in detail."
                transcription = self.transcriber.transcribe(
                    str(image_path),
                    prompt=default_prompt
                )
                extracted_data = None
            
            processing_time = time.time() - start_time
            
            return TranscriptionResult(
                image_path=str(image_path),
                transcription=transcription if isinstance(transcription, str) else json.dumps(transcription, ensure_ascii=False),
                ground_truth_path=gt_path,
                ground_truth=ground_truth,
                extracted_data=extracted_data,
                processing_time=processing_time
            )
        except Exception as e:
            processing_time = time.time() - start_time
            return TranscriptionResult(
                image_path=str(image_path),
                transcription="",
                ground_truth_path=gt_path,
                ground_truth=ground_truth,
                extracted_data=None,
                processing_time=processing_time,
                error=str(e)
            )
    
    def process_batch(
        self,
        prompt: Optional[str] = None,
        image_extensions: Tuple[str, ...] = ('.jpg', '.jpeg', '.png', '.webp'),
        max_images: Optional[int] = None,
        parallel: bool = True,
        max_workers: int = 10
    ) -> BatchProcessingResult:
        """
        Process all images in the directory
        
        Args:
            prompt: Custom prompt for transcription
            image_extensions: File extensions to process
            max_images: Maximum number of images to process (None for all)
            parallel: If True, process images in parallel
            max_workers: Number of parallel workers (if parallel=True)
        
        Returns:
            BatchProcessingResult with all transcription results
        """
        import time
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        start_time = time.time()
        image_files = self.find_image_files(image_extensions)
        
        if max_images:
            image_files = image_files[:max_images]
        
        results = []
        
        if parallel and len(image_files) > 1:
            # Parallel processing
            print(f"Processing {len(image_files)} images in parallel (max {max_workers} workers)...")
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_image = {
                    executor.submit(self.process_single_image, img_path, prompt): img_path
                    for img_path in image_files
                }
                
                # Process completed tasks
                completed = 0
                for future in as_completed(future_to_image):
                    completed += 1
                    image_path = future_to_image[future]
                    try:
                        result = future.result()
                        results.append(result)
                        if result.error:
                            print(f"  [{completed}/{len(image_files)}] {image_path.name}: Error - {result.error}")
                        else:
                            print(f"  [{completed}/{len(image_files)}] {image_path.name}: Success ({result.processing_time:.2f}s)")
                    except Exception as e:
                        print(f"  [{completed}/{len(image_files)}] {image_path.name}: Exception - {e}")
                        results.append(TranscriptionResult(
                            image_path=str(image_path),
                            transcription="",
                            ground_truth=self.load_ground_truth(image_path),
                            extracted_data=None,
                            error=str(e)
                        ))
            
            # Sort results to match original file order
            results.sort(key=lambda x: x.image_path)
        else:
            # Sequential processing
            for i, image_path in enumerate(image_files, 1):
                print(f"Processing {i}/{len(image_files)}: {image_path.name}")
                result = self.process_single_image(image_path, prompt)
                results.append(result)
                
                if result.error:
                    print(f"  Error: {result.error}")
                else:
                    print(f"  Success ({result.processing_time:.2f}s)")
        
        total_time = time.time() - start_time
        successful = sum(1 for r in results if not r.error)
        failed = len(results) - successful
        
        return BatchProcessingResult(
            results=results,
            total_images=len(image_files),
            successful=successful,
            failed=failed,
            processing_time=total_time,
            timestamp=datetime.now().isoformat()
        )
    
    def save_results(self, batch_result: BatchProcessingResult, output_path: str):
        """Save batch processing results to JSON file"""
        output_data = {
            "timestamp": batch_result.timestamp,
            "total_images": batch_result.total_images,
            "successful": batch_result.successful,
            "failed": batch_result.failed,
            "processing_time": batch_result.processing_time,
            "results": [
                {
                    "image_path": r.image_path,
                    "transcription": r.transcription,
                    "extracted_data": r.extracted_data,
                    "ground_truth_path": r.ground_truth_path,
                    "ground_truth": r.ground_truth,
                    "processing_time": r.processing_time,
                    "error": r.error
                }
                for r in batch_result.results
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to: {output_path}")

