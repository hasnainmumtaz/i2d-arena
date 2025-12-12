# Batch Processing Module

## Overview

The `batch_processor.py` module handles processing multiple images in batch mode. It supports parallel processing, ground truth matching, and structured data extraction.

## Architecture

### Data Classes

#### `TranscriptionResult`

**Location**: `batch_processor.py:14-23`

**Fields**:
- `image_path` (str): Path to the processed image
- `transcription` (str): The transcribed text or JSON string
- `ground_truth_path` (Optional[str]): Path to ground truth file
- `ground_truth` (Optional[Dict]): Loaded ground truth data
- `extracted_data` (Optional[Dict]): Parsed structured data from transcription
- `processing_time` (Optional[float]): Time taken to process (seconds)
- `error` (Optional[str]): Error message if processing failed

#### `BatchProcessingResult`

**Location**: `batch_processor.py:26-34`

**Fields**:
- `results` (List[TranscriptionResult]): List of all transcription results
- `total_images` (int): Total number of images processed
- `successful` (int): Number of successful transcriptions
- `failed` (int): Number of failed transcriptions
- `processing_time` (float): Total processing time (seconds)
- `timestamp` (str): ISO format timestamp of processing

### Main Class: `BatchProcessor`

**Location**: `batch_processor.py:37-299`

#### Initialization

```python
BatchProcessor(transcriber, images_dir, ground_truth_dir=None)
```

**Parameters**:
- `transcriber`: Instance of `ImageTranscriber` (or subclass)
- `images_dir` (str): Directory containing images to process
- `ground_truth_dir` (Optional[str]): Directory containing ground truth files

#### Key Methods

##### `find_image_files(extensions)`

**Location**: `batch_processor.py:53-59`

**Purpose**: Find all image files in the images directory

**Parameters**:
- `extensions` (Tuple[str, ...]): File extensions to search for (default: `('.jpg', '.jpeg', '.png', '.webp')`)

**Returns**: `List[Path]` - Sorted list of image file paths

**Features**:
- Searches for both lowercase and uppercase extensions
- Returns sorted list for consistent processing order

##### `load_ground_truth(image_path)`

**Location**: `batch_processor.py:61-89`

**Purpose**: Load ground truth data for an image

**Parameters**:
- `image_path` (Path): Path to the image file

**Returns**: `Optional[Dict]` - Ground truth data or None

**Features**:
- Matches ground truth files by base name (without extension)
- Tries JSON format first (`.json`)
- Falls back to text format (`.txt`) if JSON not found
- Returns `{"text": "..."}` for text files
- Handles errors gracefully with warnings

**Matching Logic**:
- Image: `images/001.jpg` → Ground truth: `gdt/001.json` or `gdt/001.txt`

##### `process_single_image(image_path, prompt)`

**Location**: `batch_processor.py:91-180`

**Purpose**: Process a single image and return transcription result

**Parameters**:
- `image_path` (Path): Path to image file
- `prompt` (Optional[str]): Custom prompt for transcription

**Returns**: `TranscriptionResult`

**Features**:
- Measures processing time
- Automatically loads ground truth if available
- Uses structured extraction if ground truth exists
- Handles both structured and unstructured transcriptions
- Parses JSON from transcription string if needed
- Captures errors and includes them in result

**Processing Flow**:
1. Load ground truth (if available)
2. Determine if structured output should be used
3. Call transcriber with appropriate parameters
4. Parse structured data if returned
5. Measure processing time
6. Return `TranscriptionResult`

**Error Handling**:
- Catches all exceptions
- Returns `TranscriptionResult` with error message
- Still includes processing time even on failure

##### `process_batch(prompt, image_extensions, max_images, parallel, max_workers)`

**Location**: `batch_processor.py:182-271`

**Purpose**: Process all images in the directory

**Parameters**:
- `prompt` (Optional[str]): Custom prompt for transcription
- `image_extensions` (Tuple[str, ...]): File extensions to process
- `max_images` (Optional[int]): Maximum number of images (None for all)
- `parallel` (bool): Enable parallel processing (default: True)
- `max_workers` (int): Number of parallel workers (default: 10)

**Returns**: `BatchProcessingResult`

**Features**:
- Supports both parallel and sequential processing
- Progress reporting during processing
- Limits number of images if `max_images` specified
- Sorts results to match original file order
- Calculates success/failure statistics

