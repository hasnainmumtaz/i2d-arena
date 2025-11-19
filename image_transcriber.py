"""
Image Transcriber using LLM Models with LangChain
Supports multiple LLM providers for image transcription/description
"""

import os
from typing import Optional, Union, Dict
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # override=True ensures .env file values take precedence over system environment variables
    # This allows local .env file to override system-wide environment variables
    load_dotenv(override=True)
except ImportError:
    # python-dotenv not installed, skip loading .env file
    import warnings
    warnings.warn("python-dotenv not installed. Install it with 'pip install python-dotenv' to use .env files.")


class ImageTranscriber:
    """Base class for image transcription using LangChain"""
    
    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None, **kwargs):
        self.model_name = model_name
        self.api_key = api_key
        self.kwargs = kwargs
        self._init_model()
    
    def _init_model(self):
        """Initialize the LangChain model - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement _init_model method")
    
    def transcribe(self, image_path: Union[str, Path], prompt: str = "Transcribe or describe everything you see in this image in detail.") -> str:
        """Transcribe image using LangChain"""
        import base64
        from langchain_core.messages import HumanMessage
        
        # Load and encode image
        image_path_str = str(image_path)
        if image_path_str.startswith(('http://', 'https://')):
            # For URLs, use directly
            image_url = image_path_str
            image_content = {"type": "image_url", "image_url": image_url}
        else:
            # For local files, encode as base64
            with open(image_path_str, 'rb') as f:
                image_data = f.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Determine MIME type
            mime_type = "image/jpeg"
            if image_path_str.lower().endswith('.png'):
                mime_type = "image/png"
            elif image_path_str.lower().endswith('.webp'):
                mime_type = "image/webp"
            elif image_path_str.lower().endswith('.gif'):
                mime_type = "image/gif"
            
            image_url = f"data:{mime_type};base64,{base64_image}"
            image_content = {"type": "image_url", "image_url": image_url}
        
        # Create message with image
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                image_content
            ]
        )
        
        # Invoke model
        response = self.model.invoke([message])
        return response.content


class OpenAITranscriber(ImageTranscriber):
    """Transcribe images using OpenAI GPT-4 Vision via LangChain"""
    
    # Models that support vision/image inputs
    VISION_MODELS = {
        "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4-vision-preview",
        "gpt-4", "gpt-4-turbo-preview", "gpt-4-1106-preview", "gpt-4-0125-preview"
    }
    
    def _init_model(self):
        try:
            from langchain_openai import ChatOpenAI
            api_key = self.api_key or os.getenv("OPENAI_API_KEY")
            model_name = self.model_name or "gpt-4o"
            
            # Build model kwargs - only include parameters if provided
            model_kwargs = {
                "model": model_name,
                "api_key": api_key
            }
            
            # Only add max_tokens if explicitly provided (some models don't support it)
            if "max_tokens" in self.kwargs:
                model_kwargs["max_tokens"] = self.kwargs["max_tokens"]
            
            # Only add temperature if explicitly provided (some models don't support it)
            if "temperature" in self.kwargs:
                model_kwargs["temperature"] = self.kwargs["temperature"]
            
            self.model = ChatOpenAI(**model_kwargs)
            self.api_key = api_key
            self.model_name = model_name
        except ImportError:
            raise ImportError("Please install langchain-openai: pip install langchain-openai")
    
    def _supports_vision(self) -> bool:
        """
        Check if the current model supports vision/image inputs
        
        Note: This is a best-effort check. Some newer models may not be in the list.
        The actual API call will validate this, and we'll catch the error.
        """
        model_name = (self.model_name or "gpt-4o").lower()
        
        # Check if model is explicitly in known vision models
        if any(vision_model.lower() in model_name for vision_model in self.VISION_MODELS):
            return True
        
        # Check for vision indicators
        if "vision" in model_name:
            return True
        
        # gpt-4o and gpt-4o-mini support vision, but be careful with other "o" models
        if model_name.startswith("gpt-4o") or model_name.startswith("gpt-4-o"):
            return True
        
        # Default to True and let API error handle it for unknown models
        # This allows trying new models that might support vision
        return True
    
    def transcribe(self, image_path: Union[str, Path], prompt: str = None, structured: bool = True) -> Union[str, Dict]:
        """
        Transcribe image using OpenAI GPT-4 Vision
        
        Args:
            image_path: Path to image file or URL
            prompt: Custom prompt (if None, uses structured extraction prompt)
            structured: If True, returns structured JSON; if False, returns text
        
        Returns:
            Dict if structured=True, str otherwise
        """
        import base64
        import json
        import re
        from langchain_core.messages import HumanMessage
        
        # Use structured extraction prompt by default
        if prompt is None:
            prompt = """Extract all information from this invoice/receipt image and return it as JSON with the following structure:
{
    "company": "Company name",
    "date": "Date in DD/MM/YYYY format",
    "address": "Full address",
    "total": "Total amount"
}

