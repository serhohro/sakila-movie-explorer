import time
import os
import sys
from pymongo import MongoClient
from sakila_manager import SakilaManager
print(" ✅")
class SystemChecker:
    def __init__(self, config_obj):
        self.cfg = config_obj

    def _progress_run(self, task_name, task_func, *args):
        """Выполняет задачу и рисует бар только до момента успеха или провала"""
        print(f"{task_name:<30}", end="", flush=True)
        bar_size = 20
        
        # 1. Сначала крутим бар до 50% (имитация подготовки)
        for i in range(11):
            bar = "█" * i + "-" * (bar_size - i)
            print(f"\r{task_name:<30} |{bar}| {i*5}%", end="", flush=True)
            time.sleep(0.05)
        
        # 2. Выполняем реальную проверку
        success, error_msg = task_func(*args)
        
        if success:
            # Если всё хорошо, докручиваем до 100%
            for i in range(11, bar_size + 1):
                bar = "█" * i + "-" * (bar_size - i)
                print(f"\r{task_name:<30} |{bar}| {i*5}%", end="", flush=True)
                time.sleep(0.05)
            print(" ✅ [OK]")
            return True, None
        else:
            # Если ошибка, рисуем красный крест и прерываемся
            # \033[91m - красный цвет для терминала
            print(f" ❌ [FAIL]") 
            return False, error_msg
    
    def _check_mysql_logic(self):
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

    def _check_mongo_logic(self):
        try:
            from pymongo import MongoClient
            client = MongoClient(self.cfg.mongodb['host'], serverSelectionTimeoutMS=2000)
            client.server_info()
            client.close()
            return True, None
        except Exception as e:
            return False, str(e)
    
    def check_credentials(self):
        """Проверка и ручной ввод конфига"""
        db_login = self.cfg.db_login
        if not db_login['user'] or not db_login['password']:
            print("\n🔑 Настройки доступа не найдены. Введите данные вручную:")
            self.cfg.db_init['host'] = input("Host (default: localhost): ") or "localhost"
            self.cfg.db_login['user'] = input("MySQL User: ")
            self.cfg.db_login['password'] = input("MySQL Password: ")
            
            # Аналогично для MongoDB, если это Atlas
            if input("Использовать MongoDB Atlas? (y/n): ").lower() == 'y':
                self.cfg.mongodb['host'] = input("Введите URI (mongodb+srv://...): ")
        
    def run_full_check(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("🚀 ЗАПУСК ДИАГНОСТИКИ СИСТЕМЫ\n" + "="*50)

        # Проверка MySQL
        ok, err = self._progress_run("Связь с MySQL", self._check_mysql_logic)
        if not ok:
            print(f"\n\n❌ ОШИБКА ПОДКЛЮЧЕНИЯ К MYSQL:\n   [!] {err}")
            print("="*50)
            input("Проверьте настройки в Config.py. Нажмите Enter для выхода...")
            return False

        # Проверка MongoDB
        ok, err = self._progress_run("Связь с MongoDB", self._check_mongo_logic)
        if not ok:
            print(f"\n\n❌ ОШИБКА ПОДКЛЮЧЕНИЯ К MONGODB:\n   [!] {err}")
            print("="*50)
            input("Проверьте, запущен ли сервер Mongo. Нажмите Enter для выхода...")
            return False

        # Если дошли сюда — всё супер
        print("\n✅ Все системы работают нормально!")
        
        choice = input("\nНачнем наше путешествие по фильмам? (y/n): ").lower()
        if choice == 'y':
            os.system('cls' if os.name == 'nt' else 'clear')
            return True
        
        print("\nЧто ж, возвращайтесь, когда будете готовы к новым открытиям! 👋")
        input("Нажмите ENTER для выхода...")
        return False