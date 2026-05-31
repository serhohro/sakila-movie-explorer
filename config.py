from typing import Dict, Any

class Config:
    """
    Application Configuration Class. 
    Contains connection settings for MySQL and MongoDB, as well as general information about the application.
    """
    
    def __init__(self) -> None:
        """Initialization of all configuration parameters."""
        
        # MySQL Database Settings
        self.db_init: Dict[str, str] = {
            'host': 'localhost',    # Enter the name of the remote host with the Sakila database installed,
                                    # or enter localhost if Sakila is installed on the local machine.
            'db_name': 'sakila'
        }

        self.db_login: Dict[str, str] = {
            'user': '',           # Enter your database username
            'password': ''    # Enter the database password
        }
        
        # MongoDB Logging Settings
        self.mongodb: Dict[str, Any] = {
            "host": "localhost",
            "port": 27017,
            "database": "final_project_logs",
            "collection": "final_project_080825_Hromyko_Serhiy"
        }
        
        # Application Metadata
        self.app_info: Dict[str, str] = {
            "name": "Sakila Movie Explorer",
            "version": "1.1.0",
            "author": "Serhiy Hromyko",
            "year": "2026",
            "db": "Sakila (MySQL)",
            "log_db": "MongoDB"
        }
