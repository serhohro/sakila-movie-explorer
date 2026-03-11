class Config:
    
    def __init__(self):
        self.db_init = {
            'host': '', # Enter the name of the remote host with the Sakila database installed, 
                        # or enter localhost if Sakila is installed on the local machine.
            'db_name': 'sakila'
        }

        self.db_login = {
            'user': '', # Enter your database username
            'password': '' # Enter the database password.
        }
        
        self.mongodb = {
            "host": "localhost",
            "port": 27017,
            "database": "final_project_logs",
            # ВАЖНО: имя коллекции по ТЗ
            "collection": "final_project_group1_Ivanov_Ivan"
        }
        
        self.app_info = {
            "name": "Sakila Movie Explorer",
            "version": "1.0.0",
            "author": "Serhiy Hromyko",
            "year": "2026"
        }