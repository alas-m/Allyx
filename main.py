import tkinter as tk
from tkinter import filedialog, ttk
import subprocess, os, re, keyword
import jedi
import tkinter.font as tkfont

COLOR_SCHEME = {
    "background": "#1e1e1e",
    "foreground": "#ffffff",
    "keyword": "#d085ff",
    "string": "#e9ffa8",
    "comment": "#a1f7bb",
    "function": "#9ee8ff",
    "number": "#ffca75",
    "error": "#ffa3b9",
    "warning": "#b273ff"
}

PYTHON_KEYWORDS = keyword.kwlist

class CodeEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Allyx")
        self.geometry("1200x700")
        self.filename = None

        self._load_fonts()
        self._create_widgets()
        self._style_scrollbars()
        self._bind_events()
        self._create_tags()
        self.iconbitmap("icon.ico")

    def _create_widgets(self):
        main_frame = tk.Frame(self, bg=COLOR_SCHEME["background"])
        main_frame.pack(fill="both", expand=True)

        # === File Explorer ===
        explorer_frame = tk.Frame(main_frame, width=200, bg="#2b2b2b", borderwidth=0, highlightthickness=0, relief="flat")
        explorer_frame.pack(side="left", fill="y")
        self.file_list = tk.Listbox(explorer_frame,
                                    bg="#2b2b2b", fg="white",
                                    selectbackground="#444",
                                    activestyle="none",
                                    borderwidth=0, highlightthickness=0,
                                    font=self.font_regular,
                                    relief="flat")
        self.file_list.pack(fill="both", expand=True, padx=10, pady=10)
        self._populate_file_explorer()
        self.file_list.bind("<<ListboxSelect>>", self._open_selected_file)

        # === Editor Area ===
        editor_frame = tk.Frame(main_frame, bg=COLOR_SCHEME["background"], borderwidth=0, highlightthickness=0, relief="flat")
        editor_frame.pack(side="right", fill="both", expand=True)

        # Toolbar
        toolbar = tk.Frame(editor_frame, bg="#333333", borderwidth=0, highlightthickness=0, relief="flat")
        toolbar.pack(fill="x")
        run_button = tk.Button(toolbar, text="▶ Run", command=self.run_code,
                               bg="#444", fg="white", font=self.font_regular,
                               bd=0, highlightthickness=0, relief="flat",
                               padx=10, pady=5)
        run_button.pack(side="left", padx=10, pady=10)

        # Editor + line number
        text_frame = tk.Frame(editor_frame, bg=COLOR_SCHEME["background"])
        text_frame.pack(fill="both", expand=True)

        self.line_numbers = tk.Text(text_frame, width=5, padx=5,
                                    bg="#2e2e2e", fg="#888888",
                                    state="disabled", font=self.font_regular,
                                    borderwidth=0, highlightthickness=0, relief="flat")
        self.line_numbers.pack(side="left", fill="y")

        self.text = tk.Text(text_frame, bg=COLOR_SCHEME["background"], fg=COLOR_SCHEME["foreground"],
                            insertbackground="white", undo=True, font=self.font_regular, wrap="none",
                            borderwidth=0, highlightthickness=0, relief="flat")
        self.text.pack(side="left", fill="both", expand=True)

        scroll_y = ttk.Scrollbar(text_frame, orient="vertical", command=self._on_scroll_y, style="Custom.Vertical.TScrollbar")
        scroll_y.pack(side="right", fill="y")
        self.text.configure(yscrollcommand=scroll_y.set)

        scroll_x = ttk.Scrollbar(editor_frame, orient="horizontal", command=self.text.xview, style="Custom.Horizontal.TScrollbar")
        scroll_x.pack(fill="x")
        self.text.configure(xscrollcommand=scroll_x.set)

        # Output Console
        self.output_console = tk.Text(self, height=8, bg="#1a1a1a", fg="#ffca75", font=self.font_regular,
                                      state="disabled", borderwidth=0, highlightthickness=0, relief="flat")
        self.output_console.pack(fill="x", side="bottom")

        # Autocomplete Listbox
        self.suggestion_box = tk.Listbox(self, bg="#292929", fg="white", height=4, font=self.font_regular,
                                         borderwidth=0, highlightthickness=0, relief="flat")
        self.suggestion_box.place(x=0, y=0)
        self.suggestion_box.place_forget()
        self.suggestion_box.bind("<<ListboxSelect>>", self.insert_completion)

        # Menu
        self._create_menu()

    def _load_fonts(self):
        base_path = os.path.join(os.getcwd(), "src")
        self.font_regular = tkfont.Font(family="Rubik", size=12)
        self.font_italic = tkfont.Font(family="Rubik", size=12, slant="italic")

    def _update_file_selection(self):
        for i in range(self.file_list.size()):
            self.file_list.itemconfig(i, bg="#2b2b2b", fg="white")
        idx = self.file_list.curselection()
        if idx:
            self.file_list.itemconfig(idx, bg="#3a3a55", fg="white")

    def _create_menu(self):
        menu_bar = tk.Menu(self)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_command(label="Save As", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menu_bar)

    def _create_tags(self):
        for name, color in COLOR_SCHEME.items():
            if name not in ("background", "foreground"):
                self.text.tag_configure(name, foreground=color)

    def _bind_events(self):
        self.text.bind("<KeyRelease>", self._on_key_release)
        self.text.bind("<MouseWheel>", lambda e: self._update_line_numbers())
        self.text.bind("<ButtonRelease-1>", lambda e: self._update_line_numbers())
        self.text.bind("<Return>", self.handle_auto_indent)
        self.text.bind("<Control-a>", self.select_all)
        self.text.bind("<Control-b>", lambda e: self.run_code())
        self.text.bind("<KeyRelease>", self.show_autocomplete)
        self.text.bind("<Tab>", self.insert_completion)

    def _on_key_release(self, event=None):
        self.highlight_syntax()
        self._update_line_numbers()

    def _populate_file_explorer(self):
        self.file_list.delete(0, tk.END)
        for file in os.listdir():
            if file.endswith(".py"):
                self.file_list.insert(tk.END, file)

    def _open_selected_file(self, event):
        index = self.file_list.curselection()
        if index:
            filename = self.file_list.get(index)
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", content)
            self.filename = filename
            self.highlight_syntax()
            self._update_line_numbers()
            self._update_file_selection()
            self.title(f"{filename} - Allyx")

    def _on_scroll_y(self, *args):
        self.text.yview(*args)
        self.line_numbers.yview(*args)

    def _update_line_numbers(self):
        self.line_numbers.config(state="normal")
        self.line_numbers.delete("1.0", "end")
        lines = int(self.text.index("end").split(".")[0]) - 1
        self.line_numbers.insert("1.0", "\n".join(str(i) for i in range(1, lines + 1)))
        self.line_numbers.config(state="disabled")

    def highlight_syntax(self):
        content = self.text.get("1.0", tk.END)
        for tag in self.text.tag_names():
            self.text.tag_remove(tag, "1.0", tk.END)

        patterns = [
            (r"#.*", "comment"),
            (r'(\".*?\"|\'.*?\')', "string"),
            (r"\b\d+(\.\d+)?\b", "number"),
            (r"\berror\b", "error"),
            (r"\bwarn\b", "warning")
        ]

        for regex, tag in patterns:
            for match in re.finditer(regex, content):
                self._apply_tag(tag, match)

        for kw in PYTHON_KEYWORDS:
            for match in re.finditer(rf"\b{kw}\b", content):
                self._apply_tag("keyword", match)

        for match in re.finditer(r"\bdef\s+(\w+)", content):
            self._apply_tag("function", match, group=1)

    def _apply_tag(self, tag, match, group=0):
        start = f"1.0+{match.start(group)}c"
        end = f"1.0+{match.end(group)}c"
        self.text.tag_add(tag, start, end)

    def handle_auto_indent(self, event):
        index = self.text.index("insert").split(".")[0]
        line = self.text.get(f"{index}.0", f"{index}.end")
        indent = re.match(r"^(\s+)", line)
        indent = indent.group(1) if indent else ""
        if line.strip().endswith(":"):
            indent += "    "
        self.text.insert("insert", f"\n{indent}")
        return "break"

    def select_all(self, event=None):
        self.text.tag_add("sel", "1.0", "end-1c")
        return "break"

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py"), ("All Files", "*.*")])
        if path:
            with open(path, "r", encoding="utf-8") as f:
                self.text.delete("1.0", tk.END)
                self.text.insert("1.0", f.read())
            self.filename = path
            self.highlight_syntax()
            self._update_line_numbers()

    def save_file(self):
        if self.filename:
            with open(self.filename, "w", encoding="utf-8") as f:
                f.write(self.text.get("1.0", tk.END))
        else:
            self.save_file_as()

    def save_file_as(self):
        path = filedialog.asksaveasfilename(defaultextension=".py")
        if path:
            self.filename = path
            self.save_file()

    def run_code(self):
        code = self.text.get("1.0", tk.END)
        self.output_console.config(state="normal")
        self.output_console.delete("1.0", tk.END)
        try:
            with open("temp_run.py", "w", encoding="utf-8") as f:
                f.write(code)
            result = subprocess.run(["python", "temp_run.py"], capture_output=True, text=True)
            self.output_console.insert("1.0", result.stdout + "\n" + result.stderr)
        except Exception as e:
            self.output_console.insert("1.0", str(e))
        self.output_console.config(state="disabled")

    def show_autocomplete(self, event=None):
        if event and event.keysym in ["space", "Return", "Tab", "BackSpace", "Escape", "parenleft", "bracketleft", "quotedbl", "apostrophe", "colon", "semicolon", "comma", "period"]:
            self.suggestion_box.place_forget()
            return

        index = self.text.index("insert")
        line, col = map(int, index.split("."))
        code = self.text.get("1.0", "end-1c")

        lines = code.splitlines()
        if line > len(lines): return
        current_line = lines[line - 1] if line <= len(lines) else ""

        if col > 0 and col <= len(current_line):
            if col < len(current_line) and current_line[col].isalnum():
                self.suggestion_box.place_forget()
                return

        try:
            script = jedi.Script(code, path=self.filename or "")
            completions = script.complete(line, col)
            if completions:
                self.suggestion_box.delete(0, tk.END)
                for c in completions:
                    self.suggestion_box.insert(tk.END, c.name)
                x, y, _, _ = self.text.bbox("insert")
                if x is not None and y is not None:
                    self.suggestion_box.place(x=x + 100, y=y + 70)
                    self.suggestion_box.lift()
            else:
                self.suggestion_box.place_forget()
        except:
            self.suggestion_box.place_forget()

    def insert_completion(self, event=None):
        if self.suggestion_box.winfo_ismapped() and self.suggestion_box.size() > 0:
            try:
                selected = self.suggestion_box.get(self.suggestion_box.curselection())
            except:
                selected = self.suggestion_box.get(0)

            index = self.text.index("insert")
            line, col = map(int, index.split("."))
            line_text = self.text.get(f"{line}.0", f"{line}.end")

            word_start = col
            while word_start > 0 and (line_text[word_start - 1].isalnum() or line_text[word_start - 1] == "_"):
                word_start -= 1

            self.text.delete(f"{line}.{word_start}", index)
            self.text.insert(f"{line}.{word_start}", selected)
            self.suggestion_box.place_forget()
            return "break"
        else:
            self.text.insert("insert", "    ")
            return "break"

    def _style_scrollbars(self):
        style = ttk.Style()
        style.theme_use('default')

        style.configure("Custom.Vertical.TScrollbar",
                        background="#444444",
                        troughcolor="#2b2b2b",
                        bordercolor="#2b2b2b",
                        arrowcolor="#888888",
                        relief="flat", gripcount=0, width=10)
        style.map("Custom.Vertical.TScrollbar",
                  background=[("active", "#666666")])

        style.configure("Custom.Horizontal.TScrollbar",
                        background="#444444",
                        troughcolor="#2b2b2b",
                        bordercolor="#2b2b2b",
                        arrowcolor="#888888",
                        relief="flat", gripcount=0, height=10)
        style.map("Custom.Horizontal.TScrollbar",
                  background=[("active", "#666666")])

if __name__ == "__main__":
    CodeEditor().mainloop()
