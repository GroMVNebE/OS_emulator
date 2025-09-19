import tkinter as tk
from tkinter import scrolledtext
import subprocess
import threading

class ConsoleEmulator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Эмулятор консоли")
        self.root.geometry("800x600")
        
        # Текстовое поле для вывода
        self.output_area = scrolledtext.ScrolledText(
            self.root, 
            wrap=tk.WORD,
            bg='black',
            fg='white',
            font=('Courier New', 12)
        )
        self.output_area.pack(expand=True, fill='both')
        self.output_area.config(state='disabled')
        
        # Поле ввода
        self.input_frame = tk.Frame(self.root)
        self.input_frame.pack(fill='x', padx=5, pady=5)
        
        self.prompt = tk.Label(self.input_frame, text="$ ", fg='green')
        self.prompt.pack(side='left')
        
        self.input_field = tk.Entry(self.input_frame, bg='black', fg='white')
        self.input_field.pack(side='left', fill='x', expand=True)
        self.input_field.bind('<Return>', self.execute_command)
        
        self.current_directory = "~"
        
    def execute_command(self, event):
        command = self.input_field.get()
        self.input_field.delete(0, tk.END)
        
        # Вывод команды в консоль
        self.append_text(f"$ {command}\n")
        
        # Здесь можно добавить обработку команд
        if command.strip() == 'clear':
            self.clear_console()
        elif command.startswith('echo '):
            self.append_text(command[5:] + "\n")
        else:
            self.append_text(f"Команда '{command}' не распознана\n")
    
    def append_text(self, text):
        self.output_area.config(state='normal')
        self.output_area.insert(tk.END, text)
        self.output_area.see(tk.END)
        self.output_area.config(state='disabled')
    
    def clear_console(self):
        self.output_area.config(state='normal')
        self.output_area.delete(1.0, tk.END)
        self.output_area.config(state='disabled')
    
    def run(self):
        self.root.mainloop()

# Запуск эмулятора
if __name__ == "__main__":
    console = ConsoleEmulator()
    console.run()