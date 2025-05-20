# Perfumery Ingredient Inventory Management WebApp - Detailed Requirements

## Application Overview
This web application will serve as a comprehensive inventory management system for perfumery ingredients, allowing users to track, categorize, and create formulas with their ingredients. [cite: 3] The application will also integrate with AI services (OpenRouter, Gemini, and Claude) to assist users in formula creation and ingredient management. [cite: 21] It features a three-column layout, data import/export, and a user-configurable dark mode. [cite: 4]

## Core Features

### Ingredient Inventory Management
- Store and manage perfumery ingredients with detailed properties (Add, view, edit (in-place and via modal), and delete). [cite: 11]
- Track ingredient quantities, suppliers, costs, and other relevant metrics.
- Support for ingredient search (across name, unit of measurement, categories, notes) and filtering by category. [cite: 12]
- CRUD operations for all ingredients. [cite: 5]
- Sort ingredients by various columns. [cite: 13]
- Batch operations: update notes, update categories, delete selected, delete all. [cite: 14]

### Smart Import Functionality
- Support for importing ingredient data from JSON and CSV files. [cite: 17]
- Intelligent schema detection to handle various file formats and provide field mapping suggestions. [cite: 18]
- Keyword-based auto-categorization during import. [cite: 18]
- Mapping capabilities to align imported data with the application's data model.
- Validation of imported data to ensure integrity (Further enhancement needed [cite: 90]).
- Preview of data before final import.

### Category Management
- Hierarchical category system for organizing ingredients (parent-child). [cite: 15]
- Ability to create, edit, and delete categories. [cite: 15]
- Assignment of ingredients to multiple categories.
- Category-based filtering and searching. [cite: 12]
- Option to reset categories to a predefined default set. [cite: 16]

### Formula Creator (Partially Implemented - UI/Basic Structure)
- Interface for creating perfume formulas using inventory ingredients. [cite: 88]
- Support for specifying ingredient quantities and proportions. [cite: 89]
- Formula saving, editing, and duplication. [cite: 89]
- Formula export functionality.
- Calculation of formula costs based on ingredient prices. [cite: 90]

### AI Integration (Placeholders and Basic Backend Routes) [cite: 21]
- Integration with OpenRouter API for accessing multiple AI models. [cite: 86]
- Integration with Google's Gemini API for formula assistance. [cite: 86]
- Integration with Anthropic's Claude API for ingredient analysis. [cite: 86]
- Secure API key management for users (UI/Logic needed).
- Option to store encrypted API keys or use session-only keys.
- System prompt section for each AI service customized for perfumery. [cite: 88]
- Interactive AI playground for perfumery and scent creation (UI/Logic needed). [cite: 87]
- Ability to save and reuse successful prompts. [cite: 88]

## User Interface Requirements

### General UI
- Responsive design for desktop and mobile devices.
- Clean, intuitive interface with consistent styling.
- User-toggleable Dark/light mode toggle. [cite: 8, 20]
- Three-column layout: Left sidebar (quick add), Main content (tables/lists), Right sidebar (data management/contextual actions). [cite: 19]
- Modals for viewing ingredient details, managing categories, importing data, and batch updates. [cite: 20]

### Tables and Data Display
- Paginated tables for ingredient listings. [cite: 8, 13]
- Dynamic adjustment of items per page based on available screen height. [cite: 7, 13]
- Resizable table columns to customize view (state not persisted [cite: 103]).
- Sortable columns for better data organization. [cite: 13]
- Sticky scrolling for headers and important UI elements.
- Filtering and search capabilities within tables (real-time, debounced search). [cite: 7, 12]
- Enhanced data display for ingredient notes and amounts/units. [cite: 9]

### Data Entry and Forms
- User-friendly forms for adding and editing ingredients (including robust in-place editing). [cite: 6]
- Form validation to ensure data integrity (Further enhancement needed [cite: 91]).
- Autocomplete functionality where appropriate.

## Technical Requirements

### Database
- Relational database (SQLite) to store ingredients, categories, and formulas. [cite: 22]
- Efficient query design for performance optimization.
- Data backup and recovery mechanisms.

### Security
- Basic authentication system (Future requirement if multi-user [cite: 93]).
- Input validation to prevent injection attacks (Ongoing enhancement [cite: 90, 91]).
- CSRF protection.
- Secure storage of user API keys (encrypted) (Planned).
- No server-side storage of API keys (client-side only option available) (Planned).

### Performance
- Optimized for handling large ingredient databases.
- Efficient pagination and data loading. [cite: 7, 13]
- Responsive UI regardless of data volume.

## Data Models

### Ingredient Model
- Name
- Description
- Category/Categories
- Supplier information
- Supplier Code
- Cost information (Cost per unit)
- Physical properties (e.g., viscosity, color, odor profile)
- Safety information (IFRA restrictions, safety notes)
- Stock quantity
- Unit of measurement
- Minimum stock threshold
- Notes/comments
- Date Added
- Last Updated

### Category Model
- Name
- Description
- Parent category (for hierarchical structure) [cite: 15]
- Color/icon for visual identification

### Formula Model (Basic)
- Name
- Description
- Creator
- Creation date
- Last modified date
- Ingredients list with proportions
- Total cost calculation
- Notes/comments
- Version information