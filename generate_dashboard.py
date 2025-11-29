import json
import os
from pathlib import Path
from datetime import datetime

def load_json(filepath):
    """Load JSON file if it exists"""
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def get_provider_logo(model_name):
    """Get provider logo HTML based on model name"""
    model_lower = model_name.lower()
    
    # OpenAI models - using official SVG from https://artificialanalysis.ai/img/logos/openai_small.svg
    if 'gpt' in model_lower or 'openai' in model_lower:
        return '<span style="display: inline-flex; align-items: center; margin-right: 8px; width: 24px; height: 24px;"><img src="https://artificialanalysis.ai/img/logos/openai_small.svg" alt="OpenAI" style="width: 24px; height: 24px; object-fit: contain;" onerror="this.style.display=\'none\'; this.nextElementSibling.style.display=\'inline\';"><span style="display:none; margin-right: 8px; font-size: 20px;">🤖</span></span>'
    
    # Anthropic/Claude models - using official SVG from https://artificialanalysis.ai/img/logos/anthropic_small.svg
    elif 'claude' in model_lower or 'anthropic' in model_lower:
        return '<span style="display: inline-flex; align-items: center; margin-right: 8px; width: 24px; height: 24px;"><img src="https://artificialanalysis.ai/img/logos/anthropic_small.svg" alt="Anthropic" style="width: 24px; height: 24px; object-fit: contain;" onerror="this.style.display=\'none\'; this.nextElementSibling.style.display=\'inline\';"><span style="display:none; margin-right: 8px; font-size: 20px;">🧠</span></span>'
    
    # Google/Gemini models - using inline SVG
    elif 'gemini' in model_lower or 'google' in model_lower:
        return '<span style="display: inline-flex; align-items: center; margin-right: 8px; width: 24px; height: 24px;"><svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="width: 24px; height: 24px;"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg></span>'
    
    # Ollama models
    elif 'ollama' in model_lower or 'llava' in model_lower:
        return '<span style="margin-right: 8px; font-size: 20px;">🦙</span>'
    
    # HuggingFace models
    elif 'huggingface' in model_lower or 'blip' in model_lower:
        return '<span style="margin-right: 8px; font-size: 20px;">🤗</span>'
    
    # Default fallback
    else:
        return '<span style="margin-right: 8px; font-size: 20px;">🤖</span>'

