# Model Comparison Module

## Overview

The `model_comparator.py` module provides functionality for comparing the performance of multiple LLM models on the same set of images. It generates comprehensive comparison reports with side-by-side metrics.

## Architecture

### Data Classes

#### `ModelComparisonResult`

**Location**: `model_comparator.py:17-24`

**Fields**:
- `models` (List[str]): List of model names compared
- `comparison_data` (Dict[str, BatchProcessingResult]): Results for each model
- `timestamp` (str): ISO format timestamp of comparison
- `images_dir` (str): Directory containing images
- `ground_truth_dir` (Optional[str]): Directory containing ground truth

### Main Class: `ModelComparator`

**Location**: `model_comparator.py:27-411`

#### Initialization

```python
ModelComparator(images_dir, ground_truth_dir=None)
```

**Parameters**:
- `images_dir` (str): Directory containing images to process
- `ground_truth_dir` (Optional[str]): Directory containing ground truth files

**Internal Setup**:
- Creates `TranscriptionEvaluator` instance for metrics calculation

#### Key Methods

##### `compare_models(model_configs, prompt, max_images, save_individual_results)`

**Location**: `model_comparator.py:42-117`

**Purpose**: Compare multiple models on the same set of images

**Parameters**:
- `model_configs` (List[Dict]): List of model configurations
  - Each config contains:
    - `name` (str): Display name for the model
    - `provider` (str): Provider name (openai, anthropic, etc.)
    - `model_name` (str): Model name/ID
    - `api_key` (Optional[str]): API key
    - `kwargs` (Optional[Dict]): Additional parameters
- `prompt` (Optional[str]): Custom prompt for transcription
- `max_images` (Optional[int]): Maximum number of images to process
- `save_individual_results` (bool): Whether to save individual model results

**Returns**: `ModelComparisonResult`

**Process Flow**:
1. Iterate through each model configuration
2. Create transcriber for each model
3. Process batch with each transcriber
4. Store results in comparison data
5. Optionally save individual results
6. Return comparison result

**Output**:
- Prints progress for each model
- Shows processing statistics
- Saves individual results if requested

##### `generate_comparison_report(comparison_result, output_path)`

**Location**: `model_comparator.py:119-226`

**Purpose**: Generate detailed comparison report

**Parameters**:
- `comparison_result` (ModelComparisonResult): Comparison results
- `output_path` (str): Path to output JSON file (default: "model_comparison_report.json")

**Returns**: `Dict` - The generated report

**Report Structure**:
```json
{
    "timestamp": "2024-01-01T12:00:00",
    "images_dir": "images",
    "ground_truth_dir": "gdt",
    "models_compared": ["GPT-4o-mini", "GPT-4o", "Claude 3.5 Sonnet"],
    "summary": {
        "best_success_rate": 1.0,
        "fastest_average_time": 3.5,
        "fastest_total_time": 105.0,
        "best_overall_accuracy": 0.92
    },
    "per_model_metrics": {
        "GPT-4o-mini": {
            "total_images": 30,
            "successful_transcriptions": 30,
            "failed_transcriptions": 0,
            "success_rate": 1.0,
            "average_processing_time": 3.5,
            "total_processing_time": 105.0,
            "images_with_ground_truth": 30,
            "overall_accuracy": 0.88,
            "field_statistics": {...}
        },
        ...
    },
    "per_image_comparison": [
        {
            "image": "001.jpg",
            "image_path": "images/001.jpg",
            "ground_truth": {...},
            "models": {
                "GPT-4o-mini": {
                    "transcription": "...",
                    "extracted_data": {...},
                    "processing_time": 3.5,
                    "error": null,
                    "success": true,
                    "comparison": {
                        "overall_accuracy": 0.85,
                        "field_accuracy": {...}
                    }
                },
                ...
            }
        },
        ...
    ],
    "accuracy_comparison": {
        "overall_accuracy": {
            "GPT-4o-mini": 0.88,
            "GPT-4o": 0.92,
            ...
        },
        "field_accuracy": {
            "company": {
                "GPT-4o-mini": {
                    "exact_match_rate": 0.83,
                    "partial_match_rate": 0.10,
                    "no_match_rate": 0.07,
                    "total": 30
                },
                ...
            },
            ...
        }
    }
}
```

**Features**:
- Per-model metrics with success rates and accuracy
- Per-image comparison showing all models side-by-side
- Field-level accuracy comparison
- Summary statistics identifying best performers

##### `_generate_accuracy_comparison(per_model_metrics)`

**Location**: `model_comparator.py:228-257`

**Purpose**: Generate accuracy comparison section

**Parameters**:
- `per_model_metrics` (Dict): Metrics for each model

**Returns**: `Dict` with accuracy comparison data

**Structure**:
- Overall accuracy for each model
- Field-level accuracy breakdown
- Match rates (exact, partial, no match) per field per model

##### `print_comparison_summary(comparison_result)`

**Location**: `model_comparator.py:259-363`

**Purpose**: Print formatted comparison summary to console

**Parameters**:
- `comparison_result` (ModelComparisonResult): Comparison results

**Output Sections**:

1. **Basic Metrics Table**:
   ```
   Model                          Success Rate    Avg Time (s)    Total Time (s)
   ------------------------------------------------------------------------------
   GPT-4o-mini                    100.0%         3.50            105.00
   GPT-4o                          100.0%         4.20            126.00
   ```

