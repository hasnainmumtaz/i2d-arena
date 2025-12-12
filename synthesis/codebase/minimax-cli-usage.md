# MiniMax CLI Usage Guide

This guide shows how to use the MiniMax transcriber via the command-line interface.

## Prerequisites

1. **Set Environment Variables** (recommended):
   ```bash
   # For international users
   export MINIMAX_API_KEY=your_api_key_here
   export MINIMAX_BASE_URL=https://api.minimax.io/v1
   
   # For users in China
   export MINIMAX_API_KEY=your_api_key_here
   export MINIMAX_BASE_URL=https://api.minimaxi.com/v1
   ```

   Or create a `.env` file:
   ```bash
   MINIMAX_API_KEY=your_api_key_here
   MINIMAX_BASE_URL=https://api.minimax.io/v1
   ```

2. **Note**: If `MINIMAX_API_KEY` is not set, it will fall back to `OPENAI_API_KEY` (since MiniMax uses OpenAI-compatible API)

## CLI Usage Examples

### 1. Single Image Mode

Process a single image with MiniMax:

```bash
# Basic usage (uses default model: MiniMax-M2)
python image_transcriber.py image.jpg --provider minimax

# Specify model explicitly
python image_transcriber.py image.jpg --provider minimax --model MiniMax-M2

# Use MiniMax-M2-Stable
python image_transcriber.py image.jpg --provider minimax --model MiniMax-M2-Stable

# With custom prompt
python image_transcriber.py image.jpg --provider minimax --prompt "Extract all text from this image"

# With API key (if not set in environment)
python image_transcriber.py image.jpg --provider minimax --api-key your_api_key_here

# With image URL
python image_transcriber.py https://example.com/image.jpg --provider minimax
```

### 2. Batch Processing Mode

Process multiple images from a directory:

```bash
# Basic batch processing
python image_transcriber.py --batch --images-dir images --provider minimax

# With ground truth comparison
python image_transcriber.py --batch --images-dir images --ground-truth-dir gdt --provider minimax

# Specify model
python image_transcriber.py --batch --images-dir images --ground-truth-dir gdt --provider minimax --model MiniMax-M2-Stable

# Limit number of images (for testing)
python image_transcriber.py --batch --images-dir images --ground-truth-dir gdt --provider minimax --max-images 10

# Custom output file
python image_transcriber.py --batch --images-dir images --ground-truth-dir gdt --provider minimax --output minimax_results.json
```

### 3. Model Comparison Mode

Compare MiniMax with other models:

```bash
# Compare MiniMax-M2 with other models
python image_transcriber.py --compare --images-dir images --ground-truth-dir gdt \
  --models "MiniMax-M2:minimax:MiniMax-M2" "GPT-4o:openai:gpt-4o" "Claude:anthropic:claude-3-5-sonnet-20241022"

# Compare both MiniMax models
python image_transcriber.py --compare --images-dir images --ground-truth-dir gdt \
  --models "MiniMax-M2:minimax:MiniMax-M2" "MiniMax-M2-Stable:minimax:MiniMax-M2-Stable"

# Custom output directory
python image_transcriber.py --compare --images-dir images --ground-truth-dir gdt \
  --models "MiniMax-M2:minimax:MiniMax-M2" "GPT-4o:openai:gpt-4o" \
  --output-dir results/minimax_comparison
```

**Model specification format**: `name:provider:model_name`
- `name`: Display name for the model (can be anything)
- `provider`: Must be `minimax` for MiniMax models
- `model_name`: `MiniMax-M2` or `MiniMax-M2-Stable`

### 4. Orientation Extraction Test Mode

Test orientation detection capabilities:

```bash
# Single MiniMax model
python image_transcriber.py --orientation-test --images-dir images \
  --models "MiniMax-M2:minimax:MiniMax-M2"

# Multiple replications (for consistency testing)
python image_transcriber.py --orientation-test --images-dir images \
  --models "MiniMax-M2:minimax:MiniMax-M2" --replications 3

# Compare multiple models including MiniMax
python image_transcriber.py --orientation-test --images-dir images \
  --models "MiniMax-M2:minimax:MiniMax-M2" "GPT-4o:openai:gpt-4o" "Claude:anthropic:claude-3-5-sonnet-20241022"

# Custom output directory
python image_transcriber.py --orientation-test --images-dir images \
  --models "MiniMax-M2:minimax:MiniMax-M2" --output-dir results/orientation
```

### 5. Rotated Extraction Test Mode

Test data extraction accuracy on rotated images:

```bash
# Single MiniMax model
python image_transcriber.py --rotated-extraction-test --images-dir images --ground-truth-dir gdt \
  --models "MiniMax-M2:minimax:MiniMax-M2"

# Compare MiniMax with other models
python image_transcriber.py --rotated-extraction-test --images-dir images --ground-truth-dir gdt \
  --models "MiniMax-M2:minimax:MiniMax-M2" "MiniMax-M2-Stable:minimax:MiniMax-M2-Stable" "GPT-4o:openai:gpt-4o"
```

## Advanced Configuration

### Using Environment Variables for Base URL

The base URL can be configured via environment variables:

```bash
# International users (default)
export MINIMAX_BASE_URL=https://api.minimax.io/v1

# China users
export MINIMAX_BASE_URL=https://api.minimaxi.com/v1

# Then run commands normally
python image_transcriber.py image.jpg --provider minimax
```

### Supported Models

- `MiniMax-M2`: Agentic capabilities, Advanced reasoning
- `MiniMax-M2-Stable`: High concurrency and commercial use

### Important Notes

1. **Temperature**: MiniMax temperature range is (0.0, 1.0], default is 1.0 (recommended)
2. **API Compatibility**: MiniMax uses OpenAI-compatible API, so you can use `OPENAI_API_KEY` if `MINIMAX_API_KEY` is not set
3. **Vision Support**: Image inputs may have limited support - check MiniMax documentation for current capabilities
4. **Reasoning Split**: The `reasoning_split` parameter is not currently exposed via CLI but can be enabled programmatically

## Troubleshooting

### API Key Issues
```bash
# Check if API key is set
echo $MINIMAX_API_KEY

# Or use --api-key flag
python image_transcriber.py image.jpg --provider minimax --api-key your_key
```

### Base URL Issues
```bash
# Check current base URL
echo $MINIMAX_BASE_URL

# Set it explicitly
export MINIMAX_BASE_URL=https://api.minimax.io/v1
```

### Model Not Found
Make sure you're using the exact model name:
- ✅ `MiniMax-M2`
- ✅ `MiniMax-M2-Stable`
- ❌ `minimax-m2` (wrong case)
- ❌ `MiniMax-M2-Pro` (doesn't exist)

## Getting Help

View all available options:
```bash
python image_transcriber.py --help
```

View examples in the help text:
```bash
python image_transcriber.py --help | grep -A 20 "Examples:"
```


