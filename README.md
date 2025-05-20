# Perfumery Ingredient Management WebApp

## 1. Project Overview
The Perfumery Ingredient Management App is a web application designed for individuals or small teams to manage their inventory of perfumery ingredients. [cite: 2] It allows users to track ingredients, categorize them, manage stock levels, and (with planned features) assist in formulation. [cite: 3] The application features a three-column layout for efficient data interaction, data import/export capabilities, and a user-configurable dark mode. [cite: 4]

## 2. Current Status
The application is in a functional state with core CRUD (Create, Read, Update, Delete) operations for ingredients and categories implemented. [cite: 5] Recent development has focused on enhancing the user experience through:
* Robust in-place editing for ingredient details. [cite: 6]
* Real-time, debounced search functionality across multiple ingredient fields. [cite: 7]
* Dynamic adjustment of the number of ingredients displayed per page based on available screen height. [cite: 7]
* A user-toggleable dark mode theme. [cite: 8]
* Improved pagination controls, including styling and placement. [cite: 8]
* Enhanced data display for ingredient notes and amounts/units. [cite: 9]
* Backend search logic expanded to cover more fields. [cite: 9]
The application is runnable, using Flask for the backend and Vue.js for the frontend. [cite: 10]

## 3. Key Features Implemented
* **Ingredient Management:**
    * Add, view, edit (in-place and via modal), and delete ingredients. [cite: 11]
    * Search across ingredient name, unit of measurement, categories, and notes. [cite: 12]
    * Filter ingredients by category. [cite: 12]
    * Sort ingredients by various columns. [cite: 13]
    * Dynamic pagination that adjusts items per page based on screen height. [cite: 13]
    * Batch operations: update notes, update categories, delete selected, delete all. [cite: 14]
* **Category Management:**
    * Add, view, edit, and delete categories. [cite: 15]
    * Support for hierarchical (parent-child) categories. [cite: 15]
    * Option to reset categories to a predefined default set. [cite: 16]
* **Data Import/Export:**
    * Import ingredients from CSV or JSON files. [cite: 17]
    * File analysis with field mapping suggestions. [cite: 18]
    * Keyword-based auto-categorization during import. [cite: 18]
    * Export ingredients to JSON. [cite: 18]
* **User Interface:**
    * Three-column layout: Left sidebar (quick add), Main content (tables/lists), Right sidebar (data management/contextual actions). [cite: 19]
    * Modals for viewing ingredient details, managing categories, importing data, and batch updates. [cite: 20]
    * User-toggleable Dark Mode. [cite: 20]
    * Improved pagination styling and placement. [cite: 21]
* **AI Assist (Placeholder):**
    * UI elements and basic backend routes for planned AI integration (OpenRouter, Gemini, Claude). [cite: 21] Functionality is not yet implemented. [cite: 22]

## 4. Technology Stack
* **Backend:**
    * Python 3.x
    * Flask (including Blueprints)
    * Flask-SQLAlchemy (ORM)
    * SQLite (Database) [cite: 22]
* **Frontend:**
    * Vue.js 3 (via global script `vue.global.js`)
    * Axios (for API calls)
    * Bootstrap 5 (for styling and components)
    * Bootstrap Icons
    * Custom CSS (`src/static/css/styles.css`) [cite: 22]
* **Development Environment:**
    * Standard Python environment with Flask and dependencies. [cite: 23]
    * Frontend assets served by Flask. [cite: 23]

## 5. Setup and Running the Application
1.  **Prerequisites:**
    * Python 3.x [cite: 104]
    * pip (Python package installer) [cite: 104]
2.  **Clone the Repository (if applicable).**
3.  **Create a Virtual Environment (recommended):** [cite: 104]
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
4.  **Install Dependencies:** [cite: 104]
    ```bash
    pip install Flask Flask-SQLAlchemy PyMySQL cryptography SQLAlchemy
    # Ensure requirements.txt is up to date with all dependencies
    # pip install -r requirements.txt
    ```
5.  **Initialize the Database:**
    * The database (`perfumery.db`) should be created automatically in the `src` directory (or instance path if configured) when the app first runs, due to `init_db(app)` and `db.create_all()` in `src/main.py` and `src/models/models.py`. [cite: 105]
    * If you encounter issues, you might need to manually ensure the `src` directory is writable or create an empty `perfumery.db` file. [cite: 106]
6.  **Run the Application:** [cite: 107]
    ```bash
    python src/main.py
    ```
    The application should then be accessible at `http://127.0.0.1:5000/` or `http://0.0.0.0:5000/`. [cite: 107]

## 6. Code Structure Overview

perfumery_app/
├── src/
│   ├── data/
│   │   └── saved_prompts.json
│   ├── models/
│   │   ├── init.py
│   │   ├── models.py
│   │   └── user.py
│   ├── routes/
│   │   ├── init.py
│   │   ├── ai.py
│   │   ├── category.py
│   │   ├── formula.py
│   │   ├── import_bp.py
│   │   ├── ingredient.py
│   │   └── user.py
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css
│   │   ├── js/
│   │   │   └── app.js
│   │   └── index.html
│   ├── templates/
│   │   └── index.html
│   └── main.py
├── requirements.txt
├── todo.md
├── README.md
└── user_guide.md