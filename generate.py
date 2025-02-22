from colorama import Fore as Color, init
from datetime import datetime
import os
import sys
import subprocess
import re
from menu import Menu
import sqlparse
import webbrowser
from random import randint

try:
    import keyring
except ImportError:
    keyring = None  # Если keyring не установлен, будет использовано обычное поведение

init()

SERVICE_NAME = "CHMIGA_SQL_NEW"  # Имя сервиса для хранения токена

def get_current_date():
    """
    Возвращает текущую дату в формате 'YYYY-MM-DD'.
    """
    return datetime.now().strftime("%Y-%m-%d")

menu = Menu(get_current_date(),
            label_color=Color.RED,
            option_color=Color.LIGHTMAGENTA_EX,
            aux_color=Color.CYAN)

def colored_input(prompt):
    """
    Запрашивает у пользователя ввод строки, выводя prompt в заданном цвете.
    Возвращает введённую строку.
    """
    return input(menu.option_color + prompt + Color.RESET)

def multi_input(prompt):
    """
    Выводит prompt (цветом option_color), затем считывает многострочный ввод пользователя
    до пустой строки. Каждую введённую строку обрабатывает через sqlparse:
      - Приводит ключевые слова SQL к верхнему регистру,
      - Не изменяет отступы (reindent=False).
    Возвращает объединённый текст введённых строк.
    """
    print(menu.option_color + prompt + Color.RESET)
    lines = []
    while True:
        line = sys.stdin.readline().rstrip('\n')
        if not line:
            break
        lines.append(sqlparse.format(line, keyword_case="upper", reindent=False, encoding="utf-8"))
    return '\n'.join(lines)

def ensure_folder_exists(folder):
    """
    Проверяет существование указанной папки. Если папки нет, создаёт её.
    """
    if not os.path.exists(folder):
        os.makedirs(folder)

def extract_table_name(sql_code):
    """
    Извлекает имя таблицы из SQL-кода, используя регулярное выражение,
    ищущее шаблон CREATE TABLE [IF NOT EXISTS] `имя`.
    Если имя не найдено, возвращает 'таблица'.
    """
    pattern = re.compile(r"create\s+table\s+(if\s+not\s+exists\s+)?[`'\"]?(\w+)[`'\"]?", re.IGNORECASE)
    match = pattern.search(sql_code)
    if match:
        return match.group(2)
    return "таблица"

def generate_aggregate_file(folder):
    """
    Генерирует общий файл (~Общий файл.md) в указанной папке:
      - Если существует файл "Создание таблицы.md", добавляет его содержимое.
      - Ищет все файлы "Задание #<номер>.md", сортирует их по номеру
        и добавляет в общий файл.
    """
    ensure_folder_exists(folder)
    aggregate_path = os.path.join(folder, "~Общий файл.md")
    aggregate_content = ""

    structure_file = os.path.join(folder, "Создание таблицы.md")
    if os.path.exists(structure_file):
        with open(structure_file, 'r', encoding='utf-8') as f:
            content = f.read()
        aggregate_content += "# Создание таблицы\n\n" + content + "\n\n"

    task_files = [f for f in os.listdir(folder) if f.startswith("Задание") and f.endswith(".md")]

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

    print(menu.aux_color + f'Общий файл обновлен: "{aggregate_path}"')

def create_table_file(folder):
    """
    Создаёт или перезаписывает файл "Создание таблицы.md" в папке folder.
    Запрашивает у пользователя SQL-код для создания и заполнения таблицы,
    добавляет название таблицы в заголовки.
    После создания файла обновляет общий файл и завершает работу.
    """
    ensure_folder_exists(folder)
    file_path = os.path.join(folder, "Создание таблицы.md")
    
    if os.path.exists(file_path):
        choice = colored_input("Файл уже существует. Перезаписать? (0/1) ")
        if choice.strip() != '1':
            print(menu.aux_color + "Создание таблицы отменено.")
            exit()

    print(menu.aux_color + "\nПример кода для создания таблицы: SHOW CREATE TABLE имя_таблицы;")
    create_code = multi_input("Введите код для создания таблицы: ")
    fill_code = multi_input("Введите код для заполнения таблицы: ")

    table_name = extract_table_name(create_code)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(
            f">СТРУКТУРА ТАБЛИЦЫ {table_name}\n```sql\n{create_code}\n```\n\n"
            f">ЗАПОЛНЕНИЕ ТАБЛИЦЫ {table_name}\n```sql\n{fill_code}\n```"
        )
    
    print(menu.aux_color + f'Файл создания таблицы создан/обновлен: "{file_path}"')
    generate_aggregate_file(folder)
    exit()

