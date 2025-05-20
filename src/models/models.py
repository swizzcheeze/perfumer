from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship

db = SQLAlchemy()

# Association table for many-to-many relationship between Ingredient and Category
ingredient_category = Table(
    'ingredient_category',
    db.metadata,
    Column('ingredient_id', Integer, ForeignKey('ingredient.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('category.id'), primary_key=True)
)

# Association table for many-to-many relationship between Formula and Ingredient with additional data
formula_ingredient = Table(
    'formula_ingredient',
    db.metadata,
    Column('formula_id', Integer, ForeignKey('formula.id'), primary_key=True),
    Column('ingredient_id', Integer, ForeignKey('ingredient.id'), primary_key=True),
    Column('quantity', Float, nullable=False),
    Column('unit', String(20), nullable=False),
    Column('percentage', Float),
    Column('notes', Text)
)

class Ingredient(db.Model):
    """Model for perfumery ingredients"""
    __tablename__ = 'ingredient'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    supplier = Column(String(100))
    supplier_code = Column(String(50))
    cost_per_unit = Column(Float)
    unit_of_measurement = Column(String(20), default='g')
    stock_quantity = Column(Float, default=0)
    minimum_stock_threshold = Column(Float, default=0)
    
    # Physical properties
    viscosity = Column(String(50))
    color = Column(String(50))
    odor_profile = Column(Text)
    
    # Safety information
    ifra_restricted = Column(Boolean, default=False)
    ifra_restriction_details = Column(Text)
    safety_notes = Column(Text)
    
    # Additional fields
    date_added = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text)
    
    # Relationships
    categories = relationship('Category', secondary=ingredient_category, back_populates='ingredients')
    formulas = relationship('Formula', secondary=formula_ingredient, back_populates='ingredients')
    
    def __repr__(self):
        return f'<Ingredient {self.name}>'


class Category(db.Model):
    """Model for ingredient categories"""
    __tablename__ = 'category'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    color_code = Column(String(20))  # For UI display
    icon = Column(String(50))  # Icon identifier
    
    # Self-referential relationship for hierarchical structure
    parent_id = Column(Integer, ForeignKey('category.id'))
    parent = relationship('Category', remote_side=[id], backref='subcategories')
    
    # Relationships
    ingredients = relationship('Ingredient', secondary=ingredient_category, back_populates='categories')
    
    def __repr__(self):
        return f'<Category {self.name}>'


class Formula(db.Model):
    """Model for perfume formulas"""
    __tablename__ = 'formula'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    creator = Column(String(100))
    
    # Version control
    version = Column(String(20), default='1.0')
    is_draft = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Formula details
    total_quantity = Column(Float)
    total_cost = Column(Float)
    notes = Column(Text)
    
    # Relationships
    ingredients = relationship('Ingredient', secondary=formula_ingredient, back_populates='formulas')
    
    def __repr__(self):
        return f'<Formula {self.name} v{self.version}>'


# Function to initialize database
def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
