# src/main.py
from flask import Flask, render_template, send_from_directory
import os
import sys

# Add parent directory to path to fix import issues when running directly
# This line assumes main.py is in a 'src' subdirectory of your project root.
# If main.py is at D:\perfumery_app\src\main.py, this adds D:\perfumery_app to sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.models import init_db
from src.routes.ingredient import ingredient_bp
from src.routes.category import category_bp # This is the import causing the error
from src.routes.formula import formula_bp
from src.routes.import_bp import import_bp # Assuming this is your import blueprint
from src.routes.ai import ai_bp

# Create Flask app
app = Flask(__name__)

# Configure app
app.config['SECRET_KEY'] = os.urandom(24)

# Use SQLite instead of MySQL for easier local development
# Ensure the database file will be created in an appropriate location.
# For instance, instance_path could be a good place.
# app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(app.instance_path, "perfumery.db")}'
# For simplicity, using a relative path (will create db in the directory where script is run, or instance folder if configured)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///perfumery.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ensure instance folder exists if using it for SQLite
# try:
#     os.makedirs(app.instance_path)
# except OSError:
#     pass

# Initialize database
init_db(app)

# Register blueprints
app.register_blueprint(ingredient_bp)
app.register_blueprint(category_bp) # This is the registration
app.register_blueprint(formula_bp)
app.register_blueprint(import_bp) # Register the import blueprint
app.register_blueprint(ai_bp)

# Serve static files (Vue frontend)
@app.route('/')
def index():
    # Renders your main HTML file that hosts the Vue app
    return render_template('index.html')

@app.route('/<path:path>')
def serve_static(path):
    # This route is generally not needed if Flask's static_folder is configured correctly
    # and your index.html correctly references static files (e.g., via url_for).
    # However, if you have specific needs for serving other static paths, it can be kept.
    # By default, Flask serves from a 'static' folder relative to the app's root or blueprint.
    # For a single 'static' folder at the app root: app = Flask(__name__, static_folder='static')
    # Then {{ url_for('static', filename='js/app.js') }} works.
    # This custom route might be for files directly under 'static' not fitting url_for patterns.
    return send_from_directory('static', path)

if __name__ == '__main__':
    # Ensures the app runs only when the script is executed directly
    app.run(host='0.0.0.0', port=5000, debug=True)