def add_task_request(folder):
    """
    Добавляет (или перезаписывает) запрос в файл "Задание #<номер>.md".
    Если файл существует и выбран режим 'добавить', увеличивает счётчик запросов.
    После записи файла обновляет общий файл и завершает работу.
    """
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
    
    print(menu.aux_color + f'Запрос добавлен в "{file_path}"')
    generate_aggregate_file(folder)
    exit()

def select_folder():
    """
    Запрашивает у пользователя название папки, формирует путь вида 'sql/<папка>',
    переключается на неё и обновляет заголовок меню.
    """
    global current_folder
    folder_name = colored_input("Введите название папки: ").strip()
    current_folder = os.path.join("sql", folder_name)
    ensure_folder_exists(current_folder)
    os.system('cls' if os.name == 'nt' else 'clear')
    menu.set_label(folder_name)

def get_github_token():
    """
    Пытается получить сохранённый GitHub-токен из системного хранилища.
    Если токен не найден, запрашивает его у пользователя и сохраняет в keyring.
    """
    token = None
    if keyring:
        token = keyring.get_password(SERVICE_NAME, "github_token")
    if not token:
        token = colored_input("Введите ваш GitHub-токен: ").strip()
        if keyring:
            keyring.set_password(SERVICE_NAME, "github_token", token)
    return token

def update_git():
    """
    Обновляет remote-URL репозитория с использованием сохранённого GitHub-токена,
    добавляет изменения, коммитит с датой и пушит в ветку main.
    При ошибке выводит сообщение и завершает работу.
    """
    token = get_github_token()
    try:
        subprocess.run([
            "git", "remote", "set-url", "origin",
            f"https://{token}@github.com/TeamKait/CHMIGA_SQL_NEW.git"
        ], check=True)

        print("\n" + menu.option_color + "git add ." + Color.LIGHTBLACK_EX)
        subprocess.run(["git", "add", "."], check=True)

        commit_message = get_current_date()
        print(menu.option_color + f"git commit -m '{commit_message}'" + Color.LIGHTBLACK_EX)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)

        print(menu.option_color + "git push origin main" + Color.LIGHTBLACK_EX)
        subprocess.run(["git", "push", "origin", "main"], check=True)

        print(menu.aux_color + "Git обновлён.")
        exit()
    except subprocess.CalledProcessError:
        print(Color.RED + "Ошибка при выполнении git команды. Проверьте введённый токен." + Color.RESET)
        exit()

def aggregate():
    generate_aggregate_file(current_folder)
    exit()

def open_github():
    webbrowser.open_new_tab("https://github.com/TeamKait/CHMIGA_SQL_NEW")

colors = [
    Color.BLUE,
    Color.CYAN,
    Color.GREEN,
    Color.LIGHTBLACK_EX,
    Color.LIGHTBLUE_EX,
    Color.LIGHTCYAN_EX,
    Color.LIGHTGREEN_EX,
    Color.LIGHTMAGENTA_EX,
    Color.LIGHTRED_EX,
    Color.LIGHTWHITE_EX,
    Color.LIGHTYELLOW_EX,
    Color.MAGENTA,
    Color.RED,
    Color.WHITE,
    Color.YELLOW
]

def set_colors():
    menu.label_color = colors[randint(0, len(colors) - 1)]
    menu.option_color = colors[randint(0, len(colors) - 1)]
    menu.aux_color = colors[randint(0, len(colors) - 1)]

if __name__ == "__main__":
    # Текущая папка по умолчанию — sql/<текущая_дата>
    current_folder = os.path.join("sql", get_current_date())

    # Добавляем пункты меню
    sql_folder = menu.set_folder("SQL")
    menu.add_option("Добавить запрос", lambda: add_task_request(current_folder), sql_folder)
    menu.add_option("Создать & заполнить таблицу", lambda: create_table_file(current_folder), sql_folder)
    menu.add_option("Создать общий файл", lambda: aggregate(), sql_folder)
    menu.add_option("Выбрать папку", select_folder)
    git_folder = menu.set_folder("GIT")
    menu.add_option("Обновить git", update_git, git_folder)
    menu.add_option("Открыть github", open_github, git_folder)
    menu.add_separator()
    menu.add_option("Сменить цвет", set_colors)

    # Вызов меню (при выборе пункта программа завершает работу, как и было)
    menu.show()
