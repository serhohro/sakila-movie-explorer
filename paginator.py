from typing import Callable, List, Dict, Any

class Paginator:
    """ Universal controller for paginated data display. """
    
    def __init__(self, total_rows: int, per_page: int = 10) -> None:
        """
        Initializes the paginator.
        :param total_rows: Total number of records in the dataset.
        :param per_page: Number of records to show per page.
        """
        self.per_page: int = per_page
        self.total_rows: int = total_rows
        # Calculate the total number of pages
        self.total_pages: int = max(1, (total_rows + per_page - 1) // per_page)
        self.current_page: int = 0  # Current page index (starts at 0)

    def run(self, 
            page_loader: Callable[[int, int], List[Dict[str, Any]]], 
            page_renderer: Callable[[List[Dict[str, Any]], int, int, int], None]) -> None:
        """
        Data navigation loop.
        :param page_loader: Function to load data (accepts offset and limit).
        :param page_renderer: Rendering function (accepts data, current page, total pages, and total rows).
        """
        while True:
            # Calculate offset for the SQL query
            offset: int = self.current_page * self.per_page
            # Load a chunk of data
            data: List[Dict[str, Any]] = page_loader(offset, self.per_page)

            # Render the page via Formatter
            page_renderer(data, self.current_page + 1, self.total_pages, self.total_rows)

            prompt: str = "\n[Enter] Next | [p] Previous | [q] To Menu | [page number]: "
            cmd: str = input(prompt).strip().lower()

            if cmd == 'q':
                break
            elif cmd == 'p':
                if self.current_page > 0:
                    self.current_page -= 1
                else:
                    print("⏪ You are on the first page.")
            elif cmd.isdigit():
                target_page: int = int(cmd)
                if 1 <= target_page <= self.total_pages:
                    self.current_page = target_page - 1
                else:
                    print(f"❌ Page {target_page} does not exist.")
            else:
                # Go to the next page
                if self.current_page < self.total_pages - 1:
                    self.current_page += 1
                else:
                    print("⏩ You are on the last page.")
                    self.current_page = 0