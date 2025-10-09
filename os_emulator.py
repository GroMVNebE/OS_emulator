import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime
import getpass
import platform
import os
from dotenv import load_dotenv, set_key
from datetime import datetime
import csv
from typing import Literal
from base64 import b64encode, b64decode

load_dotenv()


SPLIT_BLACKLIST = ['echo']


class ConsoleEmulator:
    def __init__(self):
        # Создаём окно с нужным заголовком и размером
        self.root = tk.Tk()
        # Получаем имя пользователя и название компьютера
        username = getpass.getuser()
        device_name = platform.node()
        self.current_directory = '~'
        self.root.title(
            f"Эмулятор - [{username}@{device_name}]     {self.current_directory}")

        # Настраиваем поле вывода
        # В нём будет отображаться история команд
        # И сообщения об их выполнении
        self.output_area = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            bg='black',
            fg='white',
            font=('Courier New', 12)
        )
        self.output_area.pack(expand=True, fill='both')
        self.output_area.tag_configure("directory", foreground="#87CEEB")
        self.output_area.tag_configure("file", foreground="#00FF9D")
        self.output_area.tag_configure("input", foreground="#4D8DC2")
        self.output_area.tag_configure("normal", foreground="#FFFFFF")
        self.output_area.tag_configure("error", foreground="#FF0000")
        self.append_text(
            f'Путь к VFS: {os.environ["VFS"] if os.environ["VFS"] != "None" else "не задан"}, можно изменить с помощью config --vfs="Путь/к/файлу/vfs.csv"\n')
        self.append_text(
            f'Путь к log-файлу: {os.environ["log"] if os.environ["log"] != "None" else "не задан"}, можно изменить с помощью config --log="Путь/к/файлу/log.csv"\n')
        self.append_text(
            f'Путь к стартовому скрипту: {os.environ["start-script"] if os.environ["start-script"] != "None" else "не задан"}, можно изменить с помощью config --start="Путь/к/файлу/start-script.sh"\n')
        self.output_area.config(state='disabled')

        # Настраиваем панель ввода
        self.input_frame = tk.Frame(self.root)
        self.input_frame.pack(fill='x', padx=5, pady=5)
        # Настраиваем заголовок для поля ввода
        self.prompt = tk.Label(self.input_frame, text="$", fg='green')
        self.prompt.pack(side='left')
        # Настраиваем поле ввода
        self.input_field = tk.Entry(self.input_frame, bg='black', fg='white')
        self.input_field.pack(side='left', fill='x', expand=True)
        self.input_field.bind('<Return>', self.execute_command)

        self.current_directory = "~"

        if os.environ['start-script']:
            if os.path.exists(os.environ['start-script']):
                file = open(os.environ['start-script'], encoding='utf-8')
                for line in file:
                    try:
                        parse_command(self, line)
                    except Exception as e:
                        self.append_text(f'Произошла ошибка {e}!', 'error')
                        break

    def execute_command(self, event):
        # Получаем введённую пользователем команду
        command = self.input_field.get()
        # Очищаем поле ввода
        self.input_field.delete(0, tk.END)

        # Выводим команду пользователя в консоль, указывая время отправки для удобства
        time = datetime.now()
        self.append_text(
            f"[{time.hour:02}:{time.minute:02}:{time.second:02}]: {command}\n", 'input')

        # Обрабатываем команду
        parse_command(self, command)

    def append_text(self, text, tag='normal'):
        # Включаем поле вывода и добавляем в конец переданный текст
        self.output_area.config(state='normal')
        self.output_area.insert(tk.END, text, tag)
        # Переводим положение в конец (чтобы добавленный текст был виден)
        self.output_area.see(tk.END)
        # Отключаем поле вывода
        self.output_area.config(state='disabled')

    def clear_console(self, count=None):
        # Включаем поле вывода, очищаем его, затем отключаем
        self.output_area.config(state='normal')
        if count:
            st = float(self.output_area.index(tk.END)) - (count + 2)
            if st < 1.0:
                st = 1.0
        else:
            st = 1.0
        self.output_area.delete(st, tk.END)
        if st != 1.0:
            self.append_text('\n')
        self.output_area.config(state='disabled')

    def run(self):
        self.root.mainloop()


