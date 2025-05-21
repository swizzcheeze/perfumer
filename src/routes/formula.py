# src/routes/formula.py
from flask import Blueprint, jsonify, request
from src.models.models import db, Formula, Ingredient, formula_ingredient
from datetime import datetime # Ensure datetime is imported

formula_bp = Blueprint('formula', __name__)

@formula_bp.route('/api/formulas', methods=['GET'])
def get_formulas():
    """Get all formulas with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    search_term = request.args.get('search', '')
    
    query = Formula.query
    
    if search_term:
        query = query.filter(Formula.name.ilike(f'%{search_term}%'))
    
    paginated_formulas = query.order_by(Formula.updated_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    result = {
        'items': [{
            'id': formula.id,
            'name': formula.name,
            'description': formula.description,
            'creator': formula.creator,
            'version': formula.version,
            'is_draft': formula.is_draft,
            'created_at': formula.created_at.isoformat() if formula.created_at else None,
            'updated_at': formula.updated_at.isoformat() if formula.updated_at else None,
            'total_quantity': formula.total_quantity,
            'total_cost': formula.total_cost,
            'ingredient_count': db.session.query(formula_ingredient).filter_by(formula_id=formula.id).count() # More direct count
        } for formula in paginated_formulas.items],
        'pagination': {
            'page': paginated_formulas.page,
            'per_page': paginated_formulas.per_page,
            'total_pages': paginated_formulas.pages,
            'total_items': paginated_formulas.total
        }
    }
    
    return jsonify(result)

@formula_bp.route('/api/formulas/<int:id>', methods=['GET'])
def get_formula(id):
    """Get a specific formula by ID"""
    formula = Formula.query.get_or_404(id)
    
    ingredients_data = []
    # Efficiently query association data along with ingredient details
    formula_ingredients_assoc = db.session.query(
        formula_ingredient.c.quantity,
        formula_ingredient.c.unit,
        formula_ingredient.c.percentage,
        formula_ingredient.c.notes,
        Ingredient.id,
        Ingredient.name,
        Ingredient.cost_per_unit,
        Ingredient.unit_of_measurement
    ).join(Ingredient, formula_ingredient.c.ingredient_id == Ingredient.id).filter(
        formula_ingredient.c.formula_id == formula.id
    ).all()

    for assoc in formula_ingredients_assoc:
        cost = None
        if assoc.cost_per_unit is not None and assoc.quantity is not None:
            cost = assoc.cost_per_unit * assoc.quantity
        
        ingredients_data.append({
            'id': assoc.id, # Ingredient ID
            'name': assoc.name, # Ingredient Name
            'quantity': assoc.quantity,
            'unit': assoc.unit,
            'percentage': assoc.percentage,
            'notes': assoc.notes,
            'cost': cost,
            'base_unit_of_measurement': assoc.unit_of_measurement # Original UOM of ingredient
        })
    
    result = {
        'id': formula.id,
        'name': formula.name,
        'description': formula.description,
        'creator': formula.creator,
        'version': formula.version,
        'is_draft': formula.is_draft,
        'created_at': formula.created_at.isoformat() if formula.created_at else None,
        'updated_at': formula.updated_at.isoformat() if formula.updated_at else None,
        'total_quantity': formula.total_quantity,
        'total_cost': formula.total_cost,
        'notes': formula.notes,
        'ingredients': ingredients_data
    }
    
    return jsonify(result)

def _calculate_totals_and_percentages(formula, ingredients_data_list):
    """Helper function to calculate totals and percentages for a formula."""
    current_total_quantity = 0
    current_total_cost = 0
    
    # First pass to calculate total quantity based on provided ingredient data
    for ing_data in ingredients_data_list:
        quantity = ing_data.get('quantity', 0)
        current_total_quantity += quantity
        
        ingredient_model = Ingredient.query.get(ing_data.get('id'))
        if ingredient_model and ingredient_model.cost_per_unit is not None:
            current_total_cost += ingredient_model.cost_per_unit * quantity

    formula.total_quantity = current_total_quantity
    formula.total_cost = current_total_cost
    
    # Prepare ingredient association data with percentages
    processed_ingredients_for_db = []
    for ing_data in ingredients_data_list:
        ingredient_id = ing_data.get('id')
        ingredient_model = Ingredient.query.get(ingredient_id)
        if not ingredient_model:
            continue # Or raise an error

        quantity = ing_data.get('quantity', 0)
        unit = ing_data.get('unit', ingredient_model.unit_of_measurement)
        notes = ing_data.get('notes', '')
        percentage = (quantity / current_total_quantity * 100) if current_total_quantity > 0 else 0
        
        processed_ingredients_for_db.append({
            'ingredient_id': ingredient_id,
            'quantity': quantity,
            'unit': unit,
            'percentage': percentage,
            'notes': notes
        })
    return processed_ingredients_for_db


@formula_bp.route('/api/formulas', methods=['POST'])
def create_formula():
    """Create a new formula"""
    data = request.json
    
    if not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400
    
    try:
        formula = Formula(
            name=data['name'],
            description=data.get('description', ''),
            creator=data.get('creator', ''),
            version=data.get('version', '1.0'),
            is_draft=data.get('is_draft', True),
            notes=data.get('notes', '')
            # total_quantity and total_cost will be set by helper
        )
        db.session.add(formula)
        db.session.flush()  # Get formula ID

        ingredients_input = data.get('ingredients', [])
        if not isinstance(ingredients_input, list):
            return jsonify({'error': 'Ingredients must be a list'}), 400

        processed_ingredients_db_data = _calculate_totals_and_percentages(formula, ingredients_input)
        
        for ing_db_data in processed_ingredients_db_data:
            stmt = formula_ingredient.insert().values(
                formula_id=formula.id,
                ingredient_id=ing_db_data['ingredient_id'],
                quantity=ing_db_data['quantity'],
                unit=ing_db_data['unit'],
                percentage=ing_db_data['percentage'],
                notes=ing_db_data['notes']
            )
            db.session.execute(stmt)
        
        db.session.commit()
        
        return jsonify({
            'id': formula.id,
            'name': formula.name,
            'message': 'Formula created successfully'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@formula_bp.route('/api/formulas/<int:id>', methods=['PUT'])
def update_formula(id):
    """Update an existing formula"""
    formula = Formula.query.get_or_404(id)
    data = request.json
    
    try:
        formula.name = data.get('name', formula.name)
        formula.description = data.get('description', formula.description)
        formula.creator = data.get('creator', formula.creator)
        formula.version = data.get('version', formula.version)
        formula.is_draft = data.get('is_draft', formula.is_draft)
        formula.notes = data.get('notes', formula.notes)
        
        if 'ingredients' in data:
            ingredients_input = data.get('ingredients', [])
            if not isinstance(ingredients_input, list):
                return jsonify({'error': 'Ingredients must be a list'}), 400

            # Remove existing ingredient associations
            db.session.execute(formula_ingredient.delete().where(
                formula_ingredient.c.formula_id == formula.id
            ))
            
            processed_ingredients_db_data = _calculate_totals_and_percentages(formula, ingredients_input)

            for ing_db_data in processed_ingredients_db_data:
                stmt = formula_ingredient.insert().values(
                    formula_id=formula.id, # Use the current formula's ID
                    ingredient_id=ing_db_data['ingredient_id'],
                    quantity=ing_db_data['quantity'],
                    unit=ing_db_data['unit'],
                    percentage=ing_db_data['percentage'],
                    notes=ing_db_data['notes']
                )
                db.session.execute(stmt)
        
        formula.updated_at = datetime.utcnow() # Manually update timestamp
        db.session.commit()
        
        return jsonify({
            'id': formula.id,
            'name': formula.name,
            'message': 'Formula updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@formula_bp.route('/api/formulas/<int:id>', methods=['DELETE'])
def delete_formula(id):
    """Delete a formula"""
    formula = Formula.query.get_or_404(id)
    
    try:
        # Also delete associations from formula_ingredient table
        db.session.execute(formula_ingredient.delete().where(
            formula_ingredient.c.formula_id == id
        ))
        db.session.delete(formula)
        db.session.commit()
        
        return jsonify({
            'message': f'Formula "{formula.name}" deleted successfully' # Corrected variable name
        }), 200 # Changed from jsonify(message=...) to jsonify({...}) for consistency
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@formula_bp.route('/api/formulas/<int:id>/duplicate', methods=['POST'])
def duplicate_formula(id):
    """Duplicate an existing formula"""
    original_formula = Formula.query.get_or_404(id)
    
    try:
        new_formula = Formula(
            name=f"{original_formula.name} (Copy)",
            description=original_formula.description,
            creator=original_formula.creator, # Or set to current user if auth is implemented
            version="1.0", # Reset version or increment original_formula.version
            is_draft=True,
            notes=original_formula.notes,
            total_quantity=original_formula.total_quantity, # Will be recalculated if ingredients are deeply copied
            total_cost=original_formula.total_cost
        )
        db.session.add(new_formula)
        db.session.flush() # Get new_formula.id

        # Copy ingredients
        original_ingredients_assoc = db.session.query(formula_ingredient).filter_by(formula_id=original_formula.id).all()
        
        for assoc in original_ingredients_assoc:
            stmt = formula_ingredient.insert().values(
                formula_id=new_formula.id,
                ingredient_id=assoc.ingredient_id,
                quantity=assoc.quantity,
                unit=assoc.unit,
                percentage=assoc.percentage,
                notes=assoc.notes
            )
            db.session.execute(stmt)
            
        db.session.commit()
        return jsonify({
            'id': new_formula.id,
            'name': new_formula.name,
            'message': 'Formula duplicated successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Placeholder for formula export - can be expanded
@formula_bp.route('/api/formulas/<int:id>/export', methods=['GET'])
def export_formula(id):
    """Export a formula (simple JSON for now)"""
    formula = Formula.query.get_or_404(id)
    formula_data = get_formula(id).json # Leverage existing get_formula which returns jsonify
    
    # For a text format, you'd build a string here
    # For CSV, you'd use the csv module
    
    return jsonify(formula_data)