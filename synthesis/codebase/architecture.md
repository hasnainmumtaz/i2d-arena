# Architecture Overview

## System Architecture

The Image Transcriber application follows a modular architecture with clear separation of concerns. Each module handles a specific aspect of the image transcription workflow.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI Interface                          │
│              (image_transcriber.py main())                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Image Transcriber Module                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   OpenAI     │  │  Anthropic   │  │    Google    │      │
│  │ Transcriber  │  │ Transcriber  │  │ Transcriber  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │   Ollama     │  │ HuggingFace  │                        │
│  │ Transcriber  │  │ Transcriber  │                        │
│  └──────────────┘  └──────────────┘                        │
│                                                             │
│  Base Class: ImageTranscriber                              │
│  Factory: create_transcriber()                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│            Batch Processing Module                          │
│  ┌────────────────────────────────────────────────────┐   │
│  │            BatchProcessor                            │   │
│  │  - find_image_files()                                │   │
│  │  - load_ground_truth()                               │   │
│  │  - process_single_image()                            │   │
│  │  - process_batch()                                   │   │
│  │  - save_results()                                    │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  Data Classes:                                            │
│  - TranscriptionResult                                       │
│  - BatchProcessingResult                                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│            Evaluation Module                                │
│  ┌────────────────────────────────────────────────────┐   │
│  │        TranscriptionEvaluator                       │   │
│  │  - calculate_metrics()                              │   │
│  │  - compare_with_ground_truth()                      │   │
│  │  - calculate_detailed_metrics()                      │   │
│  │  - save_detailed_report()                           │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  Data Classes:                                              │
│  - EvaluationMetrics                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│          Model Comparison Module                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │            ModelComparator                          │   │
│  │  - compare_models()                                │   │
│  │  - generate_comparison_report()                     │   │
│  │  - print_comparison_summary()                       │   │
│  │  - save_comparison_results()                       │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  Data Classes:                                              │
│  - ModelComparisonResult                                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│          Orientation Test Module                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │            OrientationTester                        │   │
│  │  - rotate_image()                                   │   │
│  │  - parse_orientation_response()                     │   │
│  │  - test_single_orientation()                        │   │
│  │  - test_batch()                                     │   │
│  │  - save_results()                                  │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  Data Classes:                                              │
│  - OrientationTestResult                                    │
│  - OrientationTestSummary                                   │
│  - OrientationTestReport                                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│          Result Compilation Module                          │
│  ┌────────────────────────────────────────────────────┐   │
│  │  - compile_comparison_results()                     │   │
│  │  - compile_orientation_results()                     │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  Output:                                                    │
│  - model_comparison_report.json                             │
│  - orientation_test_results.json                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│          Dashboard Generation Module                        │
│  ┌────────────────────────────────────────────────────┐   │
│  │  - load_json()                                      │   │
│  │  - generate_html()                                  │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  Output:                                                    │
│  - dashboard.html (Interactive HTML dashboard)              │
└─────────────────────────────────────────────────────────────┘
```

## Module Relationships

### Dependency Graph

```
image_transcriber.py
  ├── batch_processor.py
  │     └── evaluator.py
  │           └── batch_processor.py (circular import)
  └── model_comparator.py
        ├── batch_processor.py
        ├── evaluator.py
        └── image_transcriber.py

orientation_test.py
  └── image_transcriber.py

compile_results.py
  └── (standalone, reads JSON files)

generate_dashboard.py
  └── compile_results.py (optional)
```

### Import Structure

- **image_transcriber.py**: 
  - Imports: `batch_processor`, `model_comparator`, `evaluator`
  - Exports: Transcriber classes, factory function, CLI

- **batch_processor.py**:
  - Imports: None (uses transcriber instances passed in)
  - Exports: `BatchProcessor`, data classes

- **evaluator.py**:
  - Imports: `batch_processor` (for data classes)
  - Exports: `TranscriptionEvaluator`, `EvaluationMetrics`

- **model_comparator.py**:
  - Imports: `batch_processor`, `evaluator`, `image_transcriber`
  - Exports: `ModelComparator`, `ModelComparisonResult`

- **orientation_test.py**:
  - Imports: `image_transcriber` (for `create_transcriber`)
  - Exports: `OrientationTester`, data classes

- **compile_results.py**:
  - Imports: None (standalone script)
  - Exports: Compilation functions

- **generate_dashboard.py**:
  - Imports: `compile_results` (optional)
  - Exports: Dashboard generation functions

## Data Flow

### Single Image Processing Flow

```
User Input (image path)
    │
    ▼
CLI (process_single_mode)
    │
    ▼
create_transcriber()
    │
    ▼