def parse_command(console: ConsoleEmulator, raw_command: str):
    """
    #### Описание:

    Функция для **парсинга** команды и дальнейшей **обработки**

    #### Параметры:

    console – Объект класса ***ConsoleEmulator***, эмулятор консоли

    raw_command – Необработанная команда
    """

    # Получаем команду
    command = raw_command.split()[0].strip()
    # Получаем и обрабатываем аргументы
    if command not in SPLIT_BLACKLIST:
        args = raw_command.split()[1:]
        for i in range(len(args)):
            args[i] = args[i].strip()
    else:
        args = raw_command.replace(command + ' ', '', 1)
    # Запускаем обработку команды
    process_command(console, command, args)


def parse_env_variable(console: ConsoleEmulator, inp: str | list):
    """
    #### Описание:

    Функция для парсинга **переменных окружения среды** среди аргументов

    #### Параметры:

    console - Объект класса ***ConsoleEmulator***, эмулятор консоли

    inp - ***входные данные в виде строки или списка***, среди которых нужно найти **переменные среды**

    #### Возвращаемое значение:

    Возвращает изменённый **inp**, в котором подходящие переменные заменены на их значения

    Возвращает **None** в случае ошибки
    """
    if type(inp) == str:
        while '$' in inp:
            st = inp.find('$')
            end = inp.find(' ', inp.find('$'))
            if end == -1:
                end = len(inp)
            var = inp[st:end]
            if var == "$HOME":
                inp = inp.replace(var, 'C:/', 1)
            else:
                console.append_text(
                    f"Переменная '{var}' не распознана\n", 'error')
                return None
        return inp
    else:
        idx = 0
        while idx < len(inp):
            part = inp[idx]
            while '$' in part:
                st = part.find('$')
                end = part.find(' ', part.find('$'))
                if end == -1:
                    end = len(part)
                var = part[st:end]
                if var == "$HOME":
                    part = part.replace(var, 'C:/', 1)
                else:
                    console.append_text(
                        f"Переменная '{var}' не распознана\n", 'error')
                    return None
            inp[idx] = part
            idx += 1
        return inp


def send_log(log: str, type: Literal['info', 'error', 'output']):
    """
    #### Описание:

    Функция для сохранения логов в csv файле

    #### Параметры:

    log - ***Лог***, который должен быть сохранён

    type - ***Тип лога***: информация, ошибка или вывод
    """
    if os.environ['log'] != 'None':
        if os.path.exists(os.environ['log']):
            access = False
            valid = False
            with open(os.environ['log'], 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file, delimiter=';')
                access = True
                if reader.fieldnames == ['time', 'type', 'event']:
                    valid = True
            if access and valid:
                with open(os.environ['log'], 'a', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file, delimiter=';')
                    time = datetime.now()
                    writer.writerow(
                        [f'[{time.day:02}-{time.month:02}-{time.year:02}  {time.hour:02}:{time.minute:02}:{time.second:02}]', type, log])
            elif access:
                with open(os.environ['log'], 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file, delimiter=';')
                    writer.writerow(['time', 'type', 'event'])
                    time = datetime.now()
                    writer.writerow(
                        [f'[{time.day:02}-{time.month:02}-{time.year:02}  {time.hour:02}:{time.minute:02}:{time.second:02}]', type, log])


class Component():

    path: str
    """**Путь** к файлу/директории"""
    name: str
    """**Имя** файла/директории"""
    type: str
    """**Тип** компонента: ***Файл/Директория***"""

    def __init__(self, path: str, name: str, type: str, content: str):
        self.path = path
        self.name = name
        self.type = type
        self.content = content

    def view_file(self):
        if self.type == 'file':
            return b64decode(self.content).decode()


