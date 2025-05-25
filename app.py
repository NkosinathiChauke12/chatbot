import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
import subprocess
import threading
import fitz  # PyMuPDF
import markdown
from PIL import Image, ImageTk
import webbrowser
import sys
import platform
import speech_recognition as sr
import pyttsx3

class ChatApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("NSFAS Chatbot Assistant")
        self.root.geometry("900x700")
        self.root.minsize(700, 500)

        self.chat_history = []
        self.dark_mode = False
        self.font_size = 11
        self.current_file = None

        self.tts_engine = pyttsx3.init()

        self.setup_styles()
        self.create_widgets()
        self.create_menu()
        self.create_status_bar()
        self.start_chatbot_process()
        self.setup_keybindings()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_create("light", parent="alt", settings={
            "TFrame": {"configure": {"background": "#f5f5f5"}},
            "TLabel": {"configure": {"background": "#f5f5f5", "foreground": "#333333"}},
            "TButton": {"configure": {"background": "#4CAF50", "foreground": "white", "padding": 6, "relief": "flat", "font": ("Segoe UI", 10)}, "map": {"background": [("active", "#45a049")]}},
            "TEntry": {"configure": {"fieldbackground": "white", "foreground": "#333333", "padding": 8, "font": ("Segoe UI", 11)}},
            "TCombobox": {"configure": {"fieldbackground": "white", "foreground": "#333333", "selectbackground": "#e6e6e6"}}
        })
        self.style.theme_create("dark", parent="alt", settings={
            "TFrame": {"configure": {"background": "#2d2d2d"}},
            "TLabel": {"configure": {"background": "#2d2d2d", "foreground": "#f0f0f0"}},
            "TButton": {"configure": {"background": "#2E7D32", "foreground": "white", "padding": 6, "relief": "flat", "font": ("Segoe UI", 10)}, "map": {"background": [("active", "#1B5E20")]}},
            "TEntry": {"configure": {"fieldbackground": "#333333", "foreground": "#f0f0f0", "padding": 8, "font": ("Segoe UI", 11)}},
            "TCombobox": {"configure": {"fieldbackground": "#333333", "foreground": "#f0f0f0", "selectbackground": "#555555"}}
        })
        self.style.theme_use("light")

    def create_widgets(self):
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.chat_frame = ttk.Frame(self.main_frame)
        self.chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        self.text_area = scrolledtext.ScrolledText(self.chat_frame, wrap=tk.WORD, font=("Segoe UI", self.font_size), padx=10, pady=10, bg="white", fg="#333333", insertbackground="#333333", relief="flat")
        self.text_area.pack(fill=tk.BOTH, expand=True)
        self.text_area.config(state=tk.DISABLED)

        self.input_frame = ttk.Frame(self.main_frame)
        self.input_frame.pack(fill=tk.X, pady=(5, 0))

        self.input_var = tk.StringVar()
        self.entry = ttk.Entry(self.input_frame, textvariable=self.input_var, style="TEntry")
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.entry.bind("<Return>", self.send_message)

        self.send_icon = self.create_icon("#ffffff", "#4CAF50")
        self.send_btn = ttk.Button(self.input_frame, image=self.send_icon, compound=tk.LEFT, text=" Send", command=self.send_message, style="TButton")
        self.send_btn.pack(side=tk.RIGHT)

        self.create_toolbar()

    def create_toolbar(self):
        self.toolbar = ttk.Frame(self.main_frame)
        self.toolbar.pack(fill=tk.X, pady=(5, 0))

        self.upload_icon = self.create_icon("#4CAF50", "#f5f5f5")
        ttk.Button(self.toolbar, image=self.upload_icon, compound=tk.LEFT, text=" Upload", command=self.upload_document, style="TButton").pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(self.toolbar, text="Font Size:").pack(side=tk.LEFT, padx=(10, 5))
        self.font_size_var = tk.IntVar(value=self.font_size)
        ttk.Combobox(self.toolbar, textvariable=self.font_size_var, values=[9, 10, 11, 12, 14, 16], width=3, state="readonly").pack(side=tk.LEFT)
        self.font_size_var.trace_add("write", self.change_font_size)

        self.clear_icon = self.create_icon("#f44336", "#f5f5f5")
        ttk.Button(self.toolbar, image=self.clear_icon, compound=tk.LEFT, text=" Clear", command=self.clear_chat, style="TButton").pack(side=tk.RIGHT)

        ttk.Button(self.toolbar, text="🎤 Speak", command=self.voice_input, style="TButton").pack(side=tk.RIGHT, padx=(5, 5))

    def create_menu(self):
        self.menu_bar = tk.Menu(self.root)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Upload Document", command=self.upload_document, accelerator="Ctrl+O")
        self.file_menu.add_command(label="Save Chat History", command=self.save_chat_history, accelerator="Ctrl+S")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.close)

        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.edit_menu.add_command(label="Clear Chat", command=self.clear_chat, accelerator="Ctrl+Del")

        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.view_menu.add_command(label="Toggle Dark Mode", command=self.toggle_theme, accelerator="Ctrl+T")
        self.view_menu.add_separator()
        self.view_menu.add_command(label="Increase Font Size", command=lambda: self.adjust_font_size(1), accelerator="Ctrl++")
        self.view_menu.add_command(label="Decrease Font Size", command=lambda: self.adjust_font_size(-1), accelerator="Ctrl+-")

        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="Documentation", command=lambda: webbrowser.open("https://www.nsfas.org.za/content/bursary-scheme.html"))
        self.help_menu.add_command(label="About", command=self.show_about)

        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.menu_bar.add_cascade(label="Edit", menu=self.edit_menu)
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)
        self.root.config(menu=self.menu_bar)

    def create_status_bar(self):
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=(5, 2))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_keybindings(self):
        self.root.bind("<Control-o>", lambda e: self.upload_document())
        self.root.bind("<Control-s>", lambda e: self.save_chat_history())
        self.root.bind("<Control-t>", lambda e: self.toggle_theme())
        self.root.bind("<Control-plus>", lambda e: self.adjust_font_size(1))
        self.root.bind("<Control-minus>", lambda e: self.adjust_font_size(-1))
        self.root.bind("<Control-Delete>", lambda e: self.clear_chat())

    def create_icon(self, fill_color, bg_color):
        img = Image.new('RGB', (16, 16), bg_color)
        return ImageTk.PhotoImage(img)

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        theme = "dark" if self.dark_mode else "light"
        self.style.theme_use(theme)
        bg = "#1e1e1e" if self.dark_mode else "white"
        fg = "#f0f0f0" if self.dark_mode else "#333333"
        self.text_area.config(bg=bg, fg=fg, insertbackground=fg)
        self.status_var.set(f"Switched to {theme} theme")

    def upload_document(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", ".pdf"), ("Markdown", ".md"), ("Text files", ".txt"), ("All files", ".*")])
        if not file_path:
            return
        self.status_var.set(f"Uploaded {file_path}")
        self.insert_message("System", f"Document {file_path.split('/')[-1]} uploaded and ready.")
    
    def send_message(self, event=None):
        message = self.input_var.get().strip()
        if message:
            self.insert_message("You", message)
            self.input_var.set("")
            if self.chatbot_process and self.chatbot_process.stdin:
                self.chatbot_process.stdin.write(message + "\n")
                self.chatbot_process.stdin.flush()

    def insert_message(self, sender, message):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.insert(tk.END, f"{sender}: {message}\n")
        self.text_area.config(state=tk.DISABLED)
        self.text_area.see(tk.END)

        if sender == "NSFAS Chatbot":
            self.tts_engine.say(message)
            self.tts_engine.runAndWait()

    def clear_chat(self):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)
        self.text_area.config(state=tk.DISABLED)
        self.status_var.set("Chat cleared.")

    def save_chat_history(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.text_area.get(1.0, tk.END))
            self.status_var.set("Chat saved to " + file_path)

    def change_font_size(self, *args):
        self.font_size = self.font_size_var.get()
        self.text_area.config(font=("Segoe UI", self.font_size))

    def adjust_font_size(self, delta):
        self.font_size += delta
        self.font_size_var.set(self.font_size)

    def show_about(self):
        messagebox.showinfo("About", "NSFAS Chatbot that helps student with day-to-day NSFAS related question and provide prompt answers, reducing high volume calls at the call center")

    def close(self):
        self.root.quit()

    def start_chatbot_process(self):
        self.chatbot_process = subprocess.Popen(
            ["python", "chat.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        threading.Thread(target=self.read_from_chatbot, daemon=True).start()

    def read_from_chatbot(self):
        for line in self.chatbot_process.stdout:
            self.insert_message("NSFAS Chatbot", line.strip())

    def voice_input(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            self.status_var.set("Listening...")
            try:
                audio = recognizer.listen(source, timeout=15)
                text = recognizer.recognize_google(audio)
                self.input_var.set(text)
                self.send_message()
                self.status_var.set("Voice input recognized.")
            except sr.WaitTimeoutError:
                self.status_var.set("Listening timed out.")
            except sr.UnknownValueError:
                self.status_var.set("Could not understand.")
            except sr.RequestError:
                self.status_var.set("Speech service error.")


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApplication(root)
    root.mainloop()