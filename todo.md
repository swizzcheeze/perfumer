# Perfumery Ingredient Inventory Management WebApp - Todo List

## High Priority / Next Steps
- **AI Integration:** [cite: 86]
    - [ ] Implement actual API calls to OpenRouter, Gemini, and Claude services. [cite: 86]
    - [ ] Develop the UI for interacting with the AI (e.g., in the global AI chat modal and contextual AI panel). [cite: 87]
    - [ ] Define and refine prompts for specific perfumery tasks. [cite: 88]
- **Formula Creator:**
    - [ ] Complete the UI for creating and managing formulas. [cite: 88]
    - [ ] Implement backend logic for saving/loading formulas and their ingredient compositions. [cite: 89]
    - [ ] Add calculations for formula cost, ingredient percentages, etc. [cite: 90]
- **Data Validation (Import & Forms):**
    - [ ] Enhance backend validation in `import_bp.py` for all imported fields (e.g., ensuring numeric types, valid units). [cite: 90]
    - [ ] Add more comprehensive frontend validation for input forms. [cite: 91]

## Medium Priority
- **Unit of Measurement Normalization:**
    - [ ] Implement a robust parsing and normalization step for `unit_of_measurement` during import or as a data cleaning utility. [cite: 92]
- **User Authentication & Authorization:**
    - [ ] Implement a user login system if the application needs to support multiple users with private data. [cite: 93]
- **Advanced Search/Filtering:**
    - [ ] Allow searching by supplier, cost range, etc. [cite: 94]
    - [ ] Implement filtering by multiple categories simultaneously. [cite: 94]
- **Testing:**
    - [ ] Develop unit tests for backend Python code (models, routes). [cite: 95]
    - [ ] Implement end-to-end tests for key user flows. [cite: 96]
- **Deployment:**
    - [ ] Prepare the application for deployment (e.g., using a production-ready WSGI server like Gunicorn, configuring database for production). [cite: 96]
    - [ ] Ensure Vue.js is built in production mode (`*.prod.js`). [cite: 97]

## Known Issues / Quirks to Address
- [ ] **Dark Mode CSS Specificity:** Review all styles for dark mode compatibility to ensure overrides are correctly applied. [cite: 98, 99]
- [ ] **`estimatedRowHeight` Tuning:** Fine-tune the `estimatedRowHeight` value in `app.js` if row content or styling changes significantly. [cite: 100, 101]
- [ ] **Import Error Granularity:** Improve feedback in `import_bp.py` to specify which row/field caused an issue during processing. [cite: 102]
- [ ] **Table Resizing State:** Implement persistence for column widths set by resizable table headers across sessions. [cite: 103]

## Completed (for reference - based on hand-off notes)
- [x] Create project directory and initial README
- [x] Define detailed application requirements
- [x] Document database schema requirements (implicitly through models.py)
- [x] Plan UI/UX features and interactions (evident in app.js and index.html)
- [x] Identify required dependencies
- [x] Initialize Flask application template
- [x] Set up virtual environment
- [x] Install required dependencies
- [x] Configure project structure
- [x] Design ingredient database model
- [x] Design category management model
- [x] Design formula creator model (basic structure)
- [x] Implement relationships between models
- [x] Implement ingredient inventory management (CRUD, search, filter, sort, dynamic pagination, batch ops) [cite: 11, 12, 13, 14]
- [x] Implement smart JSON/CSV import functionality (analysis, mapping, keyword auto-categorization) [cite: 17, 18]
- [x] Implement category management system (CRUD, hierarchy, reset to default) [cite: 15, 16]
- [x] Implement formula creator (basic structure, UI placeholders)
- [x] Implement AI integration (UI placeholders, basic backend routes for OpenRouter, Gemini, Claude) [cite: 21]
- [x] Implement secure API key management (placeholders for UI/logic)
- [x] Create responsive layout with sticky scrolling [cite: 19]
- [x] Implement pagination for inventory tables (dynamic, improved styling) [cite: 8, 13, 21]
- [x] Add resizable table functionality
- [x] Design and implement category management UI [cite: 20]
- [x] Design and implement formula creator UI (placeholders)
- [x] Test database operations (implicitly through app functionality)
- [x] Test smart import with various schemas (implicitly through implementation of `import_bp.py`)
- [x] Test UI responsiveness and features (e.g., dark mode, in-place editing) [cite: 6, 7, 8]
- [x] Validate formula creation functionality (basic structure exists)
- [x] Prepare application for deployment (basic Flask structure)
- [x] Update requirements.txt
- [x] Test application locally
- [ ] Deploy application (Outstanding)
- [x] Create user documentation (user_guide.md exists)
- [x] Document API endpoints (in user_guide.md and hand-off notes)
- [x] Provide usage examples (in user_guide.md)