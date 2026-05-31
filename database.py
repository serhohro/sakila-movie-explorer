import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Any, Optional, Union, Tuple


class DataBase:
    """
    Class for secure and high-level interaction with a MySQL database (Sakila).
    Provides SQL injection protection and automatic transformation of results into dictionaries.
    """

    def __init__(self, db_config: Dict[str, str], auth_config: Dict[str, str]) -> None:
        """
        Initializes the database connection.
        
        Args:
            db_config: Dictionary containing base settings (host, db_name).
            auth_config: Dictionary containing credentials (user, password).
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
        except Error as error:
            print(f"❌ Connection error: {error}")

    def close(self) -> None:
        """Closes the active database connection."""
        if self._connection and self._connection.is_connected():
            self._connection.close()
            print("🔌 Database connection closed.")

    def execute(
        self, 
        sql_query: str, 
        params: Optional[Tuple[Any, ...]] = None, 
        fetch_one: bool = False, 
        as_dict: bool = True
    ) -> Any:
        """
        Universal method for executing SQL queries.
        
        Args:
            sql_query: Query string with %s placeholders.
            params: Tuple of parameters for secure substitution.
            fetch_one: Return a single row (True) or all rows (False).
            as_dict: If True, returns rows as dictionaries {column: value}.
        
        Returns:
            Query result (Dict, List[Dict], or None).
        """
        if not self._connection or not self._connection.is_connected():
            return None

        try:
            cursor = self._connection.cursor(dictionary=as_dict)
            cursor.execute(sql_query, params or ())
            result = cursor.fetchone() if fetch_one else cursor.fetchall()
            cursor.close()
            return result
        except Error as error:
            print(f"🚨 SQL execution error: {error}")
            return None if fetch_one else []

    def get_row_count(self, table_name: str) -> int:
        """
        Returns the total number of records in the specified table.
        
        Args:
            table_name: The name of the table to count rows in.
        Returns:
            The number of rows.
        """
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
        Retrieves a page of data using LIMIT and OFFSET.
        
        Args:
            table: The name of the table.
            limit: Number of records per page.
            offset: The offset (number of rows to skip).
            order_by: Column to sort by (defaults to the table's PK).
        """
        sort_column = order_by if order_by else f"{table}_id"
        sql = f"SELECT * FROM `{table}` ORDER BY `{sort_column}` LIMIT %s OFFSET %s"
        return self.execute(sql, (limit, offset))

    def find_by_column(
        self, 
        table: str, 
        column: str, 
        value: Any
    ) -> List[Dict[str, Any]]:
        """
        Finds records by an exact match in a column.
        
        Args:
            table: The name of the table.
            column: The name of the column.
            value: The value to search for.
        """
        sql = f"SELECT * FROM `{table}` WHERE `{column}` = %s"
        return self.execute(sql, (value,))

    def search_like(
        self, 
        table: str, 
        column: str, 
        search_term: str
    ) -> List[Dict[str, Any]]:
        """
        Finds records by a partial match (LIKE).
        
        Args:
            table: The name of the table.
            column: The name of the column.
            search_term: The search string (will be wrapped in %).
        """
        sql = f"SELECT * FROM `{table}` WHERE `{column}` LIKE %s"
        formatted_search = f"%{search_term}%"
        return self.execute(sql, (formatted_search,))
        
    def _format_fields(self, fields: Union[str, List[str]]) -> str:
        """
        Internal method to escape field names with backticks.
        
        Args:
            fields: A string like "col1, col2" or a list like ["col1", "col2"].
        Returns:
            A secure string for SQL: "`col1`, `col2`".
        """
        if isinstance(fields, str):
            if fields.strip() == '*': return '*'
            fields_list = [item.strip() for item in fields.split(',')]
        else:
            fields_list = fields

        return ', '.join(f"`{field}`" for field in fields_list if field)

    def select(
        self, 
        table_name: str, 
        fields: Union[str, List[str]] = '*', 
        where: Optional[str] = None, 
        order: Optional[str] = None, 
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Universal constructor for SELECT queries.
        Supports filtering, sorting, and pagination.
        
        Args:
            table_name: The table to select from.
            fields: List of fields.
            where: Condition (e.g., "status:active" or raw SQL).
            order: Column to sort by.
            limit: Row limit.
            offset: The offset.
        """
        fields_clause = self._format_fields(fields)
        order_clause = f"ORDER BY `{order}`" if order else f"ORDER BY `{table_name}_id`"
        
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