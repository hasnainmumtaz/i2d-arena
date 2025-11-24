# Orientation Test Module

## Overview

The `orientation_test.py` module provides functionality for testing LLM models' ability to detect image orientation. It systematically rotates images to different angles (0°, 90°, 180°, 270°) and evaluates how accurately each model can identify the rotation angle.

## Architecture

### Data Classes

#### `OrientationTestResult`

**Location**: `orientation_test.py:17-28`

**Fields**:
- `image_path` (str): Path to the original image
- `actual_rotation` (int): Actual rotation angle applied (0, 90, 180, or 270)
- `detected_rotation` (Optional[int]): Rotation angle detected by the model
- `model_name` (str): Name of the model being tested
- `response` (str): Raw LLM response
- `is_correct` (bool): Whether the detection was correct
- `processing_time` (Optional[float]): Time taken to process (seconds)
- `error` (Optional[str]): Error message if processing failed
- `replication` (int): Replication number (for multiple runs)

#### `OrientationTestSummary`

**Location**: `orientation_test.py:31-40`

**Fields**:
- `model_name` (str): Name of the model
- `total_tests` (int): Total number of tests performed
- `correct_detections` (int): Number of correct detections
- `accuracy` (float): Overall accuracy (0.0 to 1.0)
- `accuracy_by_rotation` (Dict[int, Dict[str, float]]): Accuracy breakdown by rotation angle
- `consistency_score` (Optional[float]): Consistency across replications (if > 1)
- `mean_processing_time` (Optional[float]): Average processing time per test

#### `OrientationTestReport`

**Location**: `orientation_test.py:43-53`

**Fields**:
- `timestamp` (str): ISO format timestamp
- `images_dir` (str): Directory containing test images
- `models_tested` (List[str]): List of model names tested
- `replications` (int): Number of replications per test
- `total_images` (int): Total number of images tested
- `results` (List[OrientationTestResult]): All test results
- `summary` (Dict[str, OrientationTestSummary]): Summary per model
- `overall_statistics` (Dict): Overall statistics across all models

### Main Class: `OrientationTester`

**Location**: `orientation_test.py:56-659`

#### Initialization

```python
OrientationTester(images_dir)
```

**Parameters**:
- `images_dir` (str): Directory containing images to test

**Constants**:
- `ROTATION_ANGLES` (List[int]): [0, 90, 180, 270] - Angles to test
- `ORIENTATION_PROMPT` (str): Prompt for orientation detection

#### Key Methods

##### `rotate_image(image_path, angle)`

**Location**: `orientation_test.py:80-103`

**Purpose**: Rotate image in memory and return as BytesIO object

**Parameters**:
- `image_path` (Path): Path to image file
- `angle` (int): Rotation angle in degrees (0, 90, 180, 270)

**Returns**: `BytesIO` object containing rotated image

**Process**:
1. Open image using PIL
2. Rotate image by negative angle (for clockwise rotation)
3. Save rotated image to BytesIO buffer
4. Return buffer

##### `parse_orientation_response(response)`

**Location**: `orientation_test.py:105-167`

**Purpose**: Parse orientation angle from LLM response

**Parameters**:
- `response`: LLM response (can be str, dict, or other type)

**Returns**: `Optional[int]` - Detected rotation angle (0, 90, 180, 270) or None

**Parsing Strategy**:
1. Convert response to string if needed
2. Extract numbers using regex patterns
3. Try keyword matching (upright, clockwise, etc.)
4. Normalize to valid angles (0, 90, 180, 270)
5. Handle edge cases (360° → 0°)

##### `test_single_orientation(image_path, rotation_angle, transcriber, model_name, replication)`

**Location**: `orientation_test.py:169-260`

**Purpose**: Test orientation detection for a single image/rotation combination

**Parameters**:
- `image_path` (Path): Path to original image
- `rotation_angle` (int): Rotation angle to test
- `transcriber`: Transcriber instance
- `model_name` (str): Name of the model
- `replication` (int): Replication number

**Returns**: `OrientationTestResult`

