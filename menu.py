from colorama import Fore as Color

class Menu:
    __name__:str
    __options__ = {}
    __repeat__ = False
    
    def __init__(self, name, repeat_menu_if_error):
        self.__name__ = f"{Color.LIGHTRED_EX}--=+=-- {name} --=+=--"
        self.__repeat__ = repeat_menu_if_error
    
    # Add option to the menu
    def AddUpdateOption(self, name, action):
        self.__options__[name] = action
        
    # Returns option if it exists, otherwise None
    def GetOption(self, name):
        try:
            return self.__options__[name]
        except:
            return None
    
    # Delete option from the menu
    def DeleteOption(self, name):
        if self.GetOption(name):
            del self.__options__[name]
    
    # Show menu
    def Show(self):
        # showing options
        keys = list(self.__options__.keys())
        
        print(self.__name__)
        for b in keys:
            print(f"{Color.CYAN}{keys.index(b) + 1}. {Color.LIGHTMAGENTA_EX}{b}{Color.WHITE}")
        print()
        
        # getting choice
        choice:int
        # check if correct
        try:
            choice = int(input(Color.CYAN + "Выбор: " + Color.WHITE))
        except:
            print(f"{Color.LIGHTRED_EX}Неверные входные данные!{Color.WHITE}\n")
            if self.__repeat__:
                self.Show()
            return False
        
        # check if corret
        if choice <= 0 or choice > len(keys):
            print(f"{Color.LIGHTRED_EX}Выбрана несуществующая опция!{Color.WHITE}\n")
            if self.__repeat__:
                self.Show()
            return False
        
        # executing
        self.__options__[keys[choice - 1]]()
        return True