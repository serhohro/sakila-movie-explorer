import sys
from config import Config
from system_checker import SystemChecker
from movie_app import MovieSearchApp 

def main() -> None:
    """
    Main entry point of the application.
    
    Performs sequential configuration checks, technical diagnostics
    of all systems, and launches the main application interface.
    """
    # Load initial configuration
    cfg: Config = Config()
    
    # Initialize the technical validation module
    checker: SystemChecker = SystemChecker(cfg)
    
    # 1. Verify availability and prompt for credentials (if empty)
    checker.check_credentials()
    
    # 2. Execute comprehensive technical diagnostics (MySQL, Sakila, MongoDB)
    if checker.run_full_check():
        # If diagnostics pass successfully — start the main application loop
        app: MovieSearchApp = MovieSearchApp(cfg)
        app.run()
    else:
        # In case of critical errors — exit gracefully
        print("👋 Shutting down due to configuration errors.")
        sys.exit(1)
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()