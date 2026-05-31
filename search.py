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
            "zebra_colors": ("\033[48;5;235m", "\033[0m"),    # Dark gray background
            "border_chars": {
                "h": "",
                "v": " ",
                "c": ""
            }
        }
        self.formatter = Formatter(formatter_config)
        # --- Sorting Settings Panel ---
        self.sort_rules = {
            "default": "f.title ASC",                       # by Alfabet
            "by_title": "f.title ASC",                      # by name
            "by_year": "f.release_year DESC, f.title ASC",  # New arrivals are above.
            "by_genre": "genres ASC, f.title ASC",          # By genre, then by title
            "complex": "genres ASC, f.release_year DESC",   # Genre + Recent Years
            "by_actor": "f.release_year DESC, f.title ASC", # by Actors
            "by_description": "f.title ASC"                 # by Description
        }

    def _get_base_query(self, where_clause: str, sort_key: str = "default") -> str:
        """
        SQL template for Sakila with genre joining.
        order_clause is used for sorting; by default, we sort by title. 
        We pass the sort_key in the parameters, and the method automatically retrieves the SQL from the dictionary.
        """
        
        order_by = self.sort_rules.get(sort_key, self.sort_rules["default"])
        
        # Here we can add or remove fields that will be displayed in the console
        return f"""
            SELECT f.film_id AS id,
                   f.title AS title, 
                   f.description AS description,
                   f.release_year AS year,
                   GROUP_CONCAT(c.name SEPARATOR ', ') AS genres
            FROM film f
            LEFT JOIN film_category fc ON f.film_id = fc.film_id
            LEFT JOIN category c ON fc.category_id = c.category_id
            WHERE {where_clause}
            GROUP BY f.film_id
            ORDER BY {order_by}
        """

    def _render_results(self, data, page, total_pages, total_rows):
        """Rendering via Formatter."""
        print(f"\n📊 Page {page} of {total_pages} | Total movies found: {total_rows}")
        print(self.formatter.make_table(data))

    def _log(self, search_type: str, params: dict, results_count: int):
        """Forwarding data to MongoLogger."""
        self.mongo_logger.log_search(search_type, params, results_count)

    def _browse(self, query_template: str, params: Tuple, label: str, search_type: str, log_params: dict):
        """Universal method with automatic logging of the actual number of results."""
        count_sql = f"SELECT COUNT(*) as total FROM ({query_template}) as t"
        total_data = self.db.execute(count_sql, params, fetch_one=True)
        total_count = total_data['total'] if total_data else 0

        # Log the actual count from the database
        self._log(search_type, log_params, total_count)

        if total_count == 0:
            print(f"\n🔍 No results found for '{label}'.")
            return

        def load_page(offset, limit):
            sql = f"{query_template} LIMIT %s OFFSET %s"
            return self.db.execute(sql, params + (limit, offset))

        paginator = Paginator(total_rows=total_count, per_page=10)
        paginator.run(page_loader=load_page, page_renderer=self._render_results)

    def get_year_range(self) -> Tuple[int, int]:
        """Retrieves the minimum and maximum release years from the database."""
        sql = "SELECT MIN(release_year) as min_y, MAX(release_year) as max_y FROM film"
        res = self.db.execute(sql, fetch_one=True)
        if res and res['min_y'] and res['max_y']:
            return int(res['min_y']), int(res['max_y'])
        return (1900, 2026)  # Fallback if the database is empty
    
