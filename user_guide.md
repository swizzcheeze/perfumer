# Perfumery Ingredient Inventory Management WebApp - User Guide

## Overview

This application is a comprehensive inventory management system for perfumery ingredients, allowing users to track, categorize, and create formulas with their ingredients. It features a user-friendly interface with advanced features like pagination, resizable tables, smart import functionality, and AI assistance for perfumery and scent creation.

## Features

### Ingredient Inventory Management
- Store and manage perfumery ingredients with detailed properties
- Track ingredient quantities, suppliers, costs, and other relevant metrics
- Search and filter ingredients by name or category
- Complete CRUD operations for all ingredients

### Category Management
- Hierarchical category system for organizing ingredients
- Create, edit, and delete categories
- Assign ingredients to multiple categories
- Category-based filtering and searching

### Formula Creator
- Create perfume formulas using inventory ingredients
- Specify ingredient quantities and proportions
- Save, edit, and duplicate formulas
- Calculate formula costs based on ingredient prices

### Smart Import
- Import ingredient data from JSON and CSV files
- Intelligent schema detection to handle various file formats
- Mapping capabilities to align imported data with the application's data model
- Preview and validation of imported data

### AI Playground
- Integration with OpenRouter, Gemini, and Claude AI services
- Customizable system prompts for perfumery assistance
- Save and reuse successful prompts
- Secure API key management

## Getting Started

### Installation

1. Clone the repository
2. Set up a virtual environment:
   ```
   cd perfumery_app
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Initialize the database:
   ```
   # The database is automatically initialized when the app starts
   ```
5. Run the application:
   ```
   python src/main.py
   ```
6. Access the application at http://localhost:5000

### Database Configuration

The application uses MySQL by default. You can configure the database connection in `src/main.py`:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USERNAME', 'root')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'mydb')}"
```

You can override these settings using environment variables:
- DB_USERNAME
- DB_PASSWORD
- DB_HOST
- DB_PORT
- DB_NAME

## Using the Application

### Ingredient Management

1. Navigate to the "Ingredients" page
2. Use the search and filter options to find specific ingredients
3. Click "Add Ingredient" to create a new ingredient
4. Use the action buttons to view, edit, or delete ingredients

### Category Management

1. Navigate to the "Categories" page
2. Browse the category hierarchy in the left panel
3. Click on a category to view its details
4. Use the buttons to add, edit, or delete categories

### Formula Creation

1. Navigate to the "Formulas" page
2. Click "Create Formula" to start a new formula
3. Add ingredients and specify quantities
4. Save your formula when complete

### Smart Import

1. Navigate to the "Import" page
2. Upload a JSON or CSV file containing ingredient data
3. Review the detected schema and sample data
4. Map the fields from your file to the application's fields
5. Click "Process Import" to import the data

### AI Playground

1. Navigate to one of the AI playground pages (OpenRouter, Gemini, or Claude)
2. Enter your API key when prompted (or in the API Settings page)
3. Customize the system prompt if desired
4. Enter your perfumery question or request
5. Click "Generate" to get AI assistance
6. Save useful prompts for future use

## API Endpoints

The application provides the following API endpoints:

### Ingredients
- GET /api/ingredients - List all ingredients (with pagination)
- GET /api/ingredients/:id - Get a specific ingredient
- POST /api/ingredients - Create a new ingredient
- PUT /api/ingredients/:id - Update an ingredient
- DELETE /api/ingredients/:id - Delete an ingredient

### Categories
- GET /api/categories - List all categories
- GET /api/categories/:id - Get a specific category
- POST /api/categories - Create a new category
- PUT /api/categories/:id - Update a category
- DELETE /api/categories/:id - Delete a category

### Formulas
- GET /api/formulas - List all formulas (with pagination)
- GET /api/formulas/:id - Get a specific formula
- POST /api/formulas - Create a new formula
- PUT /api/formulas/:id - Update a formula
- DELETE /api/formulas/:id - Delete a formula

### Import
- POST /api/import/analyze - Analyze an uploaded file
- POST /api/import/process - Process an import with mapping

### AI
- GET /api/ai/models - Get available AI models
- GET /api/ai/default-prompts - Get default system prompts
- GET /api/ai/saved-prompts - Get saved prompts
- POST /api/ai/saved-prompts - Save a new prompt
- PUT /api/ai/saved-prompts/:id - Update a saved prompt
- DELETE /api/ai/saved-prompts/:id - Delete a saved prompt
- POST /api/ai/openrouter/generate - Generate text with OpenRouter
- POST /api/ai/gemini/generate - Generate text with Gemini
- POST /api/ai/claude/generate - Generate text with Claude

## Security Considerations

- API keys for AI services are stored securely in the browser (encrypted)
- Users can choose not to store API keys and enter them only when needed
- The application validates all input to prevent injection attacks

## Customization

### Adding New Features

The application is built with a modular structure that makes it easy to add new features:

1. Add new models in `src/models/models.py`
2. Create new routes in `src/routes/`
3. Register new blueprints in `src/main.py`
4. Add new UI components in `src/templates/index.html` and `src/static/js/app.js`

### Styling

The application uses Bootstrap 5 for styling. You can customize the appearance by modifying:

- `src/static/css/styles.css` - Custom CSS styles
- Bootstrap classes in `src/templates/index.html`

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check that MySQL is running
   - Verify database credentials in environment variables or `src/main.py`

2. **Import Errors**
   - Ensure your JSON or CSV file has a consistent structure
   - Check that the file is properly formatted

3. **AI Integration Issues**
   - Verify that your API keys are correct
   - Check network connectivity to the AI service providers

## Support

For additional support or feature requests, please contact the development team.
