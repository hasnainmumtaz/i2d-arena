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

def generate_html(comparison_data, orientation_data):
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

    # Calculate best performers
    best_acc_model = "N/A"
    best_acc_val = 0
    fastest_model = "N/A"
    fastest_val = float('inf')
    
    if models:
        # Best accuracy
        max_acc = max(accuracies)
        best_acc_indices = [i for i, x in enumerate(accuracies) if x == max_acc]
        # If tie, pick the one with fastest time, or just the first one
        best_acc_model = models[best_acc_indices[0]]
        best_acc_val = max_acc
        
        # Fastest time
        min_time = min(avg_times)
        fastest_indices = [i for i, x in enumerate(avg_times) if x == min_time]
        fastest_model = models[fastest_indices[0]]
        fastest_val = min_time

    # Calculate best performers (Orientation)
    best_orient_model = "N/A"
    best_orient_val = 0
    fastest_orient_model = "N/A"
    fastest_orient_val = float('inf')
    
    if orientation_models:
        # Best accuracy
        max_orient_acc = max(orientation_accuracies)
        best_orient_indices = [i for i, x in enumerate(orientation_accuracies) if x == max_orient_acc]
        best_orient_model = orientation_models[best_orient_indices[0]]
        best_orient_val = max_orient_acc
        
        # Fastest time
        # Need to extract times from summary
        summary = orientation_data.get('summary', {})
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

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>i2d Arena</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        :root {{
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --success-gradient: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            --info-gradient: linear-gradient(135deg, #3494E6 0%, #EC6EAD 100%);
            --warning-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        
        body {{ 
            background: linear-gradient(to bottom, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        
        .navbar {{
            background: var(--primary-gradient) !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .card {{ 
            margin-bottom: 20px; 
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
            border: none;
            border-radius: 12px;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            overflow: hidden;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 12px 24px rgba(0,0,0,0.15);
        }}
        
        .card-header {{
            background: var(--primary-gradient);
            color: white;
            font-weight: 600;
            border: none;
        }}
        
        .metric-card {{
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        
        .metric-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--primary-gradient);
        }}
        
        .metric-value {{ 
            font-size: 2.5rem; 
            font-weight: bold;
            background: var(--primary-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0.5rem 0;
        }}
        
        .metric-label {{ 
            color: #6c757d;
            font-size: 0.9rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .nav-tabs {{
            border-bottom: 2px solid #e9ecef;
        }}
        
        .nav-tabs .nav-link {{
            border: none;
            color: #6c757d;
            font-weight: 500;
            padding: 0.75rem 1.5rem;
            transition: all 0.3s ease;
        }}
        
        .nav-tabs .nav-link:hover {{
            color: #667eea;
            background-color: #f8f9fa;
        }}
        
        .nav-tabs .nav-link.active {{
            color: #667eea;
            font-weight: bold;
            border-bottom: 3px solid #667eea;
            background: transparent;
        }}
        
        .badge {{
            font-size: 0.9rem;
            padding: 0.5rem 1rem;
            font-weight: 600;
        }}
        
        .table {{
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .table thead {{
            background: var(--primary-gradient);
            color: white;
        }}
        
        .table tbody tr {{
            transition: background-color 0.2s ease;
        }}
        
        .table tbody tr:hover {{
            background-color: #f8f9fa;
            cursor: pointer;
        }}
        
        .progress {{
            height: 8px;
            border-radius: 10px;
            background-color: #e9ecef;
        }}
        
        .progress-bar {{
            border-radius: 10px;
        }}
        
        .search-box {{
            position: relative;
            margin-bottom: 1rem;
        }}
        
        .search-box input {{
            padding-left: 2.5rem;
            border-radius: 8px;
            border: 2px solid #e9ecef;
            transition: border-color 0.3s ease;
        }}
        
        .search-box input:focus {{
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }}
        
        .search-box i {{
            position: absolute;
            left: 0.75rem;
            top: 50%;
            transform: translateY(-50%);
            color: #6c757d;
        }}
        
        .field-accuracy-card {{
            background: white;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
        }}
        
        .field-name {{
            font-weight: 600;
            color: #495057;
            margin-bottom: 0.5rem;
            text-transform: capitalize;
        }}
        
        .sortable {{
            cursor: pointer;
            user-select: none;
        }}
        
        .sortable:hover {{
            background-color: rgba(102, 126, 234, 0.1);
        }}
        
        .sort-icon {{
            margin-left: 0.5rem;
            opacity: 0.5;
        }}
        
        .best-performer {{
            background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-left: 0.5rem;
        }}
        
        .rank-badge {{
            font-size: 0.9rem;
            font-weight: 700;
            padding: 0.4rem 0.8rem;
            min-width: 2.5rem;
            text-align: center;
            border-radius: 6px;
        }}
        
        .rank-1 {{
            background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%) !important;
            color: #000 !important;
        }}
        
        .rank-2 {{
            background: linear-gradient(135deg, #C0C0C0 0%, #808080 100%) !important;
            color: #000 !important;
        }}
        
        .rank-3 {{
            background: linear-gradient(135deg, #CD7F32 0%, #8B4513 100%) !important;
            color: #fff !important;
        }}
        
        .rank-badge:not(.rank-1):not(.rank-2):not(.rank-3) {{
            background: #6c757d !important;
            color: #fff !important;
        }}
        
        @media print {{
            .card {{ box-shadow: none; }}
            .navbar {{ display: none; }}
        }}
    </style>
</head>
<body>
    <nav class="navbar navbar-dark bg-dark mb-4">
        <div class="container">
            <span class="navbar-brand mb-0 h1">
                <i class="bi bi-graph-up-arrow"></i> i2d Arena
            </span>
            <span class="text-light small">
                <i class="bi bi-clock"></i> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            </span>
        </div>
    </nav>

    <div class="container">
        <ul class="nav nav-tabs mb-4" id="myTab" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="overview-tab" data-bs-toggle="tab" data-bs-target="#overview" type="button" role="tab">Overview</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="comparison-tab" data-bs-toggle="tab" data-bs-target="#comparison" type="button" role="tab">As-is Data Extraction</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="orientation-tab" data-bs-toggle="tab" data-bs-target="#orientation" type="button" role="tab">Orientation Extraction Test</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="methodology-tab" data-bs-toggle="tab" data-bs-target="#methodology" type="button" role="tab">Methodology</button>
            </li>
        </ul>

        <div class="tab-content" id="myTabContent">
            <!-- Overview Tab -->
            <div class="tab-pane fade show active" id="overview" role="tabpanel">
                <div class="row">
                    <div class="col-md-4">
                        <div class="card metric-card">
                            <div class="metric-label"><i class="bi bi-cpu"></i> Models Compared</div>
                            <div class="metric-value">{len(models)}</div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card metric-card">
                            <div class="metric-label"><i class="bi bi-image"></i> Total Images (Extraction)</div>
                            <div class="metric-value">{comparison_data.get('summary', {}).get('total_images', 'N/A') if comparison_data else 'N/A'}</div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card metric-card">
                            <div class="metric-label"><i class="bi bi-arrow-repeat"></i> Orientation Tests</div>
                            <div class="metric-value">{orientation_data.get('total_images', 'N/A') if orientation_data else 'N/A'}</div>
                        </div>
                    </div>
                </div>
                
                <div class="row mt-4">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">Best Performers (Extraction)</div>
                            <div class="card-body">
                                <ul class="list-group list-group-flush">
                                    <li class="list-group-item d-flex justify-content-between align-items-center">
                                        <div>
                                            <i class="bi bi-trophy-fill text-warning"></i> Highest Accuracy
                                            <div class="text-muted small">{best_acc_model}</div>
                                        </div>
                                        <span class="badge bg-primary rounded-pill">{f"{best_acc_val:.1f}%" if models else "N/A"}</span>
                                    </li>
                                    <li class="list-group-item d-flex justify-content-between align-items-center">
                                        <div>
                                            <i class="bi bi-lightning-fill text-warning"></i> Fastest Processing
                                            <div class="text-muted small">{fastest_model}</div>
                                        </div>
                                        <span class="badge bg-success rounded-pill">{f"{fastest_val:.2f}s" if models else "N/A"}</span>
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">Best Performers (Orientation)</div>
                            <div class="card-body">
                                <ul class="list-group list-group-flush">
                                    <li class="list-group-item d-flex justify-content-between align-items-center">
                                        <div>
                                            <i class="bi bi-trophy-fill text-warning"></i> Highest Accuracy
                                            <div class="text-muted small">{best_orient_model}</div>
                                        </div>
                                        <span class="badge bg-primary rounded-pill">{f"{best_orient_val:.1f}%" if orientation_models else "N/A"}</span>
                                    </li>
                                    <li class="list-group-item d-flex justify-content-between align-items-center">
                                        <div>
                                            <i class="bi bi-lightning-fill text-warning"></i> Fastest Processing
                                            <div class="text-muted small">{fastest_orient_model}</div>
                                        </div>
                                        <span class="badge bg-success rounded-pill">{f"{fastest_orient_val:.2f}s" if orientation_models else "N/A"}</span>
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- As-is Data Extraction Tab -->
            <div class="tab-pane fade" id="comparison" role="tabpanel">
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">Model Accuracy Comparison</h5>
                                <canvas id="comparisonChart"></canvas>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">Processing Time (avg)</h5>
                                <canvas id="timeChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="card mt-4">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <span><i class="bi bi-table"></i> Detailed Metrics</span>
                        <button class="btn btn-sm btn-light" onclick="exportTable('comparisonTable', 'comparison_metrics.csv')">
                            <i class="bi bi-download"></i> Export CSV
                        </button>
                    </div>
                    <div class="card-body">
                        <div class="search-box">
                            <i class="bi bi-search"></i>
                            <input type="text" class="form-control" id="comparisonSearch" placeholder="Search models..." onkeyup="filterTable('comparisonTable', 'comparisonSearch')">
                        </div>
                        <div class="table-responsive">
                            <table class="table table-hover" id="comparisonTable">
                                <thead>
                                    <tr>
                                        <th class="sortable" onclick="sortTable('comparisonTable', 0)">Rank <i class="bi bi-arrow-down-up sort-icon"></i></th>
                                        <th class="sortable" onclick="sortTable('comparisonTable', 1)">Model <i class="bi bi-arrow-down-up sort-icon"></i></th>
                                        <th class="sortable" onclick="sortTable('comparisonTable', 2)">Accuracy <i class="bi bi-arrow-down-up sort-icon"></i></th>
                                        <th class="sortable" onclick="sortTable('comparisonTable', 3)">Avg Time (s) <i class="bi bi-arrow-down-up sort-icon"></i></th>
                                        <th class="sortable" onclick="sortTable('comparisonTable', 4)">Avg Tokens <i class="bi bi-arrow-down-up sort-icon"></i></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {''.join(f'<tr><td><span class="badge rank-badge rank-{comparison_rankings.get(m, 0)}">{comparison_rankings.get(m, 0)}</span></td><td>{get_provider_logo(m)}{m}</td><td><div class="progress mb-1"><div class="progress-bar bg-primary" style="width: {a}%"></div></div> {a:.1f}%</td><td>{t:.2f}</td><td>{int(avg_tok) if avg_tok else "N/A"}</td></tr>' for m, a, t, avg_tok in zip(models, accuracies, avg_times, avg_tokens)) if comparison_data else ''}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Orientation Extraction Test Tab -->
            <div class="tab-pane fade" id="orientation" role="tabpanel">
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">Overall Accuracy</h5>
                                <canvas id="orientationChart"></canvas>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">Accuracy by Rotation</h5>
                                <canvas id="rotationChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="card mt-4">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <span><i class="bi bi-table"></i> Detailed Orientation Results</span>
                        <button class="btn btn-sm btn-light" onclick="exportTable('orientationTable', 'orientation_metrics.csv')">
                            <i class="bi bi-download"></i> Export CSV
                        </button>
                    </div>
                    <div class="card-body">
                        <div class="search-box">
                            <i class="bi bi-search"></i>
                            <input type="text" class="form-control" id="orientationSearch" placeholder="Search models..." onkeyup="filterTable('orientationTable', 'orientationSearch')">
                        </div>
                        <div class="table-responsive">
                            <table class="table table-hover" id="orientationTable">
                                <thead>
                                    <tr>
                                        <th class="sortable" onclick="sortTable('orientationTable', 0)">Rank <i class="bi bi-arrow-down-up sort-icon"></i></th>
                                        <th class="sortable" onclick="sortTable('orientationTable', 1)">Model <i class="bi bi-arrow-down-up sort-icon"></i></th>
                                        <th class="sortable" onclick="sortTable('orientationTable', 2)">Accuracy <i class="bi bi-arrow-down-up sort-icon"></i></th>
                                        <th class="sortable" onclick="sortTable('orientationTable', 3)">Correct/Total <i class="bi bi-arrow-down-up sort-icon"></i></th>
                                        <th class="sortable" onclick="sortTable('orientationTable', 4)">Mean Time (s) <i class="bi bi-arrow-down-up sort-icon"></i></th>
                                        <th class="sortable" onclick="sortTable('orientationTable', 5)">Avg Tokens <i class="bi bi-arrow-down-up sort-icon"></i></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {''.join(f'<tr><td><span class="badge rank-badge rank-{orientation_rankings.get(m, 0)}">{orientation_rankings.get(m, 0)}</span></td><td>{get_provider_logo(m)}{m}</td><td><div class="progress mb-1"><div class="progress-bar bg-primary" style="width: {orientation_data.get("summary", {}).get(m, {}).get("accuracy", 0)*100}%"></div></div> {orientation_data.get("summary", {}).get(m, {}).get("accuracy", 0)*100:.1f}%</td><td>{orientation_data.get("summary", {}).get(m, {}).get("correct_detections", 0)}/{orientation_data.get("summary", {}).get(m, {}).get("total_tests", 0)}</td><td>{orientation_data.get("summary", {}).get(m, {}).get("mean_processing_time", 0):.2f}</td><td>{int(avg_tok) if avg_tok else "N/A"}</td></tr>' for m, avg_tok in zip(orientation_models, orientation_avg_tokens)) if orientation_data and orientation_models else ''}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Methodology Tab -->
            <div class="tab-pane fade" id="methodology" role="tabpanel">
                <div class="card">
                    <div class="card-header">
                        <h4>Testing Methodology</h4>
                    </div>
                    <div class="card-body">
                        <h5>Overview</h5>
                        <p>The i2d-arena is designed to comprehensively evaluate the capabilities of Large Language Models (LLMs) in extracting structured data from images, particularly invoices and receipts. We employ two complementary testing approaches:</p>
                        
                        <hr class="my-4">
                        
                        <h5>1. As-is Data Extraction Test</h5>
                        <p><strong>Purpose:</strong> Evaluate how accurately models can extract structured information from images in their original orientation.</p>
                        
                        <h6>Process:</h6>
                        <ul>
                            <li>Each model processes the same set of invoice/receipt images</li>
                            <li>Images are presented in their original, unmodified state</li>
                            <li>Models extract four key fields: company name, date, address, and total amount</li>
                            <li>Results are compared against manually verified ground truth data</li>
                        </ul>
                        
                        <h6>Evaluation Metrics:</h6>
                        <ul>
                            <li><strong>Success Rate:</strong> Percentage of images successfully processed without errors</li>
                            <li><strong>Overall Accuracy:</strong> Percentage of correctly extracted fields across all images</li>
                            <li><strong>Field-level Accuracy:</strong> Individual accuracy for company, date, address, and total fields</li>
                            <li><strong>Processing Time:</strong> Average time taken to process each image</li>
                            <li><strong>Failed Transcriptions:</strong> Count of images that could not be processed</li>
                        </ul>
                        
                        <hr class="my-4">
                        
                        <h5>2. Orientation Extraction Test</h5>
                        <p><strong>Purpose:</strong> Assess models' robustness in handling images at different rotations, simulating real-world scenarios where documents may be scanned or photographed at various angles.</p>
                        
                        <h6>Process:</h6>
                        <ul>
                            <li>Each image is systematically rotated to four orientations: 0°, 90°, 180°, and 270°</li>
                            <li>Models process all rotated versions of each image</li>
                            <li>Optional: Multiple replications per rotation to assess consistency</li>
                            <li>Parallel processing support for faster execution</li>
                        </ul>
                        
                        <h6>Evaluation Metrics:</h6>
                        <ul>
                            <li><strong>Overall Accuracy:</strong> Percentage of correct orientation detections across all tests</li>
                            <li><strong>Accuracy by Rotation:</strong> Performance breakdown for each rotation angle (0°, 90°, 180°, 270°)</li>
                            <li><strong>Correct/Total Tests:</strong> Number of successful detections out of total tests performed</li>
                            <li><strong>Mean Processing Time:</strong> Average time per orientation test</li>
                            <li><strong>Consistency:</strong> Variation in performance across replications (if applicable)</li>
                        </ul>
                        
                        <hr class="my-4">
                        
                        <h5>Data Structure</h5>
                        <h6>Ground Truth Format:</h6>
                        <p>Each image has a corresponding JSON file with the following structure:</p>
                        <pre class="bg-light p-3 rounded"><code>{{
  "company": "Company Name",
  "date": "DD/MM/YYYY",
  "address": "Full Address",
  "total": "Amount"
}}</code></pre>
                        
                        <h6>Supported Image Formats:</h6>
                        <ul>
                            <li>JPEG/JPG - Standard photo format</li>
                            <li>PNG - Lossless image format</li>
                            <li>WebP - Modern web image format</li>
                        </ul>
                        
                        <hr class="my-4">
                        
                        <h5>Model Configuration</h5>
                        <p>Models are tested using the LangChain framework with consistent parameters:</p>
                        <ul>
                            <li><strong>Providers Supported:</strong> OpenAI, Anthropic (Claude), Google (Gemini), Ollama (local), HuggingFace</li>
                            <li><strong>Structured Output:</strong> JSON schema enforcement for consistent data extraction</li>
                            <li><strong>Prompt Engineering:</strong> Standardized prompts across all models for fair comparison</li>
                        </ul>
                        
                        <hr class="my-4">
                        
                        <h5>Accuracy Calculation</h5>
                        <p>Field-level accuracy is calculated using exact string matching after normalization:</p>
                        <ul>
                            <li>Whitespace normalization (leading/trailing removal, multiple spaces collapsed)</li>
                            <li>Case-insensitive comparison</li>
                            <li>Each field is scored as either correct (1) or incorrect (0)</li>
                            <li>Overall accuracy = (Total correct fields) / (Total fields × Total images)</li>
                        </ul>
                        
                        <div class="alert alert-info mt-4">
                            <strong>Note:</strong> All tests are designed to be reproducible. Results may vary slightly due to the non-deterministic nature of LLM outputs, especially when temperature > 0.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
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
        
        // Comparison Chart
        const ctxComp = document.getElementById('comparisonChart').getContext('2d');
        const comparisonChart = new Chart(ctxComp, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(models)},
                datasets: [
                    {{
                        label: 'Accuracy (%)',
                        data: {json.dumps(accuracies)},
                        backgroundColor: 'rgba(54, 162, 235, 0.5)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }}
                ]
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

        // Time Chart
        const ctxTime = document.getElementById('timeChart').getContext('2d');
         const timeChart = new Chart(ctxTime, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(models)},
                datasets: [{{
                    label: 'Avg Processing Time (s)',
                    data: {json.dumps(avg_times)},
                    backgroundColor: 'rgba(255, 99, 132, 0.5)',
                    borderColor: 'rgba(255, 99, 132, 1)',
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
                         ticks: {{
                             callback: function(value) {{
                                 return value + 's';
                             }}
                         }}
                     }} 
                 }}
            }}
        }});
         
         // Token Usage Chart
         const ctxToken = document.getElementById('tokenChart');
         if (ctxToken) {{
             const tokenChart = new Chart(ctxToken.getContext('2d'), {{
                 type: 'bar',
                 data: {{
                     labels: {json.dumps(models)},
                     datasets: [{{
                         label: 'Avg Tokens per Image',
                         data: {json.dumps(avg_tokens)},
                         backgroundColor: 'rgba(75, 192, 192, 0.5)',
                         borderColor: 'rgba(75, 192, 192, 1)',
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
                             ticks: {{
                                 callback: function(value) {{
                                     return value.toLocaleString();
                                 }}
                             }}
                         }} 
                     }}
                 }}
             }});
         }}
         
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
            // Sort comparison table by rank (ascending - rank 1 first)
            const comparisonTable = document.getElementById('comparisonTable');
            if (comparisonTable) {{
                sortTable('comparisonTable', 0, true); // true = ascending (1, 2, 3...)
            }}
            
            // Sort orientation table by rank (ascending - rank 1 first)
            const orientationTable = document.getElementById('orientationTable');
            if (orientationTable) {{
                sortTable('orientationTable', 0, true); // true = ascending (1, 2, 3...)
            }}
        }});
    </script>
</body>
</html>
"""
    return html_content

def main():
    # Compile results first
    try:
        from compile_results import compile_comparison_results, compile_orientation_results
        print("Compiling results from results/ directory...")
        compile_comparison_results()
        compile_orientation_results()
    except ImportError:
        print("Warning: Could not import compile_results. Using existing JSON files.")

    # Load data
    comparison_data = load_json('model_comparison_report.json')
    orientation_data = load_json('orientation_test_results.json')
    
    if not comparison_data and not orientation_data:
        print("Error: No data files found (model_comparison_report.json or orientation_test_results.json)")
        return

    # Generate HTML
    html = generate_html(comparison_data, orientation_data)
    
    # Save HTML
    output_file = 'dashboard.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Dashboard generated successfully: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    main()