Be precise and extract the exact values as they appear in the image. If a field is not visible, use null."""
        
        # Define JSON schema for structured output
        json_schema = {
            "type": "object",
            "properties": {
                "company": {
                    "type": ["string", "null"],
                    "description": "Company or business name"
                },
                "date": {
                    "type": ["string", "null"],
                    "description": "Date in DD/MM/YYYY format"
                },
                "address": {
                    "type": ["string", "null"],
                    "description": "Full address"
                },
                "total": {
                    "type": ["string", "null"],
                    "description": "Total amount as string"
                }
            },
            "required": ["company", "date", "address", "total"],
            "additionalProperties": False
        }
        
        # Load and encode image
        image_path_str = str(image_path)
        if image_path_str.startswith(('http://', 'https://')):
            image_url = image_path_str
            image_content = {"type": "image_url", "image_url": {"url": image_url}}
        else:
            with open(image_path_str, 'rb') as f:
                image_data = f.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            mime_type = "image/jpeg"
            if image_path_str.lower().endswith('.png'):
                mime_type = "image/png"
            elif image_path_str.lower().endswith('.webp'):
                mime_type = "image/webp"
            elif image_path_str.lower().endswith('.gif'):
                mime_type = "image/gif"
            
            image_url = f"data:{mime_type};base64,{base64_image}"
            image_content = {"type": "image_url", "image_url": {"url": image_url}}
        
        # Invoke model with structured output if requested
        if structured:
            try:
                # Use OpenAI's structured output via direct client
                from openai import OpenAI
                client = OpenAI(api_key=self.api_key or os.getenv("OPENAI_API_KEY"))
                
                # Build request kwargs - only include parameters if provided
                request_kwargs = {
                    "model": self.model_name or "gpt-4o",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                image_content
                            ]
                        }
                    ],
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "invoice_extraction",
                            "strict": True,
                            "schema": json_schema
                        }
                    }
                }
                
                # Only add max_tokens if explicitly provided (some models don't support it)
                if "max_tokens" in self.kwargs:
                    request_kwargs["max_tokens"] = self.kwargs["max_tokens"]
                
                # Only add temperature if explicitly provided (some models don't support it)
                if "temperature" in self.kwargs:
                    request_kwargs["temperature"] = self.kwargs["temperature"]
                
                try:
                    response = client.chat.completions.create(**request_kwargs)
                except Exception as api_error:
                    # Check if error is about vision not being supported
                    error_str = str(api_error).lower()
                    if "image_url" in error_str or "vision" in error_str or "content type" in error_str:
                        raise ValueError(
                            f"Model '{self.model_name}' does not support vision/image inputs. "
                            f"Please use a vision-capable model like 'gpt-4o', 'gpt-4o-mini', or 'gpt-4-turbo'."
                        ) from api_error
                    raise
                
                result = json.loads(response.choices[0].message.content)
                return result
            except Exception as e:
                # Fallback to regular LangChain if structured output fails
                try:
                    message = HumanMessage(
                        content=[
                            {"type": "text", "text": prompt},
                            image_content
                        ]
                    )
                    response = self.model.invoke([message])
                    # Try to parse JSON from response
                    content = response.content
                    # Extract JSON from markdown code blocks if present
                    if "```json" in content:
                        json_start = content.find("```json") + 7
                        json_end = content.find("```", json_start)
                        content = content[json_start:json_end].strip()
                    elif "```" in content:
                        json_start = content.find("```") + 3
                        json_end = content.find("```", json_start)
                        content = content[json_start:json_end].strip()
                    return json.loads(content)
                except:
                    # Return raw response if JSON parsing fails
                    return {"raw_response": response.content if 'response' in locals() else str(e), "error": str(e)}
        else:
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    image_content
                ]
            )
            response = self.model.invoke([message])
            return response.content


class AnthropicTranscriber(ImageTranscriber):
    """Transcribe images using Anthropic Claude via LangChain"""
    
    def _init_model(self):
        try:
            from langchain_anthropic import ChatAnthropic
            api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
            model_name = self.model_name or "claude-3-5-sonnet-20241022"
            
            # Build model kwargs - only include parameters if provided
            model_kwargs = {
                "model": model_name,
                "api_key": api_key
            }
            
            # Only add max_tokens if explicitly provided (some models don't support it)
            if "max_tokens" in self.kwargs:
                model_kwargs["max_tokens"] = self.kwargs["max_tokens"]
            
            # Only add temperature if explicitly provided (some models don't support it)
            if "temperature" in self.kwargs:
                model_kwargs["temperature"] = self.kwargs["temperature"]
            
            self.model = ChatAnthropic(**model_kwargs)
        except ImportError:
            raise ImportError("Please install langchain-anthropic: pip install langchain-anthropic")


class GoogleTranscriber(ImageTranscriber):
    """Transcribe images using Google Gemini via LangChain"""
    
    def _init_model(self):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            api_key = self.api_key or os.getenv("GOOGLE_API_KEY")
            model_name = self.model_name or "gemini-pro-vision"
            # Build model kwargs - only include parameters if provided
            model_kwargs = {
                "model": model_name,
                "google_api_key": api_key
            }
            
            # Only add temperature if explicitly provided (some models don't support it)
            if "temperature" in self.kwargs:
                model_kwargs["temperature"] = self.kwargs["temperature"]
            
            self.model = ChatGoogleGenerativeAI(**model_kwargs)
        except ImportError:
            raise ImportError("Please install langchain-google-genai: pip install langchain-google-genai")


class OllamaTranscriber(ImageTranscriber):
    """Transcribe images using Ollama (local models like LLaVA) via LangChain"""
    
    def _init_model(self):
        try:
            from langchain_ollama import ChatOllama
            model_name = self.model_name or "llava"
            base_url = self.kwargs.get("base_url", "http://localhost:11434")
            # Build model kwargs - only include parameters if provided
            model_kwargs = {
                "model": model_name,
                "base_url": base_url
            }
            
            # Only add temperature if explicitly provided (some models don't support it)
            if "temperature" in self.kwargs:
                model_kwargs["temperature"] = self.kwargs["temperature"]
            
            self.model = ChatOllama(**model_kwargs)
        except ImportError:
            raise ImportError("Please install langchain-ollama: pip install langchain-ollama")
    
    def transcribe(self, image_path: Union[str, Path], prompt: str = "Transcribe or describe everything you see in this image in detail.") -> str:
        """Transcribe image using Ollama - handles base64 encoding for local files"""
        import base64
        from langchain_core.messages import HumanMessage
        
        # Load and encode image
        image_path_str = str(image_path)
        if image_path_str.startswith(('http://', 'https://')):
            # For URLs, download and encode
            import requests
            response = requests.get(image_path_str)
            response.raise_for_status()
            image_data = response.content
        else:
            # For local files, read directly
            with open(image_path_str, 'rb') as f:
                image_data = f.read()
        
        # Ollama expects base64 encoded images
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Create message - Ollama may need images passed differently
        # Try standard format first
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{base64_image}"}
            ]
        )
        
        try:
            response = self.model.invoke([message])
            return response.content
        except Exception:
            # Fallback: some Ollama setups might need different format
            # Try with just the image data
            message = HumanMessage(content=[prompt, base64_image])
            response = self.model.invoke([message])
            return response.content


class HuggingFaceTranscriber(ImageTranscriber):
    """Transcribe images using Hugging Face models via LangChain"""
    
    def _init_model(self):
        # HuggingFace vision models use direct API calls rather than LangChain chat interface
        model_name = self.model_name or "Salesforce/blip-image-captioning-base"
        api_key = self.api_key or os.getenv("HUGGINGFACE_API_KEY")
        self.model_name = model_name
        self.api_key = api_key
        # Create a dummy model object to satisfy the base class
        self.model = None
    
    def transcribe(self, image_path: Union[str, Path], prompt: str = "Transcribe or describe everything you see in this image in detail.") -> str:
        """Transcribe image using Hugging Face API directly"""
        import requests
        import base64
        
        # Load and encode image
        image_path_str = str(image_path)
        if image_path_str.startswith(('http://', 'https://')):
            response = requests.get(image_path_str)
            response.raise_for_status()
            image_data = response.content
        else:
            with open(image_path_str, 'rb') as f:
                image_data = f.read()
        
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{self.model_name}",
            headers=headers,
            json={
                "inputs": base64_image
            }
        )
        response.raise_for_status()
        
        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            return result[0].get("generated_text", str(result))
        return str(result)


def create_transcriber(provider: str, model_name: Optional[str] = None, api_key: Optional[str] = None, **kwargs):
    """
    Factory function to create a transcriber instance
    
    Args:
        provider: Provider name (openai, anthropic, google, ollama, huggingface)
        model_name: Optional model name
        api_key: Optional API key
        **kwargs: Additional provider-specific parameters
    
    Returns:
        ImageTranscriber instance
    """
    if provider == "openai":
        return OpenAITranscriber(model_name=model_name, api_key=api_key, **kwargs)
    elif provider == "anthropic":
        return AnthropicTranscriber(model_name=model_name, api_key=api_key, **kwargs)
    elif provider == "google":
        return GoogleTranscriber(model_name=model_name, api_key=api_key, **kwargs)
    elif provider == "ollama":
        return OllamaTranscriber(model_name=model_name or "llava", **kwargs)
    elif provider == "huggingface":
        return HuggingFaceTranscriber(
            model_name=model_name or "Salesforce/blip-image-captioning-base",
            api_key=api_key,
            **kwargs
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")


def process_comparison_mode(args):
    """Handle model comparison mode"""
    from model_comparator import ModelComparator
    
    # Parse model configurations from command line
    # Format: --models "name1:provider1:model1" "name2:provider2:model2"
    model_configs = []
    
    if args.models:
        for model_spec in args.models:
            parts = model_spec.split(':')
            if len(parts) >= 3:
                name, provider, model_name = parts[0], parts[1], parts[2]
                config = {
                    'name': name,
                    'provider': provider,
                    'model_name': model_name,
                    'api_key': args.api_key  # Use same API key for all if provided
                }
                model_configs.append(config)
            else:
                print(f"Warning: Invalid model specification '{model_spec}'. Expected format: 'name:provider:model_name'")
    else:
        # Default comparison: gpt-4o-mini vs gpt-4o
        model_configs = [
            {'name': 'GPT-4o-mini', 'provider': 'openai', 'model_name': 'gpt-4o-mini'},
            {'name': 'GPT-4o', 'provider': 'openai', 'model_name': 'gpt-4o'}
        ]
    
    if not model_configs:
        print("Error: No valid model configurations provided")
        return 1
    
    # Initialize comparator
    comparator = ModelComparator(
        images_dir=args.images_dir,
        ground_truth_dir=args.ground_truth_dir
    )
    
    # Run comparison
    comparison_result = comparator.compare_models(
        model_configs=model_configs,
        prompt=args.prompt,
        max_images=args.max_images,
        save_individual_results=True
    )
    
    # Print summary
    comparator.print_comparison_summary(comparison_result)
    
    # Generate report
    report_file = args.output or "model_comparison_report.json"
    comparator.generate_comparison_report(comparison_result, report_file)
    
    # Save results to directory
    if args.output_dir:
        comparator.save_comparison_results(comparison_result, args.output_dir)
    
    return 0


def process_batch_mode(args):
    """Handle batch processing mode"""
    from batch_processor import BatchProcessor
    from evaluator import TranscriptionEvaluator
    
    # Create transcriber
    transcriber = create_transcriber(
        provider=args.provider,
        model_name=args.model,
        api_key=args.api_key
    )
    
    # Initialize batch processor
    processor = BatchProcessor(
        transcriber=transcriber,
        images_dir=args.images_dir,
        ground_truth_dir=args.ground_truth_dir
    )
    
    # Process batch
    print(f"Processing images from: {args.images_dir}")
    if args.ground_truth_dir:
        print(f"Ground truth directory: {args.ground_truth_dir}")
    
    batch_result = processor.process_batch(
        prompt=args.prompt,
        max_images=args.max_images
    )
    
    # Save results
    output_file = args.output or "batch_results.json"
    processor.save_results(batch_result, output_file)
    
    # Evaluate if ground truth is available
    if args.ground_truth_dir:
        evaluator = TranscriptionEvaluator()
        metrics = evaluator.calculate_metrics(batch_result)
        evaluator.print_summary(batch_result, metrics)
        
        if args.report:
            report_file = args.report
        else:
            report_file = output_file.replace('.json', '_report.json')
        evaluator.save_detailed_report(batch_result, metrics, report_file)
    
    return 0


def process_single_mode(args):
    """Handle single image processing mode"""
    # Create transcriber
    transcriber = create_transcriber(
        provider=args.provider,
        model_name=args.model,
        api_key=args.api_key
    )
    
    # Transcribe image
    try:
        result = transcriber.transcribe(args.image, args.prompt)
        print("\n" + "="*60)
        print("TRANSCRIPTION RESULT:")
        print("="*60)
        print(result)
        print("="*60)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Transcribe images using LLM models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single image
  python image_transcriber.py image.jpg --provider openai
  
  # Batch processing
  python image_transcriber.py --batch --images-dir images --ground-truth-dir gdt --provider openai
  
  # Model comparison (compare GPT-4o-mini vs GPT-4o)
  python image_transcriber.py --compare --images-dir images --ground-truth-dir gdt
  
  # Model comparison with custom models
  python image_transcriber.py --compare --images-dir images --ground-truth-dir gdt --models "GPT-4o-mini:openai:gpt-4o-mini" "GPT-4o:openai:gpt-4o" "Claude:anthropic:claude-3-5-sonnet-20241022"
        """
    )
    
    # Mode selection
    parser.add_argument("--batch", action="store_true",
                       help="Enable batch processing mode")
    parser.add_argument("--compare", action="store_true",
                       help="Enable model comparison mode")
    
    # Single image mode arguments
    parser.add_argument("image", nargs="?", help="Path to image file or image URL (for single image mode)")
    
    # Batch/Comparison mode arguments
    parser.add_argument("--images-dir", default="images",
                       help="Directory containing images to process (batch/comparison mode)")
    parser.add_argument("--ground-truth-dir", default="gdt",
                       help="Directory containing ground truth files (batch/comparison mode)")
    parser.add_argument("--output", help="Output file for results (default: batch_results.json or model_comparison_report.json)")
    parser.add_argument("--output-dir", help="Output directory for comparison results")
    parser.add_argument("--report", help="Output file for detailed evaluation report")
    parser.add_argument("--max-images", type=int,
                       help="Maximum number of images to process (batch/comparison mode)")
    
    # Comparison mode arguments
    parser.add_argument("--models", nargs="+",
                       help="Model specifications for comparison (format: 'name:provider:model_name'). Example: 'GPT-4o-mini:openai:gpt-4o-mini' 'GPT-4o:openai:gpt-4o'")
    
    # Common arguments
    parser.add_argument("--provider", choices=["openai", "anthropic", "google", "ollama", "huggingface"],
                       default="openai", help="LLM provider to use (single/batch mode)")
    parser.add_argument("--model", help="Model name (optional, uses defaults if not specified)")
    parser.add_argument("--prompt", default="Transcribe or describe everything you see in this image in detail.",
                       help="Custom prompt for transcription")
    parser.add_argument("--api-key", help="API key (or set environment variable)")
    
    args = parser.parse_args()
    
    # Determine mode
    if args.compare:
        return process_comparison_mode(args)
    elif args.batch:
        return process_batch_mode(args)
    elif args.image:
        return process_single_mode(args)
    else:
        parser.error("Either provide an image path (single mode), use --batch flag (batch mode), or --compare flag (comparison mode)")


if __name__ == "__main__":
    exit(main())

