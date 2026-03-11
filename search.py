from typing import List, Dict, Any, Optional, Tuple
from paginator import Paginator
from formatter import Formatter
from mongo_logger import MongoLogger
from config import Config

class SearchService:
    def __init__(self, db):
        self.db = db
        self.config = Config()
        self.mongo_logger = MongoLogger(self.config)
        formatter_config = {
            "max_col_width": 50,
            "header_align": "center",
            "header_custom": None,
            "border": True,
            "zebra": True,
            "zebra_colors": ("\033[48;5;235m", "\033[0m"),    # тёмно-серый фон
            "border_chars": {
                "h": "",
                "v": " ",
                "c": ""
            }
        }
        self.formatter = Formatter(formatter_config)
        # --- ПАНЕЛЬ НАСТРОЕК СОРТИРОВКИ ---
        self.sort_rules = {
            "default": "f.title ASC",                       # По алфавиту
            "by_title": "f.title ASC",                      # По названию
            "by_year": "f.release_year DESC, f.title ASC",  # Новинки выше
            "by_genre": "genres ASC, f.title ASC",          # По жанрам, затем по названию
            "complex": "genres ASC, f.release_year DESC",   # Жанр + свежие годы
            "by_actor": "f.release_year DESC, f.title ASC"  # по актерам
        }

    def _get_base_query(self, where_clause: str, sort_key: str = "default") -> str:
        """SQL шаблон для Sakila с объединением жанров.
        order_clause для сортировки, по умолчанию сортируем по названию. В параметрах мы передаем ключ сортировки sort_key, а метод сам берет SQL из словаря"""
        
        order_by = self.sort_rules.get(sort_key, self.sort_rules["default"])
        
        return f"""
            SELECT f.film_id AS id, f.title AS title, f.release_year AS year,
                   GROUP_CONCAT(c.name SEPARATOR ', ') AS genres
            FROM film f
            LEFT JOIN film_category fc ON f.film_id = fc.film_id
            LEFT JOIN category c ON fc.category_id = c.category_id
            WHERE {where_clause}
            GROUP BY f.film_id
            ORDER BY {order_by}
        """

    def _render_results(self, data, page, total_pages, total_rows):
        """Отрисовка через Formatter."""
        print(f"\n📊 Страница {page} из {total_pages} | Всего найдено фильмов: {total_rows}")
        print(self.formatter.make_table(data))

    def _log(self, search_type: str, params: dict, results_count: int):
        """Проброс данных в MongoLogger."""
        self.mongo_logger.log_search(search_type, params, results_count)

    def _browse(self, query_template: str, params: Tuple, label: str, search_type: str, log_params: dict):
        """Универсальный метод с автоматическим логированием реального кол-ва результатов."""
        count_sql = f"SELECT COUNT(*) as total FROM ({query_template}) as t"
        total_data = self.db.execute(count_sql, params, fetch_one=True)
        total_count = total_data['total'] if total_data else 0

        # Логируем реальное количество из БД
        self._log(search_type, log_params, total_count)

        if total_count == 0:
            print(f"\n🔍 По запросу '{label}' ничего не найдено.")
            return

        def load_page(offset, limit):
            sql = f"{query_template} LIMIT %s OFFSET %s"
            return self.db.execute(sql, params + (limit, offset))

        paginator = Paginator(total_rows=total_count, per_page=10)
        paginator.run(page_loader=load_page, page_renderer=self._render_results)

    def get_year_range(self) -> Tuple[int, int]:
        """Получает минимальный и максимальный год выпуска из базы данных."""
        sql = "SELECT MIN(release_year) as min_y, MAX(release_year) as max_y FROM film"
        res = self.db.execute(sql, fetch_one=True)
        if res and res['min_y'] and res['max_y']:
            return int(res['min_y']), int(res['max_y'])
        return (1900, 2026)  # Фоллбэк, если база пуста
    
    # --- Методы поиска ---

    def browse_by_title(self, keyword: str):
        query = self._get_base_query("f.title LIKE %s", sort_key="by_title")
        self._browse(query, (f"%{keyword}%",), f"Поиск: {keyword}", "title", {"keyword": keyword})

    def browse_by_genre(self):
        genres = self.db.execute("SELECT category_id as id, name FROM category ORDER BY name")
        print("\n=== ДОСТУПНЫЕ ЖАНРЫ ===")
        for g in genres: print(f"{g['id']:>2}. {g['name']}")
        
        try:
            gid = int(input("\nВыберите ID жанра: "))
            g_name = next((g['name'] for g in genres if g['id'] == gid), "Неизвестный")
            query = self._get_base_query("fc.category_id = %s")
            self._browse(query, (gid,), f"Жанр: {g_name}", "genre", {"category_id": gid, "genre_name": g_name})
        except ValueError:
            print("❌ Ошибка: введите число.")

    def browse_by_year(self, year_input: str):
        """
        Поиск фильмов:
        - По конкретному году ('2006')
        - По диапазону ('1995-2005', '1995 - 2005')
        - По списку ('1988 2000 2014')
        """
        if not year_input:
            print("❌ Ошибка: ввод пуст.")
            return

        # 1. Предварительная очистка: убираем лишние пробелы по краям
        year_input = year_input.strip()

        try:
            # СЦЕНАРИЙ 1: Диапазон (есть дефис)
            if '-' in year_input:
                # Разбиваем по дефису и очищаем каждое число от пробелов
                parts = [p.strip() for p in year_input.split('-') if p.strip()]
                if len(parts) != 2:
                    raise ValueError("Неверный формат диапазона")
                
                y1, y2 = map(int, parts)
                start, end = min(y1, y2), max(y1, y2)
                
                where = "f.release_year BETWEEN %s AND %s"
                sql_params = (start, end)
                log_p = {"from": start, "to": end}
                s_type = "range_years"

            # СЦЕНАРИЙ 2 И 3: Одиночный год или список через пробел
            else:
                # Разбиваем строку по пробелам и превращаем в список чисел
                years = [int(y) for y in year_input.split() if y.strip()]
                
                if not years:
                    raise ValueError("Годы не найдены")

                if len(years) == 1:
                    # Одиночный год
                    where = "f.release_year = %s"
                    sql_params = (years[0],)
                    log_p = {"year": years[0]}
                    s_type = "one_year"
                else:
                    # Список лет (используем оператор IN)
                    # Создаем строку вида (%s, %s, %s) по количеству элементов
                    placeholders = ", ".join(["%s"] * len(years))
                    where = f"f.release_year IN ({placeholders})"
                    sql_params = tuple(years)
                    log_p = {"years_list": years}
                    s_type = "list_years"

            query = self._get_base_query(where, sort_key="complex")
            self._browse(query, sql_params, f"Год(ы): {year_input}", s_type, log_p)
            
        except ValueError:
            print("❌ Ошибка: проверьте формат ввода (используйте числа, пробелы или дефис).")
       
    def browse_by_actor(self):
        """Поиск фильмов по имени или фамилии актера"""
        keyword = input("\nВведите имя или фамилию актера (можно часть): ").strip()
        if not keyword: return

        # 1. Сначала найдем актеров, подходящих под запрос
        actors_sql = """
            SELECT actor_id, first_name, last_name 
            FROM actor 
            WHERE first_name LIKE %s OR last_name LIKE %s
            LIMIT 10
        """
        actors = self.db.execute(actors_sql, (f"%{keyword}%", f"%{keyword}%"))

        if not actors:
            print(f"❌ Актер '{keyword}' не найден.")
            return

        # 2. Выводим список найденных актеров для выбора
        print("\n=== НАЙДЕННЫЕ АКТЕРЫ ===")
        for a in actors:
            print(f"{a['actor_id']}. {a['first_name']} {a['last_name']}")
        
        try:
            aid = int(input("\nВыберите ID актера: "))
            actor_info = next((a for a in actors if a['actor_id'] == aid), None)
            if not actor_info: raise ValueError
            
            a_full_name = f"{actor_info['first_name']} {actor_info['last_name']}"

            # 3. Формируем запрос к фильмам через таблицу связей film_actor
            where = "f.film_id IN (SELECT film_id FROM film_actor WHERE actor_id = %s)"
            query = self._get_base_query(where, sort_key="by_actor")
            
            log_p = {"actor_id": aid, "actor_name": a_full_name}
            
            self._browse(query, (aid,), f"Фильмы актера: {a_full_name}", "actor_search", log_p)

        except ValueError:
            print("❌ Ошибка выбора.")
            
    def browse_by_genre_and_year(self):
        """Комплексный поиск (Жанр + Год)"""
        genres = self.db.execute("SELECT category_id as id, name FROM category ORDER BY name")
        print("\n=== ДОСТУПНЫЕ ЖАНРЫ ===")
        for g in genres: print(f"{g['id']:>2}. {g['name']}")
        
        try:
            gid = int(input("Введите ID жанра: "))
            g_name = next((g['name'] for g in genres if g['id'] == gid), "Неизвестный")
            y1 = int(input("Год с: "))
            y2 = int(input("Год по: "))
            
            # 1. Формируем условие
            where = "fc.category_id = %s AND f.release_year BETWEEN %s AND %s"
            
            # 2. Формируем SQL запрос (используем правило сортировки complex)
            query = self._get_base_query(where, sort_key="complex")
            
            # Записываем все параметры для истории в MongoDB
            log_p = {
                "cat": gid, 
                "genre_name": g_name, 
                "from": y1, 
                "to": y2
            }
            
            self._browse(query, (gid, y1, y2), f"Жанр {g_name} ({y1}-{y2})", "genre_year", log_p)
        except ValueError:
            print("❌ Ошибка ввода.")

    def show_all_movies(self):
        """Вывод всех фильмов."""
        total = self.db.get_row_count('film')
        query = self._get_base_query("1=1", sort_key="by_title") # По алфавиту
        self._browse(query, (), "Весь каталог", "all_movies", {})