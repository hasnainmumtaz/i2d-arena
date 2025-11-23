# Image Transcriber Module

## Overview

The `image_transcriber.py` module is the core of the Image Transcriber application. It provides a unified interface for transcribing images using various LLM providers with vision capabilities, built on top of LangChain.

## Architecture

### Base Class: `ImageTranscriber`

The base class defines the common interface for all transcriber implementations.

**Location**: `image_transcriber.py:22-74`

**Key Methods**:
- `__init__(model_name, api_key, **kwargs)`: Initialize transcriber with model configuration
- `_init_model()`: Abstract method to be implemented by subclasses
- `transcribe(image_path, prompt)`: Transcribe an image using the configured model

**Key Features**:
- Supports both local image files and image URLs
- Handles base64 encoding for local images
- Determines MIME type automatically (JPEG, PNG, WebP, GIF)
- Uses LangChain's `HumanMessage` for consistent message format

### Provider Implementations

#### 1. `OpenAITranscriber`

**Location**: `image_transcriber.py:77-296`

**Features**:
- Supports structured JSON output for invoice/receipt extraction
- Uses OpenAI's structured output API when `structured=True`
- Falls back to regular LangChain if structured output fails
- Validates vision model support
- Default model: `gpt-4o`

**Vision Models Supported**:
- `gpt-4o`, `gpt-4o-mini`
- `gpt-4-turbo`, `gpt-4-vision-preview`
- `gpt-4`, `gpt-4-turbo-preview`

**Special Methods**:
- `_supports_vision()`: Checks if model supports vision inputs
- `transcribe(image_path, prompt, structured)`: Enhanced transcription with structured output support

**Structured Output Schema**:
```json
{
    "company": "Company name",
    "date": "Date in DD/MM/YYYY format",
    "address": "Full address",
    "total": "Total amount"
}
```

#### 2. `AnthropicTranscriber`

**Location**: `image_transcriber.py:299-324`

**Features**:
- Uses LangChain's `ChatAnthropic`
- Default model: `claude-3-5-sonnet-20241022`
- Supports custom API keys and model parameters

#### 3. `GoogleTranscriber`

**Location**: `image_transcriber.py:327-347`

**Features**:
- Uses LangChain's `ChatGoogleGenerativeAI`
- Default model: `gemini-pro-vision`
- Uses `google_api_key` parameter name

#### 4. `OllamaTranscriber`

**Location**: `image_transcriber.py:350-410`

**Features**:
- Runs locally, no API key required
- Default model: `llava`
- Default base URL: `http://localhost:11434`
- Handles base64 encoding for local files
- Has fallback mechanism for different Ollama message formats

**Special Handling**:
- Downloads and encodes images from URLs
- Tries multiple message formats if first attempt fails

#### 5. `HuggingFaceTranscriber`

**Location**: `image_transcriber.py:413-456`

**Features**:
- Uses direct HuggingFace API calls (not LangChain chat interface)
- Default model: `Salesforce/blip-image-captioning-base`
- Supports optional API key for private models
- Handles both local files and URLs

**API Endpoint**: `https://api-inference.huggingface.co/models/{model_name}`

### Factory Function

**Function**: `create_transcriber(provider, model_name, api_key, **kwargs)`

**Location**: `image_transcriber.py:459-487`

**Purpose**: Creates appropriate transcriber instance based on provider name

**Supported Providers**:
- `"openai"` → `OpenAITranscriber`
- `"anthropic"` → `AnthropicTranscriber`
- `"google"` → `GoogleTranscriber`
- `"ollama"` → `OllamaTranscriber`
- `"huggingface"` → `HuggingFaceTranscriber`

### CLI Interface

**Function**: `main()`

**Location**: `image_transcriber.py:622-691`

**Modes**:
1. **Single Image Mode**: Process one image
   - Argument: `image` (positional)
   - Options: `--provider`, `--model`, `--prompt`, `--api-key`

