# Result Compilation Module

## Overview

The `compile_results.py` module provides functionality for compiling individual model result files into consolidated summary reports. It reads JSON result files from the `results/` directory structure and generates unified reports for both comparison and orientation test results.

## Architecture

### Main Functions

#### `compile_comparison_results(results_dir, output_file)`

**Location**: `compile_results.py:6-66`

**Purpose**: Compile individual comparison results into a summary report

**Parameters**:
- `results_dir` (str): Directory containing individual model result files (default: "results/comparison")
- `output_file` (str): Path to output summary JSON file (default: "model_comparison_report.json")

**Returns**: `Dict` - The compiled report, or `None` if no files found

**Process Flow**:
1. Check if results directory exists
2. Find all JSON files in the directory
3. For each JSON file:
   - Load model data
   - Extract model name
   - Extract metrics
   - Ensure required fields are present
   - Add to report
4. Calculate summary statistics
5. Save compiled report to output file

**Input File Structure** (from `results/comparison/{model_name}.json`):
```json
{
  "model": "GPT-4o-mini",
  "timestamp": "2024-01-01T12:00:00",
  "total_images": 30,
  "successful": 30,
  "failed": 0,
  "processing_time": 105.0,
  "metrics": {
    "success_rate": 1.0,
    "average_processing_time": 3.5,
    "total_processing_time": 105.0,
    "overall_accuracy": 0.88,
    "field_statistics": {...}
  },
  "results": [...]
}
```

**Output File Structure**:
```json
{
  "timestamp": "2024-01-01T12:00:00",
  "models_compared": ["GPT-4o-mini", "GPT-4o", "Claude 3.5 Sonnet"],
  "per_model_metrics": {
    "GPT-4o-mini": {
      "success_rate": 1.0,
      "average_processing_time": 3.5,
      "total_processing_time": 105.0,
      "overall_accuracy": 0.88,
      "field_statistics": {...},
      "failed_transcriptions": 0
    },
    ...
  },
  "summary": {
    "total_images": 30
  }
}
```

**Field Normalization**:
- Ensures `failed_transcriptions` is present (from `failed` if needed)
- Calculates `success_rate` if missing
- Calculates `average_processing_time` if missing
- Sets default `overall_accuracy` to 0 if missing

#### `compile_orientation_results(results_dir, output_file)`

**Location**: `compile_results.py:68-111`

**Purpose**: Compile individual orientation test results into a summary report

**Parameters**:
- `results_dir` (str): Directory containing individual model result files (default: "results/orientation")
- `output_file` (str): Path to output summary JSON file (default: "orientation_test_results.json")

**Returns**: `Dict` - The compiled report, or `None` if no files found

**Process Flow**:
1. Check if results directory exists
2. Find all JSON files in the directory
3. For each JSON file:
   - Load model data
   - Extract model name
   - Extract summary statistics
   - Add to report
4. Estimate total images from summary data
5. Save compiled report to output file

**Input File Structure** (from `results/orientation/{model_name}.json`):
```json
{
  "model": "GPT-4o-mini",
  "timestamp": "2024-01-01T12:00:00",
  "summary": {
    "total_tests": 120,
    "correct_detections": 100,
    "accuracy": 0.833,
    "accuracy_by_rotation": {
      "0": {"accuracy": 1.0, "count": 30, "correct": 30},
      "90": {"accuracy": 0.9, "count": 30, "correct": 27},
      ...
    },
    "mean_processing_time": 2.5
  },
  "results": [...]
}
```

**Output File Structure**:
```json
{
  "timestamp": "2024-01-01T12:00:00",
  "models_tested": ["GPT-4o-mini", "GPT-4o", "Claude 3.5 Sonnet"],
  "summary": {
    "GPT-4o-mini": {
      "total_tests": 120,
      "correct_detections": 100,
      "accuracy": 0.833,
      "accuracy_by_rotation": {...},
      "mean_processing_time": 2.5
    },
    ...
  },
  "total_images": 30
}
```

**Total Images Calculation**:
- Estimates from `total_tests / 4` (assuming 4 rotations per image)
- Uses data from first file if available

#### `main()`

**Location**: `compile_results.py:113-120`

**Purpose**: Main entry point for standalone execution

**Process**:
1. Calls `compile_comparison_results()`
2. Calls `compile_orientation_results()`
3. Prints completion message

## Directory Structure

### Expected Structure

```
results/
├── comparison/
│   ├── gpt-4o-mini.json
│   ├── gpt-4o.json
│   ├── claude-3-5-sonnet.json
│   └── ...
└── orientation/
    ├── gpt-4o-mini.json
    ├── gpt-4o.json
    ├── claude-3-5-sonnet.json
    └── ...
```

### Output Files

- `model_comparison_report.json` - Compiled comparison results
- `orientation_test_results.json` - Compiled orientation results

## Integration with Other Modules

### Dependencies

- **`json`**: For reading/writing JSON files
- **`pathlib.Path`**: For file system operations
- **`datetime`**: For timestamp generation

### Used By

- **`generate_dashboard.py`**: Calls compilation functions before generating dashboard
- **CLI scripts**: Can be called standalone to refresh reports

### Integration Flow

```
Individual Model Results (results/comparison/, results/orientation/)
    │
    ▼
compile_results.py
    │
    ├── compile_comparison_results()
    │   └── model_comparison_report.json
    │
    └── compile_orientation_results()
        └── orientation_test_results.json
    │
    ▼
generate_dashboard.py
    │
    └── dashboard.html
```

## Usage Examples

### Standalone Execution

```bash
python compile_results.py
```

**Output**:
```
Compiling results...
Found 7 comparison result files.
Compiled comparison report saved to: model_comparison_report.json
Found 6 orientation result files.
Compiled orientation report saved to: orientation_test_results.json
Done.
```

### Programmatic Usage

```python
from compile_results import compile_comparison_results, compile_orientation_results

# Compile comparison results
comparison_report = compile_comparison_results(
    results_dir="results/comparison",
    output_file="model_comparison_report.json"
)

# Compile orientation results
orientation_report = compile_orientation_results(
    results_dir="results/orientation",
    output_file="orientation_test_results.json"
)
```

### Custom Directories

```python
# Use custom directories
compile_comparison_results(
    results_dir="custom_results/comparison",
    output_file="custom_comparison_report.json"
)

compile_orientation_results(
    results_dir="custom_results/orientation",
    output_file="custom_orientation_report.json"
)
```

## Error Handling

### Directory Not Found

- Returns `None` if directory doesn't exist
- Prints error message: `"Directory not found: {results_dir}"`

### No JSON Files

- Returns `None` if no JSON files found
- Prints error message: `"No JSON files found in {results_dir}"`

### Missing Fields

- Handles missing fields gracefully
- Calculates missing metrics from available data
- Sets defaults for missing values

## Important Notes

- **Idempotent**: Can be run multiple times safely
- **Overwrites**: Output files are overwritten on each run
- **Timestamp**: Uses current timestamp for compiled reports
- **File Discovery**: Automatically finds all JSON files in directory
- **Field Normalization**: Ensures consistent field names across models

## Best Practices

1. **Run Before Dashboard**: Always compile results before generating dashboard
2. **Regular Updates**: Recompile after adding new model results
3. **Backup**: Keep individual result files as backup
4. **Version Control**: Consider versioning compiled reports
5. **Automation**: Integrate into CI/CD or scheduled tasks

## Performance Considerations

- **File I/O**: Reads all JSON files in directory
- **Memory**: Loads all result data into memory
- **Speed**: Fast for typical result sets (< 100 models)
- **Scalability**: Performance degrades with very large result sets

