from colorama import Fore as Color, init
from datetime import datetime
import os
from menu import Menu
import sys

init()

# Глобальная переменная для хранения текущей папки
current_folder = os.path.join("sql", datetime.now().strftime("%Y-%m-%d"))

def colored_input(prompt, color=Color.LIGHTMAGENTA_EX):
    return input(color + prompt + Color.RESET)

def multi_input(prompt, color=Color.LIGHTMAGENTA_EX):
    print(color + prompt + Color.RESET)
    lines = []
    while True:
       line = sys.stdin.readline().rstrip('\n')
       if not line:
          break
       lines.append(line)

    return '\n'.join(lines)

def ensure_folder_exists(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)

def create_table_file(folder):
    ensure_folder_exists(folder)
    file_path = os.path.join(folder, "Создание таблицы.md")
    
    if os.path.exists(file_path):
        choice = colored_input("Файл уже существует. Перезаписать? (0/1) ").lower()
        if choice != '1':
            print(Color.CYAN + "Создание таблицы отменено.")
            return

    print(Color.CYAN + "\nКод для создания таблицы: SHOW CREATE TABLE name;")
    create_code = multi_input("Введите код для создания таблицы: ")
    fill_code = multi_input("Введите код для заполнения таблицы: ")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f">СТРУКТУРА ТАБЛИЦЫ\n```sql\n{create_code}\n```\n\n>ЗАПОЛНЕНИЕ ТАБЛИЦЫ\n```sql\n{fill_code}\n```")
    
    print(Color.CYAN + f'Файл создания таблицы создан: "{file_path}"')
    exit()

def add_task_request(folder):
    ensure_folder_exists(folder)
    task_number = colored_input("Введите номер задания: ")
    file_path = os.path.join(folder, f"Задание #{task_number}.md")
    
    mode = 'a'
    if os.path.exists(file_path):
        choice = colored_input("Файл существует. Добавить запрос (1) или перезаписать (2)? ").lower()
        if choice == '2':
            mode = 'w'

    if mode == 'a' and os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            request_num = content.count('>ЗАПРОС') + 1
    else:
        request_num = 1

    request_content = multi_input("Введите содержание запроса: ")
    
    with open(file_path, mode, encoding='utf-8') as f:
        if mode == 'a' and os.path.getsize(file_path) > 0:
            f.write('\n')
        f.write(f'>ЗАПРОС {request_num}\n```sql\n{request_content}\n```\n')
    
    print(Color.CYAN + f'Запрос добавлен в "{file_path}"')
    exit()

def select_folder():
    global current_folder
    folder_name = colored_input("Введите название папки: ")
    current_folder = os.path.join("sql", folder_name)
    ensure_folder_exists(current_folder)
    os.system('cls' if os.name == 'nt' else 'clear')
    print(Color.CYAN + f'Текущая папка изменена на: {current_folder}\n')

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    menu = Menu("Выберите действие", True)
    menu.AddUpdateOption("Добавить запрос", lambda: add_task_request(current_folder))
    menu.AddUpdateOption("Выбрать папку", select_folder)
    menu.AddUpdateOption("Создать/обновить таблицу", lambda: create_table_file(current_folder))
    menu.AddUpdateOption("Выйти", lambda: exit())
    while True:
        menu.Show()