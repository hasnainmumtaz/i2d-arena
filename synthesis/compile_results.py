import json
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict


def extract_provider(model_name: str) -> str:
    """
    Extract provider name from model name.
    
    Examples:
        "Groq-Llama4-Scout" -> "groq"
        "OpenRouter-Llama4-Maverick" -> "openrouter"
        "GPT-4o" -> "openai"
        "Claude-Sonnet-4-5" -> "anthropic"
        "Gemini-2.5-Pro" -> "google"
    
    Args:
        model_name: Model display name
        
    Returns:
        Provider name (lowercase) or "unknown" if not detected
    """
    model_lower = model_name.lower()
    
    # Check for provider prefixes
    if model_lower.startswith("groq-"):
        return "groq"
    elif model_lower.startswith("openrouter-"):
        return "openrouter"
    elif model_lower.startswith("gpt-") or model_lower.startswith("openai-"):
        return "openai"
    elif model_lower.startswith("claude-") or model_lower.startswith("anthropic-"):
        return "anthropic"
    elif model_lower.startswith("gemini-") or model_lower.startswith("google-"):
        return "google"
    elif model_lower.startswith("minimax-"):
        return "minimax"
    elif model_lower.startswith("ollama-") or "llava" in model_lower:
        return "ollama"
    elif model_lower.startswith("huggingface-") or "blip" in model_lower:
        return "huggingface"
    
    return "unknown"


def extract_base_model_name(model_name: str, model_identifier: str = None) -> str:
    """
    Extract base model identifier from model name or use stored identifier.
    
    This function tries to extract a normalized base model name that can be used
    to identify the same model across different providers.
    
    Examples:
        "Groq-Llama4-Scout" -> "llama-4-scout"
        "OpenRouter-Llama4-Scout" -> "llama-4-scout"
        "GPT-4o" -> "gpt-4o"
        "Claude-Sonnet-4-5" -> "claude-sonnet-4-5"
    
    Args:
        model_name: Model display name
        model_identifier: Optional stored model identifier (e.g., "meta-llama/llama-4-scout-17b-16e-instruct")
        
    Returns:
        Base model identifier (normalized, lowercase)
    """
    # If we have a stored identifier, extract base name from it
    if model_identifier:
        # Remove provider prefix if present (e.g., "meta-llama/llama-4-scout-17b-16e-instruct")
        # Extract just the model name part
        parts = model_identifier.split("/")
        if len(parts) > 1:
            model_part = parts[-1]  # Get last part after /
        else:
            model_part = model_identifier
        
        # Remove version suffixes like "-17b-16e-instruct", "-128e-instruct", etc.
        # Keep base model name
        base_match = re.match(r"^(.+?)(?:-\d+[a-z]+(?:-\d+[a-z]+)*(?:-instruct)?)?$", model_part)
        if base_match:
            return base_match.group(1).lower().replace("_", "-")
        return model_part.lower().replace("_", "-")
    
    # Otherwise, parse from display name
    model_lower = model_name.lower()
    
    # Remove provider prefixes
    model_lower = re.sub(r"^(groq|openrouter|openai|anthropic|google|minimax|ollama|huggingface)-", "", model_lower)
    
    # Normalize common patterns
    # Handle "Llama4" -> "llama-4"
    model_lower = re.sub(r"llama(\d+)", r"llama-\1", model_lower)
    
    # Handle "GPT-4o" -> "gpt-4o" (already lowercase)
    # Handle "Claude-Sonnet-4-5" -> "claude-sonnet-4-5"
    # Handle "Gemini-2.5-Pro" -> "gemini-2.5-pro"
    
    # Remove common suffixes that don't affect model identity
    model_lower = re.sub(r"-(mini|nano|pro|flash|ultra|max)$", "", model_lower)
    
    # Normalize separators
    model_lower = model_lower.replace("_", "-")
    
    return model_lower.strip()


