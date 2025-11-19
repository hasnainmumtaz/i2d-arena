# Image Transcriber using LLM Models with LangChain

A flexible Python script that can transcribe images using various LLM (Large Language Model) providers with vision capabilities. Built with **LangChain** for a unified interface and easy extensibility.

## Features

- **Built with LangChain** - Uses LangChain's unified interface for consistent API across providers
- Support for multiple LLM providers:
  - **OpenAI** (GPT-4 Vision) via `langchain-openai`
  - **Anthropic** (Claude 3.5 Sonnet) via `langchain-anthropic`
  - **Google** (Gemini Pro Vision) via `langchain-google-genai`
  - **Ollama** (Local models like LLaVA) via `langchain-ollama`
  - **Hugging Face** (Various vision-language models)

- Supports both local image files and image URLs
- Customizable prompts for transcription
- Easy to extend with new providers using LangChain's modular architecture

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

This will install:
- `langchain-core` - Core LangChain functionality
- `langchain-openai` - OpenAI integration
- `langchain-anthropic` - Anthropic integration
- `langchain-google-genai` - Google integration
- `langchain-ollama` - Ollama integration
- `requests` - For HTTP requests (used by HuggingFace)
- `python-dotenv` - For loading API keys from .env file

2. Set up API keys (choose based on your provider):

**Option 1: Using .env file (Recommended)**
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API keys
# OPENAI_API_KEY=your_openai_api_key_here
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
# GOOGLE_API_KEY=your_google_api_key_here
# HUGGINGFACE_API_KEY=your_huggingface_api_key_here
```

**Option 2: Using environment variables**
```bash
# For OpenAI
export OPENAI_API_KEY="your-api-key"

# For Anthropic
export ANTHROPIC_API_KEY="your-api-key"

# For Google
export GOOGLE_API_KEY="your-api-key"

# For Hugging Face (optional)
export HUGGINGFACE_API_KEY="your-api-key"
```

**Note:** The `.env` file takes precedence if both `.env` and environment variables are set. Make sure to add `.env` to your `.gitignore` to keep your keys secure!

3. For Ollama (local models):
   - Install Ollama from https://ollama.ai
   - Pull a vision model: `ollama pull llava`

## Usage

### Single Image Mode

```bash
# Using OpenAI (default)
python image_transcriber.py path/to/image.jpg

# Using Anthropic Claude
python image_transcriber.py path/to/image.jpg --provider anthropic

# Using Google Gemini
python image_transcriber.py path/to/image.jpg --provider google

# Using Ollama (local)
python image_transcriber.py path/to/image.jpg --provider ollama --model llava

# Using Hugging Face
python image_transcriber.py path/to/image.jpg --provider huggingface --model Salesforce/blip-image-captioning-base

# With custom prompt
python image_transcriber.py path/to/image.jpg --prompt "What text is visible in this image?"

# With image URL
python image_transcriber.py https://example.com/image.jpg --provider openai
```

### Batch Processing Mode

Process all images in a directory and compare with ground truth:

```bash
# Basic batch processing
python image_transcriber.py --batch --images-dir images --ground-truth-dir gdt --provider openai

# With custom output file
python image_transcriber.py --batch --images-dir images --ground-truth-dir gdt --output results.json --provider anthropic

# Process only first 10 images (for testing)
python image_transcriber.py --batch --images-dir images --ground-truth-dir gdt --max-images 10 --provider openai

# Without ground truth comparison
python image_transcriber.py --batch --images-dir images --provider openai
```

**Batch Processing Features:**
- Processes all images in the specified directory
- Automatically matches images with ground truth files (same filename, different extension)
- Saves results to JSON file
- Generates evaluation report comparing transcriptions with ground truth
- Shows progress and statistics

**Output Files:**
- `batch_results.json` - Contains all transcriptions and metadata
- `batch_results_report.json` - Detailed evaluation report with metrics

### Model Comparison Mode

Compare the performance of multiple models on the same set of images:

```bash
# Compare default models (GPT-4o-mini vs GPT-4o)
python image_transcriber.py --compare --images-dir images --ground-truth-dir gdt

# Compare custom models
python image_transcriber.py --compare --images-dir images --ground-truth-dir gdt \
  --models "GPT-4o-mini:openai:gpt-4o-mini" "GPT-4o:openai:gpt-4o"

# Compare models from different providers
python image_transcriber.py --compare --images-dir images --ground-truth-dir gdt \
  --models "GPT-4o:openai:gpt-4o" "Claude:anthropic:claude-3-5-sonnet-20241022" "Gemini:google:gemini-pro-vision"

# Test on first 5 images only
python image_transcriber.py --compare --images-dir images --ground-truth-dir gdt --max-images 5

# Custom output location
python image_transcriber.py --compare --images-dir images --ground-truth-dir gdt \
  --output comparison_report.json --output-dir comparison_results/