def generate_html(comparison_data, orientation_data, rotated_extraction_data=None):
    """Generate HTML dashboard"""
    
    # Prepare data for charts
    models = []
    avg_times = []
    accuracies = []
    avg_tokens = []
    total_tokens = []
    
    if comparison_data:
        metrics = comparison_data.get('per_model_metrics', {})
        for model, data in metrics.items():
            models.append(model)
            avg_times.append(data.get('average_processing_time', 0))
            accuracies.append(data.get('overall_accuracy', 0) * 100)
            avg_tokens.append(data.get('average_total_tokens') or 0)
            total_tokens.append(data.get('total_tokens') or 0)
    
    # Calculate rankings and sort data by rank
    comparison_rankings = {}
    if models and accuracies:
        # Create list of (model, accuracy, time, avg_tokens, total_tokens) tuples
        # Use 0 as default for tokens if not available
        model_data = list(zip(models, accuracies, avg_times, 
                             [t or 0 for t in avg_tokens] if avg_tokens else [0] * len(models),
                             [t or 0 for t in total_tokens] if total_tokens else [0] * len(models)))
        # Sort by accuracy (descending), then by time (ascending) for tie-breaking
        model_data_sorted = sorted(model_data, key=lambda x: (-x[1], x[2]))
        # Assign rankings
        for rank, (model, acc, time, avg_tok, tot_tok) in enumerate(model_data_sorted, 1):
            comparison_rankings[model] = rank
        
        # Reorder all data by rank (1st, 2nd, 3rd, etc.)
        models = [m for m, _, _, _, _ in model_data_sorted]
        accuracies = [a for _, a, _, _, _ in model_data_sorted]
        avg_times = [t for _, _, t, _, _ in model_data_sorted]
        avg_tokens = [at for _, _, _, at, _ in model_data_sorted]
        total_tokens = [tt for _, _, _, _, tt in model_data_sorted]
            
    # Prepare orientation data
    orientation_models = []
    orientation_accuracies = []
    rotation_accuracies = {0: [], 90: [], 180: [], 270: []}
    orientation_avg_tokens = []
    orientation_total_tokens = []
    
    if orientation_data:
        summary = orientation_data.get('summary', {})
        for model, data in summary.items():
            orientation_models.append(model)
            orientation_accuracies.append(data.get('accuracy', 0) * 100)
            orientation_avg_tokens.append(data.get('average_total_tokens') or 0)
            orientation_total_tokens.append(data.get('total_tokens') or 0)
            
            # Get rotation accuracies
            rot_acc = data.get('accuracy_by_rotation', {})
            # Handle string keys if they come from JSON
            for angle in [0, 90, 180, 270]:
                val = rot_acc.get(str(angle), rot_acc.get(angle, 0))
                # Check if val is a dict (new structure) or float (old structure)
                if isinstance(val, dict):
                    acc = val.get('accuracy', 0)
                else:
                    acc = val
                rotation_accuracies[angle].append(acc * 100)

    # Prepare rotated extraction data
    rotated_models = []
    rotated_accuracies = []
    rotated_rotation_accuracies = {0: [], 90: [], 180: [], 270: []}
    rotated_avg_tokens = []
    rotated_total_tokens = []
    rotated_avg_times = []
    
    if rotated_extraction_data:
        summary = rotated_extraction_data.get('summary', {})
        for model, data in summary.items():
            rotated_models.append(model)
            rotated_accuracies.append(data.get('overall_accuracy', 0) * 100)
            rotated_avg_tokens.append(data.get('average_total_tokens') or 0)
            rotated_total_tokens.append(data.get('total_tokens') or 0)
            rotated_avg_times.append(data.get('mean_processing_time') or 0)
            
            # Get rotation accuracies
            rot_acc = data.get('accuracy_by_rotation', {})
            for angle in [0, 90, 180, 270]:
                val = rot_acc.get(str(angle), rot_acc.get(angle, 0))
                if isinstance(val, dict):
                    acc = val.get('accuracy', 0)
                else:
                    acc = val
                rotated_rotation_accuracies[angle].append(acc * 100)

    # Find intersection of models that exist in both tests and filter data
    common_models = set(orientation_models) & set(rotated_models)
    
    # Filter orientation data to only include common models
    if common_models and orientation_models:
        # Create mapping from model to index
        orientation_model_to_idx = {model: i for i, model in enumerate(orientation_models)}
        
        # Filter to only common models, preserving order
        filtered_orientation_models = [m for m in orientation_models if m in common_models]
        filtered_orientation_accuracies = [orientation_accuracies[orientation_model_to_idx[m]] for m in filtered_orientation_models]
        filtered_orientation_avg_tokens = [orientation_avg_tokens[orientation_model_to_idx[m]] if orientation_model_to_idx[m] < len(orientation_avg_tokens) else 0 for m in filtered_orientation_models]
        filtered_orientation_total_tokens = [orientation_total_tokens[orientation_model_to_idx[m]] if orientation_model_to_idx[m] < len(orientation_total_tokens) else 0 for m in filtered_orientation_models]
        filtered_rotation_accuracies = {angle: [rotation_accuracies[angle][orientation_model_to_idx[m]] if orientation_model_to_idx[m] < len(rotation_accuracies[angle]) else 0 for m in filtered_orientation_models] for angle in [0, 90, 180, 270]}
        
        orientation_models = filtered_orientation_models
        orientation_accuracies = filtered_orientation_accuracies
        orientation_avg_tokens = filtered_orientation_avg_tokens
        orientation_total_tokens = filtered_orientation_total_tokens
        rotation_accuracies = filtered_rotation_accuracies
    
    # Filter rotated extraction data to only include common models
    if common_models and rotated_models:
        # Create mapping from model to index
        rotated_model_to_idx = {model: i for i, model in enumerate(rotated_models)}
        
        # Filter to only common models, preserving order
        filtered_rotated_models = [m for m in rotated_models if m in common_models]
        filtered_rotated_accuracies = [rotated_accuracies[rotated_model_to_idx[m]] for m in filtered_rotated_models]
        filtered_rotated_avg_tokens = [rotated_avg_tokens[rotated_model_to_idx[m]] if rotated_model_to_idx[m] < len(rotated_avg_tokens) else 0 for m in filtered_rotated_models]
        filtered_rotated_total_tokens = [rotated_total_tokens[rotated_model_to_idx[m]] if rotated_model_to_idx[m] < len(rotated_total_tokens) else 0 for m in filtered_rotated_models]
        filtered_rotated_avg_times = [rotated_avg_times[rotated_model_to_idx[m]] if rotated_model_to_idx[m] < len(rotated_avg_times) else 0 for m in filtered_rotated_models]
        filtered_rotated_rotation_accuracies = {angle: [rotated_rotation_accuracies[angle][rotated_model_to_idx[m]] if rotated_model_to_idx[m] < len(rotated_rotation_accuracies[angle]) else 0 for m in filtered_rotated_models] for angle in [0, 90, 180, 270]}
        
        rotated_models = filtered_rotated_models
        rotated_accuracies = filtered_rotated_accuracies
        rotated_avg_tokens = filtered_rotated_avg_tokens
        rotated_total_tokens = filtered_rotated_total_tokens
        rotated_avg_times = filtered_rotated_avg_times
        rotated_rotation_accuracies = filtered_rotated_rotation_accuracies

    # Calculate best performers (Orientation)
    best_orient_model = "N/A"
    best_orient_val = 0
    fastest_orient_model = "N/A"
    fastest_orient_val = float('inf')
    
    if orientation_models:
        # Best accuracy
        max_orient_acc = max(orientation_accuracies) if orientation_accuracies else 0
        if max_orient_acc > 0:
            best_orient_indices = [i for i, x in enumerate(orientation_accuracies) if x == max_orient_acc]
            best_orient_model = orientation_models[best_orient_indices[0]]
            best_orient_val = max_orient_acc
        
        # Fastest time
        # Need to extract times from summary
        summary = orientation_data.get('summary', {}) if orientation_data else {}
        orient_times = []
        for model in orientation_models:
            orient_times.append(summary.get(model, {}).get('mean_processing_time', float('inf')))
            
        if orient_times:
            min_orient_time = min(orient_times)
            fastest_orient_indices = [i for i, x in enumerate(orient_times) if x == min_orient_time]
            fastest_orient_model = orientation_models[fastest_orient_indices[0]]
            fastest_orient_val = min_orient_time

    # Prepare field statistics data
    field_stats_data = {}
    if comparison_data:
        metrics = comparison_data.get('per_model_metrics', {})
        for model, data in metrics.items():
            field_stats = data.get('field_statistics', {})
            if field_stats:
                field_stats_data[model] = field_stats
    
    
    # Calculate rankings for orientation models and sort by rank
    orientation_rankings = {}
    if orientation_models and orientation_accuracies:
        orient_times_list = []
        if orientation_data:
            summary = orientation_data.get('summary', {})
            for model in orientation_models:
                orient_times_list.append(summary.get(model, {}).get('mean_processing_time', float('inf')))
        
        # Create list of (model, accuracy, time) tuples
        orient_model_data = list(zip(orientation_models, orientation_accuracies, orient_times_list))
        # Sort by accuracy (descending), then by time (ascending) for tie-breaking
        orient_model_data_sorted = sorted(orient_model_data, key=lambda x: (-x[1], x[2]))
        # Assign rankings
        for rank, (model, acc, time) in enumerate(orient_model_data_sorted, 1):
            orientation_rankings[model] = rank
        
        # Reorder orientation data by rank (1st, 2nd, 3rd, etc.)
        # Create mapping from model to index for reordering token data
        model_to_idx = {m: i for i, m in enumerate(orientation_models)}
        orientation_models = [m for m, _, _ in orient_model_data_sorted]
        orientation_accuracies = [a for _, a, _ in orient_model_data_sorted]
        # Reorder token data to match sorted models
        if orientation_avg_tokens and orientation_total_tokens and len(orientation_avg_tokens) == len(model_to_idx):
            orientation_avg_tokens = [orientation_avg_tokens[model_to_idx.get(m, 0)] for m in orientation_models]
            orientation_total_tokens = [orientation_total_tokens[model_to_idx.get(m, 0)] for m in orientation_models]
        else:
            # If token data not available, create empty lists
            if not orientation_avg_tokens or len(orientation_avg_tokens) != len(orientation_models):
                orientation_avg_tokens = [0] * len(orientation_models)
            if not orientation_total_tokens or len(orientation_total_tokens) != len(orientation_models):
                orientation_total_tokens = [0] * len(orientation_models)
        
        # Reorder rotation accuracies to match sorted models
        if orientation_data:
            summary = orientation_data.get('summary', {})
            rotation_accuracies = {0: [], 90: [], 180: [], 270: []}
            for model in orientation_models:
                data = summary.get(model, {})
                rot_acc = data.get('accuracy_by_rotation', {})
                for angle in [0, 90, 180, 270]:
                    val = rot_acc.get(str(angle), rot_acc.get(angle, 0))
                    if isinstance(val, dict):
                        acc = val.get('accuracy', 0)
                    else:
                        acc = val
                    rotation_accuracies[angle].append(acc * 100)

    # Prepare rotated extraction data
    rotated_models = []
    rotated_accuracies = []
    rotated_rotation_accuracies = {0: [], 90: [], 180: [], 270: []}
    rotated_avg_tokens = []
    rotated_total_tokens = []
    rotated_avg_times = []
    
    if rotated_extraction_data:
        summary = rotated_extraction_data.get('summary', {})
        for model, data in summary.items():
            rotated_models.append(model)
            rotated_accuracies.append(data.get('overall_accuracy', 0) * 100)
            rotated_avg_tokens.append(data.get('average_total_tokens') or 0)
            rotated_total_tokens.append(data.get('total_tokens') or 0)
            rotated_avg_times.append(data.get('mean_processing_time') or 0)
            
            # Get rotation accuracies
            rot_acc = data.get('accuracy_by_rotation', {})
            for angle in [0, 90, 180, 270]:
                val = rot_acc.get(str(angle), rot_acc.get(angle, 0))
                if isinstance(val, dict):
                    acc = val.get('accuracy', 0)
                else:
                    acc = val
                rotated_rotation_accuracies[angle].append(acc * 100)

    # Calculate rankings for rotated extraction models and sort by rank
    rotated_rankings = {}
    if rotated_models and rotated_accuracies:
        # Create list of (model, accuracy, time) tuples
        rotated_model_data = list(zip(rotated_models, rotated_accuracies, rotated_avg_times))
        # Sort by accuracy (descending), then by time (ascending) for tie-breaking
        rotated_model_data_sorted = sorted(rotated_model_data, key=lambda x: (-x[1], x[2]))
        # Assign rankings
        for rank, (model, acc, time) in enumerate(rotated_model_data_sorted, 1):
            rotated_rankings[model] = rank
        
        # Reorder rotated data by rank
        model_to_idx = {m: i for i, m in enumerate(rotated_models)}
        rotated_models = [m for m, _, _ in rotated_model_data_sorted]
        rotated_accuracies = [a for _, a, _ in rotated_model_data_sorted]
        rotated_avg_times = [t for _, _, t in rotated_model_data_sorted]
        
        # Reorder token data to match sorted models
        if rotated_avg_tokens and rotated_total_tokens and len(rotated_avg_tokens) == len(model_to_idx):
            rotated_avg_tokens = [rotated_avg_tokens[model_to_idx.get(m, 0)] for m in rotated_models]
            rotated_total_tokens = [rotated_total_tokens[model_to_idx.get(m, 0)] for m in rotated_models]
        else:
            if not rotated_avg_tokens or len(rotated_avg_tokens) != len(rotated_models):
                rotated_avg_tokens = [0] * len(rotated_models)
            if not rotated_total_tokens or len(rotated_total_tokens) != len(rotated_models):
                rotated_total_tokens = [0] * len(rotated_models)
        
        # Reorder rotation accuracies to match sorted models
        if rotated_extraction_data:
            summary = rotated_extraction_data.get('summary', {})
            rotated_rotation_accuracies = {0: [], 90: [], 180: [], 270: []}
            for model in rotated_models:
                data = summary.get(model, {})
                rot_acc = data.get('accuracy_by_rotation', {})
                for angle in [0, 90, 180, 270]:
                    val = rot_acc.get(str(angle), rot_acc.get(angle, 0))
                    if isinstance(val, dict):
                        acc = val.get('accuracy', 0)
                    else:
                        acc = val
                    rotated_rotation_accuracies[angle].append(acc * 100)

    # Calculate best performers (Rotated Extraction)
    best_rotated_model = "N/A"
    best_rotated_val = 0
    fastest_rotated_model = "N/A"
    fastest_rotated_val = float('inf')
    
    if rotated_models:
        # Best accuracy
        max_rotated_acc = max(rotated_accuracies) if rotated_accuracies else 0
        if max_rotated_acc > 0:
            best_rotated_indices = [i for i, x in enumerate(rotated_accuracies) if x == max_rotated_acc]
            best_rotated_model = rotated_models[best_rotated_indices[0]]
            best_rotated_val = max_rotated_acc
        
        # Fastest time
        if rotated_avg_times:
            min_rotated_time = min(rotated_avg_times)
            fastest_rotated_indices = [i for i, x in enumerate(rotated_avg_times) if x == min_rotated_time]
            fastest_rotated_model = rotated_models[fastest_rotated_indices[0]]
            fastest_rotated_val = min_rotated_time

    # Calculate pipeline configurations (Orientation + Extraction)
    pipeline_configs = []
    if orientation_data and rotated_extraction_data:
        orient_summary = orientation_data.get('summary', {})
        extract_summary = rotated_extraction_data.get('summary', {})
        
        # Get all models from both tests
        all_orient_models = set(orient_summary.keys())
        all_extract_models = set(extract_summary.keys())
        
        # Find intersection - only use models that are in both tests
        common_models = all_orient_models & all_extract_models
        
        if not common_models:
            # No common models, can't create pipelines
            pipeline_configs = []
        else:
            # Calculate pipeline metrics for each combination of models in the intersection
            for orient_model in common_models:
                for extract_model in common_models:
                    orient_data = orient_summary.get(orient_model, {})
                    extract_data = extract_summary.get(extract_model, {})
                    
                    # Get orientation accuracy and time
                    orient_acc = orient_data.get('accuracy', 0)
                    orient_time = orient_data.get('mean_processing_time', 0)
                    
                    # Get extraction accuracies by rotation
                    extract_rot_acc = extract_data.get('accuracy_by_rotation', {})
                    extract_acc_0 = extract_rot_acc.get('0', {}).get('accuracy', 0) if isinstance(extract_rot_acc.get('0', {}), dict) else extract_rot_acc.get('0', 0)
                    extract_time = extract_data.get('mean_processing_time', 0)
                    
                    # Calculate average extraction accuracy at wrong rotations (90, 180, 270)
                    wrong_rotations = []
                    for angle in [90, 180, 270]:
                        val = extract_rot_acc.get(str(angle), extract_rot_acc.get(angle, 0))
                        if isinstance(val, dict):
                            wrong_rotations.append(val.get('accuracy', 0))
                        else:
                            wrong_rotations.append(val)
                    
                    avg_wrong_extract_acc = sum(wrong_rotations) / len(wrong_rotations) if wrong_rotations else 0
                    
                    # Pipeline accuracy calculation:
                    # If orientation is correct (orient_acc), we use extraction at 0° (best case)
                    # If orientation is wrong (1 - orient_acc), we use average extraction at wrong rotations
                    pipeline_accuracy = (orient_acc * extract_acc_0) + ((1 - orient_acc) * avg_wrong_extract_acc)
                    
                    # Pipeline time is sum of both steps
                    pipeline_time = orient_time + extract_time
                    
                    pipeline_configs.append({
                        'orientation_model': orient_model,
                        'extraction_model': extract_model,
                        'pipeline_accuracy': pipeline_accuracy,
                        'pipeline_time': pipeline_time,
                        'orientation_accuracy': orient_acc,
                        'extraction_accuracy_at_0': extract_acc_0,
                        'orientation_time': orient_time,
                        'extraction_time': extract_time
                    })
        
        # Sort by pipeline accuracy (descending), then by time (ascending)
        pipeline_configs.sort(key=lambda x: (-x['pipeline_accuracy'], x['pipeline_time']))
    
    # Get top 3 pipeline configurations
    top_3_pipelines = pipeline_configs[:3] if pipeline_configs else []
    
    # Build pipeline HTML section
    pipeline_html = ""
    if top_3_pipelines:
        pipeline_items = []
        for idx, p in enumerate(top_3_pipelines):
            bg_class = 'bg-yellow-50 border-yellow-200' if idx == 0 else 'bg-gray-50' if idx == 1 else 'bg-orange-50 border-orange-200' if idx == 2 else ''
            orient_logo = get_provider_logo(p['orientation_model'])
            extract_logo = get_provider_logo(p['extraction_model'])
            efficiency = (p['pipeline_accuracy'] * 100) / p['pipeline_time'] if p['pipeline_time'] > 0 else 0
            
            pipeline_items.append(f'''
                            <div class="border border-gray-200 rounded-lg p-5 {bg_class}">
                                <div class="flex items-center justify-between mb-4">
                                    <div class="flex items-center gap-3">
                                        <span class="rank-badge rank-{idx + 1}">{idx + 1}</span>
                                        <h5 class="text-base font-semibold text-gray-900">Pipeline Configuration #{idx + 1}</h5>
                                    </div>
                                    <div class="text-right">
                                        <div class="text-2xl font-bold text-gray-900">{p['pipeline_accuracy']*100:.2f}%</div>
                                        <div class="text-xs text-gray-500">Pipeline Accuracy</div>
                                    </div>
                                </div>
                                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                                    <div class="bg-white rounded p-4 border border-gray-200">
                                        <div class="text-xs text-gray-500 mb-1">Step 1: Orientation Detection</div>
                                        <div class="flex items-center gap-2 mb-2">
                                            {orient_logo}
                                            <span class="text-sm font-medium text-gray-900">{p['orientation_model']}</span>
                                        </div>
                                        <div class="flex justify-between text-sm">
                                            <span class="text-gray-600">Accuracy:</span>
                                            <span class="font-medium text-gray-900">{p['orientation_accuracy']*100:.1f}%</span>
                                        </div>
                                        <div class="flex justify-between text-sm">
                                            <span class="text-gray-600">Time:</span>
                                            <span class="font-medium text-gray-900">{p['orientation_time']:.2f}s</span>
                                        </div>
                                    </div>
                                    <div class="bg-white rounded p-4 border border-gray-200">
                                        <div class="text-xs text-gray-500 mb-1">Step 2: Data Extraction</div>
                                        <div class="flex items-center gap-2 mb-2">
                                            {extract_logo}
                                            <span class="text-sm font-medium text-gray-900">{p['extraction_model']}</span>
                                        </div>
                                        <div class="flex justify-between text-sm">
                                            <span class="text-gray-600">Accuracy (at 0°):</span>
                                            <span class="font-medium text-gray-900">{p['extraction_accuracy_at_0']*100:.1f}%</span>
                                        </div>
                                        <div class="flex justify-between text-sm">
                                            <span class="text-gray-600">Time:</span>
                                            <span class="font-medium text-gray-900">{p['extraction_time']:.2f}s</span>
                                        </div>
                                    </div>
                                </div>
                                <div class="bg-white rounded p-4 border border-gray-200">
                                    <div class="flex justify-between items-center">
                                        <div>
                                            <div class="text-xs text-gray-500 mb-1">Total Pipeline Time</div>
                                            <div class="text-lg font-semibold text-gray-900">{p['pipeline_time']:.2f}s</div>
                                        </div>
                                        <div class="text-right">
                                            <div class="text-xs text-gray-500 mb-1">Pipeline Efficiency</div>
                                            <div class="text-lg font-semibold text-gray-900">{efficiency:.2f}% per second</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            ''')
        pipeline_html = f'''
                        <div class="space-y-6">
                            {''.join(pipeline_items)}
                        </div>
                        '''
    else:
        pipeline_html = '''
                        <div class="text-center py-8 text-gray-500">
                            <p>No pipeline configurations available. Ensure both orientation and rotated extraction test results are available.</p>
                        </div>
                        '''

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 i2d Arena</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{ 
            background: #fafafa;
            min-height: 100vh;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
            color: #1a1a1a;
            line-height: 1.6;
        }}
        
        .navbar {{
            background: #ffffff;
            border-bottom: 1px solid #e5e5e5;
            backdrop-filter: blur(10px);
        }}
        
        .card {{ 
            background: #ffffff;
            margin-bottom: 1.5rem; 
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            border: 1px solid #e5e5e5;
            border-radius: 8px;
            transition: box-shadow 0.2s ease;
            overflow: hidden;
        }}
        
        .card:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }}
        
        .card-header {{
            background: #ffffff;
            color: #1a1a1a;
            font-weight: 600;
            border-bottom: 1px solid #e5e5e5;
            padding: 1.25rem 1.5rem;
            font-size: 0.95rem;
        }}
        
        .metric-card {{
            background: #ffffff;
            border-radius: 8px;
            padding: 2rem 1.5rem;
            text-align: center;
            border: 1px solid #e5e5e5;
        }}
        
        .metric-value {{ 
            font-size: 2.25rem; 
            font-weight: 600;
            color: #1a1a1a;
            margin: 0.75rem 0;
            letter-spacing: -0.02em;
        }}
        
        .metric-label {{ 
            color: #6b7280;
            font-size: 0.875rem;
            font-weight: 500;
            text-transform: none;
            letter-spacing: 0;
        }}
        
        .tab-button {{
            border-bottom: 2px solid transparent;
            transition: all 0.2s ease;
            color: #6b7280;
        }}
        
        .tab-button:hover {{
            color: #1a1a1a;
            background-color: transparent;
        }}
        
        .tab-button.active {{
            border-bottom-color: #1a1a1a;
            color: #1a1a1a;
        }}
        
        .table {{
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .search-box {{
            position: relative;
        }}
        
        .sortable {{
            cursor: pointer;
            user-select: none;
            transition: background-color 0.15s ease;
        }}
        
        .sortable:hover {{
            background-color: rgba(0,0,0,0.02);
        }}
        
        .sort-icon {{
            margin-left: 0.5rem;
            opacity: 0.4;
            font-size: 0.75rem;
        }}
        
        .rank-badge {{
            font-size: 0.8125rem;
            font-weight: 600;
            padding: 0.375rem 0.75rem;
            min-width: 2.25rem;
            text-align: center;
            border-radius: 4px;
        }}
        
        .rank-1 {{
            background: #fef3c7 !important;
            color: #92400e !important;
        }}
        
        .rank-2 {{
            background: #e5e7eb !important;
            color: #374151 !important;
        }}
        
        .rank-3 {{
            background: #fde68a !important;
            color: #78350f !important;
        }}
        
        .rank-badge:not(.rank-1):not(.rank-2):not(.rank-3) {{
            background: #f3f4f6 !important;
            color: #6b7280 !important;
        }}
        
        @media print {{
            .card {{ box-shadow: none; border: 1px solid #e5e5e5; }}
            .navbar {{ display: none; }}
        }}
    </style>
</head>
<body>
    <nav class="navbar mb-12">
        <div class="container mx-auto px-6 py-5">
            <div class="flex justify-between items-center">
                <span class="text-xl font-semibold text-gray-900">
                    🎯i2d Arena
                </span>
                <a href="https://github.com/hasnainmumtaz/i2d-arena" target="_blank" rel="noopener noreferrer" class="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors">
                    <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                        <path fill-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clip-rule="evenodd"/>
                    </svg>
                    <span class="text-sm">GitHub</span>
                </a>
            </div>
        </div>
    </nav>

    <div class="container mx-auto px-6 max-w-7xl">
        <ul class="flex border-b border-gray-200 mb-12" id="myTab" role="tablist">
            <li class="mr-1" role="presentation">
                <button class="tab-button active px-5 py-3 text-sm font-medium bg-transparent" id="overview-tab" onclick="switchTab('overview')" type="button" role="tab">Overview</button>
            </li>
            <li class="mr-1" role="presentation">
                <button class="tab-button px-5 py-3 text-sm font-medium bg-transparent" id="orientation-tab" onclick="switchTab('orientation')" type="button" role="tab">Orientation Extraction Test</button>
            </li>
            <li class="mr-1" role="presentation">
                <button class="tab-button px-5 py-3 text-sm font-medium bg-transparent" id="rotated-extraction-tab" onclick="switchTab('rotated-extraction')" type="button" role="tab">Rotated Extraction Test</button>
            </li>
            <li class="mr-1" role="presentation">
                <button class="tab-button px-5 py-3 text-sm font-medium bg-transparent" id="methodology-tab" onclick="switchTab('methodology')" type="button" role="tab">Methodology</button>
            </li>
        </ul>

        <div id="myTabContent">
            <!-- Overview Tab -->
            <div class="tab-pane active" id="overview" role="tabpanel">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-5 mb-10">
                        <div class="card">
                        <div class="card-header">Best Performers (Orientation)</div>
                        <div class="p-6">
                            <ul class="divide-y divide-gray-100">
                                <li class="py-4 flex justify-between items-center">
                                        <div>
                                        <div class="text-sm font-medium text-gray-900 mb-1">Highest Accuracy</div>
                                        <div class="text-sm text-gray-500 flex items-center">{get_provider_logo(best_orient_model) if orientation_models else ''}<span>{best_orient_model}</span></div>
                                        </div>
                                    <span class="px-3 py-1 bg-gray-100 text-gray-700 rounded text-sm font-medium">{f"{best_orient_val:.1f}%" if orientation_models else "N/A"}</span>
                                    </li>
                                <li class="py-4 flex justify-between items-center">
                                        <div>
                                        <div class="text-sm font-medium text-gray-900 mb-1">Fastest Processing</div>
                                        <div class="text-sm text-gray-500 flex items-center">{get_provider_logo(fastest_orient_model) if orientation_models else ''}<span>{fastest_orient_model}</span></div>
                                        </div>
                                    <span class="px-3 py-1 bg-gray-100 text-gray-700 rounded text-sm font-medium">{f"{fastest_orient_val:.2f}s" if orientation_models else "N/A"}</span>
                                    </li>
                                </ul>
                            </div>
                        </div>
                        <div class="card">
                        <div class="card-header">Best Performers (Rotated Extraction)</div>
                        <div class="p-6">
                            <ul class="divide-y divide-gray-100">
                                <li class="py-4 flex justify-between items-center">
                                        <div>
                                        <div class="text-sm font-medium text-gray-900 mb-1">Highest Accuracy</div>
                                        <div class="text-sm text-gray-500 flex items-center">{get_provider_logo(best_rotated_model) if rotated_models else ''}<span>{best_rotated_model}</span></div>
                                        </div>
                                    <span class="px-3 py-1 bg-gray-100 text-gray-700 rounded text-sm font-medium">{f"{best_rotated_val:.1f}%" if rotated_models else "N/A"}</span>
                                    </li>
                                <li class="py-4 flex justify-between items-center">
                                        <div>
                                        <div class="text-sm font-medium text-gray-900 mb-1">Fastest Processing</div>
                                        <div class="text-sm text-gray-500 flex items-center">{get_provider_logo(fastest_rotated_model) if rotated_models else ''}<span>{fastest_rotated_model}</span></div>
                                        </div>
                                    <span class="px-3 py-1 bg-gray-100 text-gray-700 rounded text-sm font-medium">{f"{fastest_rotated_val:.2f}s" if rotated_models else "N/A"}</span>
                                    </li>
                                </ul>
                        </div>
                    </div>
                </div>
                
                <!-- Pipeline Configurations Section -->
                <div class="card mb-10">
                    <div class="card-header">
                        <h4 class="text-base font-semibold text-gray-900">Top 3 Pipeline Configurations</h4>
                        <p class="text-xs text-gray-500 mt-1 font-normal">Pipeline: Orientation Detection → Data Extraction</p>
                    </div>
                    <div class="p-6">
                        {pipeline_html}
                    </div>
                </div>
            </div>

            <!-- Orientation Extraction Test Tab -->
            <div class="tab-pane hidden" id="orientation" role="tabpanel">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-5 mb-8">
                        <div class="card">
                        <div class="p-6">
                            <h5 class="text-base font-semibold mb-4 text-gray-900">Overall Accuracy</h5>
                                <canvas id="orientationChart"></canvas>
                            </div>
                        </div>
                        <div class="card">
                        <div class="p-6">
                            <h5 class="text-base font-semibold mb-4 text-gray-900">Accuracy by Rotation</h5>
                                <canvas id="rotationChart"></canvas>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header flex justify-between items-center">
                        <span class="text-gray-900">Detailed Orientation Results</span>
                        <button class="px-3 py-1.5 bg-gray-50 hover:bg-gray-100 text-gray-700 rounded text-sm font-medium transition-colors border border-gray-200" onclick="exportTable('orientationTable', 'orientation_metrics.csv')">
                            Export CSV
                        </button>
                    </div>
                    <div class="p-6">
                        <div class="search-box mb-4">
                            <i class="bi bi-search absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"></i>
                            <input type="text" class="w-full pl-10 pr-4 py-2 border border-gray-200 rounded focus:border-gray-400 focus:outline-none focus:ring-1 focus:ring-gray-200 bg-white" id="orientationSearch" placeholder="Search models..." onkeyup="filterTable('orientationTable', 'orientationSearch')">
                        </div>
                        <div class="overflow-x-auto">
                            <table class="w-full table" id="orientationTable">
                                <thead class="bg-gray-50 text-gray-900">
                                    <tr>
                                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider sortable" onclick="sortTable('orientationTable', 0)">Rank <i class="bi bi-arrow-down-up sort-icon"></i></th>
                                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider sortable" onclick="sortTable('orientationTable', 1)">Model <i class="bi bi-arrow-down-up sort-icon"></i></th>
                                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider sortable" onclick="sortTable('orientationTable', 2)">Accuracy <i class="bi bi-arrow-down-up sort-icon"></i></th>
                                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider sortable" onclick="sortTable('orientationTable', 3)">Correct/Total <i class="bi bi-arrow-down-up sort-icon"></i></th>
                                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider sortable" onclick="sortTable('orientationTable', 4)">Mean Time (s) <i class="bi bi-arrow-down-up sort-icon"></i></th>
                                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider sortable" onclick="sortTable('orientationTable', 5)">Avg Tokens <i class="bi bi-arrow-down-up sort-icon"></i></th>
                                    </tr>
                                </thead>
                                <tbody class="bg-white divide-y divide-gray-100">
                                    {''.join(f'<tr class="hover:bg-gray-50 transition-colors cursor-pointer"><td class="px-4 py-3 whitespace-nowrap text-sm"><span class="rank-badge rank-{orientation_rankings.get(m, 0)}">{orientation_rankings.get(m, 0)}</span></td><td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900">{get_provider_logo(m)}{m}</td><td class="px-4 py-3 whitespace-nowrap text-sm"><div class="h-1.5 bg-gray-100 rounded-full mb-1"><div class="h-1.5 bg-gray-600 rounded-full" style="width: {orientation_data.get("summary", {}).get(m, {}).get("accuracy", 0)*100}%"></div></div> <span class="text-gray-700">{orientation_data.get("summary", {}).get(m, {}).get("accuracy", 0)*100:.1f}%</span></td><td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{orientation_data.get("summary", {}).get(m, {}).get("correct_detections", 0)}/{orientation_data.get("summary", {}).get(m, {}).get("total_tests", 0)}</td><td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{orientation_data.get("summary", {}).get(m, {}).get("mean_processing_time", 0):.2f}</td><td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{int(avg_tok) if avg_tok else "N/A"}</td></tr>' for m, avg_tok in zip(orientation_models, orientation_avg_tokens)) if orientation_data and orientation_models else ''}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Rotated Extraction Test Tab -->
            <div class="tab-pane hidden" id="rotated-extraction" role="tabpanel">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-5 mb-8">
                        <div class="card">
                        <div class="p-6">
                            <h5 class="text-base font-semibold mb-4 text-gray-900">Overall Accuracy</h5>
                            <canvas id="rotatedExtractionChart"></canvas>
                            </div>
                        </div>
                        <div class="card">
                        <div class="p-6">
                            <h5 class="text-base font-semibold mb-4 text-gray-900">Accuracy by Rotation</h5>
                            <canvas id="rotatedRotationChart"></canvas>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header flex justify-between items-center">
                        <span class="text-gray-900">Detailed Rotated Extraction Results</span>
                        <button class="px-3 py-1.5 bg-gray-50 hover:bg-gray-100 text-gray-700 rounded text-sm font-medium transition-colors border border-gray-200" onclick="exportTable('rotatedExtractionTable', 'rotated_extraction_metrics.csv')">
                            Export CSV
                        </button>
                    </div>
                    <div class="p-6">
                        <div class="search-box mb-4">
                            <i class="bi bi-search absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"></i>
                            <input type="text" class="w-full pl-10 pr-4 py-2 border border-gray-200 rounded focus:border-gray-400 focus:outline-none focus:ring-1 focus:ring-gray-200 bg-white" id="rotatedExtractionSearch" placeholder="Search models..." onkeyup="filterTable('rotatedExtractionTable', 'rotatedExtractionSearch')">
                        </div>
                        <div class="overflow-x-auto">
                            <table class="w-full table" id="rotatedExtractionTable">
                                <thead class="bg-gray-50 text-gray-900">
                                    <tr>
                                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider sortable" onclick="sortTable('rotatedExtractionTable', 0)">Rank <i class="bi bi-arrow-down-up sort-icon"></i></th>
                                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider sortable" onclick="sortTable('rotatedExtractionTable', 1)">Model <i class="bi bi-arrow-down-up sort-icon"></i></th>
                                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider sortable" onclick="sortTable('rotatedExtractionTable', 2)">Accuracy <i class="bi bi-arrow-down-up sort-icon"></i></th>
                                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider sortable" onclick="sortTable('rotatedExtractionTable', 3)">Successful/Total <i class="bi bi-arrow-down-up sort-icon"></i></th>
                                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider sortable" onclick="sortTable('rotatedExtractionTable', 4)">Mean Time (s) <i class="bi bi-arrow-down-up sort-icon"></i></th>
                                        <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider sortable" onclick="sortTable('rotatedExtractionTable', 5)">Avg Tokens <i class="bi bi-arrow-down-up sort-icon"></i></th>
                                    </tr>
                                </thead>
                                <tbody class="bg-white divide-y divide-gray-100">
                                    {''.join(f'<tr class="hover:bg-gray-50 transition-colors cursor-pointer"><td class="px-4 py-3 whitespace-nowrap text-sm"><span class="rank-badge rank-{rotated_rankings.get(m, 0)}">{rotated_rankings.get(m, 0)}</span></td><td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900">{get_provider_logo(m)}{m}</td><td class="px-4 py-3 whitespace-nowrap text-sm"><div class="h-1.5 bg-gray-100 rounded-full mb-1"><div class="h-1.5 bg-gray-600 rounded-full" style="width: {a}%"></div></div> <span class="text-gray-700">{a:.1f}%</span></td><td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{rotated_extraction_data.get("summary", {}).get(m, {}).get("successful_extractions", 0) if rotated_extraction_data else 0}/{rotated_extraction_data.get("summary", {}).get(m, {}).get("total_tests", 0) if rotated_extraction_data else 0}</td><td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{t:.2f}</td><td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{int(avg_tok) if avg_tok else "N/A"}</td></tr>' for m, a, t, avg_tok in zip(rotated_models, rotated_accuracies, rotated_avg_times, rotated_avg_tokens)) if rotated_extraction_data and rotated_models else ''}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Methodology Tab -->
            <div class="tab-pane hidden" id="methodology" role="tabpanel">
                <div class="card">
                    <div class="card-header">
                        <h4 class="text-base font-semibold text-gray-900">Testing Methodology</h4>
                    </div>
                    <div class="p-6">
                        <h5 class="text-base font-semibold mb-3 text-gray-900">Overview</h5>
                        <p class="mb-6 text-gray-700 leading-relaxed">The i2d Arena is a comprehensive benchmarking platform designed to evaluate the capabilities of Large Language Models (LLMs) with vision capabilities in extracting structured data from document images, particularly invoices and receipts. The platform employs two complementary testing methodologies and a pipeline analysis to assess different aspects of model performance.</p>
                        
                        <hr class="my-8 border-gray-200">
                        
                        <h5 class="text-base font-semibold mb-3 text-gray-900">1. Orientation Extraction Test</h5>
                        
                        <p class="mb-4 text-gray-700 leading-relaxed"><strong>Description:</strong> This test evaluates how accurately LLM models can detect the rotation angle of document images. Each test image is systematically rotated to four different orientations (0°, 90°, 180°, 270°) and the model must identify the correct rotation angle. This test assesses the model's spatial reasoning and ability to understand image orientation, which is critical for handling documents that may be scanned or photographed at various angles.</p>
                        
                        <p class="mb-3 text-gray-700"><strong>Purpose:</strong> Evaluate model robustness in handling rotated images and assess their ability to detect and potentially correct for orientation issues, which is essential for real-world document processing pipelines where documents may not always be properly oriented.</p>
                        
                        <h6 class="text-sm font-semibold mb-2 text-gray-800">Test Process:</h6>
                        <ul class="list-disc list-inside mb-5 space-y-1.5 text-gray-700">
                            <li>Each test image is systematically rotated to four orientations: 0° (upright), 90° (rotated clockwise), 180° (upside down), and 270° (rotated counter-clockwise)</li>
                            <li>For each image, models process all four rotated versions</li>
                            <li>Models are prompted to identify the rotation angle and respond with one of: 0, 90, 180, or 270 degrees</li>
                            <li>The model's response is parsed to extract the detected rotation angle (handling various response formats like "0 degrees", "upright", "0°", etc.)</li>
                            <li>Each detection is marked as correct or incorrect based on whether it matches the actual rotation applied</li>
                            <li>Optional: Multiple replications per rotation can be performed to assess consistency and account for non-deterministic model outputs</li>
                            <li>Parallel processing is supported for faster execution when testing multiple models</li>
                        </ul>
                        
                        <h6 class="text-sm font-semibold mb-2 text-gray-800">Evaluation Metrics:</h6>
                        <ul class="list-disc list-inside mb-8 space-y-1.5 text-gray-700">
                            <li><strong>Overall Accuracy:</strong> Percentage of correct orientation detections across all tests (all images × all rotations × replications)</li>
                            <li><strong>Accuracy by Rotation:</strong> Performance breakdown for each rotation angle (0°, 90°, 180°, 270°), revealing which orientations are most challenging for each model</li>
                            <li><strong>Correct/Total Tests:</strong> Raw count of successful detections out of total tests performed, providing absolute performance numbers</li>
                            <li><strong>Mean Processing Time:</strong> Average time per orientation test, measured in seconds</li>
                            <li><strong>Token Usage:</strong> Average number of tokens consumed per orientation test for cost analysis</li>
                            <li><strong>Consistency Score:</strong> When multiple replications are performed, this measures the variation in performance across replications, indicating model stability</li>
                        </ul>
                        
                        <h6 class="text-sm font-semibold mb-2 text-gray-800">Response Parsing:</h6>
                        <ul class="list-disc list-inside mb-8 space-y-1.5 text-gray-700">
                            <li>The system uses flexible parsing to extract rotation angles from various response formats</li>
                            <li>Accepts numeric values (0, 90, 180, 270), degree symbols (0°, 90°, etc.), and descriptive terms (upright, clockwise, upside down, counter-clockwise)</li>
                            <li>Handles edge cases like 360° being normalized to 0°</li>
                            <li>Invalid or unparseable responses are marked as incorrect</li>
                        </ul>
                        
                        <hr class="my-8 border-gray-200">
                        
                        <h5 class="text-base font-semibold mb-3 text-gray-900">2. Rotated Extraction Test</h5>
                        
                        <p class="mb-4 text-gray-700 leading-relaxed"><strong>Description:</strong> This test evaluates how accurately LLM models can extract structured data from document images that have been rotated to different orientations. Each test image is systematically rotated to four different angles (0°, 90°, 180°, 270°) and the model must extract the same structured information (company, date, address, total) from each rotated version. This test assesses the model's robustness in handling orientation variations while maintaining data extraction accuracy.</p>
                        
                        <p class="mb-3 text-gray-700"><strong>Purpose:</strong> Evaluate model performance in real-world scenarios where documents may be scanned or photographed at various angles. This test determines whether models can maintain high accuracy in data extraction regardless of image orientation, which is critical for automated document processing systems that receive images from various sources and orientations.</p>
                        
                        <h6 class="text-sm font-semibold mb-2 text-gray-800">Test Process:</h6>
                        <ul class="list-disc list-inside mb-5 space-y-1.5 text-gray-700">
                            <li>Each test image is rotated to four different orientations: 0° (upright), 90° (clockwise), 180° (upside down), and 270° (counter-clockwise)</li>
                            <li>For each rotated version, the model extracts four key structured fields:
                                <ul class="list-disc list-inside ml-4 mt-1 space-y-1">
                                    <li><strong>Company Name:</strong> The name of the business or vendor</li>
                                    <li><strong>Date:</strong> The transaction or invoice date</li>
                                    <li><strong>Address:</strong> The business address or location</li>
                                    <li><strong>Total Amount:</strong> The total monetary value of the transaction</li>
                                </ul>
                            </li>
                            <li>Models return structured JSON responses with the extracted fields for each rotation</li>
                            <li>Results for each rotation are compared against manually verified ground truth data</li>
                            <li>Accuracy is calculated separately for each rotation angle and then averaged to determine overall performance</li>
                            <li>All models are tested using identical prompts and parameters to ensure fair comparison</li>
                        </ul>
                        
                        <h6 class="text-sm font-semibold mb-2 text-gray-800">Evaluation Metrics:</h6>
                        <ul class="list-disc list-inside mb-5 space-y-1.5 text-gray-700">
                            <li><strong>Overall Accuracy:</strong> Average accuracy across all rotation angles, calculated as the mean of accuracies at 0°, 90°, 180°, and 270°</li>
                            <li><strong>Accuracy by Rotation:</strong> Individual accuracy scores for each rotation angle (0°, 90°, 180°, 270°), allowing identification of which orientations are most challenging for each model</li>
                            <li><strong>Field-level Accuracy:</strong> Per-field accuracy scores for each rotation, showing which fields are most affected by rotation</li>
                            <li><strong>Successful Extractions:</strong> Number of successful extractions (no errors) versus total tests, indicating model reliability</li>
                            <li><strong>Mean Processing Time:</strong> Average time taken to process each rotated image, measured in seconds</li>
                            <li><strong>Token Usage:</strong> Average number of tokens consumed per rotated image test for cost and efficiency analysis</li>
                        </ul>
                        
                        <h6 class="text-sm font-semibold mb-2 text-gray-800">Technical Implementation:</h6>
                        <ul class="list-disc list-inside mb-8 space-y-1.5 text-gray-700">
                            <li>Images are rotated in memory using PIL (Python Imaging Library) before being sent to the model</li>
                            <li>Rotated images are encoded as base64 data URLs for transmission to the LLM API</li>
                            <li>The same ground truth data is used for all rotations of the same image, ensuring consistent evaluation</li>
                            <li>Accuracy calculation uses field-level matching logic (exact match, partial match, no match)</li>
                            <li>Results are aggregated per model and per rotation angle for comprehensive analysis</li>
                        </ul>
                        
                        <h6 class="text-sm font-semibold mb-2 text-gray-800">Accuracy Calculation:</h6>
                        <ul class="list-disc list-inside mb-8 space-y-1.5 text-gray-700">
                            <li>For each rotated image, accuracy is calculated using field-level matching logic</li>
                            <li>Overall accuracy for a model = Average of (accuracy at 0° + accuracy at 90° + accuracy at 180° + accuracy at 270°)</li>
                            <li>Rotation-specific accuracy = (Number of correctly extracted fields at that rotation) / (Total fields × Number of images)</li>
                            <li>This allows identification of whether certain rotations (e.g., 180° upside down) are more challenging than others</li>
                        </ul>
                        
                        <hr class="my-8 border-gray-200">
                        
                        <h5 class="text-base font-semibold mb-3 text-gray-900">3. Pipeline Analysis</h5>
                        
                        <p class="mb-4 text-gray-700 leading-relaxed"><strong>Description:</strong> The pipeline analysis evaluates two-step processing workflows that combine orientation detection with data extraction. This analysis identifies optimal model combinations for real-world document processing scenarios where images may arrive in various orientations and need both orientation correction and accurate data extraction.</p>
                        
                        <p class="mb-3 text-gray-700"><strong>Purpose:</strong> Determine the best model combinations for production pipelines that must handle both orientation detection and data extraction, providing practical recommendations for building robust document processing systems.</p>
                        
                        <h6 class="text-sm font-semibold mb-2 text-gray-800">Pipeline Structure:</h6>
                        <ul class="list-disc list-inside mb-5 space-y-1.5 text-gray-700">
                            <li><strong>Step 1 - Orientation Detection:</strong> A model identifies the rotation angle of the document image (0°, 90°, 180°, or 270°)</li>
                            <li><strong>Step 2 - Data Extraction:</strong> A model extracts structured data (company, date, address, total) from the document</li>
                            <li>If orientation is correctly detected, the image is rotated to 0° before extraction (optimal scenario)</li>
                            <li>If orientation is incorrectly detected, extraction proceeds on the misoriented image (degraded performance)</li>
                        </ul>
                        
                        <h6 class="text-sm font-semibold mb-2 text-gray-800">Model Selection:</h6>
                        <ul class="list-disc list-inside mb-5 space-y-1.5 text-gray-700">
                            <li>Only models that appear in both orientation detection and rotated extraction tests are considered</li>
                            <li>All combinations of models from this intersection are evaluated</li>
                            <li>Each model can be used for either orientation detection or data extraction (or both)</li>
                            <li>This ensures all pipeline configurations are based on models with known performance in both tasks</li>
                        </ul>
                        
                        <h6 class="text-sm font-semibold mb-2 text-gray-800">Pipeline Accuracy Calculation:</h6>
                        <ul class="list-disc list-inside mb-5 space-y-1.5 text-gray-700">
                            <li>Pipeline accuracy is calculated as a weighted average of two scenarios:</li>
                            <li><strong>When orientation is correct:</strong> Uses extraction accuracy at 0° (best case scenario)</li>
                            <li><strong>When orientation is wrong:</strong> Uses average extraction accuracy at wrong rotations (90°, 180°, 270°)</li>
                            <li><strong>Formula:</strong> Pipeline Accuracy = (Orientation Accuracy × Extraction Accuracy at 0°) + ((1 - Orientation Accuracy) × Average Extraction Accuracy at Wrong Rotations)</li>
                            <li>This provides an expected accuracy that accounts for both correct and incorrect orientation detections</li>
                        </ul>
                        
                        <h6 class="text-sm font-semibold mb-2 text-gray-800">Pipeline Time Calculation:</h6>
                        <ul class="list-disc list-inside mb-5 space-y-1.5 text-gray-700">
                            <li>Total pipeline time = Orientation detection time + Data extraction time</li>
                            <li>Represents the end-to-end processing time for a single document through both steps</li>
                            <li>Includes all API call overhead and processing time for both steps</li>
                        </ul>
                        
                        <h6 class="text-sm font-semibold mb-2 text-gray-800">Ranking & Selection:</h6>
                        <ul class="list-disc list-inside mb-8 space-y-1.5 text-gray-700">
                            <li>Pipeline configurations are ranked by pipeline accuracy (descending)</li>
                            <li>For configurations with equal accuracy, faster pipelines are ranked higher</li>
                            <li>The top 3 configurations are displayed on the Overview tab</li>
                            <li>Each configuration shows detailed metrics for both steps, total time, and efficiency (accuracy per second)</li>
                        </ul>
                        
                        <h6 class="text-sm font-semibold mb-2 text-gray-800">Example Calculation:</h6>
                        <p class="mb-3 text-gray-700">If a pipeline uses:</p>
                        <ul class="list-disc list-inside mb-5 space-y-1.5 text-gray-700">
                            <li>Orientation model with 80% accuracy (0.8)</li>
                            <li>Extraction model with 90% accuracy at 0° (0.9)</li>
                            <li>Extraction model with 30% average accuracy at wrong rotations (0.3)</li>
                        </ul>
                        <p class="mb-5 text-gray-700">Then: Pipeline Accuracy = (0.8 × 0.9) + (0.2 × 0.3) = 0.72 + 0.06 = 0.78 (78%)</p>
                        
                        <hr class="my-8 border-gray-200">
                        
                        <h5 class="text-base font-semibold mb-3 text-gray-900">Data Structure & Ground Truth</h5>
                        <h6 class="text-sm font-semibold mb-2 text-gray-800">Ground Truth Format:</h6>
                        <p class="mb-2 text-gray-700">Each image has a corresponding JSON file in the ground truth directory with the following structure:</p>
                        <pre class="bg-gray-50 border border-gray-200 p-4 rounded mb-4 overflow-x-auto text-sm text-gray-800"><code>{{
  "company": "Company Name",
  "date": "DD/MM/YYYY",
  "address": "Full Address",
  "total": "Amount"
}}</code></pre>
                        <p class="mb-4 text-gray-700 text-sm">The ground truth files are manually verified to ensure accuracy. For the Orientation Extraction Test, the ground truth is the known rotation angle applied to each image (0°, 90°, 180°, or 270°). For the Rotated Extraction Test, the same ground truth JSON structure is used for all rotations of each image.</p>
                        
                        <h6 class="text-sm font-semibold mb-2 text-gray-800">Supported Image Formats:</h6>
                        <ul class="list-disc list-inside mb-8 space-y-1.5 text-gray-700">
                            <li><strong>JPEG/JPG:</strong> Standard photo format, most common for scanned documents</li>
                            <li><strong>PNG:</strong> Lossless image format, preserves quality but larger file sizes</li>
                            <li><strong>WebP:</strong> Modern web image format with good compression</li>
                        </ul>
                        
                        <hr class="my-8 border-gray-200">
                        
                        <h5 class="text-base font-semibold mb-3 text-gray-900">Technical Implementation</h5>
                        <h6 class="text-sm font-semibold mb-2 text-gray-800">Framework & Infrastructure:</h6>
                        <ul class="list-disc list-inside mb-5 space-y-1.5 text-gray-700">
                            <li><strong>LangChain Integration:</strong> All models are tested using the LangChain framework, ensuring consistent API interfaces and error handling</li>
                            <li><strong>Structured Output:</strong> For data extraction tests, JSON schema enforcement ensures models return data in the expected format</li>
                            <li><strong>Parallel Processing:</strong> Both tests support parallel execution for faster completion when testing multiple models or images</li>
                            <li><strong>Token Tracking:</strong> All API calls track token usage (input, output, and total) for cost analysis and efficiency monitoring</li>
                        </ul>
                        
                        <h6 class="text-sm font-semibold mb-2 text-gray-800">Supported LLM Providers:</h6>
                        <ul class="list-disc list-inside mb-8 space-y-1.5 text-gray-700">
                            <li><strong>OpenAI:</strong> GPT-4o, GPT-4o-mini, GPT-4 Turbo, and other vision-capable models</li>
                            <li><strong>Anthropic:</strong> Claude 3.5 Sonnet, Claude 3 Opus, and other Claude models with vision</li>
                            <li><strong>Google:</strong> Gemini Pro, Gemini Ultra, and other Gemini models</li>
                            <li><strong>Ollama:</strong> Local models like LLaVA for on-premise testing</li>
                            <li><strong>HuggingFace:</strong> Open-source vision-language models via API</li>
                        </ul>
                        
                        <h6 class="text-sm font-semibold mb-2 text-gray-800">Prompt Engineering:</h6>
                        <ul class="list-disc list-inside mb-8 space-y-1.5 text-gray-700">
                            <li>Standardized prompts are used across all models to ensure fair comparison</li>
                            <li>Prompts are optimized for structured output and clear instructions</li>
                            <li>For orientation tests, prompts explicitly request numeric angle responses (0, 90, 180, 270)</li>
                            <li>For data extraction, prompts specify the four required fields and JSON format</li>
                        </ul>
                        
                        <hr class="my-8 border-gray-200">
                        
                        <h5 class="text-base font-semibold mb-3 text-gray-900">Accuracy Calculation & Scoring</h5>
                        <h6 class="text-sm font-semibold mb-2 text-gray-800">Data Extraction Scoring:</h6>
                        <ul class="list-disc list-inside mb-5 space-y-1.5 text-gray-700">
                            <li><strong>Text Normalization:</strong> All text is normalized before comparison (whitespace removal, case-insensitive)</li>
                            <li><strong>Exact Match:</strong> Field matches ground truth exactly after normalization (score: 1.0)</li>
                            <li><strong>Partial Match:</strong> Field has ≥70% word overlap for text, or matching numeric values for dates/totals (score: 0.7)</li>
                            <li><strong>No Match:</strong> Field does not match (score: 0.0)</li>
                            <li><strong>Field Accuracy:</strong> Average score for each field across all images</li>
                            <li><strong>Overall Accuracy:</strong> Average of all field scores across all images = (Sum of all field scores) / (Number of fields × Number of images)</li>
                        </ul>
                        
                        <h6 class="text-sm font-semibold mb-2 text-gray-800">Orientation Extraction Scoring:</h6>
                        <ul class="list-disc list-inside mb-8 space-y-1.5 text-gray-700">
                            <li>Each test is binary: correct (1) or incorrect (0)</li>
                            <li>Accuracy = (Number of correct detections) / (Total number of tests)</li>
                            <li>Accuracy is calculated overall and separately for each rotation angle</li>
                            <li>When replications are used, consistency is measured as the standard deviation of accuracy across replications</li>
                        </ul>
                        
                        <hr class="my-8 border-gray-200">
                        
                        <h5 class="text-base font-semibold mb-3 text-gray-900">Test Execution & Results</h5>
                        <ul class="list-disc list-inside mb-8 space-y-1.5 text-gray-700">
                            <li>Tests can be run individually or in batch mode for multiple models</li>
                            <li>Results are saved in JSON format with detailed metrics for each model</li>
                            <li>Individual test results include processing times, token usage, and error information</li>
                            <li>Summary statistics are calculated automatically and included in reports</li>
                            <li>Results can be compiled across multiple test runs to generate aggregate statistics</li>
                        </ul>
                        
                        <div class="bg-gray-50 border-l-2 border-gray-400 p-4 mt-6">
                            <p class="text-gray-700 text-sm"><strong>Note on Reproducibility:</strong> All tests are designed to be reproducible. However, results may vary slightly between runs due to the non-deterministic nature of LLM outputs, especially when temperature > 0. For more consistent results, consider using temperature=0 or running multiple replications and averaging the results.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Tab switching function
        function switchTab(tabName) {{
            // Hide all tab panes
            document.querySelectorAll('.tab-pane').forEach(pane => {{
                pane.classList.add('hidden');
                pane.classList.remove('active');
            }});
            
            // Remove active class from all tab buttons
            document.querySelectorAll('.tab-button').forEach(btn => {{
                btn.classList.remove('active', 'text-indigo-600', 'border-indigo-600');
                btn.classList.add('text-gray-600');
            }});
            
            // Show selected tab pane
            const selectedPane = document.getElementById(tabName);
            if (selectedPane) {{
                selectedPane.classList.remove('hidden');
                selectedPane.classList.add('active');
            }}
            
            // Add active class to selected tab button
            const selectedButton = document.getElementById(tabName + '-tab');
            if (selectedButton) {{
                selectedButton.classList.add('active');
                selectedButton.classList.remove('text-gray-600');
            }}
        }}
        
        // Enhanced chart configurations (defined first)
        const chartOptions = {{
            responsive: true,
            maintainAspectRatio: true,
            plugins: {{
                legend: {{
                    display: true,
                    position: 'top',
                    labels: {{
                        usePointStyle: true,
                        padding: 15,
                        font: {{
                            size: 12,
                            weight: '500'
                        }}
                    }}
                }},
                tooltip: {{
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: {{
                        size: 14,
                        weight: 'bold'
                    }},
                    bodyFont: {{
                        size: 12
                    }},
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    displayColors: true
                }}
            }},
            animation: {{
                duration: 1500,
                easing: 'easeInOutQuart'
            }},
            interaction: {{
                mode: 'index',
                intersect: false
            }}
        }};
        
        // Orientation Chart
        const ctxOrient = document.getElementById('orientationChart').getContext('2d');
        const orientationChart = new Chart(ctxOrient, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(orientation_models)},
                datasets: [{{
                    label: 'Orientation Accuracy (%)',
                    data: {json.dumps(orientation_accuracies)},
                    backgroundColor: 'rgba(153, 102, 255, 0.5)',
                    borderColor: 'rgba(153, 102, 255, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: chartOptions.responsive,
                maintainAspectRatio: chartOptions.maintainAspectRatio,
                plugins: chartOptions.plugins,
                animation: chartOptions.animation,
                interaction: chartOptions.interaction,
                scales: {{ 
                    y: {{ 
                        beginAtZero: true, 
                        max: 100,
                        ticks: {{
                            callback: function(value) {{
                                return value + '%';
                            }}
                        }}
                    }} 
                }}
            }}
        }});
        
        // Rotation Accuracy Chart
        const ctxRot = document.getElementById('rotationChart').getContext('2d');
        const rotationChart = new Chart(ctxRot, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(orientation_models)},
                datasets: [
                    {{
                        label: '0°',
                        data: {json.dumps(rotation_accuracies[0])},
                        backgroundColor: 'rgba(255, 99, 132, 0.5)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1
                    }},
                    {{
                        label: '90°',
                        data: {json.dumps(rotation_accuracies[90])},
                        backgroundColor: 'rgba(54, 162, 235, 0.5)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }},
                    {{
                        label: '180°',
                        data: {json.dumps(rotation_accuracies[180])},
                        backgroundColor: 'rgba(255, 206, 86, 0.5)',
                        borderColor: 'rgba(255, 206, 86, 1)',
                        borderWidth: 1
                    }},
                    {{
                        label: '270°',
                        data: {json.dumps(rotation_accuracies[270])},
                        backgroundColor: 'rgba(75, 192, 192, 0.5)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1
                    }}
                ]
            }},
            options: {{
                responsive: chartOptions.responsive,
                maintainAspectRatio: chartOptions.maintainAspectRatio,
                plugins: {{
                    legend: chartOptions.plugins.legend,
                    tooltip: {{
                        backgroundColor: chartOptions.plugins.tooltip.backgroundColor,
                        padding: chartOptions.plugins.tooltip.padding,
                        titleFont: chartOptions.plugins.tooltip.titleFont,
                        bodyFont: chartOptions.plugins.tooltip.bodyFont,
                        borderColor: chartOptions.plugins.tooltip.borderColor,
                        borderWidth: chartOptions.plugins.tooltip.borderWidth,
                        cornerRadius: chartOptions.plugins.tooltip.cornerRadius,
                        displayColors: chartOptions.plugins.tooltip.displayColors,
                        callbacks: {{
                            label: function(context) {{
                                return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + '%';
                            }}
                        }}
                    }}
                }},
                animation: chartOptions.animation,
                interaction: chartOptions.interaction,
                scales: {{ 
                    y: {{ 
                        beginAtZero: true, 
                        max: 100,
                        ticks: {{
                            callback: function(value) {{
                                return value + '%';
                            }}
                        }}
                    }} 
                }}
            }}
        }});

        // Rotated Extraction Chart
        const ctxRotExt = document.getElementById('rotatedExtractionChart');
        if (ctxRotExt) {{
            const rotatedExtractionChart = new Chart(ctxRotExt.getContext('2d'), {{
            type: 'bar',
            data: {{
                    labels: {json.dumps(rotated_models)},
                datasets: [{{
                        label: 'Rotated Extraction Accuracy (%)',
                        data: {json.dumps(rotated_accuracies)},
                    backgroundColor: 'rgba(153, 102, 255, 0.5)',
                    borderColor: 'rgba(153, 102, 255, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                    responsive: chartOptions.responsive,
                    maintainAspectRatio: chartOptions.maintainAspectRatio,
                    plugins: chartOptions.plugins,
                    animation: chartOptions.animation,
                    interaction: chartOptions.interaction,
                    scales: {{ 
                        y: {{ 
                            beginAtZero: true, 
                            max: 100,
                            ticks: {{
                                callback: function(value) {{
                                    return value + '%';
                                }}
                            }}
                        }} 
                    }}
            }}
        }});
        }}
        
        // Rotated Rotation Accuracy Chart
        const ctxRotRot = document.getElementById('rotatedRotationChart');
        if (ctxRotRot) {{
            const rotatedRotationChart = new Chart(ctxRotRot.getContext('2d'), {{
            type: 'bar',
            data: {{
                    labels: {json.dumps(rotated_models)},
                datasets: [
                    {{
                        label: '0°',
                            data: {json.dumps(rotated_rotation_accuracies[0])},
                        backgroundColor: 'rgba(255, 99, 132, 0.5)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1
                    }},
                    {{
                        label: '90°',
                            data: {json.dumps(rotated_rotation_accuracies[90])},
                        backgroundColor: 'rgba(54, 162, 235, 0.5)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }},
                    {{
                        label: '180°',
                            data: {json.dumps(rotated_rotation_accuracies[180])},
                        backgroundColor: 'rgba(255, 206, 86, 0.5)',
                        borderColor: 'rgba(255, 206, 86, 1)',
                        borderWidth: 1
                    }},
                    {{
                        label: '270°',
                            data: {json.dumps(rotated_rotation_accuracies[270])},
                        backgroundColor: 'rgba(75, 192, 192, 0.5)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1
                    }}
                ]
            }},
            options: {{
                    responsive: chartOptions.responsive,
                    maintainAspectRatio: chartOptions.maintainAspectRatio,
                    plugins: {{
                        legend: chartOptions.plugins.legend,
                        tooltip: {{
                            backgroundColor: chartOptions.plugins.tooltip.backgroundColor,
                            padding: chartOptions.plugins.tooltip.padding,
                            titleFont: chartOptions.plugins.tooltip.titleFont,
                            bodyFont: chartOptions.plugins.tooltip.bodyFont,
                            borderColor: chartOptions.plugins.tooltip.borderColor,
                            borderWidth: chartOptions.plugins.tooltip.borderWidth,
                            cornerRadius: chartOptions.plugins.tooltip.cornerRadius,
                            displayColors: chartOptions.plugins.tooltip.displayColors,
                            callbacks: {{
                                label: function(context) {{
                                    return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + '%';
                                }}
                            }}
                        }}
                    }},
                    animation: chartOptions.animation,
                    interaction: chartOptions.interaction,
                    scales: {{ 
                        y: {{ 
                            beginAtZero: true, 
                            max: 100,
                            ticks: {{
                                callback: function(value) {{
                                    return value + '%';
                                }}
                            }}
                        }} 
                    }}
                }}
            }});
        }}
        
        // Table sorting function
        let sortDirection = {{}};
        function sortTable(tableId, columnIndex, initialDirection = null) {{
            const table = document.getElementById(tableId);
            if (!table) return;
            
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            // Rank column (0) and numeric columns are numeric
            const isNumeric = columnIndex === 0 || columnIndex > 1;
            
            const key = tableId + '_' + columnIndex;
            if (initialDirection !== null) {{
                sortDirection[key] = initialDirection;
            }} else {{
                sortDirection[key] = !sortDirection[key];
            }}
            const direction = sortDirection[key] ? 1 : -1;
            
            rows.sort((a, b) => {{
                let aVal = a.cells[columnIndex].textContent.trim();
                let bVal = b.cells[columnIndex].textContent.trim();
                
                if (isNumeric) {{
                    // Extract numeric value
                    aVal = parseFloat(aVal.replace(/[^0-9.]/g, '')) || 0;
                    bVal = parseFloat(bVal.replace(/[^0-9.]/g, '')) || 0;
                }}
                
                if (aVal < bVal) return -1 * direction;
                if (aVal > bVal) return 1 * direction;
                return 0;
            }});
            
            rows.forEach(row => tbody.appendChild(row));
            
            // Update sort icons
            const headers = table.querySelectorAll('th');
            headers.forEach((header, idx) => {{
                const icon = header.querySelector('.sort-icon');
                if (icon) {{
                    if (idx === columnIndex) {{
                        icon.className = 'bi bi-arrow-' + (direction === 1 ? 'down' : 'up') + ' sort-icon';
                    }} else {{
                        icon.className = 'bi bi-arrow-down-up sort-icon';
                    }}
                }}
            }});
        }}
        
        // Table filtering function
        function filterTable(tableId, searchId) {{
            const searchInput = document.getElementById(searchId);
            const filter = searchInput.value.toUpperCase();
            const table = document.getElementById(tableId);
            const rows = table.querySelectorAll('tbody tr');
            
            rows.forEach(row => {{
                const text = row.textContent.toUpperCase();
                row.style.display = text.indexOf(filter) > -1 ? '' : 'none';
            }});
        }}
        
        // Export table to CSV
        function exportTable(tableId, filename) {{
            const table = document.getElementById(tableId);
            let csv = [];
            const rows = table.querySelectorAll('tr');
            
            for (let i = 0; i < rows.length; i++) {{
                const row = [], cols = rows[i].querySelectorAll('td, th');
                
                for (let j = 0; j < cols.length; j++) {{
                    let data = cols[j].innerText.replace(/[\\r\\n]/g, '').replace(/"/g, '""');
                    row.push('"' + data + '"');
                }}
                
                csv.push(row.join(','));
            }}
            
            const csvFile = new Blob([csv.join('\\n')], {{ type: 'text/csv' }});
            const downloadLink = document.createElement('a');
            downloadLink.download = filename;
            downloadLink.href = window.URL.createObjectURL(csvFile);
            downloadLink.style.display = 'none';
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
        }}
        
        // Sort tables by rank by default on page load
        document.addEventListener('DOMContentLoaded', function() {{
            // Sort orientation table by rank (ascending - rank 1 first)
            const orientationTable = document.getElementById('orientationTable');
            if (orientationTable) {{
                sortTable('orientationTable', 0, true); // true = ascending (1, 2, 3...)
            }}
            
            // Sort rotated extraction table by rank on load
            if (document.getElementById('rotatedExtractionTable')) {{
                sortTable('rotatedExtractionTable', 0, true); // true = ascending (1, 2, 3...)
            }}
        }});
    </script>
    
    <footer class="mt-16 py-8 border-t border-gray-200 bg-white">
        <div class="container mx-auto px-6 max-w-7xl">
            <div class="flex flex-col md:flex-row justify-center items-center gap-4 text-sm text-gray-500">
                <span>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</span>
                <span class="hidden md:inline">•</span>
                <span>
                    Contact: <a href="mailto:naqvi@uni.minerva.edu" class="text-gray-700 hover:text-gray-900 underline transition-colors">naqvi@uni.minerva.edu</a>
                </span>
            </div>
        </div>
    </footer>
</body>
</html>
"""
    return html_content

def main():
    # Compile results first
    try:
        from compile_results import compile_comparison_results, compile_orientation_results, compile_rotated_extraction_results
        print("Compiling results from results/ directory...")
        compile_comparison_results()
        compile_orientation_results()
        compile_rotated_extraction_results()
    except ImportError:
        print("Warning: Could not import compile_results. Using existing JSON files.")

    # Load data
    comparison_data = load_json('model_comparison_report.json')
    orientation_data = load_json('orientation_test_results.json')
    rotated_extraction_data = load_json('rotated_extraction_test_results.json')
    
    if not comparison_data and not orientation_data and not rotated_extraction_data:
        print("Error: No data files found (model_comparison_report.json, orientation_test_results.json, or rotated_extraction_test_results.json)")
        return

    # Generate HTML
    html = generate_html(comparison_data, orientation_data, rotated_extraction_data)
    
    # Save HTML
    output_file = 'index.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Dashboard generated successfully: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    main()