def get_directory_content(path_to_dir: str):
    """
    #### Описание:

    Функция для получения содержимого директории

    #### Параметры:

    path_to_dir – Путь к директории

    #### Возвращаемое значение:

    Возвращает список компонентов (***директорий/файлов***), расположенных по переданному пути

    Возвращает **None** в случае ошибки
    """
    files = None
    if os.environ['VFS']:
        if os.path.exists(os.environ['VFS']):
            files = []
            with open(os.environ['VFS'], 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file, delimiter=';')
                if reader.fieldnames == ['path', 'filename', 'type', 'content']:
                    for row in reader:
                        if row['path'] == path_to_dir:
                            files.append(
                                Component(row['path'], row['filename'], row['type'], row['content']))
    return files


def get_file(path_to_file: str):
    file = None
    if os.environ['VFS']:
        if os.path.exists(os.environ['VFS']):
            with open(os.environ['VFS'], 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file, delimiter=';')
                if reader.fieldnames == ['path', 'filename', 'type', 'content']:
                    for row in reader:
                        if row['path'] + row['filename'] == path_to_file and row['type'] == 'file':
                            file = Component(
                                row['path'], row['filename'], row['type'], row['content'])
                            return file
    return file


def exist_file(path_to_file: str):
    """
    #### Описание:

    Функция для проверки существования директории

    #### Параметры:

    path_to_file – Путь к директории

    #### Возвращаемое значение:

    Возвращает **True/False** в зависимости от существования файла
    """
    exists = False
    if os.environ['VFS']:
        if os.path.exists(os.environ['VFS']):
            with open(os.environ['VFS'], 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file, delimiter=';')
                if reader.fieldnames == ['path', 'filename', 'type', 'content']:
                    for row in reader:
                        if row['path'] + row['filename'] == path_to_file and row['type'] == 'file':
                            exists = True
                            return exists
    return exists


def exist_directory(path_to_dir: str):
    """
    #### Описание:

    Функция для проверки существования директории

    #### Параметры:

    path_to_dir – Путь к директории

    #### Возвращаемое значение:

    Возвращает **True/False** в зависимости от существования директории
    """
    exists = False
    if os.environ['VFS']:
        if os.path.exists(os.environ['VFS']):
            with open(os.environ['VFS'], 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file, delimiter=';')
                if reader.fieldnames == ['path', 'filename', 'type', 'content']:
                    for row in reader:
                        if row['path'] == path_to_dir or (row['path'] + row['filename'] + '/' == path_to_dir and row['type'] == 'directory'):
                            exists = True
                            return exists
    return exists


def parse_rel_path(path: str, cur_path: str):
    """
    #### Описание:

    Функция для парсинга относительного пути и конвертации его в абсолютный

    #### Параметры:

    path - **Переданный** путь

    cur_path - ***Текущий*** путь

    #### Возвращаемое значение:

    Возвращает ***абсолютный путь***
    """
    parts = path.split('/')
    for part in parts:
        if part == '..':
            cur_path = cur_path[0:cur_path.rfind('/')]
        elif part == '.':
            cur_path = cur_path
        else:
            cur_path = cur_path + '/' + part
    return cur_path

def check_directory_name(dir_name: str):
    """
    #### Описание:

    Функция для проверки имени директории

    #### Параметры:

    dir_name - **Имя директории**

    #### Возвращаемое значение:

    Возвращает **True/False** в завимости от того, соответствует ли имя файла шаблону
    """
    correct = True
    for sym in dir_name:
        if not(sym >= 'a' and sym <= 'z' or sym >= 'A' and sym <= 'Z' or sym >= '0' and sym <= '9' or sym == '_'):
            correct = False
            break
    return correct

def create_dir(dir_name: str, path: str):
    """
    #### Описание:

    Функция для создания директории

    #### Параметры:

    dir_name - **Имя директории**

    path - **Путь**, по которому располагается директория
    """
    if os.environ['VFS']:
        if os.path.exists(os.environ['VFS']):
            with open(os.environ['VFS'], 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file, delimiter=';')
                writer.writerow([path, dir_name, 'directory', None])

def get_all_content():
    files: list[Component] = get_directory_content('~/')
    idx = 0
    while idx < len(files):
        if files[idx].type == 'directory':
            files = files.__add__(get_directory_content(files[idx].path + files[idx].name + '/'))
        idx += 1
    return files