**Parallel Processing**:
- Uses `ThreadPoolExecutor` for concurrent execution
- Processes up to `max_workers` images simultaneously
- Shows progress with `[completed/total]` format
- Handles exceptions from individual tasks

**Sequential Processing**:
- Processes images one by one
- Shows detailed progress for each image
- Better for debugging or when API rate limits are strict

##### `save_results(batch_result, output_path)`

**Location**: `batch_processor.py:273-298`

**Purpose**: Save batch processing results to JSON file

**Parameters**:
- `batch_result` (BatchProcessingResult): Results to save
- `output_path` (str): Path to output JSON file

**Output Format**:
```json
{
    "timestamp": "2024-01-01T12:00:00",
    "total_images": 30,
    "successful": 28,
    "failed": 2,
    "processing_time": 120.5,
    "results": [
        {
            "image_path": "images/001.jpg",
            "transcription": "...",
            "extracted_data": {...},
            "ground_truth_path": "gdt/001.json",
            "ground_truth": {...},
            "processing_time": 4.2,
            "error": null
        },
        ...
    ]
}
```

## Processing Flow

### Batch Processing Workflow

1. **Initialization**:
   - Create `BatchProcessor` with transcriber and directories
   - Set up image and ground truth directory paths

2. **Image Discovery**:
   - Find all image files matching extensions
   - Sort files for consistent processing

3. **Image Limiting** (if `max_images` specified):
   - Take first N images from sorted list

4. **Processing**:
   - **Parallel Mode**: Submit all tasks to thread pool, process as completed
   - **Sequential Mode**: Process one image at a time

5. **Result Collection**:
   - Collect all `TranscriptionResult` objects
   - Sort results to match original file order (for parallel mode)

6. **Statistics Calculation**:
   - Count successful/failed transcriptions
   - Calculate total processing time
   - Generate timestamp

7. **Output**:
   - Save results to JSON file
   - Print summary statistics

### Single Image Processing Flow

1. **Ground Truth Loading**:
   - Try to load matching ground truth file
   - Handle JSON and text formats

2. **Transcription**:
   - Use structured extraction if ground truth exists
   - Fall back to regular transcription if structured fails
   - Parse JSON from transcription if needed

3. **Result Creation**:
   - Create `TranscriptionResult` with all data
   - Include processing time and any errors

## Integration with Other Modules

### Dependencies

- **`image_transcriber`**: Uses transcriber instances for actual transcription
- **`evaluator`**: Results are used by `TranscriptionEvaluator` for evaluation

### Usage in CLI

The batch processor is invoked via:
```python
process_batch_mode(args)  # in image_transcriber.py
```

This function:
1. Creates transcriber using `create_transcriber()`
2. Creates `BatchProcessor` instance
3. Calls `process_batch()`
4. Saves results
5. Optionally runs evaluation if ground truth available

## Error Handling

- **File Not Found**: Handled gracefully, returns None for ground truth
- **JSON Parsing Errors**: Warns but continues processing
- **Transcription Errors**: Captured in `TranscriptionResult.error`
- **Thread Pool Exceptions**: Caught and reported per image

## Performance Considerations

### Parallel Processing

- **Benefits**: Significantly faster for multiple images
- **Limitations**: 
  - API rate limits may require sequential processing
  - Thread pool overhead for small batches
  - Memory usage increases with parallel workers

### Optimization Tips

- Use `max_images` for testing
- Adjust `max_workers` based on API rate limits
- Use sequential mode if encountering rate limit errors
- Process in smaller batches if memory is limited

## Usage Examples

### Basic Batch Processing

```python
from image_transcriber import create_transcriber
from batch_processor import BatchProcessor

transcriber = create_transcriber(provider="openai")
processor = BatchProcessor(
    transcriber=transcriber,
    images_dir="images",
    ground_truth_dir="gdt"
)

result = processor.process_batch(
    prompt="Extract all text from this image.",
    max_images=10
)

processor.save_results(result, "results.json")
```

### Sequential Processing

```python
result = processor.process_batch(
    prompt="Describe this image",
    parallel=False  # Process one at a time
)
```

### Custom Extensions

```python
result = processor.process_batch(
    image_extensions=('.jpg', '.png', '.tiff')
)
```

## Important Notes

- **Ground Truth Matching**: Files must have same base name (different extensions)
- **Structured Output**: Automatically enabled if ground truth exists
- **Result Ordering**: Results are sorted by image path for consistency
- **Error Recovery**: Individual image failures don't stop batch processing
- **Progress Reporting**: Shows real-time progress during processing

