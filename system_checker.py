import time
import os
import sys
from typing import Any, Callable, Optional, Tuple
from pymongo import MongoClient
from sakila_manager import SakilaManager

class SystemChecker:
    """
    Class for conducting diagnostic checks before launching the main application.
    Ensures database connectivity and configuration correctness.
    """

    def __init__(self, config_obj: Any) -> None:
        """
        Initializes the diagnostics module.
        :param config_obj: Configuration object (Config) containing connection parameters.
        """
        self.cfg: Any = config_obj

    def _progress_run(self, 
                      task_name: str, 
                      task_func: Callable[..., Tuple[bool, Optional[str]]], 
                      *args: Any) -> Tuple[bool, Optional[str]]:
        """
        Visualizes the progress of a task using an animated progress bar.
        The bar reaches 100% only upon successful execution of the function.
        
        :param task_name: Description of the check being performed for console output.
        :param task_func: Logical function of the check, returning (status, error_message).
        :param args: Arguments to be passed to the function.
        :return: Tuple (success: bool, error_text: str or None).
        """
        print(f"{task_name:<30}", end="", flush=True)
        bar_size: int = 20
        
        # 1. Preparation Simulation (0–50%)
        for i in range(11):
            bar = "█" * i + "-" * (bar_size - i)
            print(f"\r{task_name:<30} |{bar}| {i*5}%", end="", flush=True)
            time.sleep(0.05)
        
        # 2. Conducting the Actual Verification
        success, error_msg = task_func(*args)
        
        if success:
            # Complete animation to 100% upon success
            for i in range(11, bar_size + 1):
                bar = "█" * i + "-" * (bar_size - i)
                print(f"\r{task_name:<30} |{bar}| {i*5}%", end="", flush=True)
                time.sleep(0.05)
            print(" ✅ [OK]")
            return True, None
        else:
            # Interrupt on Error
            print(f" ❌ [FAIL]") 
            return False, error_msg
    
    def _check_mysql_logic(self) -> Tuple[bool, Optional[str]]:
        """
        Performs a technical check of the MySQL server connection.
        :return: (True, None) on success, or (False, error_message) on failure.
        """
        try:
            import mysql.connector
            conn = mysql.connector.connect(
                host=self.cfg.db_init['host'],
                user=self.cfg.db_login['user'],
                password=self.cfg.db_login['password'],
                connect_timeout=2
            )
            conn.close()
            return True, None
        except Exception as e:
            return False, str(e)

    def _check_mongo_logic(self) -> Tuple[bool, Optional[str]]:
        """
        Technical check of the connection to the MongoDB server. 
        :return: (True, None) on success, or (False, error_message) on failure.
        """
        try:
            from pymongo import MongoClient
            client = MongoClient(self.cfg.mongodb['host'], serverSelectionTimeoutMS=2000)
            client.server_info()  # Verifying Actual Server Response
            client.close()
            return True, None
        except Exception as e:
            return False, str(e)
    
    def check_credentials(self) -> None:
        """
        Checks for the presence of credentials.
        """
        db_login = self.cfg.db_login
        if not db_login['user'] or not db_login['password']:
            print("\n🔑 Access settings not found. Check the data in the config.py file.")
        
    def run_full_check(self) -> bool:
        """
        Launches the complete system diagnostic cycle.
        Outputs results to the console and awaits user confirmation to proceed.
        
        :return: True if all checks pass and the user confirms the launch.
        """
        os.system('cls' if os.name == 'nt' else 'clear')
        print("🚀 STARTING SYSTEM DIAGNOSTICS\n" + "="*50)

        # 1. Verify MySQL
        ok, err = self._progress_run("MySQL Connection", self._check_mysql_logic)
        if not ok:
            print(f"\n\n❌ MYSQL CONNECTION ERROR:\n   [!] {err}")
            print("="*50)
            input("Please check your settings in Config.py. Press Enter to exit...")
            return False

        # 2. Verify MongoDB
        ok, err = self._progress_run("MongoDB Connection", self._check_mongo_logic)
        if not ok:
            print(f"\n\n❌ MONGODB CONNECTION ERROR:\n   [!] {err}")
            print("="*50)
            input("Please check if the Mongo server is running. Press Enter to exit...")
            return False

        # 3. Final report
        print("\n✅ All systems are operating normally!")
        
        choice: str = input("\nStart our movie journey? (y/n): ").lower().strip()
        if choice == 'y':
            os.system('cls' if os.name == 'nt' else 'clear')
            return True
        
        print("\nWell, come back when you're ready for new discoveries! 👋")
        input("Press ENTER to exit...")
        return False