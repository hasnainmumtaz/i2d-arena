# Dashboard Generation Module

## Overview

The `generate_dashboard.py` module generates an interactive HTML dashboard that visualizes model comparison and orientation test results. It compiles results from JSON files and creates a comprehensive web-based dashboard with charts, tables, and detailed metrics.

## Architecture

### Main Functions

#### `load_json(filepath)`

**Location**: `generate_dashboard.py:6-11`

**Purpose**: Load JSON file if it exists

**Parameters**:
- `filepath` (str): Path to JSON file

**Returns**: `Dict` - Parsed JSON data, or `None` if file doesn't exist

**Error Handling**: Returns `None` gracefully if file is missing

#### `generate_html(comparison_data, orientation_data)`

**Location**: `generate_dashboard.py:13-516`

**Purpose**: Generate HTML dashboard from comparison and orientation data

**Parameters**:
- `comparison_data` (Dict): Model comparison data from `model_comparison_report.json`
- `orientation_data` (Dict): Orientation test data from `orientation_test_results.json`

**Returns**: `str` - Complete HTML content

**Features**:
- Interactive Bootstrap-based UI
- Chart.js visualizations
- Tabbed interface for different views
- Responsive design
- Methodology documentation

**Dashboard Sections**:

1. **Overview Tab**:
   - Summary metrics (models compared, total images)
   - Best performers for extraction and orientation
   - Quick statistics

2. **As-is Data Extraction Tab**:
   - Accuracy vs Success Rate chart
   - Processing time chart
   - Detailed metrics table
   - Per-model comparison

3. **Orientation Extraction Test Tab**:
   - Overall accuracy chart
   - Accuracy by rotation chart
   - Detailed orientation results table
   - Rotation-specific performance

4. **Methodology Tab**:
   - Testing methodology documentation
   - Process descriptions
   - Evaluation metrics explanation
   - Data structure information

#### `main()`

**Location**: `generate_dashboard.py:518-547`

**Purpose**: Main entry point for dashboard generation

**Process Flow**:
1. Attempts to compile results first (calls `compile_results.py`)
2. Loads comparison data from `model_comparison_report.json`
3. Loads orientation data from `orientation_test_results.json`
4. Generates HTML dashboard
5. Saves to `dashboard.html`

**Error Handling**:
- Handles missing `compile_results` module gracefully
- Warns if no data files found
- Provides helpful error messages

## Dashboard Structure

### HTML Components

#### Navigation

- Bootstrap navbar with project title
- Tab navigation for different views
- Timestamp display

#### Overview Section

**Metrics Cards**:
- Models Compared count
- Total Images (Extraction)
- Orientation Extraction Tests count

**Best Performers**:
- Highest Accuracy (Extraction)
- Fastest Processing (Extraction)
- Highest Accuracy (Orientation)
- Fastest Processing (Orientation)

#### Charts

**Chart.js Integration**:
- Bar charts for accuracy and success rates
- Processing time visualizations
- Rotation-specific accuracy charts
- Color-coded datasets

**Chart Types**:
1. **Comparison Chart**: Accuracy vs Success Rate (bar chart)
2. **Time Chart**: Average Processing Time (bar chart)
3. **Orientation Chart**: Overall Orientation Accuracy (bar chart)
4. **Rotation Chart**: Accuracy by Rotation Angle (grouped bar chart)

#### Tables

**Detailed Metrics Tables**:
- Model names
- Success rates
- Accuracy percentages
- Processing times
- Failed transcriptions
- Correct/Total counts

### Data Processing

#### Comparison Data Processing

**Extracted Metrics**:
- Model names
- Success rates (converted to percentages)
- Average processing times
- Overall accuracies (converted to percentages)

**Best Performer Calculation**:
- Finds model with highest accuracy
- Finds model with fastest processing time
- Handles ties gracefully

#### Orientation Data Processing

**Extracted Metrics**:
- Model names
- Overall accuracies
- Accuracy by rotation (0°, 90°, 180°, 270°)
- Mean processing times

**Rotation Data Handling**:
- Handles both string and integer keys
- Supports both dict and float values
- Normalizes to percentage format

## Integration with Other Modules

### Dependencies

- **`compile_results.py`**: Compiles results before dashboard generation
- **`json`**: For loading JSON data files
- **`os`**: For file path operations
- **`pathlib.Path`**: For file system operations
- **`datetime`**: For timestamp display

### Data Sources

1. **`model_comparison_report.json`**: Model comparison results
2. **`orientation_test_results.json`**: Orientation test results