Transcriber.transcribe()
    │
    ├── Load/Encode Image
    ├── Create LangChain Message
    ├── Invoke Model
    └── Return Result
    │
    ▼
Print Result
```

### Batch Processing Flow

```
User Input (--batch flag)
    │
    ▼
CLI (process_batch_mode)
    │
    ├── create_transcriber()
    └── BatchProcessor()
        │
        ├── find_image_files()
        ├── For each image:
        │   ├── load_ground_truth()
        │   ├── process_single_image()
        │   │   └── transcriber.transcribe()
        │   └── Create TranscriptionResult
        │
        ├── Aggregate Results
        └── save_results()
            │
            ▼
        TranscriptionEvaluator (if ground truth)
            ├── calculate_metrics()
            ├── compare_with_ground_truth()
            ├── calculate_detailed_metrics()
            └── save_detailed_report()
```

### Model Comparison Flow

```
User Input (--compare flag)
    │
    ▼
CLI (process_comparison_mode)
    │
    ▼
ModelComparator()
    │
    ├── For each model:
    │   ├── create_transcriber()
    │   ├── BatchProcessor()
    │   │   └── Process all images
    │   └── Store BatchProcessingResult
    │
    ├── generate_comparison_report()
    │   ├── Calculate metrics per model
    │   ├── Per-image comparison
    │   └── Accuracy comparison
    │
    ├── print_comparison_summary()
    └── save_comparison_results()
```

### Orientation Test Flow

```
User Input (orientation test)
    │
    ▼
OrientationTester.test_batch()
    │
    ├── Find image files
    ├── For each model:
    │   ├── create_transcriber()
    │   ├── For each image:
    │   │   ├── For each rotation (0°, 90°, 180°, 270°):
    │   │   │   ├── rotate_image() (in memory)
    │   │   │   ├── Encode to base64
    │   │   │   ├── transcriber.transcribe()
    │   │   │   ├── parse_orientation_response()
    │   │   │   └── Record result
    │   │   └── (Optional: replications)
    │   └── Collect results
    │
    ├── Calculate summary statistics
    ├── Calculate overall statistics
    ├── print_summary()
    └── save_results()
        │
        ├── Save summary: orientation_test_results.json
        └── Save individual: results/orientation/{model}.json
```

### Result Compilation Flow

```
Individual Results (results/comparison/, results/orientation/)
    │
    ▼
compile_results.py
    │
    ├── compile_comparison_results()
    │   ├── Read all JSON files from results/comparison/
    │   ├── Extract metrics per model
    │   ├── Normalize fields
    │   └── Save: model_comparison_report.json
    │
    └── compile_orientation_results()
        ├── Read all JSON files from results/orientation/
        ├── Extract summary per model
        └── Save: orientation_test_results.json
```

### Dashboard Generation Flow

```
Compiled Results (JSON files)
    │
    ▼
generate_dashboard.py
    │
    ├── (Optional) compile_results.py
    │   └── Refresh JSON files
    │
    ├── load_json('model_comparison_report.json')
    ├── load_json('orientation_test_results.json')
    │
    ├── generate_html()
    │   ├── Process comparison data
    │   ├── Process orientation data
    │   ├── Generate HTML structure
    │   ├── Generate Chart.js configurations
    │   └── Embed Bootstrap UI
    │
    └── Save: dashboard.html
