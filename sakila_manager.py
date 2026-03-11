# sakila_manager.py
import mysql.connector

class SakilaManager:
    def __init__(self, db_init, db_login):
        self.config = {**db_init, **db_login}

    def check_connection(self) -> bool:
        """Проверка физического доступа к серверу"""
        try:
            conn = mysql.connector.connect(
                host=self.config['host'],
                user=self.config['user'],
                password=self.config['password']
            )
            conn.close()
            return True
        except:
            return False

    def database_exists(self) -> bool:
        """Проверка наличия именно базы sakila"""
        try:
            conn = mysql.connector.connect(
                host=self.config['host'],
                user=self.config['user'],
                password=self.config['password']
            )
            cursor = conn.cursor()
            cursor.execute(f"SHOW DATABASES LIKE '{self.config['db_name']}'")
            exists = cursor.fetchone() is not None
            conn.close()
            return exists
        except:
            return False