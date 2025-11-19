# Evaluation Module

## Overview

The `evaluator.py` module provides functionality for evaluating transcription results against ground truth data. It calculates accuracy metrics, compares extracted data with expected values, and generates detailed evaluation reports.

## Architecture

### Data Classes

#### `EvaluationMetrics`

**Location**: `evaluator.py:13-21`

**Fields**:
- `total_images` (int): Total number of images processed
- `successful_transcriptions` (int): Number of successful transcriptions
- `failed_transcriptions` (int): Number of failed transcriptions
- `images_with_ground_truth` (int): Number of images with ground truth data
- `average_processing_time` (float): Average time per image (seconds)
- `total_processing_time` (float): Total processing time (seconds)

### Main Class: `TranscriptionEvaluator`

**Location**: `evaluator.py:24-317`

#### Initialization

```python
TranscriptionEvaluator()
```

No parameters required - evaluator is stateless.

#### Key Methods

##### `calculate_metrics(batch_result)`

**Location**: `evaluator.py:30-46`

**Purpose**: Calculate basic evaluation metrics from batch results

**Parameters**:
- `batch_result` (BatchProcessingResult): Results from batch processing

**Returns**: `EvaluationMetrics`

**Calculations**:
- Counts successful/failed transcriptions
- Counts images with ground truth
- Calculates average processing time
- Extracts total processing time

##### `print_summary(batch_result, metrics)`

**Location**: `evaluator.py:48-65`

**Purpose**: Print a formatted summary of batch processing results

**Parameters**:
- `batch_result` (BatchProcessingResult): Batch processing results
- `metrics` (EvaluationMetrics): Calculated metrics

**Output Format**:
```
======================================================================
BATCH PROCESSING SUMMARY
======================================================================
Total images processed: 30
Successful transcriptions: 28
Failed transcriptions: 2
Images with ground truth: 30
Average processing time: 4.20s
Total processing time: 126.00s
======================================================================
```

Also prints list of failed images if any.

##### `save_detailed_report(batch_result, metrics, output_path)`

**Location**: `evaluator.py:67-132`

**Purpose**: Save comprehensive evaluation report to JSON file

**Parameters**:
- `batch_result` (BatchProcessingResult): Batch processing results
- `metrics` (EvaluationMetrics): Basic metrics
- `output_path` (str): Path to output JSON file

**Report Structure**:
```json
{
    "summary": {
        "total_images": 30,
        "successful_transcriptions": 28,
        "failed_transcriptions": 2,
        "images_with_ground_truth": 30,
        "average_processing_time": 4.2,
        "total_processing_time": 126.0,
        "overall_accuracy": 0.85,
        "total_comparisons": 30
    },
    "field_statistics": {
        "company": {
            "total": 30,
            "exact_matches": 25,
            "partial_matches": 3,
            "no_matches": 2,
            "exact_match_rate": 0.833,
            "partial_match_rate": 0.100,
            "no_match_rate": 0.067
        },
        ...
    },
    "results": [
        {
            "image": "001.jpg",
            "image_path": "images/001.jpg",
            "transcription": "...",
            "extracted_data": {...},
            "ground_truth": {...},
            "processing_time": 4.2,
            "error": null,
            "has_ground_truth": true,
            "comparison": {...}
        },
        ...
    ]
}
```

**Features**:
- Includes detailed comparison for each image
- Calculates field-level statistics
- Prints field-level accuracy summary
- Shows overall accuracy percentage

##### `compare_with_ground_truth(transcription, ground_truth, extracted_data)`

**Location**: `evaluator.py:134-265`

**Purpose**: Compare transcription with ground truth using improved metrics

**Parameters**:
- `transcription` (str): The transcribed text (may be JSON string)
- `ground_truth` (Dict): Ground truth dictionary
- `extracted_data` (Optional[Dict]): Pre-parsed structured data

**Returns**: `Dict` with detailed comparison results

**Comparison Structure**:
```json
{
    "transcription": "...",
    "ground_truth": {...},
    "extracted_data": {...},
    "matches": {
        "company": {
            "expected": "Acme Corp",
            "extracted": "Acme Corporation",
            "found_in_text": null,
            "exact_match": false,
            "partial_match": true
        },
        ...
    },
    "field_accuracy": {
        "company": 0.7,
        "date": 1.0,
        ...
    },
    "overall_accuracy": 0.85
}
```

**Matching Logic**:

1. **JSON Parsing**:
   - Tries to parse transcription as JSON
   - Extracts JSON from markdown code blocks if present
   - Uses `extracted_data` if provided

2. **Field Comparison**:
   - For each field in ground truth:
     - If extracted value exists: Compare directly
     - If not found: Search in raw transcription text
   