2. **Batch Mode**: Process multiple images
   - Flag: `--batch`
   - Options: `--images-dir`, `--ground-truth-dir`, `--output`, `--max-images`, `--report`

3. **As-is Data Extraction Mode**: Compare multiple models for data extraction
   - Flag: `--compare`
   - Options: `--models`, `--images-dir`, `--ground-truth-dir`, `--output`, `--output-dir`

4. **Orientation Extraction Test Mode**: Test orientation detection capabilities
   - Flag: `--orientation-test`
   - Options: `--models`, `--images-dir`, `--output-dir`

**Mode Handlers**:
- `process_single_mode(args)`: Handles single image processing
- `process_batch_mode(args)`: Handles batch processing (delegates to `BatchProcessor`)
- `process_comparison_mode(args)`: Handles as-is data extraction (delegates to `ModelComparator`)
- `process_orientation_test_mode(args)`: Handles orientation testing (delegates to `OrientationTest`)

## Environment Variables

The module loads API keys from environment variables or `.env` file:

- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key
- `GOOGLE_API_KEY`: Google API key
- `HUGGINGFACE_API_KEY`: HuggingFace API key (optional)

**Loading Priority**: `.env` file values override system environment variables (using `load_dotenv(override=True)`)

## Image Handling

### Supported Formats
- JPEG/JPG
- PNG
- WebP
- GIF

### Image Processing Flow

1. **Local Files**:
   - Read file as binary
   - Encode to base64
   - Determine MIME type from extension
   - Create data URL: `data:{mime_type};base64,{base64_data}`

2. **URLs**:
   - Use URL directly (for OpenAI, Anthropic, Google)
   - Download and encode (for Ollama, HuggingFace)

## Error Handling

- **Import Errors**: Raises `ImportError` with installation instructions
- **API Errors**: Catches and reports model-specific errors
- **Vision Model Errors**: Validates model support and provides helpful error messages
- **JSON Parsing**: Falls back gracefully if structured output parsing fails

## Dependencies

- `langchain-core`: Core LangChain functionality
- `langchain-openai`: OpenAI integration
- `langchain-anthropic`: Anthropic integration
- `langchain-google-genai`: Google integration
- `langchain-ollama`: Ollama integration
- `python-dotenv`: Environment variable loading
- `openai`: Direct OpenAI client (for structured output)
- `requests`: HTTP requests (for HuggingFace)

## Usage Examples

### Basic Usage
```python
from image_transcriber import OpenAITranscriber

transcriber = OpenAITranscriber(model_name="gpt-4o")
result = transcriber.transcribe("image.jpg")
```

### Structured Output
```python
from image_transcriber import OpenAITranscriber

transcriber = OpenAITranscriber(model_name="gpt-4o")
result = transcriber.transcribe("invoice.jpg", structured=True)
# Returns: {"company": "...", "date": "...", "address": "...", "total": "..."}
```

### Using Factory Function
```python
from image_transcriber import create_transcriber

transcriber = create_transcriber(
    provider="anthropic",
    model_name="claude-3-5-sonnet-20241022",
    temperature=0.5
)
result = transcriber.transcribe("image.jpg", prompt="Describe this image")
```

## Important Notes

- **Structured Output**: Only `OpenAITranscriber` supports structured JSON output
- **Model Parameters**: Not all models support all parameters (e.g., `max_tokens`, `temperature`)
- **API Keys**: Can be provided via constructor, environment variable, or `.env` file
- **URL Support**: All providers support image URLs, but processing may differ
- **Error Recovery**: OpenAI transcriber has fallback mechanisms for structured output failures

## Extension Points

To add a new provider:

1. Create a new class inheriting from `ImageTranscriber`
2. Implement `_init_model()` method
3. Optionally override `transcribe()` if special handling is needed
4. Add provider to `create_transcriber()` factory function
5. Add provider to CLI argument choices