# --- Search Methods ---

    def browse_by_title(self, keyword: str):
        """Search movies by title."""
        query = self._get_base_query("f.title LIKE %s", sort_key="by_title")
        self._browse(query, (f"%{keyword}%",), f"Search: {keyword}", "title", {"keyword": keyword})

    def browse_by_genre(self):
        """Search movies by genre."""
        genres = self.db.execute("SELECT category_id as id, name FROM category ORDER BY name")
        print("\n=== AVAILABLE GENRES ===")
        for g in genres: print(f"{g['id']:>2}. {g['name']}")
        
        try:
            gid = int(input("\nSelect genre ID: "))
            g_name = next((g['name'] for g in genres if g['id'] == gid), "Unknown")
            query = self._get_base_query("fc.category_id = %s")
            self._browse(query, (gid,), f"Genre: {g_name}", "genre", {"category_id": gid, "genre_name": g_name})
        except ValueError:
            print("❌ Error: please enter a number.")
    
    def browse_by_description(self):
        """Search movies by keywords in description"""
        keyword = input("\n📝 Enter keyword to search in description: ").strip()
        
        if not keyword:
            print("❌ Error: keyword cannot be empty.")
            return

        # 1. Formulate the search condition
        where = "f.description LIKE %s"
        sql_params = (f"%{keyword}%",)
        
        # 2. Retrieve SQL via our base method with the required sorting
        query = self._get_base_query(where, sort_key="by_description")
        
        # 3. Prepare data for the logger
        log_p = {"keyword": keyword}
        
        # 4. Trigger pagination and output
        self._browse(query, sql_params, f"Description: '{keyword}'", "description_search", log_p)
        
    def browse_by_year(self, year_input: str):
        """
        Search movies:
        - By specific year ('2006')
        - By range ('1995-2005', '1995 - 2005')
        - By list ('1988 2000 2014')
        """
        if not year_input:
            print("❌ Error: input is empty.")
            return

        # 1. Pre-cleaning: strip trailing and leading spaces
        year_input = year_input.strip()

        try:
            # SCENARIO 1: Range (contains a hyphen)
            if '-' in year_input:
                # Split by hyphen and strip spaces from each number
                parts = [p.strip() for p in year_input.split('-') if p.strip()]
                if len(parts) != 2:
                    raise ValueError("Invalid range format")
                
                y1, y2 = map(int, parts)
                start, end = min(y1, y2), max(y1, y2)
                
                where = "f.release_year BETWEEN %s AND %s"
                sql_params = (start, end)
                log_p = {"from": start, "to": end}
                s_type = "range_years"

            # SCENARIO 2 AND 3: Single year or space-separated list
            else:
                # Split the string by spaces and convert into a list of integers
                years = [int(y) for y in year_input.split() if y.strip()]
                
                if not years:
                    raise ValueError("No years found")

                if len(years) == 1:
                    # Single year
                    where = "f.release_year = %s"
                    sql_params = (years[0],)
                    log_p = {"year": years[0]}
                    s_type = "one_year"
                else:
                    # List of years (using IN operator)
                    # Create a string like (%s, %s, %s) based on the number of elements
                    placeholders = ", ".join(["%s"] * len(years))
                    where = f"f.release_year IN ({placeholders})"
                    sql_params = tuple(years)
                    log_p = {"years_list": years}
                    s_type = "list_years"

            query = self._get_base_query(where, sort_key="complex")
            self._browse(query, sql_params, f"Year(s): {year_input}", s_type, log_p)
            
        except ValueError:
            print("❌ Error: check input format (use numbers, spaces, or hyphens).")
       
    def browse_by_actor(self):
        """Search movies by actor's first or last name"""
        keyword = input("\nEnter actor's first or last name (partial match allowed): ").strip()
        if not keyword: return

        # 1. First, find actors matching the search query
        actors_sql = """
            SELECT actor_id, first_name, last_name 
            FROM actor 
            WHERE first_name LIKE %s OR last_name LIKE %s
            LIMIT 10
        """
        actors = self.db.execute(actors_sql, (f"%{keyword}%", f"%{keyword}%"))

        if not actors:
            print(f"❌ Actor '{keyword}' not found.")
            return

        # 2. Display the list of matching actors for selection
        print("\n=== MATCHING ACTORS ===")
        for a in actors:
            print(f"{a['actor_id']}. {a['first_name']} {a['last_name']}")
        
        try:
            aid = int(input("\nSelect actor ID: "))
            actor_info = next((a for a in actors if a['actor_id'] == aid), None)
            if not actor_info: raise ValueError
            
            a_full_name = f"{actor_info['first_name']} {actor_info['last_name']}"

            # 3. Formulate the movie query via the film_actor junction table
            where = "f.film_id IN (SELECT film_id FROM film_actor WHERE actor_id = %s)"
            query = self._get_base_query(where, sort_key="by_actor")
            
            log_p = {"actor_id": aid, "actor_name": a_full_name}
            
            self._browse(query, (aid,), f"Movies featuring: {a_full_name}", "actor_search", log_p)

        except ValueError:
            print("❌ Invalid selection.")
            
    def browse_by_genre_and_year(self):
        """Complex search (Genre + Year)"""
        genres = self.db.execute("SELECT category_id as id, name FROM category ORDER BY name")
        print("\n=== AVAILABLE GENRES ===")
        for g in genres: print(f"{g['id']:>2}. {g['name']}")
        
        try:
            gid = int(input("Enter genre ID: "))
            g_name = next((g['name'] for g in genres if g['id'] == gid), "Unknown")
            min_y, max_y = self.get_year_range()
            print(f"\n📅 Available period in database: {min_y} — {max_y}")
            y1 = int(input("Year from: "))
            y2 = int(input("Year to: "))
            
            # 1. Formulate the condition
            where = "fc.category_id = %s AND f.release_year BETWEEN %s AND %s"
            
            # 2. Formulate the SQL query (using the complex sorting rule)
            query = self._get_base_query(where, sort_key="complex")
            
            # Save all parameters for history in MongoDB
            log_p = {
                "cat": gid, 
                "genre_name": g_name, 
                "from": y1, 
                "to": y2
            }
            
            self._browse(query, (gid, y1, y2), f"Genre {g_name} ({y1}-{y2})", "genre_year", log_p)
        except ValueError:
            print("❌ Input error.")

    def show_all_movies(self):
        """Display all movies."""
        total = self.db.get_row_count('film')
        query = self._get_base_query("1=1", sort_key="by_title") # По алфавиту
        self._browse(query, (), "Весь каталог", "all_movies", {})