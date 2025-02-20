from __future__ import annotations
from colorama import Fore as Color, init
from typing import Callable
from os import system

init()


class Menu:
    """
    Terminal Menu system supporting options, folders (submenus), and separators.
    It offers two modes: 
      - Expanded: displays the full menu tree with composite numbering.
      - Collapsed: step-by-step navigation (folders open on demand).
    """

    def __init__(self, label: str, label_color=Color.LIGHTRED_EX,
                 option_color=Color.LIGHTMAGENTA_EX, aux_color=Color.CYAN,
                 include_exit: bool = True):
        """
        Initialize the Menu.

        :param label: The menu title.
        :param label_color: The color for the title.
        :param option_color: The color for options.
        :param aux_color: The auxiliary color (used for numbering, extra text, etc.).
        :param include_exit: If True, automatically add an "exit" option.
        """
        self.__items__ = []
        self.set_label(label, label_color)
        self.label_color = label_color
        self.option_color = option_color
        self.aux_color = aux_color
        self.__include_exit__ = include_exit
        self.__exit_included__ = False

    def set_label(self, label: str, color=Color.RED) -> str:
        """
        Set the menu title with optional color formatting.

        :param label: The menu title.
        :param color: Color code for the title.
        :return: The formatted title.
        """
        if color is not None:
            self.__label__ = f"{color}=== {label} ==={Color.RESET}"
        else:
            self.__label__ = label
        return self.__label__

    def add_option(self, name: str, action: Callable[[], None],
                   parent: MenuFolder = None) -> MenuOption:
        """
        Add an option to the menu (or to a specified folder).

        :param name: The option's name.
        :param action: A callable to execute when the option is selected.
        :param parent: Optional parent folder; if None, the option is added at root.
        :return: The created MenuOption instance.
        """
        option = MenuOption(name, action, parent)
        if parent is None:
            self.__items__.append(option)
        else:
            parent.add_child(option)
        return option

    def set_folder(self, name: str, parent: MenuFolder = None) -> MenuFolder:
        """
        Create a folder (submenu) and add it to the menu or a specified folder.

        :param name: The folder's name.
        :param parent: Optional parent folder; if None, the folder is added at root.
        :return: The created MenuFolder instance.
        """
        folder = MenuFolder(name, parent)
        if parent is None:
            self.__items__.append(folder)
        else:
            parent.add_child(folder)
        return folder

    def add_separator(self, parent: MenuFolder = None) -> MenuSeparator:
        """
        Add a separator to the menu or to a specified folder.

        :param parent: Optional parent folder; if None, the separator is added at root.
        :return: The created MenuSeparator instance.
        """
        separator = MenuSeparator()
        if parent is None:
            self.__items__.append(separator)
        else:
            parent.add_child(separator)
        return separator

    def get_item(self, name: str):
        """
        Retrieve a menu item by name (if the item has a 'name' attribute).

        :param name: The name of the item.
        :return: The menu item if found; otherwise, None.
        """
        for item in self.__items__:
            if hasattr(item, 'name') and item.name == name:
                return item
        return None

    def remove_item(self, name: str):
        """
        Remove a menu item by its name.

        :param name: The name of the item to remove.
        """
        item = self.get_item(name)
        if item is not None:
            self.__items__.remove(item)

    def __clear_console__(self):
        """
        Clear the console screen.
        """
        system('cls')

    def show(self, clear_console: bool = True, collapsed: bool = False):
        """
        Display the menu.

        In collapsed mode, navigation is step-by-step through folders.
        In expanded mode, the full menu tree with composite numbering is shown.

        :param clear_console: If True, clears the console before displaying.
        :param collapsed: If True, use collapsed (step-by-step) mode.
        """
        # Automatically add the exit option only once if requested.
        if self.__include_exit__ and not self.__exit_included__:
            self.add_option("exit", exit)
            self.__exit_included__ = True

        if clear_console:
            self.__clear_console__()
        print(self.__label__)

        if collapsed:
            selected_option = self.__show_collapsed(self.__items__, path=[])
            if selected_option is not None and selected_option != "back":
                self.__clear_console__()
                selected_option.invoke()
            else:
                print(f"{Color.RED}No available options or menu closed.{Color.RESET}")
        else:
            # Expanded mode: display the full menu tree with composite numbering.
            selectable = {}

            def recursive_print(items, parent_number="", depth=0):
                indent = "   " * depth
                counter = 0
                for item in items:
                    if isinstance(item, MenuSeparator):
                        print(f"{indent}{self.aux_color}- - -{Color.RESET}")
                    elif isinstance(item, MenuFolder):
                        if item.children:
                            counter += 1
                            number = (f"{parent_number}{counter}" if parent_number == ""
                                      else f"{parent_number}.{counter}")
                            print(f"{indent}{self.aux_color}{number}. "
                                  f"{self.option_color}[{item.name}]{Color.RESET}")
                            recursive_print(item.children, number, depth + 1)
                        else:
                            print(f"{indent}{self.option_color}[{item.name}]{Color.RESET} "
                                  f"{self.aux_color}<empty>{Color.RESET}")
                    elif isinstance(item, MenuOption):
                        counter += 1
                        number = (f"{parent_number}{counter}" if parent_number == ""
                                  else f"{parent_number}.{counter}")
                        print(f"{indent}{self.aux_color}{number}. "
                              f"{self.option_color}{item.name}{Color.RESET}")
                        selectable[number] = item

            recursive_print(self.__items__, "", 0)
            selection = input(f"\n{self.aux_color}Select an option: {Color.RESET}")
            if selection in selectable:
                chosen_option = selectable[selection]
                self.__clear_console__()
                chosen_option.invoke()
            else:
                print(f"{Color.RED}Invalid selection!{Color.RESET}")

    def __show_collapsed(self, items, path):
        """
        Private method for displaying the menu in collapsed mode (step-by-step navigation).

        :param items: List of menu items at the current level.
        :param path: List of selected folders from the root to the current level.
        :return: The selected MenuOption, or "back" if the user chooses to go back.
        """
        while True:
            self.__clear_console__()
            current_path = " / ".join(folder.name for folder in path) if path else "ROOT"
            print(f"{self.__label__} (Current path: {current_path})\n")

            # At root level, if folders exist, we normally show only folders.
            # However, we always want to include the exit option.
            if not path:
                folders = [item for item in items if isinstance(item, MenuFolder)]
                exit_options = [item for item in items
                                if isinstance(item, MenuOption) and item.name.lower() == "exit"]
                current_items = folders + exit_options if folders else items
            else:
                current_items = items

            if not current_items:
                print(f"{self.aux_color}<empty>{Color.RESET}")
                input(f"\n{self.aux_color}Press Enter to go back...{Color.RESET}")
                return "back"

            # In nested levels, display "0. Back" at the beginning.
            if path:
                print(f"{self.aux_color}0. Back{Color.RESET}")

            mapping = {}
            num = 1
            for item in current_items:
                if isinstance(item, MenuSeparator):
                    print(f"{self.aux_color}- - -{Color.RESET}")
                else:
                    if isinstance(item, MenuFolder):
                        if not item.children:
                            print(f"{self.aux_color}{num}. "
                                  f"{self.option_color}[{item.name}]{Color.RESET} "
                                  f"{self.aux_color}<empty>{Color.RESET}")
                        else:
                            print(f"{self.aux_color}{num}. "
                                  f"{self.option_color}[{item.name}]{Color.RESET}")
                    elif isinstance(item, MenuOption):
                        print(f"{self.aux_color}{num}. "
                              f"{self.option_color}{item.name}{Color.RESET}")
                    mapping[num] = item
                    num += 1

            selection = input(f"\n{self.aux_color}Select an option: {Color.RESET}")
            if path and selection == "0":
                return "back"

            try:
                choice = int(selection)
            except ValueError:
                print(f"{Color.RED}Invalid selection!{Color.RESET}")
                input("Press Enter to continue...")
                continue

            if choice not in mapping:
                print(f"{Color.RED}Invalid selection!{Color.RESET}")
                input("Press Enter to continue...")
                continue

            selected_item = mapping[choice]
            if isinstance(selected_item, MenuFolder):
                if not selected_item.children:
                    print(f"{Color.RED}Folder is empty!{Color.RESET}")
                    input("Press Enter to continue...")
                    continue
                else:
                    result = self.__show_collapsed(selected_item.children, path + [selected_item])
                    if result == "back":
                        continue
                    elif result is not None:
                        return result
            elif isinstance(selected_item, MenuOption):
                return selected_item


class MenuFolder:
    """
    Represents a folder (submenu) in the menu.
    """

    def __init__(self, name: str, parent: MenuFolder = None):
        """
        Initialize a MenuFolder.

        :param name: The folder's name.
        :param parent: Optional parent folder.
        """
        self.name = name
        self.parent = parent
        self.children = []
        self.dimension = 0 if parent is None else parent.dimension + 1

    def add_child(self, item):
        """
        Add a child item (option, folder, or separator) to this folder.

        :param item: The child item to add.
        """
        self.children.append(item)


class MenuOption:
    """
    Represents an actionable option in the menu.
    """

    def __init__(self, name: str, action: Callable[[], None],
                 folder: MenuFolder = None):
        """
        Initialize a MenuOption.

        :param name: The option's name.
        :param action: A callable to execute when the option is selected.
        :param folder: Optional parent folder.
        """
        self.name = name
        self.action = action
        self.folder = folder
        self.dimension = 0 if folder is None else folder.dimension + 1

    def invoke(self):
        """
        Execute the option's action.
        """
        self.action()


class MenuSeparator:
    """
    Represents a visual separator in the menu.
    Separators are not selectable and are displayed as a line.
    """

    def __init__(self):
        pass