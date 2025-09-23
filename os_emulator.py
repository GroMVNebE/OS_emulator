import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime
import getpass
import platform


SPLIT_BLACKLIST = ['echo']


class ConsoleEmulator:
    def __init__(self):
        # Создаём окно с нужным заголовком и размером
        self.root = tk.Tk()
        # Получаем имя пользователя и название компьютера
        username = getpass.getuser()
        device_name = platform.node()
        self.root.title(f"Эмулятор - [{username}@{device_name}]")

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
        self.output_area.config(state='disabled')

        # Настраиваем панель ввода
        self.input_frame = tk.Frame(self.root)
        self.input_frame.pack(fill='x', padx=5, pady=5)
        # Настраиваем заголовок для поля ввода
        self.prompt = tk.Label(self.input_frame, text="$ ", fg='green')
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
        self.append_text(
            f"[{time.hour:02}:{time.minute:02}:{time.second:02}]: {command}\n")

        parse_command(self, command)

    def append_text(self, text):
        # Включаем поле вывода и добавляем в конец переданный текст
        self.output_area.config(state='normal')
        self.output_area.insert(tk.END, text)
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


def process_command(console: ConsoleEmulator, command: str, args: list | None):
    """
    #### Описание:

    Функция для исполнения команды

    #### Параметры:

    console – Объект класса ***ConsoleEmulator***, эмулятор консоли

    command – Команда

    args – список аргументов
    """

    if command == 'clear':
        console.clear_console()
    elif command == 'echo':
        console.append_text(args + '\n')
    else:
        console.append_text(f"Команда '{command}' не распознана\n")

    # Запускаем окно Эмулятора консоли, если программа запущена напрямую (не в тестах)
if __name__ == "__main__":
    console = ConsoleEmulator()
    console.run()