3. **Match Types**:
   - **Exact Match**: Values match exactly (case-insensitive)
   - **Partial Match**: 
     - Dates: Numbers match
     - Totals: Numeric values match (ignoring currency)
     - Text: ≥70% word overlap
   - **No Match**: No similarity found

4. **Scoring**:
   - Exact match: 1.0
   - Partial match: 0.7
   - No match: 0.0

5. **Overall Accuracy**: Average of all field scores

**Special Field Handling**:

- **Date Fields**: Compares numeric components
- **Total Fields**: Extracts and compares numeric values
- **Text Fields**: Uses word overlap for partial matching

##### `calculate_detailed_metrics(batch_result)`

**Location**: `evaluator.py:267-317`

**Purpose**: Calculate detailed field-level accuracy metrics

**Parameters**:
- `batch_result` (BatchProcessingResult): Batch processing results

**Returns**: `Dict` with field statistics and overall accuracy

**Statistics Calculated**:
- Total comparisons per field
- Exact match count and rate
- Partial match count and rate
- No match count and rate

**Output Structure**:
```json
{
    "field_statistics": {
        "company": {
            "total": 30,
            "exact_matches": 25,
            "partial_matches": 3,
            "no_matches": 2,
            "exact_match_rate": 0.833,
            "partial_match_rate": 0.100,
            "no_match_rate": 0.067
        },
        ...
    },
    "overall_accuracy": 0.85,
    "total_comparisons": 30
}
```

## Evaluation Flow

### Comparison Process

1. **Data Preparation**:
   - Parse transcription as JSON if possible
   - Extract structured data
   - Load ground truth data

2. **Field-by-Field Comparison**:
   - For each field in ground truth:
     - Extract expected value
     - Extract or search for actual value
     - Determine match type (exact/partial/none)
     - Calculate field score

3. **Accuracy Calculation**:
   - Calculate field-level accuracy
   - Calculate overall accuracy (average of field scores)

4. **Statistics Aggregation**:
   - Aggregate across all images
   - Calculate match rates per field
   - Generate summary statistics

## Integration with Other Modules

### Dependencies

- **`batch_processor`**: Uses `BatchProcessingResult` and `TranscriptionResult`
- Used by **`model_comparator`**: For comparing model performance

### Usage in CLI

The evaluator is invoked in batch mode:
```python
# In process_batch_mode() in image_transcriber.py
if args.ground_truth_dir:
    evaluator = TranscriptionEvaluator()
    metrics = evaluator.calculate_metrics(batch_result)
    evaluator.print_summary(batch_result, metrics)
    evaluator.save_detailed_report(batch_result, metrics, report_file)
```

## Accuracy Metrics

### Field-Level Metrics

- **Exact Match Rate**: Percentage of fields with exact matches
- **Partial Match Rate**: Percentage of fields with partial matches
- **No Match Rate**: Percentage of fields with no matches

### Overall Metrics

- **Overall Accuracy**: Average of all field accuracy scores
- **Success Rate**: Percentage of successful transcriptions
- **Processing Efficiency**: Average processing time per image

## Error Handling

- **JSON Parsing Errors**: Handled gracefully, falls back to text search
- **Missing Fields**: Treated as no match (score: 0.0)
- **Type Mismatches**: Converts to string for comparison
- **Empty Values**: Handled as null/empty string

## Usage Examples

### Basic Evaluation

```python
from evaluator import TranscriptionEvaluator
from batch_processor import BatchProcessor

# After batch processing
evaluator = TranscriptionEvaluator()
metrics = evaluator.calculate_metrics(batch_result)
evaluator.print_summary(batch_result, metrics)
```

### Detailed Report

```python
evaluator.save_detailed_report(
    batch_result,
    metrics,
    "evaluation_report.json"
)
```

### Custom Comparison

```python
comparison = evaluator.compare_with_ground_truth(
    transcription="...",
    ground_truth={"company": "Acme", "date": "01/01/2024"},
    extracted_data={"company": "Acme Corp", "date": "01/01/2024"}
)

print(f"Overall accuracy: {comparison['overall_accuracy']:.1%}")
print(f"Field accuracy: {comparison['field_accuracy']}")
```

## Important Notes

- **Case Insensitive**: All comparisons are case-insensitive
- **Whitespace Handling**: Values are stripped before comparison
- **Partial Matching**: Uses intelligent heuristics for different field types
- **JSON Extraction**: Automatically extracts JSON from markdown code blocks
- **Null Handling**: Null values in extracted data are treated as empty strings

## Performance Considerations

- **Comparison Speed**: Field-by-field comparison is fast
- **JSON Parsing**: May add overhead for large transcriptions
- **Text Search**: Used as fallback, may be slower for large texts
- **Aggregation**: Statistics calculation is efficient