```

## Design Patterns

### 1. Factory Pattern

**Location**: `create_transcriber()` in `image_transcriber.py`

**Purpose**: Create appropriate transcriber instance based on provider name

**Benefits**:
- Encapsulates creation logic
- Easy to add new providers
- Consistent interface

### 2. Template Method Pattern

**Location**: `ImageTranscriber` base class

**Purpose**: Define common structure, let subclasses implement specifics

**Structure**:
- Base class defines `transcribe()` template
- Subclasses implement `_init_model()`
- Some subclasses override `transcribe()` for special handling

### 3. Strategy Pattern

**Location**: Provider-specific transcriber classes

**Purpose**: Different strategies (providers) for same operation

**Benefits**:
- Interchangeable providers
- Easy to add new strategies
- Consistent interface

### 4. Data Class Pattern

**Location**: All modules use `@dataclass`

**Purpose**: Structured data containers

**Classes**:
- `TranscriptionResult`
- `BatchProcessingResult`
- `EvaluationMetrics`
- `ModelComparisonResult`
- `OrientationTestResult`
- `OrientationTestSummary`
- `OrientationTestReport`

## Component Responsibilities

### Image Transcriber Module

**Responsibilities**:
- Provider abstraction
- Image encoding/loading
- LangChain integration
- Structured output handling
- CLI interface

**Key Design Decisions**:
- Base class for common interface
- Provider-specific implementations
- Factory function for creation
- Support for both structured and unstructured output

### Batch Processor Module

**Responsibilities**:
- Image discovery
- Ground truth matching
- Parallel/sequential processing
- Result aggregation
- Result serialization

**Key Design Decisions**:
- Stateless processor (transcriber passed in)
- Parallel processing with thread pool
- Automatic ground truth matching
- Flexible result storage

### Evaluation Module

**Responsibilities**:
- Metrics calculation
- Ground truth comparison
- Accuracy scoring
- Report generation

**Key Design Decisions**:
- Field-level accuracy metrics
- Intelligent matching (exact/partial/none)
- Detailed reporting
- Stateless evaluator

### Model Comparison Module

**Responsibilities**:
- Multi-model processing
- Side-by-side comparison
- Report generation
- Summary statistics

**Key Design Decisions**:
- Processes same images with all models
- Comprehensive comparison reports
- Per-image and per-model metrics
- Best performer identification

### Orientation Test Module

**Responsibilities**:
- Image rotation in memory
- Orientation detection testing
- Multi-model orientation evaluation
- Rotation-specific accuracy analysis

**Key Design Decisions**:
- In-memory rotation (no disk writes)
- Parallel processing support
- Robust response parsing
- Comprehensive statistics

### Result Compilation Module

**Responsibilities**:
- Consolidate individual results
- Field normalization
- Summary report generation
- Data aggregation

**Key Design Decisions**:
- Standalone script (no dependencies)
- Handles missing fields gracefully
- Idempotent operations
- Flexible directory structure

### Dashboard Generation Module

**Responsibilities**:
- HTML dashboard generation
- Data visualization
- Interactive charts
- Result presentation

**Key Design Decisions**:
- Bootstrap-based UI
- Chart.js for visualizations
- Self-contained HTML output
- Optional result compilation

## Error Handling Strategy

### Levels of Error Handling

1. **Provider Level**:
   - API errors caught and reported
   - Model validation errors
   - Import errors with helpful messages

2. **Processing Level**:
   - Individual image failures don't stop batch
   - Errors captured in `TranscriptionResult.error`
   - Graceful degradation

3. **Evaluation Level**:
   - JSON parsing errors handled
   - Missing fields treated as no match
   - Comparison errors logged

4. **Comparison Level**:
   - Model failures don't stop comparison
   - Partial results included in report
   - Error statistics in summary

## Extension Points

### Adding a New Provider

1. Create new class inheriting from `ImageTranscriber`
2. Implement `_init_model()` method
3. Optionally override `transcribe()` if needed
4. Add to `create_transcriber()` factory
5. Add to CLI argument choices

### Adding New Metrics

1. Extend `EvaluationMetrics` dataclass
2. Update `calculate_metrics()` method
3. Update report generation
4. Update summary printing

### Adding New Comparison Features

1. Extend `ModelComparisonResult` if needed
2. Add new comparison logic to `ModelComparator`
3. Update report structure
4. Update summary printing

## Performance Considerations

### Parallel Processing

- **Batch Processing**: Uses `ThreadPoolExecutor` for parallel image processing
- **Model Comparison**: Models processed sequentially (to avoid API rate limits)
- **Worker Count**: Configurable `max_workers` parameter

### Memory Management

- **Results Storage**: All results kept in memory during processing
- **Large Batches**: Consider processing in chunks for very large batches
- **Image Encoding**: Base64 encoding increases memory usage

### API Rate Limits

- **Sequential Mode**: Use for strict rate limits
- **Worker Count**: Adjust based on provider limits
- **Error Recovery**: Handles rate limit errors gracefully

## Security Considerations

### API Key Management

- **Environment Variables**: Preferred method
- **`.env` File**: Local development
- **Override Priority**: `.env` > environment variables
- **Never Commit**: `.env` in `.gitignore`

### Input Validation

- **Image Paths**: Validated before processing
- **URLs**: Validated for HTTP/HTTPS
- **File Existence**: Checked before reading

## Testing Considerations

### Unit Testing

- Each module can be tested independently
- Mock transcriber for batch processor tests
- Mock results for evaluator tests

### Integration Testing

- Test full workflows
- Test with real images (small set)
- Test error scenarios

### Test Data

- Use small image sets for testing
- Ground truth files for validation
- Error cases for edge testing

## Future Enhancements

### Potential Additions

1. **Caching**: Cache transcriptions to avoid reprocessing
2. **Database Storage**: Store results in database
3. **Web Interface**: REST API or web UI
4. **Streaming**: Process images as they arrive
5. **Advanced Metrics**: More sophisticated accuracy metrics
6. **Model Fine-tuning**: Support for fine-tuned models
7. **Multi-image Support**: Process multiple images in one request