def compile_comparison_results(results_dir="results/comparison", output_file="model_comparison_report.json"):
    """Compile individual comparison results into a summary report"""
    results_path = Path(results_dir)
    if not results_path.exists():
        print(f"Directory not found: {results_dir}")
        return None

    report = {
        "timestamp": datetime.now().isoformat(),
        "models_compared": [],
        "per_model_metrics": {},
        "summary": {}
    }

    json_files = list(results_path.glob("*.json"))
    if not json_files:
        print(f"No JSON files found in {results_dir}")
        return None

    print(f"Found {len(json_files)} comparison result files.")

    for file_path in json_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            model_name = data.get("model")
            if model_name:
                report["models_compared"].append(model_name)
                metrics = data.get("metrics", {}).copy()
                
                # Ensure failed_transcriptions is present
                if "failed_transcriptions" not in metrics:
                    metrics["failed_transcriptions"] = data.get("failed", 0)
                
                # Ensure other keys expected by dashboard are present
                if "success_rate" not in metrics:
                    metrics["success_rate"] = data.get("successful", 0) / data.get("total_images", 1)
                if "average_processing_time" not in metrics:
                    metrics["average_processing_time"] = data.get("processing_time", 0) / data.get("total_images", 1) if data.get("total_images", 0) > 0 else 0
                if "overall_accuracy" not in metrics:
                    metrics["overall_accuracy"] = 0
                
                # Aggregate token usage from results
                results = data.get("results", [])
                total_input_tokens = 0
                total_output_tokens = 0
                total_tokens = 0
                token_count = 0
                
                for result in results:
                    input_tok = result.get("input_tokens")
                    output_tok = result.get("output_tokens")
                    total_tok = result.get("total_tokens")
                    
                    if input_tok is not None:
                        total_input_tokens += input_tok or 0
                        total_output_tokens += output_tok or 0
                        total_tokens += total_tok or 0
                        token_count += 1
                
                if token_count > 0:
                    metrics["total_input_tokens"] = total_input_tokens
                    metrics["total_output_tokens"] = total_output_tokens
                    metrics["total_tokens"] = total_tokens
                    metrics["average_input_tokens"] = total_input_tokens / token_count
                    metrics["average_output_tokens"] = total_output_tokens / token_count
                    metrics["average_total_tokens"] = total_tokens / token_count
                else:
                    metrics["total_input_tokens"] = None
                    metrics["total_output_tokens"] = None
                    metrics["total_tokens"] = None
                    metrics["average_input_tokens"] = None
                    metrics["average_output_tokens"] = None
                    metrics["average_total_tokens"] = None
                    
                report["per_model_metrics"][model_name] = metrics

    # Calculate summary stats
    if report["per_model_metrics"]:
        metrics = report["per_model_metrics"]
        report["summary"] = {
            "total_images": json_files[0].stat().st_size, # Placeholder, hard to get total images without reading all results details
             # Actually, let's just take it from the first valid file
             "total_images": "N/A"
        }
        # Try to get total images from first file
        with open(json_files[0], 'r', encoding='utf-8') as f:
             first_data = json.load(f)
             report["summary"]["total_images"] = first_data.get("total_images", "N/A")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"Compiled comparison report saved to: {output_file}")
    return report

