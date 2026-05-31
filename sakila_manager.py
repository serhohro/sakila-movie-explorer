import mysql.connector
from typing import Dict, Any

class SakilaManager:
    """
    Class for managing the technical state of the Sakila database.
    
    Responsible for checking the physical connection to the MySQL server and 
    verifying the presence of the target data schema.
    """

    def __init__(self, db_init: Dict[str, str], db_login: Dict[str, str]) -> None:
        """
        Initializes the manager, merging initialization and authorization parameters.
        
        :param db_init: Dictionary containing host and DB name parameters.
        :param db_login: Dictionary containing user login and password credentials.
        """
        # Merging dictionaries for convenient settings access
        self.config: Dict[str, Any] = {**db_init, **db_login}

    def check_connection(self) -> bool:
        """
        Checks the ability to establish a physical connection to the MySQL server.
        
        Uses the host, username, and password provided in the configuration.
        
        :return: True if the connection is successfully established and closed; 
                 False in case of any connection error.
        """
        try:
            conn = mysql.connector.connect(
                host=self.config['host'],
                user=self.config['user'],
                password=self.config['password']
            )
            conn.close()
            return True
        except Exception:
            return False

    def database_exists(self) -> bool:
        """
        Checks for the presence of a specific database (sakila) on the server.
        
        Executes a SHOW DATABASES SQL query to search for the schema 
        specified in the settings (db_name).
        
        :return: True if a database with this name is found; 
                 False if the database is missing or a query error occurs.
        """
        try:
            conn = mysql.connector.connect(
                host=self.config['host'],
                user=self.config['user'],
                password=self.config['password']
            )
            cursor = conn.cursor()
            # Search for the database using the template from the config
            cursor.execute(f"SHOW DATABASES LIKE '{self.config['db_name']}'")
            exists: bool = cursor.fetchone() is not None
            conn.close()
            return exists
        except Exception:
            return False