def remove_dir(dir_name: str, path: str):
    """
    #### Описание:

    Функция для удаления директории

    #### Параметры:

    dir_name - **Имя директории**

    path - **Путь**, по которому располагается директория
    """
    if os.environ['VFS']:
        if os.path.exists(os.environ['VFS']):
            all_files = get_all_content()
            deleted_path = path + dir_name
            with open(os.environ['VFS'], 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file, delimiter=';')
                writer.writerow(['path', 'filename', 'type', 'content'])
                for file in all_files:
                    if file.path.find(deleted_path) != 0 and file.path + file.name != deleted_path:
                        writer.writerow([file.path, file.name, file.type, file.content])



def process_command(console: ConsoleEmulator, command: str, args: list | None):
    """
    #### Описание:

    Функция для исполнения команды

    #### Параметры:

    console – Объект класса ***ConsoleEmulator***, эмулятор консоли

    command – Команда

    args – список аргументов
    """
    raw_command = command
    if type(args) == list:
        for arg in args:
            raw_command += ' ' + arg
    elif type(args) == str:
        raw_command += args
    send_log(raw_command, 'info')

    if args != None:
        args = parse_env_variable(console, args)
        if args == None:
            return
    if command == 'clear':
        if len(args) == 0:
            console.clear_console()
        elif len(args) == 1:
            if args[0] == '-h' or args[0] == '--help':
                console.append_text(
                    '-h/--help - отобразить помощь по использованию команды\n-с=N/--count=N - удалить N последних строк в консоли\nБез аргументов - очистить консоль\n')
            if '=' in args[0]:
                subcom = args[0].split('=')[0]
                subarg = args[0].split('=')[1]
                if subcom == '-c' or subcom == '--count':
                    n = None
                    try:
                        n = int(subarg)
                    except Exception as e:
                        console.append_text(
                            'Требуется указать целое число строк\n', 'error')
                        return
                    if n != None:
                        console.clear_console(n)
                else:
                    console.append_text(
                        f'Неизвестный аргумент {args[0]}. Для помощи введите clear -h\n', 'error')
            else:
                console.append_text(
                    f'Неизвестный аргумент {args[0]}. Для помощи введите clear -h\n', 'error')
        else:
            console.append_text(
                'Команда clear поддерживает только 1 аргумент', 'error')
    elif command == 'echo':
        console.append_text(args + '\n')
    elif command == 'ls':
        if len(args) == 0:
            console.append_text(f'Содержимое {console.current_directory}\n')
            files: list[Component] = get_directory_content(
                console.current_directory + '/')
            if files:
                for file in files:
                    console.append_text(f'{file.name}\n', file.type)
        elif len(args) == 1:
            if args[0] == '-h' or args[0] == '--help':
                console.append_text(
                    '-h/--help - отобразить помощь по использованию команды\nПуть/к/файлу - просмотреть содержимое по указанному пути\nБез аргументов - просмотреть содержимое текущей директории\n')
            else:
                while args[0] != '' and args[0][-1] == '/':
                    args[0] = args[0][0:-1]
                if args[0] == '':
                    return
                if args[0][0] != '~':
                    args[0] = parse_rel_path(
                        args[0], console.current_directory)
                if exist_directory(args[0] + '/'):
                    console.append_text(f'Содержимое {args[0] + "/"}\n')
                    files: list[Component] = get_directory_content(
                        args[0] + '/')
                    if files:
                        for file in files:
                            console.append_text(f'{file.name}\n', file.type)
                else:
                    console.append_text(
                        f'Не найдена директория {args[0] + "/"}\n', 'error')
        else:
            console.append_text(
                'Команда ls поддерживает только 1 аргумент', 'error')
    elif command == 'cd':
        if len(args) != 1:
            console.append_text(
                'В качестве аргумента команды требуется указать путь к файлу\n', 'error')
            return
        while args[0] != '' and args[0][-1] == '/':
            args[0] = args[0][0:-1]
        if args[0] == '':
            return
        if args[0][0] != '~':
            args[0] = parse_rel_path(args[0], console.current_directory)
        if exist_directory(args[0] + '/'):
            console.current_directory = args[0]
            username = getpass.getuser()
            device_name = platform.node()
            console.root.title(
                f"Эмулятор - [{username}@{device_name}]     {console.current_directory}")
    elif command == 'who':
        if len(args) == 1:
            if args[0] == '-h' or args[0] == '--help':
                console.append_text(
                    'Без аргументов - отобразить текущего пользователя\n-h/--help - отобразить помощь по использованию команды\n')
            else:
                console.append_text(
                    f'Неизвестный аргумент {args[0]}. Для помощи введите clear -h\n', 'error')
        elif len(args) == 0:
            username = getpass.getuser()
            console.append_text(f'Текущий пользователь - {username}\n')
        else:
            console.append_text(
                f'Команда принимает не более 1 аргумента\n', 'error')
    elif command == 'wc':
        if len(args) == 1:
            if args[0] == '-h' or args[0] == '--help':
                console.append_text(
                    'Один аргумент (путь к файлу) - отображает кол-во символов, строк и слов\nДва аргумента (путь к файлу, аргумент для вывода)\n-h/--help - отобразить помощь по использованию команды\n-m - показать кол-во символов в файле\n-l - показать кол-во строк в файле\n-w - показать кол-во слов в файле\n')
            else:
                while args[0] != '' and args[0][-1] == '/':
                    args[0] = args[0][0:-1]
                if args[0] == '':
                    return
                if args[0][0] != '~':
                    args[0] = parse_rel_path(
                        args[0], console.current_directory)
                if exist_file(args[0]):
                    file: Component = get_file(args[0])
                    content = b64decode(file.content).decode()
                    while '  ' in content:
                        content = content.replace('  ', ' ', 1)
                    lines = content.count("\n") + 1
                    console.append_text(
                        f'{len(content)} {lines} {len(content.split())}')
                else:
                    console.append_text(
                        f'Не найден файл {args[0]}\n', 'error')
        elif len(args) == 2:
            while args[0] != '' and args[0][-1] == '/':
                args[0] = args[0][0:-1]
            if args[0] == '':
                return
            if args[0][0] != '~':
                args[0] = parse_rel_path(
                    args[0], console.current_directory)
            if exist_file(args[0]):
                file: Component = get_file(args[0])
                content = b64decode(file.content).decode()
                while '  ' in content:
                    content = content.replace('  ', ' ', 1)
                if args[1] in ['-m', '-l', '-w']:
                    if args[1] == '-m':
                        console.append_text(f'{len(content)}')
                    elif args[1] == '-l':
                        lines = content.count("\n") + 1
                        console.append_text(f'{lines}')
                    else:
                        console.append_text(f'{len(content.split())}')
                else:
                    console.append_text(
                        f'Неизвестный аргумент {args[1]}. Для помощи используйте -h\n', 'error')
            else:
                console.append_text(
                    f'Не найден файл {args[0]}\n', 'error')
        else:
            console.append_text(
                f'Команда принимает не более 2 аргументов\n', 'error')    elif command == "mkdir":
        if len(args) == 1:
            if args[0] == '-h' or args[0] == '--help':
                console.append_text('Один аргумент - имя создаваемой директории, -h/--help - отобразить помощь по использованию команды\n')
            else:
                if check_directory_name(args[0]) and exist_directory(console.current_directory + '/' + args[0] + '/') is False:
                    create_dir(args[0], console.current_directory + '/')
                    console.append_text('Директория успешно создана\n')
                else:
                    if check_directory_name(args[0]) is False:
                        console.append_text(f'Имя {args[0]} содержит недопустимые символы. Имя директории может состоять только из символов a-Z, 0-9 и "_"\n', 'error')
                    else:
                        console.append_text(f'Директория {args[0]} уже существует!\n', 'error')
        else:
            console.append_text('mkdir принимает один аргумент - название директории! Для помощи используйте mkdir -h\n', 'error')
    elif command == "rm":
        if len(args) == 1:
            if args[0] == '-h' or args[0] == '--help':
                console.append_text('Один аргумент - имя удаляемого файла/директории, -h/--help - отобразить помощь по использованию команды\n')
            else:
                if exist_directory(console.current_directory + '/' + args[0] + '/'):
                    remove_dir(args[0], console.current_directory + '/')
                    console.append_text('Директория успешно удалена\n')
                else:
                    console.append_text(f'Директории {args[0]} не существует!\n', 'error')
        else:
            console.append_text('rm принимает один аргумент - название директории! Для помощи используйте rm -h\n', 'error')

    elif command == 'exit':
        if len(args) == 0:
            exit()
        elif len(args) == 1 and (args[0] == '-h' or args[0] == '--help'):
            console.append_text(
                'Без аргументов - завершить работу Эмулятора\n-h/--help - отобразить помощь по использованию команды\n')
        else:
            if len(args) == 1:
                console.append_text(
                    f'Неизвестный аргумент {args[0]}. Для помощи введите clear -h\n', 'error')
            else:
                console.append_text(
                    f'Команда принимает не более 1 аргумента\n', 'error')
    elif command == 'config':
        if len(args) == 0:
            console.append_text(
                f'Путь к VFS: {os.environ["VFS"] if os.environ["VFS"] != "None" else "не задан"}, можно изменить с помощью config --vfs="Путь/к/файлу/vfs.csv"\n')
            console.append_text(
                f'Путь к log-файлу: {os.environ["log"] if os.environ["log"] != "None" else "не задан"}, можно изменить с помощью config --log="Путь/к/файлу/log.csv"\n')
            console.append_text(
                f'Путь к стартовому скрипту: {os.environ["start-script"] if os.environ["start-script"] != "None" else "не задан"}, можно изменить с помощью config --start="Путь/к/файлу/start-script.sh"\n')
            return
        for arg in args:
            if '=' not in arg or arg.count('"') != 2:
                console.append_text(
                    f'Неверный формат записи аргумента: {arg}. Требуется: --arg="Path"\n', 'error')
                return
            subcom = arg.split('=')[0]
            subarg = arg.split('=')[1]
            if type(subarg) != str:
                console.append_text(
                    'В качестве пути требуется указать строку!\n', 'error')
                return
            subarg = subarg.replace('"', '')
            if subcom == '--vfs':
                if os.path.exists(subarg):
                    if '.' not in subarg or subarg.split('.')[-1] != 'csv':
                        console.append_text(
                            f'В качестве VFS требуется указывать .csv файл!\n', 'error')
                        return
                    set_key('.env', 'VFS', subarg)
                    load_dotenv(override=True)
                    console.append_text(f'Путь к VFS: "{subarg}"\n')
                else:
                    console.append_text(f'Файл {subarg} не найден!\n', 'error')
                    return
            elif subcom == '--log':
                if os.path.exists(subarg):
                    if '.' not in subarg or subarg.split('.')[-1] != 'csv':
                        console.append_text(
                            f'В качестве log-файла требуется указывать .csv файл!\n', 'error')
                        return
                    set_key('.env', 'log', subarg)
                    load_dotenv(override=True)
                    console.append_text(f'Путь к log-файлу: "{subarg}"\n')
                else:
                    console.append_text(f'Файл {subarg} не найден!\n', 'error')
                    return
            elif subcom == '--start':
                if os.path.exists(subarg):
                    if '.' not in subarg or subarg.split('.')[-1] != 'txt':
                        console.append_text(
                            f'В качестве start-файла требуется указывать .txt файл!\n', 'error')
                        return
                    set_key('.env', 'start-script', subarg)
                    load_dotenv(override=True)
                    console.append_text(f'Путь к start-файлу: "{subarg}"\n')
                else:
                    console.append_text(f'Файл {subarg} не найден!\n', 'error')
                    return
            else:
                console.append_text(f'Неверный аргумент: {subcom}\n', 'error')
                return
    else:
        console.append_text(f"Команда '{command}' не распознана\n", 'error')


# Запускаем окно Эмулятора консоли, если программа запущена напрямую (не в тестах)
if __name__ == "__main__":
    console = ConsoleEmulator()
    console.run()
