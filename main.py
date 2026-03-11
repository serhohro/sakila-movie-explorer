from config import Config
from system_checker import SystemChecker
from movie_app import MovieSearchApp # Ваш основной класс приложения

if __name__ == "__main__":
    cfg = Config()
    checker = SystemChecker(cfg)
    
    # 1. Проверяем наличие логинов
    checker.check_credentials()
    
    # 2. Проводим техническую проверку
    if checker.run_full_check():
        app = MovieSearchApp(cfg)
        app.run()
    else:
        print("👋 Завершение работы из-за ошибок конфигурации.")