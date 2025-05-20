# src/routes/category.py
from flask import Blueprint, jsonify, request
from src.models.models import db, Category, ingredient_category # Ensure ingredient_category is imported

# Correct Blueprint definition
# This is the line that defines category_bp. Ensure it's exactly like this.
category_bp = Blueprint('category_bp', __name__)

@category_bp.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all categories with optional parent filter"""
    parent_id = request.args.get('parent_id', type=int)
    query = Category.query
    if parent_id is not None:
        query = query.filter(Category.parent_id == parent_id)
    
    categories = query.order_by(Category.name).all()
    result = [{
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'color_code': category.color_code,
        'icon': category.icon,
        'parent_id': category.parent_id,
        'has_subcategories': len(category.subcategories) > 0,
        'ingredient_count': len(category.ingredients) 
    } for category in categories]
    return jsonify(result)

@category_bp.route('/api/categories/<int:id>', methods=['GET'])
def get_category(id):
    """Get a specific category by ID"""
    category = Category.query.get_or_404(id)
    subcategories = [{'id': subcat.id, 'name': subcat.name} for subcat in category.subcategories]
    result = {
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'color_code': category.color_code,
        'icon': category.icon,
        'parent_id': category.parent_id,
        'subcategories': subcategories,
        'ingredient_count': len(category.ingredients)
    }
    return jsonify(result)

@category_bp.route('/api/categories', methods=['POST'])
def create_category():
    """Create a new category"""
    data = request.json
    if not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400
    # Case-insensitive check for existing category name
    existing = Category.query.filter(Category.name.ilike(data['name'])).first() 
    if existing:
        return jsonify({'error': 'A category with this name already exists'}), 409
    
    category = Category(
        name=data['name'],
        description=data.get('description', ''),
        color_code=data.get('color_code', ''),
        icon=data.get('icon', ''),
        parent_id=data.get('parent_id')
    )
    db.session.add(category)
    db.session.commit()
    return jsonify({
        'id': category.id,
        'name': category.name,
        'message': 'Category created successfully'
    }), 201

@category_bp.route('/api/categories/<int:id>', methods=['PUT'])
def update_category(id):
    """Update an existing category"""
    category = Category.query.get_or_404(id)
    data = request.json
    
    if 'name' in data:
        # Case-insensitive comparison for new name
        if data['name'].lower() != category.name.lower(): 
            existing = Category.query.filter(Category.name.ilike(data['name']), Category.id != id).first()
            if existing:
                return jsonify({'error': 'A category with this name already exists'}), 409
        category.name = data['name']
    
    if 'description' in data:
        category.description = data['description']
    if 'color_code' in data:
        category.color_code = data['color_code']
    if 'icon' in data:
        category.icon = data['icon']
    if 'parent_id' in data: # Allows setting parent_id to null or a valid ID
        # Ensure parent_id is not the category itself
        if data['parent_id'] is not None and int(data['parent_id']) == category.id:
            return jsonify({'error': 'A category cannot be its own parent'}), 400
        category.parent_id = data['parent_id']
    
    db.session.commit()
    return jsonify({
        'id': category.id,
        'name': category.name,
        'message': 'Category updated successfully'
    })

@category_bp.route('/api/categories/<int:id>', methods=['DELETE'])
def delete_category_single(id): # Renamed to avoid conflict if you had another delete_category
    """Delete a category if it has no ingredients."""
    category = Category.query.get_or_404(id)
    if category.ingredients: # Check if there are any ingredients associated
        return jsonify({
            'error': 'Cannot delete category: ingredients are still assigned to it. Please reassign or delete them first.'
        }), 400
    
    # Optional: Re-parent subcategories to this category's parent (or to None if it's a top-level category)
    for subcategory in category.subcategories:
        subcategory.parent_id = category.parent_id # Or None, depending on desired behavior

    db.session.delete(category)
    db.session.commit()
    return jsonify({
        'message': f'Category "{category.name}" deleted successfully.'
    })

@category_bp.route('/api/categories/reset-to-defaults', methods=['POST']) 
def reset_categories_to_defaults():
    """
    Deletes all ingredient-category associations, then all existing categories,
    and finally creates a predefined list of default categories.
    USE WITH EXTREME CAUTION - THIS IS A DESTRUCTIVE OPERATION.
    """
    try:
        # Step 1: Delete all rows from the ingredient_category association table
        db.session.execute(ingredient_category.delete())
        print("Cleared ingredient_category associations.")

        # Step 2: Delete all categories from the Category table
        num_deleted_categories = Category.query.delete()
        print(f"Deleted {num_deleted_categories} old categories.")

        # Step 3: Define and create default categories
        default_categories = [
            {"name": "Citrus", "description": "Bright, zesty, and refreshing notes like lemon, bergamot, orange, grapefruit."},
            {"name": "Woody", "description": "Earthy, warm, and dry notes from woods like sandalwood, cedarwood, vetiver, patchouli."},
            {"name": "Floral", "description": "Notes from flowers like rose, jasmine, lily, tuberose, ylang-ylang."},
            {"name": "Bases & Accords", "description": "Pre-compounded fragrance bases or common accords."},
            {"name": "Spicy", "description": "Warm or fresh spicy notes like cinnamon, clove, pepper, cardamom, ginger."},
            {"name": "Resinous & Balsamic", "description": "Rich, warm, and often sweet notes from resins and balsams like frankincense, myrrh, benzoin, labdanum."},
            {"name": "Fruity", "description": "Sweet and edible notes from fruits other than citrus, e.g., berries, peach, apple."},
            {"name": "Green & Herbal", "description": "Fresh, sharp notes reminiscent of cut grass, leaves, and herbs like basil, mint, lavender."},
            {"name": "Musk", "description": "Soft, warm, animalic or clean skin-like notes, mostly synthetic."},
            {"name": "Amber", "description": "Warm, sweet, often powdery and resinous notes, typically a blend creating an 'amber' accord."},
            {"name": "Aquatic & Ozonic", "description": "Fresh, marine, and airy notes reminiscent of sea breeze or fresh air."},
            {"name": "Gourmand", "description": "Sweet, edible notes reminiscent of desserts and confections like vanilla, chocolate, caramel."},
            {"name": "Aldehydic", "description": "Characteristic fatty, waxy, or sometimes metallic notes from aldehydes."},
            {"name": "Aroma Chemicals", "description": "Single synthetic molecules, specialty bases, or ingredients from specific manufacturers."},
            {"name": "Lactonic", "description": "Creamy, milky, peachy, or coconut-like notes derived from lactones."},
            {"name": "Powdery", "description": "Soft, talc-like, often associated with iris, violet, or certain musks."},
            {"name": "Leathery", "description": "Notes reminiscent of cured hides, suede, or smoky leather."},
            {"name": "Animalic", "description": "Notes with animal-derived characteristics (e.g., musk, civet, castoreum), often synthetic recreations."},
            {"name": "Smoky & Incense", "description": "Notes reminiscent of smoke, burning wood, or traditional incense materials."},
            {"name": "Unique & Niche", "description": "Ingredients with unusual, distinctive, or hard-to-categorize scent profiles."},
            {"name": "Raw Materials", "description": "Basic, unprocessed or minimally processed perfumery inputs."},
            {"name": "Soapy & Clean", "description": "Notes reminiscent of soap, clean laundry, or fresh air."},
            {"name": "Earthy", "description": "Notes reminiscent of soil, damp earth, moss, or forest floor."},
            {"name": "Metallic", "description": "Sharp, cool, and sometimes tangy notes with a metallic character."},
            {"name": "Top Note", "description": "Volatile ingredients that form the initial impression of a fragrance."},
            {"name": "Middle Note", "description": "Ingredients that form the heart of a fragrance, emerging after top notes fade."},
            {"name": "Base Note", "description": "Long-lasting ingredients that form the foundation and dry down of a fragrance."}
        ]

        created_categories_info = []
        for cat_data in default_categories:
            # Check if category already exists (case-insensitive)
            existing_cat = Category.query.filter(Category.name.ilike(cat_data["name"])).first()
            if not existing_cat:
                new_cat = Category(name=cat_data["name"], description=cat_data.get("description", ""))
                db.session.add(new_cat)
                created_categories_info.append({"name": new_cat.name}) # Store info for response
            else:
                print(f"Default category '{cat_data['name']}' already exists, skipping creation.")
        
        db.session.commit() # Commit all changes (deletions and creations)
        print(f"Created {len(created_categories_info)} new default categories if they didn't already exist.")

        return jsonify({
            "message": "Categories have been reset to defaults successfully.",
            "old_categories_deleted": num_deleted_categories,
            "new_categories_created_count": len(created_categories_info),
            "new_categories_list": [c["name"] for c in created_categories_info] # Send back names of created categories
        }), 200

    except Exception as e:
        db.session.rollback() # Rollback in case of any error during the process
        print(f"Error resetting categories: {str(e)}")
        # Log the full traceback here for better debugging in a real scenario
        return jsonify({"error": f"An error occurred while resetting categories: {str(e)}"}), 500
