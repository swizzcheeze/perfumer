# Perfumery Ingredient Inventory Management WebApp - Detailed Requirements

## Application Overview
This web application will serve as a comprehensive inventory management system for perfumery ingredients, allowing users to track, categorize, and create formulas with their ingredients. The application will also integrate with AI services (OpenRouter, Gemini, and Claude) to assist users in formula creation and ingredient management.

## Core Features

### Ingredient Inventory Management
- Store and manage perfumery ingredients with detailed properties
- Track ingredient quantities, suppliers, costs, and other relevant metrics
- Support for ingredient search and filtering
- CRUD operations for all ingredients

### Smart Import Functionality
- Support for importing ingredient data from JSON and CSV files
- Intelligent schema detection to handle various file formats
- Mapping capabilities to align imported data with the application's data model
- Validation of imported data to ensure integrity
- Preview of data before final import

### Category Management
- Hierarchical category system for organizing ingredients
- Ability to create, edit, and delete categories
- Assignment of ingredients to multiple categories
- Category-based filtering and searching

### Formula Creator
- Interface for creating perfume formulas using inventory ingredients
- Support for specifying ingredient quantities and proportions
- Formula saving, editing, and duplication
- Formula export functionality
- Calculation of formula costs based on ingredient prices

## User Interface Requirements

### General UI
- Responsive design for desktop and mobile devices
- Clean, intuitive interface with consistent styling
- Dark/light mode toggle

### Tables and Data Display
- Paginated tables for ingredient listings
- Resizable table columns to customize view
- Sortable columns for better data organization
- Sticky scrolling for headers and important UI elements
- Filtering and search capabilities within tables

### Data Entry and Forms
- User-friendly forms for adding and editing ingredients
- Form validation to ensure data integrity
- Autocomplete functionality where appropriate

## Technical Requirements

### Database
- Relational database to store ingredients, categories, and formulas
- Efficient query design for performance optimization
- Data backup and recovery mechanisms

### Security
- Basic authentication system
- Input validation to prevent injection attacks
- CSRF protection
- Secure storage of user API keys (encrypted)
- No server-side storage of API keys (client-side only option available)

### Performance
- Optimized for handling large ingredient databases
- Efficient pagination and data loading
- Responsive UI regardless of data volume

### AI Integration
- Integration with OpenRouter API for accessing multiple AI models
- Integration with Google's Gemini API for formula assistance
- Integration with Anthropic's Claude API for ingredient analysis
- Secure API key management for users
- Option to store encrypted API keys or use session-only keys
- System prompt section for each AI service customized for perfumery
- Interactive AI playground for perfumery and scent creation
- Ability to save and reuse successful prompts

## Data Models

### Ingredient Model
- Name
- Description
- Category/Categories
- Supplier information
- Cost information
- Physical properties (e.g., viscosity, color, odor profile)
- Safety information
- Stock quantity
- Unit of measurement
- Minimum stock threshold
- IFRA restrictions (if applicable)
- Notes/comments

### Category Model
- Name
- Description
- Parent category (for hierarchical structure)
- Color/icon for visual identification

### Formula Model
- Name
- Description
- Creator
- Creation date
- Last modified date
- Ingredients list with proportions
- Total cost calculation
- Notes/comments
- Version information
