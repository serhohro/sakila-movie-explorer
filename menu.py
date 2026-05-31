from typing import Callable, Dict, Optional, Tuple, Any

class Menu:
    """
    Universal class for creating and managing a console-based application menu.
    Supports automatic item numbering and callback functions.
    """

    def __init__(self, title: str = "MENU") -> None:
        """
        Initializes the menu.
        :param title: The header text displayed above the menu options.
        """
        self.title: str = title
        # Store menu items as: {number: (description, function)}
        self._items: Dict[str, Tuple[str, Optional[Callable[..., Any]]]] = {}
        self._is_running: bool = True

    def add_item(self, text: str, action: Optional[Callable[..., Any]]) -> None:
        """
        Adds a new option to the menu with an automatically assigned index 
        (the choice number displayed to the user in the app).
        :param text: Text description of the command.
        :param action: The function to call when selected. If None, triggers program exit.
        """
        # Index is determined based on the current size of the items dictionary
        next_index: str = str(len(self._items) + 1)
        self._items[next_index] = (text, action)

    def _display_menu(self) -> None:
        """ 
        Renders the menu interface in the console:
        Displays the header and all available menu options.
        """
        print(f"\n=== {self.title.upper()} ===")
        for key, (label, _) in self._items.items():
            print(f"{key}. {label}")

    def run(self) -> None:
        """
        Starts the infinite loop for processing user input.
        Runs until exit_program is called or an exit option is selected.
        """
        while self._is_running:
            self._display_menu()
            user_choice: str = input("👉 Select an option: ").strip()

            if user_choice not in self._items:
                print("❌ Error: Invalid menu option. Please try again.")
                continue

            # Extract the associated action
            _, callback_function = self._items[user_choice]

            if callback_function:
                callback_function() # Execute the command
            else:
                self.exit_program() # Exit if no function is provided

    def exit_program(self) -> None:
        """
        Gracefully terminates the menu loop and application execution:
        Stops the main menu processing loop.
        """
        print("\n👋 Ending your movie journey. See you next time!")
        self._is_running = False