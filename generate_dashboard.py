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

def generate_html(comparison_data, orientation_data):
    """Generate HTML dashboard"""
    
    # Prepare data for charts
    models = []
    success_rates = []
    avg_times = []
    accuracies = []
    
    if comparison_data:
        metrics = comparison_data.get('per_model_metrics', {})
        for model, data in metrics.items():
            models.append(model)
            success_rates.append(data.get('success_rate', 0) * 100)
            avg_times.append(data.get('average_processing_time', 0))
            accuracies.append(data.get('overall_accuracy', 0) * 100)
            
    # Prepare orientation data
    orientation_models = []
    orientation_accuracies = []
    rotation_accuracies = {0: [], 90: [], 180: [], 270: []}
    
    if orientation_data:
        summary = orientation_data.get('summary', {})
        for model, data in summary.items():
            orientation_models.append(model)
            orientation_accuracies.append(data.get('accuracy', 0) * 100)
            
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

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>i2d-arena Results Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ background-color: #f8f9fa; }}
        .card {{ margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .metric-value {{ font-size: 2rem; font-weight: bold; }}
        .metric-label {{ color: #6c757d; }}
        .nav-tabs .nav-link.active {{ font-weight: bold; border-bottom: 3px solid #0d6efd; }}
    </style>
</head>
<body>
    <nav class="navbar navbar-dark bg-dark mb-4">
        <div class="container">
            <span class="navbar-brand mb-0 h1">🎯 i2d-arena Dashboard</span>
            <span class="text-light small">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</span>
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
        </ul>

        <div class="tab-content" id="myTabContent">
            <!-- Overview Tab -->
            <div class="tab-pane fade show active" id="overview" role="tabpanel">
                <div class="row">
                    <div class="col-md-4">
                        <div class="card text-center p-3">
                            <div class="metric-label">Models Compared</div>
                            <div class="metric-value">{len(models)}</div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card text-center p-3">
                            <div class="metric-label">Total Images (Extraction)</div>
                            <div class="metric-value">{comparison_data.get('summary', {}).get('total_images', 'N/A') if comparison_data else 'N/A'}</div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card text-center p-3">
                            <div class="metric-label">Orientation Extraction Tests</div>
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
                                            Highest Accuracy
                                            <div class="text-muted small">{best_acc_model}</div>
                                        </div>
                                        <span class="badge bg-primary rounded-pill">{f"{best_acc_val:.1f}%" if models else "N/A"}</span>
                                    </li>
                                    <li class="list-group-item d-flex justify-content-between align-items-center">
                                        <div>
                                            Fastest Processing
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
                                            Highest Accuracy
                                            <div class="text-muted small">{best_orient_model}</div>
                                        </div>
                                        <span class="badge bg-primary rounded-pill">{f"{best_orient_val:.1f}%" if orientation_models else "N/A"}</span>
                                    </li>
                                    <li class="list-group-item d-flex justify-content-between align-items-center">
                                        <div>
                                            Fastest Processing
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
                                <h5 class="card-title">Accuracy vs Success Rate</h5>
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
                    <div class="card-header">Detailed Metrics</div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead>
                                    <tr>
                                        <th>Model</th>
                                        <th>Success Rate</th>
                                        <th>Accuracy</th>
                                        <th>Avg Time (s)</th>
                                        <th>Failed</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {''.join(f'<tr><td>{m}</td><td>{s:.1f}%</td><td>{a:.1f}%</td><td>{t:.2f}</td><td>{comparison_data["per_model_metrics"][m]["failed_transcriptions"]}</td></tr>' for m, s, a, t in zip(models, success_rates, accuracies, avg_times)) if comparison_data else ''}
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
                    <div class="card-header">Detailed Orientation Results</div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead>
                                    <tr>
                                        <th>Model</th>
                                        <th>Accuracy</th>
                                        <th>Correct/Total</th>
                                        <th>Mean Time (s)</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {''.join(f'<tr><td>{m}</td><td>{d["accuracy"]*100:.1f}%</td><td>{d["correct_detections"]}/{d["total_tests"]}</td><td>{d["mean_processing_time"]:.2f}</td></tr>' for m, d in orientation_data.get("summary", {}).items()) if orientation_data else ''}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Comparison Chart
        const ctxComp = document.getElementById('comparisonChart').getContext('2d');
        new Chart(ctxComp, {{
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
                    }},
                    {{
                        label: 'Success Rate (%)',
                        data: {json.dumps(success_rates)},
                        backgroundColor: 'rgba(75, 192, 192, 0.5)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1
                    }}
                ]
            }},
            options: {{
                scales: {{ y: {{ beginAtZero: true, max: 100 }} }}
            }}
        }});

        // Time Chart
        const ctxTime = document.getElementById('timeChart').getContext('2d');
        new Chart(ctxTime, {{
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
                scales: {{ y: {{ beginAtZero: true }} }}
            }}
        }});

        // Orientation Chart
        const ctxOrient = document.getElementById('orientationChart').getContext('2d');
        new Chart(ctxOrient, {{
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
                scales: {{ y: {{ beginAtZero: true, max: 100 }} }}
            }}
        }});
        
        // Rotation Accuracy Chart
        const ctxRot = document.getElementById('rotationChart').getContext('2d');
        new Chart(ctxRot, {{
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
                scales: {{ y: {{ beginAtZero: true, max: 100 }} }}
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
