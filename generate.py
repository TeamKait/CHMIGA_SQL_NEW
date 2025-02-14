from colorama import Fore as Color, init
from datetime import datetime
import os
import sys
import subprocess
import re
from menu import Menu

init()

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

def extract_table_name(sql_code):
    """
    Извлекает имя таблицы из SQL-кода, ищет шаблон CREATE TABLE [IF NOT EXISTS] `имя`
    """
    pattern = re.compile(r"create\s+table\s+(if\s+not\s+exists\s+)?[`'\"]?(\w+)[`'\"]?", re.IGNORECASE)
    match = pattern.search(sql_code)
    if match:
        return match.group(2)
    return "таблица"

def generate_aggregate_file(folder):
    """
    Генерирует общий файл (Общий_файл.md) на основе файла создания таблицы
    и всех файлов с запросами (название которых начинается с "Задание #")
    """
    ensure_folder_exists(folder)
    aggregate_path = os.path.join(folder, "Общий_файл.md")
    aggregate_content = ""

    structure_file = os.path.join(folder, "Создание таблицы.md")
    if os.path.exists(structure_file):
        with open(structure_file, 'r', encoding='utf-8') as f:
            content = f.read()
        aggregate_content += "# Создание таблицы\n\n" + content + "\n\n"

    # Находим все файлы с запросами
    task_files = [f for f in os.listdir(folder) if f.startswith("Задание") and f.endswith(".md")]
    # Сортируем по номеру задания
    def extract_task_number(filename):
        m = re.search(r'Задание\s*#\s*(\d+)', filename)
        return int(m.group(1)) if m else 0
    task_files.sort(key=extract_task_number)

    if task_files:
        aggregate_content += "# Запросы\n\n"
        for task_file in task_files:
            path = os.path.join(folder, task_file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            aggregate_content += f"## {task_file}\n\n" + content + "\n\n"

    with open(aggregate_path, 'w', encoding='utf-8') as f:
        f.write(aggregate_content)
    print(Color.CYAN + f'Общий файл обновлен: "{aggregate_path}"')

def create_table_file(folder):
    ensure_folder_exists(folder)
    file_path = os.path.join(folder, "Создание таблицы.md")
    
    if os.path.exists(file_path):
        choice = colored_input("Файл уже существует. Перезаписать? (0/1) ")
        if choice.strip() != '1':
            print(Color.CYAN + "Создание таблицы отменено.")
            exit()

    print(Color.CYAN + "\nПример кода для создания таблицы: SHOW CREATE TABLE имя_таблицы;")
    create_code = multi_input("Введите код для создания таблицы: ")
    fill_code = multi_input("Введите код для заполнения таблицы: ")

    table_name = extract_table_name(create_code)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f">СТРУКТУРА ТАБЛИЦЫ {table_name}\n```sql\n{create_code}\n```\n\n>ЗАПОЛНЕНИЕ ТАБЛИЦЫ {table_name}\n```sql\n{fill_code}\n```")
    
    print(Color.CYAN + f'Файл создания таблицы создан/обновлен: "{file_path}"')
    generate_aggregate_file(folder)
    exit()

def add_task_request(folder):
    ensure_folder_exists(folder)
    task_number = colored_input("Введите номер задания: ").strip()
    file_path = os.path.join(folder, f"Задание #{task_number}.md")
    
    mode = 'a'
    request_num = 1
    if os.path.exists(file_path):
        choice = colored_input("Файл существует. Добавить запрос (1) или перезаписать (2)? ").strip()
        if choice == '2':
            mode = 'w'
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            request_num = content.count('>ЗАПРОС') + 1

    request_content = multi_input("Введите содержание запроса: ")
    
    with open(file_path, mode, encoding='utf-8') as f:
        if mode == 'a' and os.path.getsize(file_path) > 0:
            f.write('\n')
        f.write(f'>ЗАПРОС {request_num}\n```sql\n{request_content}\n```\n')
    
    print(Color.CYAN + f'Запрос добавлен в "{file_path}"')
    generate_aggregate_file(folder)
    exit()

def select_folder():
    global current_folder
    folder_name = colored_input("Введите название папки: ").strip()
    current_folder = os.path.join("sql", folder_name)
    ensure_folder_exists(current_folder)
    os.system('cls' if os.name == 'nt' else 'clear')
    print(Color.CYAN + f'Текущая папка изменена на: {current_folder}\n')
    generate_aggregate_file(current_folder)

def update_git():
    generate_aggregate_file(current_folder)
    print("\n" + Color.MAGENTA + "git add ." + Color.LIGHTBLACK_EX)
    subprocess.run(["git", "add", "."], check=True)

    commit_message = datetime.now().strftime('%Y-%m-%d')
    print(Color.MAGENTA + f"git commit -m '{commit_message}'" + Color.LIGHTBLACK_EX)
    subprocess.run(["git", "commit", "-m", commit_message], check=True)

    print(Color.MAGENTA + "git push origin main" + Color.LIGHTBLACK_EX)
    subprocess.run(["git", "push", "origin", "main"], check=True)
    print(Color.CYAN + "Git обновлён.")
    exit()

def aggregate():
    generate_aggregate_file(current_folder)
    exit()

if __name__ == "__main__":
    current_folder = os.path.join("sql", datetime.now().strftime("%Y-%m-%d"))
    ensure_folder_exists(current_folder)
    os.system('cls' if os.name == 'nt' else 'clear')
    menu = Menu("Выберите действие", True)
    menu.AddUpdateOption("Добавить запрос", lambda: add_task_request(current_folder))
    menu.AddUpdateOption("Выбрать папку", select_folder)
    menu.AddUpdateOption("Создать/обновить таблицу", lambda: create_table_file(current_folder))
    menu.AddUpdateOption("Создать общий файл", aggregate)
    menu.AddUpdateOption("Обновить git", update_git)
    menu.AddUpdateOption("Выйти", lambda: exit())
    while True:
        menu.Show()