2. **Overall Accuracy Comparison**:
   ```
   Model                          Accuracy
   ------------------------------------------------------------------------------
   GPT-4o                          92.0%
   GPT-4o-mini                     88.0%
   ```

3. **Field-Level Accuracy Comparison**:
   ```
   COMPANY:
     Model                        Exact         Partial       Total
     ------------------------------------------------------------------------
     GPT-4o                       90.0%        5.0%          95.0%
     GPT-4o-mini                  83.3%        10.0%         93.3%
   ```

4. **Best Performers**:
   ```
   Best Success Rate: GPT-4o-mini (30/30)
   Best Overall Accuracy: GPT-4o (92.0%)
   Fastest Average Time: GPT-4o-mini (3.50s)
   Fastest Total Time: GPT-4o-mini (105.00s)
   ```

##### `save_comparison_results(comparison_result, output_dir)`

**Location**: `model_comparator.py:365-410`

**Purpose**: Save all comparison results to a directory

**Parameters**:
- `comparison_result` (ModelComparisonResult): Comparison results
- `output_dir` (str): Output directory path (default: "comparison_results")

**Features**:
- Creates output directory if it doesn't exist
- Saves individual model results as separate JSON files
- File naming: `{model_name}_results.json`

## Comparison Flow

### Workflow

1. **Initialization**:
   - Create `ModelComparator` with image and ground truth directories
   - Initialize evaluator

2. **Model Processing**:
   - For each model configuration:
     - Create transcriber
     - Process batch of images
     - Store results
     - Optionally save individual results

3. **Report Generation**:
   - Calculate metrics for each model
   - Generate per-image comparisons
   - Calculate accuracy comparisons
   - Generate summary statistics

4. **Output**:
   - Print formatted summary
   - Save detailed report to JSON
   - Optionally save individual results to directory

## Integration with Other Modules

### Dependencies

- **`image_transcriber`**: Uses `create_transcriber()` to create transcribers
- **`batch_processor`**: Uses `BatchProcessor` for processing
- **`evaluator`**: Uses `TranscriptionEvaluator` for metrics

### Usage in CLI

The comparator is invoked via:
```python
process_comparison_mode(args)  # in image_transcriber.py
```

**Command Line Format**:
```bash
python image_transcriber.py --compare \
  --images-dir images \
  --ground-truth-dir gdt \
  --models "GPT-4o-mini:openai:gpt-4o-mini" "GPT-4o:openai:gpt-4o"
```

## Model Configuration Format

### Configuration Dictionary

```python
{
    'name': 'GPT-4o-mini',           # Display name
    'provider': 'openai',             # Provider name
    'model_name': 'gpt-4o-mini',      # Model identifier
    'api_key': 'optional-key',        # Optional API key
    'kwargs': {                       # Optional additional parameters
        'temperature': 0.5,
        'max_tokens': 2000
    }
}
```

### Command Line Format

Format: `"name:provider:model_name"`

Example: `"GPT-4o-mini:openai:gpt-4o-mini"`

## Metrics Comparison

### Per-Model Metrics

- **Success Rate**: Percentage of successful transcriptions
- **Processing Time**: Average and total processing time
- **Overall Accuracy**: Average accuracy across all fields
- **Field Statistics**: Per-field match rates

### Summary Statistics

- **Best Success Rate**: Model with highest success rate
- **Best Overall Accuracy**: Model with highest accuracy
- **Fastest Average Time**: Model with lowest average processing time
- **Fastest Total Time**: Model with lowest total processing time

## Usage Examples

### Basic Comparison

```python
from model_comparator import ModelComparator

comparator = ModelComparator(
    images_dir="images",
    ground_truth_dir="gdt"
)

model_configs = [
    {
        'name': 'GPT-4o-mini',
        'provider': 'openai',
        'model_name': 'gpt-4o-mini'
    },
    {
        'name': 'GPT-4o',
        'provider': 'openai',
        'model_name': 'gpt-4o'
    }
]

comparison = comparator.compare_models(
    model_configs=model_configs,
    prompt="Extract all text from this image.",
    max_images=10
)

comparator.print_comparison_summary(comparison)
comparator.generate_comparison_report(comparison, "comparison.json")
```

### Cross-Provider Comparison

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
        'name': 'Gemini Pro Vision',
        'provider': 'google',
        'model_name': 'gemini-pro-vision'
    }
]

comparison = comparator.compare_models(model_configs)
```

### Save Individual Results

```python
comparison = comparator.compare_models(
    model_configs=model_configs,
    save_individual_results=True  # Saves results_{model_name}.json
)

comparator.save_comparison_results(
    comparison,
    output_dir="comparison_results"
)
```

## Important Notes

- **Same Images**: All models process the same set of images for fair comparison
- **Individual Results**: Can save individual model results for detailed analysis
- **Ground Truth**: Required for accuracy metrics, optional for basic comparison
- **Processing Order**: Models are processed sequentially (one after another)
- **Error Handling**: Individual model failures don't stop comparison

## Performance Considerations

- **Processing Time**: Total time = sum of all model processing times
- **API Costs**: Each model processes all images (costs multiply)
- **Memory**: Results for all models are kept in memory
- **Parallel Processing**: Models process sequentially, but each model can use parallel processing internally

## Best Practices

1. **Start Small**: Use `max_images` to test with a few images first
2. **Save Results**: Always save individual results for later analysis
3. **Compare Fairly**: Use same prompt and settings for all models
4. **Check Costs**: Be aware of API costs when comparing multiple models
5. **Review Reports**: Use detailed reports to identify model strengths/weaknesses

