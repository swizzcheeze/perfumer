from flask import Blueprint, jsonify, request
from sqlalchemy import asc, desc, or_ # Import or_ for combining search conditions
from src.models.models import db, Ingredient, Category, ingredient_category, formula_ingredient 
from datetime import datetime

ingredient_bp = Blueprint('ingredient_bp', __name__)

@ingredient_bp.route('/api/ingredients', methods=['GET'])
def get_ingredients():
    """Get all ingredients with pagination, filtering, and sorting"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    category_id_filter = request.args.get('category_id', type=int) # Renamed to avoid conflict
    search_term = request.args.get('search', '')
    
    sort_by = request.args.get('sort_by', 'name') 
    sort_direction = request.args.get('sort_direction', 'asc')

    query = Ingredient.query
    
    if category_id_filter:
        query = query.join(Ingredient.categories).filter(Category.id == category_id_filter)
    
    if search_term:
        search_pattern = f"%{search_term}%"
        # Conditions for searching in various fields
        # We'll build a list of conditions to be ORed together
        search_conditions = []
        search_conditions.append(Ingredient.name.ilike(search_pattern))
        search_conditions.append(Ingredient.unit_of_measurement.ilike(search_pattern))
        search_conditions.append(Ingredient.notes.ilike(search_pattern))
        
        # To search in category names, we need to join with the Category table
        # Using outerjoin to ensure ingredients are still listed if they match in other fields
        # but might not have categories or categories that match.
        # The distinct() call later will handle potential duplicates if an ingredient matches in multiple ways.
        query = query.outerjoin(Ingredient.categories) 
        search_conditions.append(Category.name.ilike(search_pattern))
        
        query = query.filter(or_(*search_conditions)).distinct()

    # Apply sorting
    if hasattr(Ingredient, sort_by):
        column_to_sort = getattr(Ingredient, sort_by)
        if sort_direction.lower() == 'desc':
            query = query.order_by(desc(column_to_sort))
        else:
            query = query.order_by(asc(column_to_sort))
    else:
        # Default sort if sort_by is invalid or not applicable after joins in a simple way
        query = query.order_by(Ingredient.name) 

    paginated_ingredients = query.paginate(page=page, per_page=per_page, error_out=False)
    
    result = {
        'items': [{
            'id': ingredient.id,
            'name': ingredient.name,
            'description': ingredient.description,
            'supplier': ingredient.supplier,
            'cost_per_unit': ingredient.cost_per_unit,
            'unit_of_measurement': ingredient.unit_of_measurement,
            'stock_quantity': ingredient.stock_quantity,
            'categories': [{'id': cat.id, 'name': cat.name} for cat in ingredient.categories],
            'supplier_code': ingredient.supplier_code,
            'minimum_stock_threshold': ingredient.minimum_stock_threshold,
            'notes': ingredient.notes,
            'date_added': ingredient.date_added.isoformat() if ingredient.date_added else None,
            'last_updated': ingredient.last_updated.isoformat() if ingredient.last_updated else None,
        } for ingredient in paginated_ingredients.items],
        'pagination': {
            'page': paginated_ingredients.page,
            'per_page': paginated_ingredients.per_page,
            'total_pages': paginated_ingredients.pages,
            'total_items': paginated_ingredients.total
        }
    }
    
    return jsonify(result)

# --- Other ingredient routes (GET by ID, POST, PUT, DELETE) remain the same ---
# For brevity, they are not repeated here but should be in your file.

@ingredient_bp.route('/api/ingredients/<int:id>', methods=['GET'])
def get_ingredient(id):
    """Get a specific ingredient by ID"""
    ingredient = Ingredient.query.get_or_404(id)
    result = {
        'id': ingredient.id, 'name': ingredient.name, 'description': ingredient.description,
        'supplier': ingredient.supplier, 'supplier_code': ingredient.supplier_code,
        'cost_per_unit': ingredient.cost_per_unit, 'unit_of_measurement': ingredient.unit_of_measurement,
        'stock_quantity': ingredient.stock_quantity, 'minimum_stock_threshold': ingredient.minimum_stock_threshold,
        'viscosity': ingredient.viscosity, 'color': ingredient.color, 'odor_profile': ingredient.odor_profile,
        'ifra_restricted': ingredient.ifra_restricted, 'ifra_restriction_details': ingredient.ifra_restriction_details,
        'safety_notes': ingredient.safety_notes, 'notes': ingredient.notes,
        'categories': [{'id': cat.id, 'name': cat.name} for cat in ingredient.categories],
        'date_added': ingredient.date_added.isoformat() if ingredient.date_added else None,
        'last_updated': ingredient.last_updated.isoformat() if ingredient.last_updated else None
    }
    return jsonify(result)

@ingredient_bp.route('/api/ingredients', methods=['POST'])
def create_ingredient():
    data = request.json
    if not data.get('name'): return jsonify({'error': 'Name is required'}), 400
    if Ingredient.query.filter_by(name=data['name']).first(): return jsonify({'error': 'Ingredient name already exists'}), 409
    try:
        new_ingredient = Ingredient(
            name=data['name'], description=data.get('description'), supplier=data.get('supplier'),
            supplier_code=data.get('supplier_code'),
            cost_per_unit=float(data['cost_per_unit']) if data.get('cost_per_unit') is not None else None,
            unit_of_measurement=data.get('unit_of_measurement', 'g'),
            stock_quantity=float(data['stock_quantity']) if data.get('stock_quantity') is not None else 0,
            minimum_stock_threshold=float(data.get('minimum_stock_threshold')) if data.get('minimum_stock_threshold') is not None else 0,
            viscosity=data.get('viscosity'), color=data.get('color'), odor_profile=data.get('odor_profile'),
            ifra_restricted=data.get('ifra_restricted', False), ifra_restriction_details=data.get('ifra_restriction_details'),
            safety_notes=data.get('safety_notes'), notes=data.get('notes')
        )
        if 'category_ids' in data and isinstance(data['category_ids'], list):
            categories = Category.query.filter(Category.id.in_(data['category_ids'])).all()
            new_ingredient.categories = categories
        db.session.add(new_ingredient)
        db.session.commit()
        return jsonify({'id': new_ingredient.id, 'name': new_ingredient.name, 'message': 'Ingredient created successfully'}), 201
    except (ValueError, TypeError) as e: db.session.rollback(); return jsonify({'error': f'Invalid data type: {str(e)}'}), 400
    except Exception as e: db.session.rollback(); print(f"Error creating: {str(e)}"); return jsonify({'error': f'Error: {str(e)}'}), 500

@ingredient_bp.route('/api/ingredients/<int:id>', methods=['PUT'])
def update_ingredient(id):
    ingredient = Ingredient.query.get_or_404(id)
    data = request.json
    try:
        if 'name' in data:
            if data['name'] != ingredient.name and Ingredient.query.filter(Ingredient.name == data['name'], Ingredient.id != id).first():
                return jsonify({'error': 'Ingredient name already exists'}), 409
            ingredient.name = data['name']
        for field in ['description','supplier','supplier_code','unit_of_measurement','viscosity','color','odor_profile','ifra_restriction_details','safety_notes','notes']:
            if field in data: setattr(ingredient, field, data[field])
        for field in ['cost_per_unit','stock_quantity','minimum_stock_threshold']:
            if field in data:
                value = data[field]
                setattr(ingredient, field, float(value) if value is not None and str(value).strip() != '' else None)
        if 'ifra_restricted' in data: ingredient.ifra_restricted = data['ifra_restricted']
        if 'category_ids' in data and isinstance(data['category_ids'], list):
            ingredient.categories = [] 
            if data['category_ids']:
                ingredient.categories = Category.query.filter(Category.id.in_(data['category_ids'])).all()
        ingredient.last_updated = datetime.utcnow()
        db.session.commit()
        updated_ingredient = Ingredient.query.get(id) # Re-fetch for updated relationships
        return jsonify({
            'id': updated_ingredient.id, 'name': updated_ingredient.name, 'message': 'Ingredient updated successfully',
            'ingredient': { # Return full object
                'id': updated_ingredient.id, 'name': updated_ingredient.name, 'description': updated_ingredient.description,
                'supplier': updated_ingredient.supplier, 'supplier_code': updated_ingredient.supplier_code,
                'cost_per_unit': updated_ingredient.cost_per_unit, 'unit_of_measurement': updated_ingredient.unit_of_measurement,
                'stock_quantity': updated_ingredient.stock_quantity, 'minimum_stock_threshold': updated_ingredient.minimum_stock_threshold,
                'viscosity': updated_ingredient.viscosity, 'color': updated_ingredient.color, 'odor_profile': updated_ingredient.odor_profile,
                'ifra_restricted': updated_ingredient.ifra_restricted, 'ifra_restriction_details': updated_ingredient.ifra_restriction_details,
                'safety_notes': updated_ingredient.safety_notes, 'notes': updated_ingredient.notes,
                'categories': [{'id': cat.id, 'name': cat.name} for cat in updated_ingredient.categories],
                'date_added': updated_ingredient.date_added.isoformat() if updated_ingredient.date_added else None,
                'last_updated': updated_ingredient.last_updated.isoformat() if updated_ingredient.last_updated else None
            }
        })
    except (ValueError, TypeError) as e: db.session.rollback(); return jsonify({'error': f'Invalid data type: {str(e)}'}), 400
    except Exception as e: db.session.rollback(); print(f"Error updating {id}: {str(e)}"); return jsonify({'error': f'Error: {str(e)}'}), 500

@ingredient_bp.route('/api/ingredients/<int:id>', methods=['DELETE'])
def delete_ingredient_single(id):
    ingredient = Ingredient.query.get_or_404(id)
    try:
        ingredient.categories = [] 
        db.session.execute(formula_ingredient.delete().where(formula_ingredient.c.ingredient_id == id))
        db.session.delete(ingredient)
        db.session.commit()
        return jsonify({'message': f'Ingredient "{ingredient.name}" deleted'}), 200
    except Exception as e: db.session.rollback(); print(f"Error deleting {id}: {str(e)}"); return jsonify({'error': f'Error: {str(e)}'}), 500

@ingredient_bp.route('/api/ingredients/all', methods=['DELETE'])
def delete_all_ingredients_endpoint():
    try:
        db.session.execute(formula_ingredient.delete())
        db.session.execute(ingredient_category.delete())
        num_deleted = db.session.query(Ingredient).delete()
        db.session.commit()
        return jsonify({'message': f'Deleted {num_deleted} ingredients and associations.'}), 200
    except Exception as e: db.session.rollback(); print(f"Error deleting all: {str(e)}"); return jsonify({'error': f'Error: {str(e)}'}), 500

@ingredient_bp.route('/api/ingredients/delete-selected', methods=['POST'])
def delete_selected_ingredients_endpoint():
    data = request.json; ids = data.get('ids')
    if not ids or not isinstance(ids, list) or not all(isinstance(i, int) for i in ids):
        return jsonify({'error': 'Invalid IDs.'}), 400
    if not ids: return jsonify({'message': 'No IDs provided.'}), 200
    try:
        db.session.execute(formula_ingredient.delete().where(formula_ingredient.c.ingredient_id.in_(ids)))
        db.session.execute(ingredient_category.delete().where(ingredient_category.c.ingredient_id.in_(ids)))
        count = Ingredient.query.filter(Ingredient.id.in_(ids)).delete(synchronize_session='fetch') 
        db.session.commit()
        if count == 0 and ids: return jsonify({'message': 'No matching items found for deletion.'}), 200
        return jsonify({'message': f'{count} selected ingredients deleted.'}), 200
    except Exception as e: db.session.rollback(); print(f"Error deleting selected: {str(e)}"); return jsonify({'error': f'Error: {str(e)}'}), 500

@ingredient_bp.route('/api/ingredients/batch-update', methods=['POST'])
def batch_update_ingredients():
    data = request.json; ids = data.get('ids'); notes = data.get('notes'); cat_ids = data.get('category_ids')
    if not ids or not isinstance(ids,list) or not all(isinstance(i,int) for i in ids): return jsonify({'error':'Invalid IDs.'}),400
    if notes is None and cat_ids is None: return jsonify({'error':'No update data.'}),400
    if cat_ids is not None and not isinstance(cat_ids,list): return jsonify({'error':"'category_ids' must be list."}),400
    try:
        updated_count = 0
        ingredients_to_update = Ingredient.query.filter(Ingredient.id.in_(ids)).all()
        if not ingredients_to_update: return jsonify({'message': 'No matching items found.'}), 200
        for ing in ingredients_to_update:
            if notes is not None: ing.notes = notes
            if cat_ids is not None:
                ing.categories = [] 
                if cat_ids: ing.categories = Category.query.filter(Category.id.in_(cat_ids)).all()
            ing.last_updated = datetime.utcnow(); updated_count +=1
        db.session.commit()
        return jsonify({'message': f'Batch updated {updated_count} ingredients.'}), 200
    except Exception as e: db.session.rollback(); print(f"Error batch updating: {str(e)}"); return jsonify({'error': f'Error: {str(e)}'}), 500