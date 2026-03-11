class Paginator:
    """Универсальный контроллер для постраничного отображения данных."""
    
    def __init__(self, total_rows: int, per_page: int = 10):
        self.per_page = per_page
        self.total_rows = total_rows
        self.total_pages = max(1, (total_rows + per_page - 1) // per_page)
        self.current_page = 0  # 0-based индекс

    def run(self, page_loader, page_renderer):
        """Цикл навигации: Enter — вперед, p — назад, q — выход."""
        while True:
            offset = self.current_page * self.per_page
            data = page_loader(offset, self.per_page)

            # Отрисовка данных
            page_renderer(data, self.current_page + 1, self.total_pages, self.total_rows)

            prompt = "\n[Enter] Вперед | [p] Назад | [q] В меню | [номер страницы]: "
            cmd = input(prompt).strip().lower()

            if cmd == 'q':
                break
            elif cmd == 'p':
                if self.current_page > 0:
                    self.current_page -= 1
                else:
                    print("⏪ Вы на первой странице.")
            elif cmd.isdigit():
                target_page = int(cmd)
                if 1 <= target_page <= self.total_pages:
                    self.current_page = target_page - 1
                else:
                    print(f"❌ Страницы {target_page} не существует.")
            else:
                if self.current_page < self.total_pages - 1:
                    self.current_page += 1
                else:
                    print("🛑 Конец списка. Возврат в начало.")
                    self.current_page = 0