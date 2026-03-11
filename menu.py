from typing import Callable, Dict, Optional, Tuple


class Menu:
    """Класс для создания и управления консольным меню."""

    def __init__(self, title: str = "МЕНЮ"):
        self.title: str = title
        # Храним элементы в словаре: {номер_строка: (текст, функция)}
        self._items: Dict[str, Tuple[str, Optional[Callable]]] = {}
        self._is_running: bool = True

    def add_item(self, text: str, action: Optional[Callable]) -> None:
        """
        Добавляет пункт меню с автоматическим назначением порядкового номера.

        Args:
            text: Описание пункта меню.
            action: Функция-коллбэк, вызываемая при выборе. 
                    Если None, выполнение приведет к выходу.
        """
        # Определяем следующий номер на основе текущего количества элементов
        next_index = str(len(self._items) + 1)
        self._items[next_index] = (text, action)

    def _display_menu(self) -> None:
        """Отрисовывает заголовок и все доступные пункты меню."""
        print(f"\n=== {self.title} ===")
        for key, (label, _) in self._items.items():
            print(f"{key}. {label}")

    def run(self) -> None:
        """Запускает бесконечный цикл обработки пользовательского ввода."""
        while self._is_running:
            self._display_menu()
            user_choice = input("Выберите пункт: ").strip()

            if user_choice not in self._items:
                print("❌ Неверный пункт меню. Попробуйте снова.")
                continue

            # Извлекаем функцию (callback) из кортежа по ключу
            _, callback_function = self._items[user_choice]

            if callback_function:
                callback_function()
            else:
                self.exit_program()

    def exit_program(self) -> None:
        """Останавливает цикл выполнения меню."""
        print("👋 Выход из программы")
        self._is_running = False