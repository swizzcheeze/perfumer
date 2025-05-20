from flask import Blueprint, jsonify, request
from src.models.models import db, Formula, Ingredient, formula_ingredient

formula_bp = Blueprint('formula', __name__)

@formula_bp.route('/api/formulas', methods=['GET'])
def get_formulas():
    """Get all formulas with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Get optional filter parameters
    search_term = request.args.get('search', '')
    
    query = Formula.query
    
    # Apply filters if provided
    if search_term:
        query = query.filter(Formula.name.ilike(f'%{search_term}%'))
    
    # Execute paginated query
    paginated_formulas = query.order_by(Formula.updated_at.desc()).paginate(page=page, per_page=per_page)
    
    # Format response
    result = {
        'items': [{
            'id': formula.id,
            'name': formula.name,
            'description': formula.description,
            'creator': formula.creator,
            'version': formula.version,
            'is_draft': formula.is_draft,
            'created_at': formula.created_at.isoformat(),
            'updated_at': formula.updated_at.isoformat(),
            'total_quantity': formula.total_quantity,
            'total_cost': formula.total_cost,
            'ingredient_count': len(formula.ingredients)
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
    
    # Get formula ingredients with their details
    ingredients = []
    for ingredient in formula.ingredients:
        # Get the association data (quantity, unit, etc.)
        assoc = db.session.query(formula_ingredient).filter_by(
            formula_id=formula.id, 
            ingredient_id=ingredient.id
        ).first()
        
        ingredients.append({
            'id': ingredient.id,
            'name': ingredient.name,
            'quantity': assoc.quantity,
            'unit': assoc.unit,
            'percentage': assoc.percentage,
            'notes': assoc.notes,
            'cost': ingredient.cost_per_unit * assoc.quantity if ingredient.cost_per_unit else None
        })
    
    # Format response
    result = {
        'id': formula.id,
        'name': formula.name,
        'description': formula.description,
        'creator': formula.creator,
        'version': formula.version,
        'is_draft': formula.is_draft,
        'created_at': formula.created_at.isoformat(),
        'updated_at': formula.updated_at.isoformat(),
        'total_quantity': formula.total_quantity,
        'total_cost': formula.total_cost,
        'notes': formula.notes,
        'ingredients': ingredients
    }
    
    return jsonify(result)

@formula_bp.route('/api/formulas', methods=['POST'])
def create_formula():
    """Create a new formula"""
    data = request.json
    
    # Validate required fields
    if not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400
    
    # Create new formula
    formula = Formula(
        name=data['name'],
        description=data.get('description', ''),
        creator=data.get('creator', ''),
        version=data.get('version', '1.0'),
        is_draft=data.get('is_draft', True),
        total_quantity=data.get('total_quantity', 0),
        total_cost=data.get('total_cost', 0),
        notes=data.get('notes', '')
    )
    
    db.session.add(formula)
    db.session.flush()  # Get formula ID without committing
    
    # Add ingredients if provided
    if 'ingredients' in data and isinstance(data['ingredients'], list):
        total_cost = 0
        total_quantity = 0
        
        for ingredient_data in data['ingredients']:
            ingredient_id = ingredient_data.get('id')
            ingredient = Ingredient.query.get(ingredient_id)
            
            if ingredient:
                quantity = ingredient_data.get('quantity', 0)
                unit = ingredient_data.get('unit', ingredient.unit_of_measurement)
                percentage = ingredient_data.get('percentage')
                notes = ingredient_data.get('notes', '')
                
                # Add to formula with association data
                stmt = formula_ingredient.insert().values(
                    formula_id=formula.id,
                    ingredient_id=ingredient.id,
                    quantity=quantity,
                    unit=unit,
                    percentage=percentage,
                    notes=notes
                )
                db.session.execute(stmt)
                
                # Update totals
                total_quantity += quantity
                if ingredient.cost_per_unit:
                    total_cost += ingredient.cost_per_unit * quantity
        
        # Update formula totals
        formula.total_quantity = total_quantity
        formula.total_cost = total_cost
    
    db.session.commit()
    
    return jsonify({
        'id': formula.id,
        'name': formula.name,
        'message': 'Formula created successfully'
    }), 201

@formula_bp.route('/api/formulas/<int:id>', methods=['PUT'])
def update_formula(id):
    """Update an existing formula"""
    formula = Formula.query.get_or_404(id)
    data = request.json
    
    # Update fields if provided
    if 'name' in data:
        formula.name = data['name']
    if 'description' in data:
        formula.description = data['description']
    if 'creator' in data:
        formula.creator = data['creator']
    if 'version' in data:
        formula.version = data['version']
    if 'is_draft' in data:
        formula.is_draft = data['is_draft']
    if 'notes' in data:
        formula.notes = data['notes']
    
    # Update ingredients if provided
    if 'ingredients' in data and isinstance(data['ingredients'], list):
        # Remove existing ingredient associations
        db.session.execute(formula_ingredient.delete().where(
            formula_ingredient.c.formula_id == formula.id
        ))
        
        total_cost = 0
        total_quantity = 0
        
        for ingredient_data in data['ingredients']:
            ingredient_id = ingredient_data.get('id')
            ingredient = Ingredient.query.get(ingredient_id)
            
            if ingredient:
                quantity = ingredient_data.get('quantity', 0)
                unit = ingredient_data.get('unit', ingredient.unit_of_measurement)
                percentage = ingredient_data.get('percentage')
                notes = ingredient_data.get('notes', '')
                
                # Add to formula with association data
                stmt = formula_ingredient.insert().values(
                    formula_id=formula.id,
                    ingredient_id=ingredient.id,
                    quantity=quantity,
                    unit=unit,
                    percentage=percentage,
                    notes=notes
                )
                db.session.execute(stmt)
                
                # Update totals
                total_quantity += quantity
                if ingredient.cost_per_unit:
                    total_cost += ingredient.cost_per_unit * quantity
        
        # Update formula totals
        formula.total_quantity = total_quantity
        formula.total_cost = total_cost
    
    db.session.commit()
    
    return jsonify({
        'id': formula.id,
        'name': formula.name,
        'message': 'Formula updated successfully'
    })

@formula_bp.route('/api/formulas/<int:id>', methods=['DELETE'])
def delete_formula(id):
    """Delete a formula"""
    formula = Formula.query.get_or_404(id)
    
    db.session.delete(formula)
    db.session.commit()
    
    return jsonify({
        'message': f'Formula {formula.name} deleted successfully'
    })
