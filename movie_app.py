import os
import sys

# Path configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.append(BASE_DIR)

from database       import DataBase
from menu           import Menu
from search         import SearchService
from mongo_logger   import MongoLogger
from sakila_manager import SakilaManager
from formatter      import Formatter

class MovieSearchApp:
    """
    Main application class (Controller).
    Handles system initialization and menu navigation.
    """
    
    def __init__(self, config):
        self.config = config
        
        # Set our application title in the console window
        self._set_console_title()
        
        # Database initialization and readiness check
        self.sakila = SakilaManager(self.config.db_init, self.config.db_login)

        # Core services initialization
        self.db = DataBase(self.config.db_init, self.config.db_login)
        self.search = SearchService(self.db)
        self.mongo_logger = MongoLogger(self.config)
    
    def _set_console_title(self):
        """Sets the console window title."""
        title_str = f"{self.config.app_info['name']} v{self.config.app_info['version']}"
        
        if sys.platform == "win32":
            # For Windows, os.system expects format: title Text
            os.system(f"title {title_str}")
        else:
            # For Linux/macOS
            sys.stdout.write(f"\x1b]2;{title_str}\x07")
    
    def _check_database(self):
        """Verifies and provisions the Sakila database if missing."""
        if not self.sakila.database_exists():
            print("⚠ Sakila database not found. Starting setup...")
            self.sakila.install_database()
        else:
            print("✅ Sakila database is ready.")

    # --- Menu Item Handlers ---

    def search_by_title(self):
        """Searches by title with input normalization."""
        print("\n🔍 SEARCH BY TITLE")
        title = input("Enter movie title: ").strip()
        title = " ".join(title.split()) # Clean up redundant spaces
        
        if title:
            self.search.browse_by_title(title)
        else:
            print("❌ Error: empty input.")

    def search_by_genre(self):
        """Searches by genre (selection logic is encapsulated inside the service)."""
        print("\n🎭 SEARCH BY GENRE")
        self.search.browse_by_genre()

    def search_by_year(self):
        """Searches by a single year or a range."""
        print("\n📅 SEARCH BY YEAR")
        min_y, max_y = self.search.get_year_range()
        print(f"\n📅 Available span in database: {min_y} — {max_y}")
        print("Formats: '2006', '1995-2005', '1988 2000'")
        year_input = input("Enter data: ").strip()
        
        if year_input:
            self.search.browse_by_year(year_input)
        else:
            print("❌ Error: year not provided.")
    
    def search_by_actor(self):
        print("\n🔍 SEARCH BY ACTORS")
        self.search.browse_by_actor()
        
    def search_by_genre_and_year(self):
        """Performs a complex multi-criteria search."""
        print("\n🧩 COMBINED SEARCH (GENRE + YEAR)")
        self.search.browse_by_genre_and_year()
    
    def search_by_description(self):
        print("\n🔍 SEARCH BY PLOT / DESCRIPTION")
        self.search.browse_by_description()
    
    def show_all(self):
        """Outputs all movies along with their genres."""
        print("\n🎬 ENTIRE MOVIE CATALOG")
        self.search.show_all_movies()

    def show_statistics_odd(self):
        """Displays raw search history statistics from MongoDB."""
        print("\n📊 SEARCH HISTORY STATISTICS")
        
        print("\n🕒 Recent 5 queries:")
        # Invoke and print formatted string logs
        for entry in self.mongo_logger.get_last_searches_formatted():
            print(f" • {entry}")
        
        print("\n🔥 Most popular queries:")
        # Straightforward mapping for basic aggregation logs
        for entry in self.mongo_logger.get_popular_searches_formatted():
            print(f" • {entry}")

    def show_statistics(self):
        print("\n")
        print(f" {'📊 ANALYTICS AND SEARCH HISTORY':^66} ")
        print("═"*66)

        # Create formatter instance specifically for statistical tabular layouts
        stats_fmt = Formatter({"zebra": True, "border": True})

        # 1. Recent queries section
        last_data = self.mongo_logger.get_last_searches_raw(5)
        if last_data:
            print("\n🕒 RECENT QUERIES:")
            # Relies on tabular dict format translation done inside mongo_logger
            print(stats_fmt.make_table(last_data))
        else:
            print("\n🕒 Search history is currently empty.")

        # 2. Popular queries section
        popular_data = self.mongo_logger.get_popular_searches_raw(5)
        if popular_data:
            print("\n🔥 TOP POPULAR QUERIES:")
            print(stats_fmt.make_table(popular_data))
        
        input("\nPress Enter to return...")
    
    def show_about(self):
        """Renders an informational context card for the application."""
        info = self.config.app_info # Extract data from our Config instance
        
        # Layout card width settings
        width = 50
        line = "═" * (width - 2)
        
        # Display the informational bounding box
        print(f"\n╔{line}╗")
        print(f"║{info['name'].upper():^{width-2}}║")
        print(f"╠{line}╣")
        
        # Mapping dictionary for clean output lines
        details = {
            "Version": info["version"],
            "Developer": info["author"],
            "Year": info["year"],
            "Database": info["db"],
            "Logging": info["log_db"]
        }

        for key, value in details.items():
            # Align keys to the left, values to the right
            content = f" {key}: {value} "
            print(f"║{content:<{width-2}}║")

        print(f"╚{line}╝")
        input("\nPress Enter to return to the menu...")
    
    def exit_app(self):
        """Gracefully terminates application processing loops."""
        choice = input("\nAre you sure you want to exit? (y/n): ").strip().lower()
        if choice == 'y':
            self.db.close() # Close active MySQL connections
            print("👋 Goodbye!")
            sys.exit(0)

    def run(self):
        """Launches the primary application loop."""
        menu = Menu("MOVIE SEARCH SYSTEM")
        menu.add_item("Search by title", self.search_by_title)
        menu.add_item("Search by description", self.search_by_description)
        menu.add_item("Search by genre", self.search_by_genre)
        menu.add_item("Search by year", self.search_by_year)
        menu.add_item("Search by actor", self.search_by_actor)
        menu.add_item("Search by genre + year", self.search_by_genre_and_year)
        menu.add_item("Show all movies", self.show_all)
        menu.add_item("Top queries (Statistics)", self.show_statistics)
        menu.add_item("About application", self.show_about)
        menu.add_item("Exit", self.exit_app)
        
        menu.run()

if __name__ == "__main__":
    app = MovieSearchApp()
    app.run()