```

**Model Comparison Features:**
- Processes the same images with multiple models
- Compares success rates, processing times, and accuracy
- Generates side-by-side comparison reports
- Saves individual model results for detailed analysis
- Identifies best performing models for different metrics

**Comparison Output Files:**
- `model_comparison_report.json` - Detailed comparison with per-image and per-model metrics
- `results_<model_name>.json` - Individual results for each model
- `comparison_results/` - Directory with organized results (if --output-dir specified)

### Python API

#### Single Image

```python
from image_transcriber import OpenAITranscriber, AnthropicTranscriber, GoogleTranscriber, OllamaTranscriber

# OpenAI (using LangChain ChatOpenAI)
transcriber = OpenAITranscriber(model_name="gpt-4o")
result = transcriber.transcribe("image.jpg")
print(result)

# Anthropic (using LangChain ChatAnthropic)
transcriber = AnthropicTranscriber(model_name="claude-3-5-sonnet-20241022")
result = transcriber.transcribe("image.jpg", prompt="Describe this image in detail")

# Google (using LangChain ChatGoogleGenerativeAI)
transcriber = GoogleTranscriber(model_name="gemini-pro-vision")
result = transcriber.transcribe("https://example.com/image.jpg")

# Ollama (local, using LangChain ChatOllama)
transcriber = OllamaTranscriber(model_name="llava")
result = transcriber.transcribe("image.jpg")

# With custom parameters
transcriber = OpenAITranscriber(
    model_name="gpt-4o",
    api_key="your-key",
    max_tokens=2000,
    temperature=0.5
)
```

#### Batch Processing

```python
from image_transcriber import create_transcriber
from batch_processor import BatchProcessor
from evaluator import TranscriptionEvaluator

# Create transcriber
transcriber = create_transcriber(provider="openai", model_name="gpt-4o")

# Initialize batch processor
processor = BatchProcessor(
    transcriber=transcriber,
    images_dir="images",
    ground_truth_dir="gdt"
)

# Process all images
batch_result = processor.process_batch(
    prompt="Extract all text from this image.",
    max_images=None  # Process all, or specify a number
)

# Save results
processor.save_results(batch_result, "results.json")

# Evaluate results
evaluator = TranscriptionEvaluator()
metrics = evaluator.calculate_metrics(batch_result)
evaluator.print_summary(batch_result, metrics)
evaluator.save_detailed_report(batch_result, metrics, "report.json")
```

#### Model Comparison

```python
from model_comparator import ModelComparator

# Define models to compare
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
    },
    {
        'name': 'Claude 3.5 Sonnet',
        'provider': 'anthropic',
        'model_name': 'claude-3-5-sonnet-20241022'
    }
]

# Initialize comparator
comparator = ModelComparator(
    images_dir="images",
    ground_truth_dir="gdt"
)

# Run comparison
comparison_result = comparator.compare_models(
    model_configs=model_configs,
    prompt="Extract all text from this image.",
    max_images=None  # Process all images
)

# Print summary
comparator.print_comparison_summary(comparison_result)

# Generate detailed report
comparator.generate_comparison_report(
    comparison_result,
    output_path="comparison_report.json"
)

# Save individual results
comparator.save_comparison_results(
    comparison_result,
    output_dir="comparison_results"
)
```

## Supported Image Formats

- JPEG/JPG
- PNG
- WebP
- Other formats supported by PIL/Pillow

## Examples

### Basic Transcription
```bash
python image_transcriber.py photo.jpg
```

### Extract Text from Image
```bash
python image_transcriber.py document.jpg --prompt "Extract all text from this image exactly as it appears"
```

### Detailed Description
```bash
python image_transcriber.py scene.jpg --prompt "Provide a detailed description of this scene, including all objects, people, and their positions"
```

## Notes

- **LangChain Benefits**: Using LangChain provides a unified interface, making it easy to switch between providers and extend functionality
- **API Costs**: Using cloud providers (OpenAI, Anthropic, Google) will incur API costs
- **Ollama**: Free and runs locally, but requires installation and model download
- **Hugging Face**: Some models are free, but may have rate limits. Note: HuggingFace uses direct API calls as LangChain's HuggingFace integration for vision models is limited
- **Image Size**: Very large images may need to be resized before processing
- **Model Parameters**: You can pass additional parameters (like `temperature`, `max_tokens`) via kwargs when initializing transcribers

## Troubleshooting

1. **Import Errors**: Make sure all required packages are installed: `pip install -r requirements.txt`
2. **API Key Errors**: 
   - Verify your API key is set correctly in `.env` file or environment variables
   - Check that `.env` file exists and contains the correct keys
   - Ensure `.env` file is in the same directory as the script
3. **Ollama Connection**: Ensure Ollama is running: `ollama serve`
4. **Image Loading**: Check that the image path is correct and the file exists
5. **.env file not loading**: Make sure `python-dotenv` is installed: `pip install python-dotenv`

## License

MIT License - feel free to use and modify as needed.

