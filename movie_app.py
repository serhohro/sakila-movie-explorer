import os
import sys

# Настройка путей
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
    Главный класс приложения (Контроллер).
    Отвечает за инициализацию систем и навигацию по меню.
    """
    
    def __init__(self, config):
        self.config = config
        
        # Устанавливаем название нашего приложения в консоли
        self._set_console_title()
        
        # Инициализация БД и проверка её наличия
        self.sakila = SakilaManager(self.config.db_init, self.config.db_login)
        self._check_database()

        # Инициализация ключевых сервисов
        self.db = DataBase(self.config.db_init, self.config.db_login)
        self.search = SearchService(self.db)
        self.mongo_logger = MongoLogger(self.config)
    
    def _set_console_title(self):
        """Устанавливает заголовок окна консоли"""
        title_str = f"{self.config.app_info['name']} v{self.config.app_info['version']}"
        
        if sys.platform == "win32":
            # Для Windows команда os.system ожидает формат: title Текст
            os.system(f"title {title_str}")
        else:
            # Для Linux/macOS
            sys.stdout.write(f"\x1b]2;{title_str}\x07")
    
    def _check_database(self):
        """Проверка и установка БД Sakila."""
        if not self.sakila.database_exists():
            print("⚠ База данных Sakila не найдена. Начинаю установку...")
            self.sakila.install_database()
        else:
            print("✅ База данных Sakila готова к работе.")

    # --- Обработчики пунктов меню ---

    def search_by_title(self):
        """Поиск по названию с нормализацией ввода."""
        print("\n🔍 ПОИСК ПО НАЗВАНИЮ")
        title = input("Введите название фильма: ").strip()
        title = " ".join(title.split()) # Очистка от лишних пробелов
        
        if title:
            self.search.browse_by_title(title)
        else:
            print("❌ Ошибка: пустой ввод.")

    def search_by_genre(self):
        """Поиск по жанру (логика выбора теперь внутри сервиса)."""
        print("\n🎭 ПОИСК ПО ЖАНРУ")
        self.search.browse_by_genre()

    def search_by_year(self):
        """Поиск по году или диапазону."""
        print("\n📅 ПОИСК ПО ГОДУ")
        min_y, max_y = self.search.get_year_range()
        print(f"\n📅 Доступный период в базе: {min_y} — {max_y}")
        print("Форматы: '2006', '1995-2005', '1988 2000'")
        year_input = input("Введите данные: ").strip()
        
        if year_input:
            self.search.browse_by_year(year_input)
        else:
            print("❌ Ошибка: год не указан.")
    
    def search_by_actor(self):
        print("\n🔍 ПОИСК ПО АКТЕРАМ")
        self.search.browse_by_actor()
        
    def search_by_genre_and_year(self):
        """Комплексный поиск."""
        print("\n🧩 КОМБИНИРОВАННЫЙ ПОИСК (ЖАНР + ГОД)")
        self.search.browse_by_genre_and_year()

    def show_all(self):
        """Вывод всех фильмов с жанрами."""
        print("\n🎬 ВЕСЬ КАТАЛОГ ФИЛЬМОВ")
        self.search.show_all_movies()

    def show_statistics_odd(self):
        """Отображение статистики запросов из MongoDB."""
        print("\n📊 СТАТИСТИКА ИСТОРИИ ПОИСКА")
        
        print("\n🕒 Последние 5 запросов:")
        # Просто вызываем и печатаем готовые строки
        for entry in self.mongo_logger.get_last_searches_formatted():
            print(f" • {entry}")
        
        print("\n🔥 Самые популярные запросы:")
        # Логика здесь такая же простая
        for entry in self.mongo_logger.get_popular_searches_formatted():
            print(f" • {entry}")

    def show_statistics(self):
        print("\n")
        print(f" {'📊 АНАЛИТИКА И ИСТОРИЯ ПОИСКА':^66} ")
        print("═"*66)

        # Создаем экземпляр форматтера для статистики
        stats_fmt = Formatter({"zebra": True, "border": True})

        # 1. Секция последних запросов
        last_data = self.mongo_logger.get_last_searches_raw(5)
        if last_data:
            print("\n🕒 ПОСЛЕДНИЕ ЗАПРОСЫ:")
            print(stats_fmt.make_table(last_data))
        else:
            print("\n🕒 История поиска пока пуста.")

        # 2. Секция популярных запросов
        popular_data = self.mongo_logger.get_popular_searches_raw(5)
        if popular_data:
            print("\n🔥 ТОП ПОПУЛЯРНЫХ ЗАПРОСОВ:")
            print(stats_fmt.make_table(popular_data))
        
        input("\nНажмите Enter, чтобы вернуться...")
    def show_about(self):
        """Информационная карточка приложения"""
        info = self.config.app_info # Берем данные из нашего Config
        
        # Настройки ширины карточки
        width = 50
        line = "═" * (width - 2)
        
        # Выводим «коробочку» с данными
        print(f"\n╔{line}╗")
        print(f"║{info['name'].upper():^{width-2}}║")
        print(f"╠{line}╣")
        
        # Словарь для удобного вывода строк
        details = {
            "Версия": info["version"],
            "Разработчик": info["author"],
            "Год": info["year"],
            "База данных": "MySQL (Sakila)",
            "Логирование": "MongoDB (Atlas)"
        }

        for key, value in details.items():
            # Выравниваем ключ по левому краю, значение по правому
            content = f" {key}: {value} "
            print(f"║{content:<{width-2}}║")

        print(f"╚{line}╝")
        input("\nНажмите Enter, чтобы вернуться в меню...")
    
    def exit_app(self):
        """Безопасный выход из приложения."""
        choice = input("\nВы действительно хотите выйти? (y/n): ").strip().lower()
        if choice == 'y':
            self.db.close() # Закрываем соединение с MySQL
            print("👋 До свидания!")
            sys.exit(0)

    def run(self):
        """Запуск главного меню."""
        menu = Menu("MOVIE SEARCH SYSTEM")
        menu.add_item("Поиск по названию", self.search_by_title)
        menu.add_item("Поиск по жанру", self.search_by_genre)
        menu.add_item("Поиск по году", self.search_by_year)
        menu.add_item("Поиск по актеру", self.search_by_actor)
        menu.add_item("Поиск по жанру + году", self.search_by_genre_and_year)
        menu.add_item("Показать все фильмы", self.show_all)
        menu.add_item("Топ запросов (Статистика)", self.show_statistics)
        menu.add_item("О приложении", self.show_about)
        menu.add_item("Выход", self.exit_app)
        
        menu.run()

if __name__ == "__main__":
    app = MovieSearchApp()
    app.run()