### Integration Flow

```
Individual Results (results/comparison/, results/orientation/)
    │
    ▼
compile_results.py
    │
    ├── model_comparison_report.json
    └── orientation_test_results.json
    │
    ▼
generate_dashboard.py
    │
    └── dashboard.html
```

## External Dependencies

### CDN Resources

**Bootstrap 5.3.0**:
- CSS: `https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css`
- JS: `https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js`

**Chart.js**:
- JS: `https://cdn.jsdelivr.net/npm/chart.js`

**Note**: Dashboard requires internet connection for CDN resources, or can be modified to use local files.

## Usage Examples

### Standalone Execution

```bash
python generate_dashboard.py
```

**Output**:
```
Compiling results from results/ directory...
Found 7 comparison result files.
Compiled comparison report saved to: model_comparison_report.json
Found 6 orientation result files.
Compiled orientation report saved to: orientation_test_results.json
Dashboard generated successfully: /path/to/dashboard.html
```

### Programmatic Usage

```python
from generate_dashboard import generate_html, load_json

# Load data
comparison_data = load_json('model_comparison_report.json')
orientation_data = load_json('orientation_test_results.json')

# Generate HTML
html = generate_html(comparison_data, orientation_data)

# Save to file
with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
```

### Custom Data Sources

```python
# Load from custom locations
comparison_data = load_json('custom_comparison_report.json')
orientation_data = load_json('custom_orientation_report.json')

html = generate_html(comparison_data, orientation_data)

with open('custom_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
```

## Dashboard Features

### Interactive Elements

1. **Tab Navigation**: Switch between different views
2. **Charts**: Interactive Chart.js visualizations
3. **Responsive Tables**: Scrollable tables for large datasets
4. **Bootstrap Styling**: Modern, professional appearance

### Visualizations

1. **Bar Charts**: Compare metrics across models
2. **Grouped Bars**: Show multiple metrics side-by-side
3. **Color Coding**: Different colors for different metrics
4. **Scales**: Automatic scaling with appropriate ranges

### Data Presentation

1. **Summary Cards**: Quick overview metrics
2. **Detailed Tables**: Comprehensive data tables
3. **Best Performers**: Highlighted top performers
4. **Methodology**: Embedded documentation

## Error Handling

### Missing Data Files

- Warns if no data files found
- Continues with available data
- Shows "N/A" for missing metrics

### Missing Compile Module

- Handles `ImportError` gracefully
- Uses existing JSON files if available
- Warns user about missing compilation

### Invalid Data

- Handles missing fields gracefully
- Uses default values (0, "N/A")
- Continues processing with available data

## Customization

### Styling

The dashboard uses Bootstrap classes and custom CSS. Key styling elements:

- **Background**: Light gray (`#f8f9fa`)
- **Cards**: White cards with shadows
- **Navbar**: Dark theme
- **Charts**: Color-coded datasets

### Adding New Sections

To add new sections:

1. Add new tab button in navigation
2. Add new tab pane with content
3. Add data processing logic if needed
4. Add charts/tables as required

### Modifying Charts

Chart configurations can be modified in the JavaScript section:

- Chart types (bar, line, pie, etc.)
- Colors and styling
- Scales and axes
- Labels and tooltips

## Important Notes

- **Internet Required**: CDN resources require internet connection
- **Browser Compatibility**: Modern browsers (Chrome, Firefox, Safari, Edge)
- **File Size**: Dashboard HTML can be large with many models
- **Data Freshness**: Re-run to update with latest results
- **Portability**: Self-contained HTML file (except CDN resources)

## Best Practices

1. **Regular Updates**: Regenerate dashboard after new results
2. **Compile First**: Always compile results before generating dashboard
3. **Version Control**: Consider versioning dashboard HTML
4. **Sharing**: Dashboard can be shared as standalone HTML file
5. **Backup**: Keep source JSON files as backup

## Performance Considerations

- **File Size**: Large result sets create larger HTML files
- **Rendering**: Browser rendering time increases with more data
- **CDN Loading**: Initial load depends on CDN availability
- **Chart Rendering**: Many charts may slow down page load

## Future Enhancements

Potential improvements:

1. **Export Functionality**: Export charts as images
2. **Filtering**: Filter models or metrics
3. **Sorting**: Sortable tables
4. **Search**: Search functionality
5. **Comparison Mode**: Compare specific models
6. **Historical Data**: Track results over time
7. **Local Resources**: Bundle CDN resources locally

