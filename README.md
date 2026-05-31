# 🎬 Sakila Movie Explorer

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg?style=flat-square&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-4.4+-green.svg?style=flat-square&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![License](https://img.shields.io/badge/License-MIT-brightgreen.svg?style=flat-square)](LICENSE)

An advanced console client application for movie search, navigation, and analytics based on the classic **Sakila** sample database schema. The project is built at the intersection of relational and NoSQL technologies, utilizing a hybrid data storage architecture (MySQL + MongoDB) and a clean modular design.

**Author:** Serhiy Hromyko  
**GitHub Repository:** [https://github.com/serhohro/sakila-movie-explorer](https://github.com/serhohro/sakila-movie-explorer)

---

## 🚀 Key Features

* **Hybrid Data Storage:** The main movie catalog is powered by the high-performance **MySQL** DBMS, while search activity history and aggregated analytics are logged in **MongoDB**.
* **Flexible Search Engine:** Allows users to search for movies using multiple criteria:
    * By title (with automatic whitespace trimming).
    * By description and plot keywords.
    * By genre via an interactive catalog.
    * By actor's first or last name (with an intermediate step to choose a specific actor).
    * By release year (supports exact year, ranges like `1995-2005`, or space-separated lists of years).
    * Combined search (Selected Genre + Year Range).
* **Advanced CLI UX:**
    * *Pagination:* Page-by-page output for long lists (10 records per page) with quick page jumps and forward/backward navigation.
    * *Formatting:* Adaptive pseudographic tables featuring automatic text wrapping, column alignment, and "zebra" row coloring.
    * *Interactive Menu:* A modular console menu with automatic item numbering and input validation.
* **Fault Tolerance & Diagnostics:** A pre-launch verification module (`SystemChecker`) with a visualized progress bar tests the physical availability of MySQL and MongoDB servers before the application starts, preventing runtime crashes.
* **Built-in Analytics:** View recent search queries and display the top 5 most popular search directions powered by MongoDB aggregation pipelines.

---

## 🏗 Project Architecture & Module Structure

The project is designed with a strict **Separation of Concerns**. Modules are isolated from each other and easily scalable:

* `main.py` — The entry point of the application. It initializes the configuration, runs pre-launch diagnostics, and transfers control to the main execution loop.
* `movie_app.py` (`MovieSearchApp`) — The core application controller. It orchestrates the logic between user input, search services, and the analytics logger.
* `system_checker.py` (`SystemChecker`) — The technical environment verification module that checks database connections and statuses.
* `sakila_manager.py` (`SakilaManager`) — The schema state manager. It verifies the presence and readiness of the relational schema on the MySQL server.
* `database.py` (`DataBase`) — The Data Access Layer (DAL). A wrapper over `mysql.connector` featuring automatic tuple-to-dictionary mapping and **SQL injection** protection.
* `search.py` (`SearchService`) — The business logic layer. Contains optimized complex SQL queries using `LEFT JOIN`, `GROUP_CONCAT`, and custom sorting rules.
* `paginator.py` (`Paginator`) — A universal pagination controller for navigating large datasets without overloading the RAM.
* `formatter.py` (`Formatter`) — The View component. Formats raw data structures into clean text tables with ANSI color support.
* `mongo_logger.py` (`MongoLogger`) — The analytical logger. It translates technical query parameters into human-readable logs and generates aggregated reports.
* `menu.py` (`Menu`) — An abstraction layer for dynamically building command-line interfaces.

---

## 🛠 Requirements & Installation

### 1. Environment Setup
Make sure you have **Python 3.8+** installed, and that you have **MySQL** and **MongoDB** servers running locally or inside Docker containers.

### 2. Cloning the Repository and Installing Dependencies
```bash
git clone [https://github.com/serhohro/sakila-movie-explorer.git](https://github.com/serhohro/sakila-movie-explorer.git)
cd sakila-movie-explorer
pip install -r requirements.txt