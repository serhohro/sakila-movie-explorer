Sakila Movie Explorer
Sakila Movie Explorer is a robust, modular console application designed for searching and analyzing the classic Sakila MySQL database.

The project is built with a focus on clean architecture, utilizing MVC (Model-View-Controller) patterns and a Service Layer to ensure low coupling and adherence to SOLID principles.

Core Features
Advanced Search: Search by title, description, genre, year, or actor.

Flexible Filtering: Combine criteria, such as genre + year range.

Pagination: Seamless browsing of results using LIMIT and OFFSET.

Analytics & Logging: Tracks user queries in MongoDB, providing a "Top-5 Popular" and "Recent Searches" history.

Professional UI: Includes a formatted "zebra-striped" table view for better readability.

Project Architecture
The system is designed as a set of decoupled modules coordinated by MovieSearchApp (the Orchestrator):

main.py (Controller): Entry point and diagnostic.

database.py (Model): Encapsulation of MySQL operations.

search.py (Service Layer): Business logic and SQL query construction.

menu.py (View): Interactive navigation and input handling.

formatter.py (View): Data visualization and table formatting.

mongo_logger.py (Service): MongoDB logging and analytics.

paginator.py (Utility): Handling pagination logic.

Technical Highlights
Security: 100% parameterization of SQL queries to prevent SQL injection.

Extensibility: Built using the Open/Closed Principle; new search types can be added without modifying the existing core logic.

Maintainability: Clear separation between data access, business logic, and presentation layers.

Roadmap
Caching: Implementation of Redis to reduce database load.

Testing: Integration of pytest for unit testing.

Web Interface: Migration to FastAPI/Flask for a web-based experience.

Internationalization (i18n): Adding multi-language support.

Installation
Clone the repository.

Ensure you have MySQL (with Sakila DB loaded) and MongoDB instances running.

Configure your connection strings in config.py.

Run the application:
python main.py
