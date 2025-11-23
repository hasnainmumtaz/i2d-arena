import json
import os
from pathlib import Path
from datetime import datetime

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
                report["summary"][model_name] = data.get("summary", {})
                
    # Try to set total images from one of the files
    if json_files:
         with open(json_files[0], 'r', encoding='utf-8') as f:
             first_data = json.load(f)
             # Estimate total images from results length / replications (assuming 1 rep for now)
             # Or just use the summary total_tests / 4 (rotations)
             summary = first_data.get("summary", {})
             if summary:
                 report["total_images"] = summary.get("total_tests", 0) // 4

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Compiled orientation report saved to: {output_file}")
    return report

def main():
    print("Compiling results...")
    compile_comparison_results()
    compile_orientation_results()
    print("Done.")

if __name__ == "__main__":
    main()
