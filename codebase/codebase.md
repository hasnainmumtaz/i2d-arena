# Codebase Documentation

This directory contains comprehensive documentation for the Image Transcriber project. The project is a flexible Python application that transcribes images using various LLM (Large Language Model) providers with vision capabilities, built with LangChain for a unified interface.

## Project Overview

The Image Transcriber is designed to extract text and information from images using multiple LLM providers. It supports single image processing, batch processing, and model comparison modes.

## Documentation Structure

### Core Modules

1. **[Image Transcriber Module](image-transcriber.md)**
   - Base `ImageTranscriber` class
   - Provider-specific implementations (OpenAI, Anthropic, Google, Ollama, HuggingFace)
   - Factory function for creating transcribers
   - CLI interface with three modes: single, batch, and comparison

2. **[Batch Processing Module](batch-processing.md)**
   - `BatchProcessor` class for processing multiple images
   - `TranscriptionResult` and `BatchProcessingResult` dataclasses
   - Parallel and sequential processing support
   - Ground truth matching and loading

3. **[Evaluation Module](evaluation.md)**
   - `TranscriptionEvaluator` class
   - `EvaluationMetrics` dataclass
   - Comparison with ground truth data
   - Field-level accuracy metrics
   - Detailed reporting

4. **[Model Comparison Module](model-comparison.md)**
   - `ModelComparator` class
   - `ModelComparisonResult` dataclass
   - Side-by-side model performance comparison
   - Comprehensive comparison reports

### Architecture

- **[Architecture Overview](architecture.md)**
  - System architecture
  - Module relationships
  - Data flow
  - Design patterns used

## Key Features

- **Multi-Provider Support**: Works with OpenAI, Anthropic, Google, Ollama, and HuggingFace
- **Structured Output**: Extracts structured JSON data from invoices/receipts
- **Batch Processing**: Process multiple images with parallel execution
- **As-is Data Extraction**: Compare performance of different models for data extraction
- **Orientation Extraction Test**: Test model capabilities in detecting image orientation
- **Evaluation**: Compare transcriptions with ground truth data
- **CLI Interface**: Easy-to-use command-line interface

## File Structure

```
.
├── image_transcriber.py      # Main transcriber module
├── batch_processor.py         # Batch processing functionality
├── evaluator.py               # Evaluation and metrics
├── model_comparator.py        # As-is data extraction functionality
├── orientation_test.py        # Orientation testing functionality
├── compile_results.py         # Result compilation script
├── generate_dashboard.py      # Dashboard generation script
├── dashboard.html             # Generated results dashboard
├── requirements.txt           # Python dependencies
├── README.md                  # User documentation
└── codebase/                  # This documentation
    ├── codebase.md            # Main documentation index (this file)
    ├── image-transcriber.md   # Image transcriber module docs
    ├── batch-processing.md    # Batch processing module docs
    ├── evaluation.md          # Evaluation module docs
    ├── model-comparison.md    # As-is data extraction module docs
    └── architecture.md        # Architecture overview
```

## Usage Patterns

### Single Image Processing
```python
from image_transcriber import create_transcriber

transcriber = create_transcriber(provider="openai", model_name="gpt-4o")
result = transcriber.transcribe("image.jpg")
```

### Batch Processing
```python
from image_transcriber import create_transcriber
from batch_processor import BatchProcessor

transcriber = create_transcriber(provider="openai")
processor = BatchProcessor(transcriber, images_dir="images", ground_truth_dir="gdt")
result = processor.process_batch()
```

### Model Comparison
```python
from model_comparator import ModelComparator

comparator = ModelComparator(images_dir="images", ground_truth_dir="gdt")
comparison = comparator.compare_models(model_configs)
```

## Important Notes

- **Before making changes**: Always consult the relevant documentation files in this codebase folder
- **API Keys**: The system supports loading API keys from `.env` files or environment variables
- **Structured Output**: OpenAI transcriber supports structured JSON output for invoice/receipt extraction
- **Error Handling**: All modules include comprehensive error handling and fallback mechanisms
- **Parallel Processing**: Batch processor supports parallel execution for faster processing

## Dependencies

- `langchain-core` - Core LangChain functionality
- `langchain-openai` - OpenAI integration
- `langchain-anthropic` - Anthropic integration
- `langchain-google-genai` - Google integration
- `langchain-ollama` - Ollama integration
- `python-dotenv` - Environment variable management
- `requests` - HTTP requests (for HuggingFace)

## Contributing

When making changes to the codebase:
1. Review the relevant documentation file in this `codebase/` folder
2. Understand the module's purpose and dependencies
3. Ensure changes don't break existing functionality
4. Update documentation if adding new features