**Process**:
1. Rotate image in memory
2. Encode rotated image to base64
3. Create data URL for transcriber
4. Call transcriber with orientation prompt
5. Parse response to get detected angle
6. Check if detection is correct
7. Return result with timing and error info

##### `test_batch(model_configs, max_images, replications, parallel, max_workers)`

**Location**: `orientation_test.py:273-428`

**Purpose**: Test orientation detection for multiple images and models

**Parameters**:
- `model_configs` (List[Dict]): List of model configurations
- `max_images` (Optional[int]): Maximum number of images to test
- `replications` (int): Number of times to test each image/rotation
- `parallel` (bool): Whether to use parallel processing
- `max_workers` (int): Maximum number of parallel workers

**Returns**: `OrientationTestReport`

**Process Flow**:
1. Find all image files in directory
2. For each model:
   - Create transcriber
   - Prepare all test tasks (image × rotation × replication)
   - Process tasks (parallel or sequential)
   - Collect results
3. Calculate summary statistics
4. Generate overall statistics
5. Return complete report

**Parallel Processing**:
- Uses `ThreadPoolExecutor` for parallel execution
- Configurable worker count
- Progress tracking during execution

##### `_calculate_summary(results, model_names, replications)`

**Location**: `orientation_test.py:430-500`

**Purpose**: Calculate summary statistics for each model

**Returns**: `Dict[str, OrientationTestSummary]`

**Calculations**:
- Total tests and correct detections
- Overall accuracy
- Accuracy by rotation angle
- Consistency score (if replications > 1)
- Mean processing time

##### `_calculate_overall_statistics(results, model_names)`

**Location**: `orientation_test.py:502-541`

**Purpose**: Calculate overall statistics across all models

**Returns**: `Dict` with overall statistics

**Statistics**:
- Total tests and correct detections
- Overall accuracy
- Accuracy by rotation (across all models)
- Best and worst performing rotations

##### `save_results(report, output_path)`

**Location**: `orientation_test.py:543-606`

**Purpose**: Save orientation test results to JSON files

**Parameters**:
- `report` (OrientationTestReport): Report to save
- `output_path` (str): Path to output summary JSON file

**Output Files**:
1. Summary report: `orientation_test_results.json` (or specified path)
2. Individual model results: `results/orientation/{model_name}.json`

**File Structure**:
```json
{
  "timestamp": "2024-01-01T12:00:00",
  "images_dir": "images",
  "models_tested": ["GPT-4o", "Claude 3.5 Sonnet"],
  "replications": 1,
  "total_images": 30,
  "results": [...],
  "summary": {
    "GPT-4o": {
      "total_tests": 120,
      "correct_detections": 100,
      "accuracy": 0.833,
      "accuracy_by_rotation": {
        "0": {"accuracy": 1.0, "count": 30, "correct": 30},
        "90": {"accuracy": 0.9, "count": 30, "correct": 27},
        ...
      },
      "mean_processing_time": 2.5
    }
  },
  "overall_statistics": {...}
}
```

##### `print_summary(report)`

**Location**: `orientation_test.py:608-658`

**Purpose**: Print formatted summary of orientation test results

**Output Sections**:
1. Header with test parameters
2. Per-model results with accuracy breakdown
3. Overall statistics
4. Best/worst performing rotations

## Testing Flow

### Workflow

1. **Initialization**:
   - Create `OrientationTester` with images directory
   - Find all image files

2. **Image Rotation**:
   - For each image, rotate to 0°, 90°, 180°, 270°
   - Rotations done in memory (no disk writes)

3. **Model Testing**:
   - For each model:
     - Create transcriber
     - Process all rotated images
     - Parse orientation responses
     - Record results

4. **Replication** (optional):
   - Repeat tests multiple times for consistency
   - Calculate consistency scores

5. **Analysis**:
   - Calculate per-model statistics
   - Calculate overall statistics
   - Identify best/worst rotations

6. **Output**:
   - Save results to JSON
   - Print formatted summary

## Integration with Other Modules

### Dependencies

- **`image_transcriber`**: Uses `create_transcriber()` to create transcribers
- **`PIL` (Pillow)**: For image rotation
- **`base64`**: For image encoding

