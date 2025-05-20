from flask import Blueprint, jsonify, request
import json
import csv
import io
import os

import_bp = Blueprint('import', __name__)

@import_bp.route('/api/import/analyze', methods=['POST'])
def analyze_import_file():
    """Analyze uploaded file and detect schema"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    # Process based on file type
    if file_ext == '.json':
        return analyze_json(file)
    elif file_ext == '.csv':
        return analyze_csv(file)
    else:
        return jsonify({'error': 'Unsupported file format. Please upload JSON or CSV'}), 400

def analyze_json(file):
    """Analyze JSON file and detect schema"""
    try:
        # Read and parse JSON
        content = file.read()
        data = json.loads(content)
        
        # Handle different JSON structures
        if isinstance(data, list):
            # Array of objects
            if len(data) == 0:
                return jsonify({'error': 'Empty JSON array'}), 400
            
            # Get fields from first item
            first_item = data[0]
            if not isinstance(first_item, dict):
                return jsonify({'error': 'JSON array must contain objects'}), 400
            
            fields = list(first_item.keys())
            sample_data = data[:5] if len(data) > 5 else data
            
            return jsonify({
                'format': 'json',
                'structure': 'array',
                'fields': fields,
                'item_count': len(data),
                'sample_data': sample_data,
                'mapping_suggestion': suggest_mapping(fields)
            })
        elif isinstance(data, dict):
            # Single object or object with nested arrays
            # Check for common patterns
            
            # Case 1: Single object with properties
            if not any(isinstance(v, list) for v in data.values()):
                fields = list(data.keys())
                return jsonify({
                    'format': 'json',
                    'structure': 'single_object',
                    'fields': fields,
                    'item_count': 1,
                    'sample_data': [data],
                    'mapping_suggestion': suggest_mapping(fields)
                })
            
            # Case 2: Object with a main array property
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                    items = value
                    fields = list(items[0].keys())
                    sample_data = items[:5] if len(items) > 5 else items
                    
                    return jsonify({
                        'format': 'json',
                        'structure': f'object_with_array_{key}',
                        'main_array_key': key,
                        'fields': fields,
                        'item_count': len(items),
                        'sample_data': sample_data,
                        'mapping_suggestion': suggest_mapping(fields)
                    })
            
            # If we get here, it's a complex structure we can't easily map
            return jsonify({
                'format': 'json',
                'structure': 'complex',
                'fields': list(data.keys()),
                'item_count': 1,
                'sample_data': [data],
                'mapping_suggestion': None,
                'message': 'Complex JSON structure detected. Please review the data and provide custom mapping.'
            })
        else:
            return jsonify({'error': 'Invalid JSON structure'}), 400
    
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON format'}), 400
    except Exception as e:
        return jsonify({'error': f'Error analyzing JSON: {str(e)}'}), 500

def analyze_csv(file):
    """Analyze CSV file and detect schema"""
    try:
        # Read CSV content
        content = file.read().decode('utf-8')
        csv_reader = csv.reader(io.StringIO(content))
        
        # Get header row and data rows
        rows = list(csv_reader)
        if len(rows) < 1:
            return jsonify({'error': 'Empty CSV file'}), 400
        
        header = rows[0]
        data = rows[1:6]  # Get up to 5 rows for sample
        
        # Convert sample data to list of dicts
        sample_data = []
        for row in data:
            if len(row) == len(header):
                sample_data.append(dict(zip(header, row)))
        
        return jsonify({
            'format': 'csv',
            'structure': 'tabular',
            'fields': header,
            'item_count': len(rows) - 1,
            'sample_data': sample_data,
            'mapping_suggestion': suggest_mapping(header)
        })
    
    except Exception as e:
        return jsonify({'error': f'Error analyzing CSV: {str(e)}'}), 500

def suggest_mapping(fields):
    """Suggest mapping between file fields and application model fields"""
    # Define known fields for ingredients
    ingredient_fields = {
        'name': ['name', 'ingredient_name', 'ingredient', 'title'],
        'description': ['description', 'desc', 'details', 'info'],
        'supplier': ['supplier', 'vendor', 'manufacturer', 'source'],
        'supplier_code': ['supplier_code', 'vendor_code', 'product_code', 'sku', 'item_code'],
        'cost_per_unit': ['cost_per_unit', 'cost', 'price', 'unit_cost', 'price_per_unit'],
        'unit_of_measurement': ['unit_of_measurement', 'unit', 'uom', 'measurement_unit'],
        'stock_quantity': ['stock_quantity', 'quantity', 'stock', 'inventory', 'amount'],
        'minimum_stock_threshold': ['minimum_stock_threshold', 'min_stock', 'reorder_point', 'minimum_quantity'],
        'viscosity': ['viscosity', 'thickness'],
        'color': ['color', 'colour'],
        'odor_profile': ['odor_profile', 'scent', 'smell', 'aroma', 'fragrance', 'odor', 'odour'],
        'ifra_restricted': ['ifra_restricted', 'restricted', 'ifra_restriction', 'restriction'],
        'ifra_restriction_details': ['ifra_restriction_details', 'restriction_details', 'ifra_details'],
        'safety_notes': ['safety_notes', 'safety', 'safety_info', 'hazards'],
        'notes': ['notes', 'comments', 'additional_info', 'remarks']
    }
    
    # Initialize mapping with null values
    mapping = {target: None for target in ingredient_fields.keys()}
    
    # For each target field, look for matching source fields
    for target, possible_matches in ingredient_fields.items():
        for field in fields:
            field_lower = field.lower().replace(' ', '_')
            if field_lower in possible_matches or any(match in field_lower for match in possible_matches):
                mapping[target] = field
                break
    
    return mapping

@import_bp.route('/api/import/process', methods=['POST'])
def process_import():
    """Process the import with provided mapping"""
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
    
    data = request.json
    
    # Validate required fields
    required_fields = ['format', 'data', 'mapping']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # In a real implementation, this would process the data and save to database
    # For now, we'll return a mock response
    
    return jsonify({
        'success': True,
        'message': 'Import processed successfully',
        'imported_count': len(data['data']),
        'skipped_count': 0,
        'error_count': 0
    })
