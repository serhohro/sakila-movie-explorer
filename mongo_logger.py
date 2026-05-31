from pymongo import MongoClient
from pymongo.collection import Collection
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

class MongoLogger:
    """
    Class for logging search queries into a MongoDB database.
    Allows tracking search histories and compiling analytical reports.
    """

    def __init__(self, config: Any) -> None:
        """
        Initializes the MongoDB connection based on the provided configuration.
        :param config: Configuration object containing a mongodb attribute (dict).
        """
        mongo_cfg: Dict[str, Any] = config.mongodb
        self.client: MongoClient = MongoClient(host=mongo_cfg["host"], port=mongo_cfg["port"])
        self.db = self.client[mongo_cfg["database"]]
        self.collection: Collection = self.db[mongo_cfg["collection"]]

    def log_search(self, search_type: str, params: Dict[str, Any], results_count: int) -> None:
        """
        Saves a record of a search query into the MongoDB collection.
        :param search_type: Code type of the search (e.g., 'title', 'genre').
        :param params: Dictionary with search parameters (keywords, IDs, etc.).
        :param results_count: Number of records matching the query.
        """
        document: Dict[str, Any] = {
            "timestamp": datetime.utcnow(),
            "search_type": search_type,
            "params": params,
            "results_count": results_count
        }
        self.collection.insert_one(document)

    @staticmethod
    def _pluralize(number: int, forms: List[str]) -> str:
        """
        Selects the correct singular/plural form of a word based on the count.
        :param number: The number to analyze.
        :param forms: List of 2 forms of the word (e.g., ["results", "result"]).
        :return: Correct word form.
        """
        return forms[1] if abs(number) == 1 else forms[0]

    def _format_params(self, search_type: str, params: Dict[str, Any]) -> str:
        """
        Converts technical search parameters into a human-readable string.
        :param search_type: The search type string.
        :param params: Dictionary of parameters.
        :return: Descriptive text string (e.g., "title 'Matrix'").
        """
        g_name: Optional[str] = params.get('genre_name')
        g_id: Optional[Union[int, str]] = params.get('category_id') or params.get('cat')
        
        # Use genre name if saved, otherwise fall back to ID
        genre_display: str = f"genre '{g_name}'" if g_name else f"genre ID {g_id}"

        mapping: Dict[str, Any] = {
            'title': lambda p: f"title '{p.get('keyword')}'",
            'one_year': lambda p: f"year {p.get('year')}",
            'range_years': lambda p: f"period {p.get('from')}-{p.get('to')}",
            'list_years': lambda p: f"years: {', '.join(map(str, p.get('years_list', [])))}",
            'genre': lambda p: genre_display,
            'genre_year': lambda p: f"{genre_display} ({p.get('from')}-{p.get('to')})",
            'all_movies': lambda p: "entire catalog",
            'actor_search': lambda p: f"movies featuring actor '{p.get('actor_name')}'",
            'description_search': lambda p: f"by plot description: '{p.get('keyword')}'",
        }
        
        formatter = mapping.get(search_type, lambda p: str(p))
        return formatter(params)

    def get_last_searches_formatted(self, limit: int = 5) -> List[str]:
        """
        Returns a list of the latest queries in text format.
        :param limit: Number of entries to retrieve.
        :return: List of strings containing the date and search description.
        """
        cursor = self.collection.find().sort("timestamp", -1).limit(limit)
        logs: List[str] = []
        for doc in cursor:
            dt: str = doc['timestamp'].strftime("%Y-%m-%d %H:%M")
            p_text: str = self._format_params(doc['search_type'], doc['params'])
            count: int = doc['results_count']
            res_word: str = self._pluralize(count, ["results", "result"])
            logs.append(f"[{dt}] Search: {p_text} (Found: {count} {res_word})")
        return logs

    def get_popular_searches_formatted(self, limit: int = 5) -> List[str]:
        """
        Compiles a list of the most frequent search queries using aggregation.
        :param limit: Maximum entries in the top list.
        :return: List of strings (e.g., "Entire catalog — searched 10 times").
        """
        pipeline: List[Dict[str, Any]] = [
            {"$group": {"_id": {"st": "$search_type", "pa": "$params"}, "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}, 
            {"$limit": limit}
        ]
        popular = list(self.collection.aggregate(pipeline))
        results: List[str] = []
        for item in popular:
            p_text: str = self._format_params(item['_id']['st'], item['_id']['pa'])
            times_word: str = self._pluralize(item['count'], ["times", "time"])
            results.append(f"{p_text.capitalize()} — searched {item['count']} {times_word}")
        return results
        
    def get_last_searches_raw(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Returns latest searches as a list of dictionaries for Formatter.
        :param limit: Record limit.
        :return: Formatted dictionary data ready for table rendering.
        """
        cursor = self.collection.find().sort("timestamp", -1).limit(limit)
        raw_data: List[Dict[str, Any]] = []
        for doc in cursor:
            raw_data.append({
                "Date/Time": doc['timestamp'].strftime("%d.%m.%y %H:%M"),
                "Request Type": doc['search_type'].replace('_', ' ').capitalize(),
                "Parameters": self._format_params(doc['search_type'], doc['params']),
                "Found": f"{doc['results_count']} pcs."
            })
        return raw_data

    def get_popular_searches_raw(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Returns top popular queries as a list of dictionaries for Formatter.
        :param limit: Count of popular queries to return.
        :return: Formatted dictionary data for rendering a popularity table.
        """
        pipeline: List[Dict[str, Any]] = [
            {"$group": {"_id": {"st": "$search_type", "pa": "$params"}, "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}, 
            {"$limit": limit}
        ]
        popular = list(self.collection.aggregate(pipeline))
        raw_data: List[Dict[str, Any]] = []
        for item in popular:
            raw_data.append({
                "Query": self._format_params(item['_id']['st'], item['_id']['pa']).capitalize(),
                "Frequency": f"{item['count']} {self._pluralize(item['count'], ['times', 'time'])}"
            })
        return raw_data