def analyze_provider_comparisons(results_data: Dict, test_type: str = "orientation") -> Dict:
    """
    Analyze provider comparisons for models tested across multiple providers.
    
    Groups models by base model name and compares metrics across providers,
    determining the best provider for each metric.
    
    Args:
        results_data: Dictionary with model summaries (from compiled results)
        test_type: Type of test ("orientation" or "rotated_extraction")
    
    Returns:
        Dictionary with provider comparison data:
        {
            "base_model_name": {
                "providers": ["groq", "openrouter"],
                "orientation": {
                    "accuracy": {"groq": 0.65, "openrouter": 0.72, "best": "openrouter"},
                    "mean_processing_time": {"groq": 0.73, "openrouter": 1.2, "best": "groq"},
                    ...
                }
            }
        }
    """
    # Use the functions defined in this module
    
    provider_comparisons = {}
    
    # Group models by base model name
    model_groups = {}
    for model_name, summary in results_data.items():
        # Try to get model_identifier from summary if available (from new results)
        model_identifier = summary.get("model_identifier") if isinstance(summary, dict) else None
        provider = summary.get("provider") if isinstance(summary, dict) else None
        
        # Extract base model name
        base_name = extract_base_model_name(model_name, model_identifier)
        
        # Extract provider if not stored
        if not provider:
            provider = extract_provider(model_name)
        
        if base_name not in model_groups:
            model_groups[base_name] = []
        
        model_groups[base_name].append({
            "model_name": model_name,
            "provider": provider,
            "model_identifier": model_identifier,
            "summary": summary
        })
    
    # Only process groups with multiple providers
    for base_name, models in model_groups.items():
        providers = [m["provider"] for m in models]
        unique_providers = list(set([p for p in providers if p and p != "unknown"]))
        
        # Skip if only one provider or no valid providers
        if len(unique_providers) < 2:
            continue
        
        comparison = {
            "providers": unique_providers,
            "models": {m["provider"]: m["model_name"] for m in models}
        }
        
        if test_type == "orientation":
            # Compare orientation metrics
            orientation_metrics = {}
            
            # Accuracy
            accuracy_data = {}
            for model in models:
                provider = model["provider"]
                summary = model["summary"]
                if isinstance(summary, dict):
                    accuracy = summary.get("accuracy")
                    if accuracy is not None:
                        accuracy_data[provider] = accuracy
            
            if accuracy_data:
                best_accuracy_provider = max(accuracy_data.items(), key=lambda x: x[1])[0]
                accuracy_data["best"] = best_accuracy_provider
                orientation_metrics["accuracy"] = accuracy_data
            
            # Mean processing time (lower is better)
            time_data = {}
            for model in models:
                provider = model["provider"]
                summary = model["summary"]
                if isinstance(summary, dict):
                    time = summary.get("mean_processing_time")
                    if time is not None:
                        time_data[provider] = time
            
            if time_data:
                best_time_provider = min(time_data.items(), key=lambda x: x[1])[0]
                time_data["best"] = best_time_provider
                orientation_metrics["mean_processing_time"] = time_data
            
            # Total tokens (lower is better)
            tokens_data = {}
            for model in models:
                provider = model["provider"]
                summary = model["summary"]
                if isinstance(summary, dict):
                    tokens = summary.get("total_tokens")
                    if tokens is not None:
                        tokens_data[provider] = tokens
            
            if tokens_data:
                best_tokens_provider = min(tokens_data.items(), key=lambda x: x[1])[0]
                tokens_data["best"] = best_tokens_provider
                orientation_metrics["total_tokens"] = tokens_data
            
            # Average tokens (lower is better)
            avg_tokens_data = {}
            for model in models:
                provider = model["provider"]
                summary = model["summary"]
                if isinstance(summary, dict):
                    avg_tokens = summary.get("average_total_tokens")
                    if avg_tokens is not None:
                        avg_tokens_data[provider] = avg_tokens
            
            if avg_tokens_data:
                best_avg_tokens_provider = min(avg_tokens_data.items(), key=lambda x: x[1])[0]
                avg_tokens_data["best"] = best_avg_tokens_provider
                orientation_metrics["average_total_tokens"] = avg_tokens_data
            
            # Accuracy by rotation
            accuracy_by_rotation = {}
            for angle in [0, 90, 180, 270]:
                angle_data = {}
                for model in models:
                    provider = model["provider"]
                    summary = model["summary"]
                    if isinstance(summary, dict):
                        rot_acc = summary.get("accuracy_by_rotation", {})
                        angle_acc = rot_acc.get(str(angle)) or rot_acc.get(angle)
                        if isinstance(angle_acc, dict):
                            acc = angle_acc.get("accuracy")
                        elif isinstance(angle_acc, (int, float)):
                            acc = angle_acc
                        else:
                            acc = None
                        
                        if acc is not None:
                            angle_data[provider] = acc
                
                if angle_data:
                    best_angle_provider = max(angle_data.items(), key=lambda x: x[1])[0]
                    angle_data["best"] = best_angle_provider
                    accuracy_by_rotation[str(angle)] = angle_data
            
            if accuracy_by_rotation:
                orientation_metrics["accuracy_by_rotation"] = accuracy_by_rotation
            
            comparison["orientation"] = orientation_metrics
        
        elif test_type == "rotated_extraction":
            # Compare rotated extraction metrics
            extraction_metrics = {}
            
            # Overall accuracy
            accuracy_data = {}
            for model in models:
                provider = model["provider"]
                summary = model["summary"]
                if isinstance(summary, dict):
                    accuracy = summary.get("overall_accuracy")
                    if accuracy is not None:
                        accuracy_data[provider] = accuracy
            
            if accuracy_data:
                best_accuracy_provider = max(accuracy_data.items(), key=lambda x: x[1])[0]
                accuracy_data["best"] = best_accuracy_provider
                extraction_metrics["overall_accuracy"] = accuracy_data
            
            # Success rate
            success_rate_data = {}
            for model in models:
                provider = model["provider"]
                summary = model["summary"]
                if isinstance(summary, dict):
                    total = summary.get("total_tests", 0)
                    successful = summary.get("successful_extractions", 0)
                    if total > 0:
                        success_rate = successful / total
                        success_rate_data[provider] = success_rate
            
            if success_rate_data:
                best_success_provider = max(success_rate_data.items(), key=lambda x: x[1])[0]
                success_rate_data["best"] = best_success_provider
                extraction_metrics["success_rate"] = success_rate_data
            
            # Mean processing time
            time_data = {}
            for model in models:
                provider = model["provider"]
                summary = model["summary"]
                if isinstance(summary, dict):
                    time = summary.get("mean_processing_time")
                    if time is not None:
                        time_data[provider] = time
            
            if time_data:
                best_time_provider = min(time_data.items(), key=lambda x: x[1])[0]
                time_data["best"] = best_time_provider
                extraction_metrics["mean_processing_time"] = time_data
            
            # Token usage
            tokens_data = {}
            for model in models:
                provider = model["provider"]
                summary = model["summary"]
                if isinstance(summary, dict):
                    tokens = summary.get("total_tokens")
                    if tokens is not None:
                        tokens_data[provider] = tokens
            
            if tokens_data:
                best_tokens_provider = min(tokens_data.items(), key=lambda x: x[1])[0]
                tokens_data["best"] = best_tokens_provider
                extraction_metrics["total_tokens"] = tokens_data
            
            comparison["rotated_extraction"] = extraction_metrics
        
        if (test_type == "orientation" and "orientation" in comparison) or \
           (test_type == "rotated_extraction" and "rotated_extraction" in comparison):
            provider_comparisons[base_name] = comparison
    
    return provider_comparisons


