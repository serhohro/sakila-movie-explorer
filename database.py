import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Any, Optional, Union, Tuple


class DataBase:
    """Класс для безопасного взаимодействия с базой данных MySQL (Sakila)."""

    def __init__(self, db_config: Dict[str, str], auth_config: Dict[str, str]):
        """
        Инициализирует подключение к БД.
        
        Args:
            db_config: Словарь с ключами 'host' и 'db_name'.
            auth_config: Словарь с ключами 'user' and 'password'.
        """
        self._host: str = db_config['host']
        self._db_name: str = db_config['db_name']
        self._user: str = auth_config['user']
        self._password: str = auth_config['password']
        self._connection: Optional[mysql.connector.MySQLConnection] = None

        try:
            self._connection = mysql.connector.connect(
                host=self._host,
                database=self._db_name,
                user=self._user,
                password=self._password,
                autocommit=True
            )
            print(f"✅ Соединение с БД '{self._db_name}' установлено.")
        except Error as error:
            print(f"❌ Ошибка подключения: {error}")

    def close(self) -> None:
        """Закрывает активное соединение с базой данных."""
        if self._connection and self._connection.is_connected():
            self._connection.close()
            print("🔌 Соединение с БД закрыто.")

    def execute(
        self, 
        sql_query: str, 
        params: Optional[Tuple] = None, 
        fetch_one: bool = False, 
        as_dict: bool = True
    ) -> Any:
        """
        Универсальный метод для выполнения SQL-запросов.
        
        Args:
            sql_query: SQL-строка с плейсхолдерами %s.
            params: Кортеж параметров для безопасной подстановки.
            fetch_one: Если True, возвращает только одну строку.
            as_dict: Если True, возвращает результат в виде словаря.
        """
        if not self._connection or not self._connection.is_connected():
            return None

        try:
            # Используем dictionary=True для автоматического маппинга имён колонок
            cursor = self._connection.cursor(dictionary=as_dict)
            cursor.execute(sql_query, params or ())
            
            result = cursor.fetchone() if fetch_one else cursor.fetchall()
            cursor.close()
            return result
        except Error as error:
            print(f"🚨 Ошибка выполнения SQL: {error}")
            return None if fetch_one else []

    def get_row_count(self, table_name: str) -> int:
        """Возвращает общее количество записей в таблице."""
        # Таблицы нельзя передавать как параметры %s, поэтому экранируем вручную
        sql = f"SELECT COUNT(*) as total FROM `{table_name}`"
        result = self.execute(sql, fetch_one=True)
        return result['total'] if result else 0

    def select_paginated(
        self, 
        table: str, 
        limit: int, 
        offset: int, 
        order_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Получает страницу данных из таблицы с защитой от инъекций в LIMIT/OFFSET.
        """
        # По умолчанию сортируем по первичному ключу (напр. film_id)
        sort_column = order_by if order_by else f"{table}_id"
        
        sql = f"""
            SELECT * FROM `{table}`
            ORDER BY `{sort_column}`
            LIMIT %s OFFSET %s
        """
        return self.execute(sql, (limit, offset))

    def find_by_column(
        self, 
        table: str, 
        column: str, 
        value: Any
    ) -> List[Dict[str, Any]]:
        """
        Поиск записей по точному совпадению значения в колонке.
        Безопасно подставляет значение value через параметры.
        """
        sql = f"SELECT * FROM `{table}` WHERE `{column}` = %s"
        return self.execute(sql, (value,))

    def search_like(
        self, 
        table: str, 
        column: str, 
        search_term: str
    ) -> List[Dict[str, Any]]:
        """Поиск по частичному совпадению (LIKE)."""
        sql = f"SELECT * FROM `{table}` WHERE `{column}` LIKE %s"
        # Оборачиваем поисковый запрос в проценты для SQL
        formatted_search = f"%{search_term}%"
        return self.execute(sql, (formatted_search,))
        
    # --- Вспомогательные методы для обработки SQL-частей ---

    def _format_fields(self, fields: Union[str, List[str]]) -> str:
        """
        Преобразует строку или список полей в безопасный формат для SQL.
        Пример: "id, title" -> "`id`, `title`"
        """
        # Если передана строка, превращаем в список
        if isinstance(fields, str):
            if fields.strip() == '*':
                return '*'
            fields_list = [item.strip() for item in fields.split(',')]
        else:
            fields_list = fields

        # Экранируем каждое имя поля обратными кавычками
        return ', '.join(f"`{field}`" for field in fields_list if field)

    def select(
        self, 
        table_name: str, 
        fields: Union[str, List[str]] = '*', 
        where: Optional[str] = None, 
        order: Optional[str] = None, 
        limit: Optional[int] = None,
        offset: Optional[int] = None  # Добавили offset
    ) -> List[Dict[str, Any]]:
        """Универсальный метод выбора данных с поддержкой пагинации."""
        fields_clause = self._format_fields(fields)
        
        order_clause = f"ORDER BY `{order}`" if order else f"ORDER BY `{table_name}_id`"
        
        # Формируем LIMIT и OFFSET
        limit_clause = ""
        if limit is not None:
            limit_clause = f"LIMIT {limit}"
            if offset is not None:
                limit_clause += f" OFFSET {offset}"
        
        where_clause = ""
        params = None
        if where and ':' in where:
            field, value = where.split(':', 1)
            where_clause = f"WHERE `{field.strip()}` = %s"
            params = (value.strip(),)
        elif where:
            where_clause = f"WHERE {where}"

        sql = f"SELECT {fields_clause} FROM `{table_name}` {where_clause} {order_clause} {limit_clause}"
        return self.execute(sql, params)