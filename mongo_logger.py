from pymongo import MongoClient
from datetime import datetime

class MongoLogger:
    def __init__(self, config):
        mongo_cfg = config.mongodb
        self.client = MongoClient(host=mongo_cfg["host"], port=mongo_cfg["port"])
        self.db = self.client[mongo_cfg["database"]]
        self.collection = self.db[mongo_cfg["collection"]]

    def log_search(self, search_type: str, params: dict, results_count: int):
        """Сохраняет лог в БД (Метод, который вызывается из SearchService)"""
        document = {
            "timestamp": datetime.utcnow(),
            "search_type": search_type,
            "params": params,
            "results_count": results_count
        }
        self.collection.insert_one(document)

    @staticmethod
    def _pluralize(number, forms):
        n = abs(number) % 100
        n1 = n % 10
        if 10 < n < 20: return forms[0]
        if n1 > 1 and n1 < 5: return forms[2]
        if n1 == 1: return forms[1]
        return forms[0]

    def _format_params(self, search_type: str, params: dict) -> str:
        """Красивое описание параметров для статистики."""
        g_name = params.get('genre_name')
        g_id = params.get('category_id') or params.get('cat')
        
        # Если имя жанра сохранено — используем его
        genre_display = f"жанр '{g_name}'" if g_name else f"жанр ID {g_id}"

        mapping = {
            'title': lambda p: f"название '{p.get('keyword')}'",
            'one_year': lambda p: f"год {p.get('year')}",
            'range_years': lambda p: f"период {p.get('from')}-{p.get('to')}",
            'list_years': lambda p: f"годы: {', '.join(map(str, p.get('years_list', [])))}",
            'genre': lambda p: genre_display,
            'genre_year': lambda p: f"{genre_display} ({p.get('from')}-{p.get('to')})",
            'all_movies': lambda p: "весь каталог",
            'actor_search': lambda p: f"фильмы актера '{p.get('actor_name')}'",
        }
        
        formatter = mapping.get(search_type, lambda p: str(p))
        return formatter(params)

    def get_last_searches_formatted(self, limit=5):
        cursor = self.collection.find().sort("timestamp", -1).limit(limit)
        logs = []
        for doc in cursor:
            dt = doc['timestamp'].strftime("%Y-%m-%d %H:%M")
            p_text = self._format_params(doc['search_type'], doc['params'])
            count = doc['results_count']
            res_word = self._pluralize(count, ["результатов", "результат", "результата"])
            logs.append(f"[{dt}] Поиск: {p_text} (Найдено: {count} {res_word})")
        return logs

    def get_popular_searches_formatted(self, limit=5):
        pipeline = [
            {"$group": {"_id": {"st": "$search_type", "pa": "$params"}, "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}, {"$limit": limit}
        ]
        popular = list(self.collection.aggregate(pipeline))
        results = []
        for item in popular:
            p_text = self._format_params(item['_id']['st'], item['_id']['pa'])
            times = self._pluralize(item['count'], ["раз", "раз", "раза"])
            results.append(f"{p_text.capitalize()} — искали {item['count']} {times}")
        return results
        
    def get_last_searches_raw(self, limit=5):
        """Возвращает последние запросы в виде списка словарей для Formatter"""
        cursor = self.collection.find().sort("timestamp", -1).limit(limit)
        raw_data = []
        for doc in cursor:
            raw_data.append({
                "Дата/Время": doc['timestamp'].strftime("%d.%m.%y %H:%M"),
                "Тип запроса": doc['search_type'].replace('_', ' ').capitalize(),
                "Параметры": self._format_params(doc['search_type'], doc['params']),
                "Найдено": f"{doc['results_count']} экз."
            })
        return raw_data

    def get_popular_searches_raw(self, limit=5):
        """Возвращает топ запросов в виде списка словарей для Formatter"""
        pipeline = [
            {"$group": {"_id": {"st": "$search_type", "pa": "$params"}, "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}, 
            {"$limit": limit}
        ]
        popular = list(self.collection.aggregate(pipeline))
        raw_data = []
        for item in popular:
            raw_data.append({
                "Запрос": self._format_params(item['_id']['st'], item['_id']['pa']).capitalize(),
                "Частота": f"{item['count']} {self._pluralize(item['count'], ['раз', 'раз', 'раза'])}"
            })
        return raw_data