def compile_orientation_results(results_dir="results/orientation", output_file="orientation_test_results.json"):
    """Compile individual orientation results into a summary report"""
    results_path = Path(results_dir)
    if not results_path.exists():
        print(f"Directory not found: {results_dir}")
        return None

    report = {
        "timestamp": datetime.now().isoformat(),
        "models_tested": [],
        "summary": {},
        "total_images": 0
    }

    json_files = list(results_path.glob("*.json"))
    if not json_files:
        print(f"No JSON files found in {results_dir}")
        return None

    print(f"Found {len(json_files)} orientation result files.")

    for file_path in json_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            model_name = data.get("model")
            if model_name:
                report["models_tested"].append(model_name)
                summary_data = data.get("summary", {}).copy()
                
                # Include provider and model_identifier if available
                if "provider" in data:
                    summary_data["provider"] = data.get("provider")
                if "model_identifier" in data:
                    summary_data["model_identifier"] = data.get("model_identifier")
                
                # Ensure token usage fields are present (they should be from orientation_test.py)
                # But if not, calculate from results
                if "total_tokens" not in summary_data or summary_data.get("total_tokens") is None:
                    results = data.get("results", [])
                    total_input_tokens = sum(r.get("input_tokens", 0) or 0 for r in results)
                    total_output_tokens = sum(r.get("output_tokens", 0) or 0 for r in results)
                    total_tokens = sum(r.get("total_tokens", 0) or 0 for r in results)
                    
                    token_results = [r for r in results if r.get("total_tokens") is not None]
                    if token_results:
                        avg_input = sum(r.get("input_tokens", 0) or 0 for r in token_results) / len(token_results)
                        avg_output = sum(r.get("output_tokens", 0) or 0 for r in token_results) / len(token_results)
                        avg_total = sum(r.get("total_tokens", 0) or 0 for r in token_results) / len(token_results)
                    else:
                        avg_input = avg_output = avg_total = None
                    
                    if total_tokens > 0:
                        summary_data["total_input_tokens"] = total_input_tokens
                        summary_data["total_output_tokens"] = total_output_tokens
                        summary_data["total_tokens"] = total_tokens
                        summary_data["average_input_tokens"] = avg_input
                        summary_data["average_output_tokens"] = avg_output
                        summary_data["average_total_tokens"] = avg_total
                
                report["summary"][model_name] = summary_data
                
    # Try to set total images from one of the files
    if json_files:
         with open(json_files[0], 'r', encoding='utf-8') as f:
             first_data = json.load(f)
             # Estimate total images from results length / replications (assuming 1 rep for now)
             # Or just use the summary total_tests / 4 (rotations)
             summary = first_data.get("summary", {})
             if summary:
                 report["total_images"] = summary.get("total_tests", 0) // 4

    # Analyze provider comparisons
    provider_comparisons = analyze_provider_comparisons(report["summary"], test_type="orientation")
    if provider_comparisons:
        report["provider_comparisons"] = provider_comparisons
        print(f"Found {len(provider_comparisons)} model(s) tested across multiple providers.")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Compiled orientation report saved to: {output_file}")
    return report