### Usage Pattern

```python
from orientation_test import OrientationTester
from image_transcriber import create_transcriber

tester = OrientationTester(images_dir="images")

model_configs = [
    {
        'name': 'GPT-4o',
        'provider': 'openai',
        'model_name': 'gpt-4o'
    }
]

report = tester.test_batch(
    model_configs=model_configs,
    max_images=30,
    replications=1,
    parallel=True,
    max_workers=10
)

tester.print_summary(report)
tester.save_results(report, "orientation_test_results.json")
```

## Response Parsing

### Supported Response Formats

The parser handles various response formats:

1. **Direct Numbers**: "0", "90", "180", "270"
2. **With Units**: "0 degrees", "90°", "180 deg"
3. **Text Descriptions**: "upright", "clockwise", "upside down"
4. **Dictionary Responses**: Extracts text from dict structures

### Parsing Patterns

- Regex patterns for number extraction
- Keyword matching for text descriptions
- Normalization to valid angles
- Edge case handling (360° → 0°)

## Metrics and Statistics

### Per-Model Metrics

- **Total Tests**: Number of orientation tests performed
- **Correct Detections**: Number of correct angle detections
- **Overall Accuracy**: Percentage of correct detections
- **Accuracy by Rotation**: Breakdown for each angle (0°, 90°, 180°, 270°)
- **Consistency Score**: Agreement across replications (if applicable)
- **Mean Processing Time**: Average time per test

### Overall Statistics

- **Overall Accuracy**: Across all models and tests
- **Accuracy by Rotation**: Performance for each angle across all models
- **Best/Worst Rotations**: Angles with highest/lowest accuracy

## Usage Examples

### Basic Orientation Test

```python
from orientation_test import OrientationTester

tester = OrientationTester(images_dir="images")

model_configs = [
    {
        'name': 'GPT-4o-mini',
        'provider': 'openai',
        'model_name': 'gpt-4o-mini'
    }
]

report = tester.test_batch(
    model_configs=model_configs,
    max_images=10
)

tester.print_summary(report)
```

### Multi-Model Comparison

```python
model_configs = [
    {
        'name': 'GPT-4o',
        'provider': 'openai',
        'model_name': 'gpt-4o'
    },
    {
        'name': 'Claude 3.5 Sonnet',
        'provider': 'anthropic',
        'model_name': 'claude-3-5-sonnet-20241022'
    },
    {
        'name': 'Gemini Pro',
        'provider': 'google',
        'model_name': 'gemini-pro-vision'
    }
]

report = tester.test_batch(
    model_configs=model_configs,
    max_images=30,
    parallel=True,
    max_workers=10
)
```

### With Replications

```python
report = tester.test_batch(
    model_configs=model_configs,
    max_images=30,
    replications=3,  # Test each rotation 3 times
    parallel=True
)

# Consistency score will be calculated
```

## Important Notes

- **Image Rotation**: Rotations are done in memory, original images are not modified
- **Parallel Processing**: Can significantly speed up testing with multiple workers
- **Response Parsing**: Robust parsing handles various response formats
- **Error Handling**: Individual test failures don't stop the batch
- **Memory Usage**: All rotated images are kept in memory during processing
- **API Costs**: Each rotation counts as a separate API call

## Performance Considerations

### Parallel Processing

- **Speed**: Parallel processing can significantly reduce total time
- **Worker Count**: Adjust based on API rate limits
- **Memory**: More workers = more memory usage

### Processing Time

- **Per Test**: Typically 1-5 seconds depending on model
- **Total Time**: images × rotations × models × replications
- **Example**: 30 images × 4 rotations × 3 models × 1 replication = 360 tests

## Best Practices

1. **Start Small**: Test with a few images first
2. **Use Parallel**: Enable parallel processing for faster execution
3. **Check Costs**: Be aware of API costs (each rotation is a separate call)
4. **Review Results**: Check accuracy by rotation to identify model weaknesses
5. **Replications**: Use replications for consistency testing
6. **Save Results**: Always save results for later analysis

