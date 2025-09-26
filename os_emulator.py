import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime
import getpass
import platform
import os


SPLIT_BLACKLIST = ['echo']


class ConsoleEmulator:
    def __init__(self):
        # Создаём окно с нужным заголовком и размером
        self.root = tk.Tk()
        # Получаем имя пользователя и название компьютера
        username = getpass.getuser()
        device_name = platform.node()
        current_dir = os.getcwd()
        full_path = os.path.join(current_dir)
        self.root.title(f"Эмулятор - [{username}@{device_name}]     {full_path}")

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
        self.output_area.tag_configure("executable", foreground="#00FF00")
        self.output_area.tag_configure("symlink", foreground="#00FFFF")
        self.output_area.tag_configure("normal", foreground="#FFFFFF")
        self.output_area.tag_configure("error", foreground="#FF0000")
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

    def execute_command(self, event):
        # Получаем введённую пользователем команду
        command = self.input_field.get()
        # Очищаем поле ввода
        self.input_field.delete(0, tk.END)

        # Выводим команду пользователя в консоль, указывая время отправки для удобства
        time = datetime.now()
        self.append_text(f"[{time.hour:02}:{time.minute:02}:{time.second:02}]: {command}\n")
        
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

    def clear_console(self):
        # Включаем поле вывода, очищаем его, затем отключаем
        self.output_area.config(state='normal')
        self.output_area.delete(1.0, tk.END)
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
                console.append_text(f"Переменная '{var}' не распознана\n", 'error')
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
                    console.append_text(f"Переменная '{var}' не распознана\n", 'error')
                    return None
            inp[idx] = part
            idx += 1
        return inp


def process_command(console: ConsoleEmulator, command: str, args: list | None):
    """
    #### Описание:

    Функция для исполнения команды

    #### Параметры:

    console – Объект класса ***ConsoleEmulator***, эмулятор консоли

    command – Команда

    args – список аргументов
    """

    if args != None:
        args = parse_env_variable(console, args)
        if args == None:
            return
    if command == 'clear':
        console.clear_console()
    elif command == 'echo':
        console.append_text(args + '\n')
    elif command == 'ls':
        try:
            current_dir = os.getcwd()
            items = os.listdir(current_dir)
            items.sort()
            
            for item in items:
                full_path = os.path.join(current_dir, item)
                
                if os.path.isdir(full_path):
                    console.append_text(item + '\n', 'directory')
                elif os.path.islink(full_path):
                    console.append_text(item + '\n', 'symlink')
                elif os.access(full_path, os.X_OK):
                    console.append_text(item + '\n', 'executable')
                else:
                    console.append_text(item + '\n', 'normal')
                    
        except Exception as e:
            console.append_text(f"Произошла ошибка: {e}", 'error')
    elif command == 'cd':
        if args == []:
            console.append_text(f"cd требуется указать пункт", 'error')
            return
        try:
            os.chdir(args[0])
            username = getpass.getuser()
            device_name = platform.node()
            current_dir = os.getcwd()
            full_path = os.path.join(current_dir)
            console.root.title(f"Эмулятор - [{username}@{device_name}]     {full_path}")
                    
        except Exception as e:
            console.append_text(f"Произошла ошибка: {e}", 'error')
    elif command == 'exit':
        exit()
    else:
        console.append_text(f"Команда '{command}' не распознана\n", 'error')

    # Запускаем окно Эмулятора консоли, если программа запущена напрямую (не в тестах)
if __name__ == "__main__":
    console = ConsoleEmulator()
    console.run()