def compile_rotated_extraction_results(results_dir="results/rotated_extraction", output_file="rotated_extraction_test_results.json"):
    """Compile individual rotated extraction results into a summary report"""
    results_path = Path(results_dir)
    if not results_path.exists():
        print(f"Directory not found: {results_dir}")
        return None

    report = {
        "timestamp": datetime.now().isoformat(),
        "models_tested": [],
        "summary": {},
        "total_images": 0
    }

    json_files = list(results_path.glob("*.json"))
    if not json_files:
        print(f"No JSON files found in {results_dir}")
        return None

    print(f"Found {len(json_files)} rotated extraction result files.")

    for file_path in json_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            model_name = data.get("model")
            if model_name:
                report["models_tested"].append(model_name)
                summary_data = data.get("summary", {}).copy()
                
                # Include provider and model_identifier if available
                if "provider" in data:
                    summary_data["provider"] = data.get("provider")
                if "model_identifier" in data:
                    summary_data["model_identifier"] = data.get("model_identifier")
                
                # Ensure token usage fields are present
                if "total_tokens" not in summary_data or summary_data.get("total_tokens") is None:
                    results = data.get("results", [])
                    total_input_tokens = sum(r.get("input_tokens", 0) or 0 for r in results)
                    total_output_tokens = sum(r.get("output_tokens", 0) or 0 for r in results)
                    total_tokens = sum(r.get("total_tokens", 0) or 0 for r in results)
                    
                    token_results = [r for r in results if r.get("total_tokens") is not None]
                    if token_results:
                        avg_input = sum(r.get("input_tokens", 0) or 0 for r in token_results) / len(token_results)
                        avg_output = sum(r.get("output_tokens", 0) or 0 for r in token_results) / len(token_results)
                        avg_total = sum(r.get("total_tokens", 0) or 0 for r in token_results) / len(token_results)
                    else:
                        avg_input = avg_output = avg_total = None
                    
                    if total_tokens > 0:
                        summary_data["total_input_tokens"] = total_input_tokens
                        summary_data["total_output_tokens"] = total_output_tokens
                        summary_data["total_tokens"] = total_tokens
                        summary_data["average_input_tokens"] = avg_input
                        summary_data["average_output_tokens"] = avg_output
                        summary_data["average_total_tokens"] = avg_total
                
                report["summary"][model_name] = summary_data
                
    # Try to set total images from one of the files
    if json_files:
         with open(json_files[0], 'r', encoding='utf-8') as f:
             first_data = json.load(f)
             summary = first_data.get("summary", {})
             if summary:
                 # Estimate total images from total_tests / 4 (rotations)
                 report["total_images"] = summary.get("total_tests", 0) // 4

    # Analyze provider comparisons
    provider_comparisons = analyze_provider_comparisons(report["summary"], test_type="rotated_extraction")
    if provider_comparisons:
        report["provider_comparisons"] = provider_comparisons
        print(f"Found {len(provider_comparisons)} model(s) tested across multiple providers.")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Compiled rotated extraction report saved to: {output_file}")
    return report

def main():
    print("Compiling results...")
    compile_comparison_results()
    compile_orientation_results()
    compile_rotated_extraction_results()
    print("Done.")

if __name__ == "__main__":
    main()
