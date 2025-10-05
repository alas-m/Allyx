import tkinter as tk
from tkinter import filedialog, ttk
import subprocess, os, re, keyword
import jedi
import tkinter.font as tkfont

COLOR_SCHEME = {
    "background": "#1e1e1e",
    "foreground": "#d4d4d4",
    "keyword": "#569cd6",
    "string": "#ce9178",
    "comment": "#6a9955",
    "function": "#dcdcaa",
    "number": "#b5cea8",
    "error": "#f44747",
    "warning": "#ff8800",
    "class": "#4ec9b0",
    "parameter": "#9cdcfe"
}

PYTHON_KEYWORDS = keyword.kwlist

class CodeEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Allyx")
        self.geometry("1200x700")
        self.filename = None
        self.run_button_state = "normal"
        self.current_explorer_path = os.getcwd()

        self._load_fonts()
        self._create_widgets()
        self._style_scrollbars()
        self._bind_events()
        self._create_tags()
        try:
            self.iconbitmap("icon.ico")
        except:
            pass

    def _create_widgets(self):
        self.configure(bg=COLOR_SCHEME["background"])
        main_container = tk.Frame(self, bg="#252526", bd=0, highlightthickness=0)
        main_container.pack(fill="both", expand=True, padx=1, pady=1)
        
        main_frame = tk.Frame(main_container, bg=COLOR_SCHEME["background"])
        main_frame.pack(fill="both", expand=True)

        sidebar = tk.Frame(main_frame, width=220, bg="#252526", borderwidth=0, highlightthickness=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        explorer_header = tk.Frame(sidebar, bg="#2d2d30", height=60)
        explorer_header.pack(fill="x", pady=(0, 5))
        explorer_header.pack_propagate(False)

        explorer_label = tk.Label(explorer_header, text="EXPLORER", 
                                 bg="#2d2d30", fg="#cccccc", font=(self.font_regular.actual("family"), 9, "bold"),
                                 anchor="w", padx=10)
        explorer_label.pack(fill="x", side="top", pady=(5, 0))

        folder_button = tk.Button(explorer_header, text="📁", 
                                 command=self.change_directory,
                                 bg="#2d2d30", fg="#cccccc",
                                 bd=0, highlightthickness=0, relief="flat",
                                 font=(self.font_regular.actual("family"), 12))
        folder_button.pack(side="left", padx=10, pady=5)

        self.path_label = tk.Label(explorer_header, text=os.path.basename(os.getcwd()),
                                  bg="#2d2d30", fg="#888888", 
                                  font=(self.font_regular.actual("family"), 8),
                                  anchor="w")
        self.path_label.pack(fill="x", side="bottom", padx=10, pady=(0, 5))

        file_frame = tk.Frame(sidebar, bg="#252526")
        file_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.file_list = tk.Listbox(file_frame,
                                   bg="#252526", fg="#cccccc",
                                   selectbackground="#37373d",
                                   selectforeground="#ffffff",
                                   activestyle="none",
                                   borderwidth=0, 
                                   highlightthickness=0,
                                   font=self.font_regular,
                                   relief="flat")
        self.file_list.pack(fill="both", expand=True)
        self._populate_file_explorer()
        self.file_list.bind("<<ListboxSelect>>", self._open_selected_file)

        editor_area = tk.Frame(main_frame, bg=COLOR_SCHEME["background"], borderwidth=0, highlightthickness=0)
        editor_area.pack(side="right", fill="both", expand=True)

        toolbar = tk.Frame(editor_area, bg="#2d2d30", height=40, borderwidth=0, highlightthickness=0)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        self.run_button = tk.Button(toolbar, text="▶ Run", command=self.run_code,
                                   bg="#0dbc79", fg="white", 
                                   font=(self.font_regular.actual("family"), 10, "bold"),
                                   bd=0, highlightthickness=0, relief="flat",
                                   padx=15, pady=6,
                                   activebackground="#17c98f",
                                   activeforeground="white")
        self.run_button.pack(side="left", padx=10, pady=8)
        
        spacer = tk.Frame(toolbar, bg="#2d2d30", width=10)
        spacer.pack(side="left")

        self.file_label = tk.Label(toolbar, text="Untitled", bg="#2d2d30", fg="#cccccc", 
                                  font=(self.font_regular.actual("family"), 9), anchor="w")
        self.file_label.pack(side="left", padx=10)

        text_frame = tk.Frame(editor_area, bg=COLOR_SCHEME["background"])
        text_frame.pack(fill="both", expand=True, padx=(0, 5), pady=5)

        self.line_numbers = tk.Text(text_frame, width=4, padx=8, pady=2,
                                   bg="#1e1e1e", fg="#858585",
                                   state="disabled", 
                                   font=self.font_regular,
                                   borderwidth=0, 
                                   highlightthickness=0, 
                                   relief="flat",
                                   takefocus=0)
        self.line_numbers.pack(side="left", fill="y")

        self.text = tk.Text(text_frame, 
                           bg=COLOR_SCHEME["background"], 
                           fg=COLOR_SCHEME["foreground"],
                           insertbackground="#aeafad",
                           undo=True, 
                           font=self.font_regular, 
                           wrap="none",
                           borderwidth=0, 
                           highlightthickness=0, 
                           relief="flat",
                           padx=10, pady=5,
                           selectbackground="#264f78")
        self.text.pack(side="left", fill="both", expand=True)

        scroll_y = ttk.Scrollbar(text_frame, orient="vertical", command=self._sync_scroll, style="Custom.Vertical.TScrollbar")
        scroll_y.pack(side="right", fill="y")
        self.text.configure(yscrollcommand=scroll_y.set)

        scroll_x = ttk.Scrollbar(editor_area, orient="horizontal", command=self.text.xview, style="Custom.Horizontal.TScrollbar")
        scroll_x.pack(fill="x", padx=(0, 5))
        self.text.configure(xscrollcommand=scroll_x.set)

        console_frame = tk.Frame(self, bg="#1e1e1e", height=150)
        console_frame.pack(fill="x", side="bottom")
        console_frame.pack_propagate(False)
        
        console_header = tk.Frame(console_frame, bg="#2d2d30", height=25)
        console_header.pack(fill="x")
        
        console_label = tk.Label(console_header, text="OUTPUT", 
                               bg="#2d2d30", fg="#cccccc", 
                               font=(self.font_regular.actual("family"), 9, "bold"),
                               anchor="w", padx=10)
        console_label.pack(fill="x", side="left")
        
        self.output_console = tk.Text(console_frame, 
                                     bg="#1e1e1e", 
                                     fg="#cccccc", 
                                     font=self.font_regular,
                                     state="disabled", 
                                     borderwidth=0, 
                                     highlightthickness=0, 
                                     relief="flat",
                                     padx=10, pady=5)
        self.output_console.pack(fill="both", expand=True)

        self.suggestion_box = tk.Listbox(self, 
                                        bg="#252526", 
                                        fg="#d4d4d4",
                                        selectbackground="#094771",
                                        selectforeground="#ffffff",
                                        height=6, 
                                        font=self.font_regular,
                                        borderwidth=1,
                                        highlightthickness=0,
                                        relief="solid")
        self.suggestion_box.place(x=0, y=0)
        self.suggestion_box.place_forget()
        self.suggestion_box.bind("<<ListboxSelect>>", self.insert_completion)

        self._create_menu()

    def _load_fonts(self):
        try:
            self.font_regular = tkfont.Font(family="Consolas", size=12)
            self.font_italic = tkfont.Font(family="Consolas", size=12, slant="italic")
        except:
            try:
                self.font_regular = tkfont.Font(family="Courier New", size=12)
                self.font_italic = tkfont.Font(family="Courier New", size=12, slant="italic")
            except:
                self.font_regular = tkfont.Font(family="TkFixedFont", size=12)
                self.font_italic = tkfont.Font(family="TkFixedFont", size=12, slant="italic")

    def _update_file_selection(self):
        for i in range(self.file_list.size()):
            self.file_list.itemconfig(i, bg="#252526", fg="#cccccc")
        idx = self.file_list.curselection()
        if idx:
            self.file_list.itemconfig(idx, bg="#37373d", fg="#ffffff")

    def _create_menu(self):
        menu_bar = tk.Menu(self, bg="#2d2d30", fg="#cccccc", activebackground="#3e3e42", activeforeground="#ffffff")
        
        file_menu = tk.Menu(menu_bar, tearoff=0, bg="#2d2d30", fg="#cccccc", activebackground="#3e3e42", activeforeground="#ffffff")
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
        
        self.text.tag_configure("class", foreground=COLOR_SCHEME["class"])
        self.text.tag_configure("parameter", foreground=COLOR_SCHEME["parameter"])

    def _on_mouse_wheel(self, event):
        if event.delta:
            self.text.yview_scroll(int(-1 * (event.delta / 120)), "units")
        else:
            self.text.yview_scroll(int(-1 * event.num), "units")
        self._update_line_numbers()
        return "break"

    def _on_return_press(self, event):
        result = self.handle_auto_indent(event)
        self.after_idle(self._update_line_numbers)
        return result

    def _bind_events(self):
        self.text.bind("<KeyRelease>", self._on_key_release)
        self.text.bind("<MouseWheel>", self._on_mouse_wheel)
        self.text.bind("<Button-4>", self._on_mouse_wheel)
        self.text.bind("<Button-5>", self._on_mouse_wheel)
        self.text.bind("<ButtonRelease-1>", lambda e: self._update_line_numbers())
        self.text.bind("<Return>", self._on_return_press)
        self.text.bind("<Control-a>", self.select_all)
        self.text.bind("<Control-b>", lambda e: self.run_code())
        self.text.bind("<KeyRelease>", self.show_autocomplete)
        self.text.bind("<Tab>", self.insert_completion)
        
        self.run_button.bind("<ButtonPress-1>", self._on_run_button_press)
        self.run_button.bind("<ButtonRelease-1>", self._on_run_button_release)

    def _on_run_button_press(self, event=None):
        self.run_button.config(bg="#17c98f")

    def _on_run_button_release(self, event=None):
        self.run_button.config(bg="#0dbc79")

    def _on_key_release(self, event=None):
        self.highlight_syntax()
        if event.keysym in ['Return', 'BackSpace', 'Delete']:
            self.after_idle(self._update_line_numbers)

    def _populate_file_explorer(self, path=None):
        if path is None:
            path = os.getcwd()
        
        self.current_explorer_path = path
        self.file_list.delete(0, tk.END)

        display_path = path
        if len(path) > 30:
            display_path = "..." + path[-27:]
        self.path_label.config(text=display_path)
        
        if path != os.path.dirname(path):
            self.file_list.insert(tk.END, "📁 ..")
        
        try:
            items = os.listdir(path)
            
            folders = []
            py_files = []
            txt_files = []
            other_files = []
            
            for item in items:
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    folders.append(item)
                elif item.endswith('.py'):
                    py_files.append(item)
                elif item.endswith('.txt'):
                    txt_files.append(item)
            
            folders.sort()
            py_files.sort()
            txt_files.sort()
            
            for folder in folders:
                self.file_list.insert(tk.END, f"📁 {folder}")
            
            for py_file in py_files:
                self.file_list.insert(tk.END, f"🐍 {py_file}")
            
            for txt_file in txt_files:
                self.file_list.insert(tk.END, f"📄 {txt_file}")
                
        except PermissionError:
            self.file_list.insert(tk.END, "⛔ Permission denied")

    def _update_file_selection(self):
        for i in range(self.file_list.size()):
            self.file_list.itemconfig(i, bg="#252526", fg="#cccccc")
        idx = self.file_list.curselection()
        if idx:
            self.file_list.itemconfig(idx, bg="#37373d", fg="#ffffff")

    def change_directory(self, path=None):
        if path is None:
            path = filedialog.askdirectory(title="Select Directory")
        
        if path:
            self._populate_file_explorer(path)

    def _open_selected_file(self, event):
        index = self.file_list.curselection()
        if not index:
            return
            
        selected = self.file_list.get(index)
        
        if selected == "📁 ..":
            parent_dir = os.path.dirname(self.current_explorer_path)
            self._populate_file_explorer(parent_dir)
            return
        
        clean_name = selected[2:] if len(selected) > 2 else selected
        
        full_path = os.path.join(self.current_explorer_path, clean_name)
        
        if os.path.isdir(full_path):
            self._populate_file_explorer(full_path)
        elif clean_name.endswith(('.py', '.txt')):
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.text.delete("1.0", tk.END)
                self.text.insert("1.0", content)
                self.filename = full_path
                self.file_label.config(text=clean_name)
                self.highlight_syntax()
                self._update_line_numbers()
                self._update_file_selection()
                self.title(f"{clean_name} - Allyx")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file: {str(e)}")

    def _on_scroll_y(self, *args):
        self.text.yview(*args)
        self.line_numbers.yview(*args)

    def _sync_scroll(self, *args):
        self.text.yview(*args)
        self.line_numbers.yview(*args)

    def _update_line_numbers(self):
        self.line_numbers.config(state="normal")
        self.line_numbers.delete("1.0", "end")
        
        content = self.text.get("1.0", "end-1c")
        if content:
            lines = content.count('\n') + 1
        else:
            lines = 1
        
        line_numbers_text = "\n".join(str(i) for i in range(1, lines + 1))
        self.line_numbers.insert("1.0", line_numbers_text)
        self.line_numbers.config(state="disabled")
        
        first_visible = self.text.yview()[0]
        self.line_numbers.yview_moveto(first_visible)

    def highlight_syntax(self):
        content = self.text.get("1.0", tk.END)
        for tag in self.text.tag_names():
            self.text.tag_remove(tag, "1.0", tk.END)

        patterns = [
            (r"#.*", "comment"),
            (r'(\".*?\"|\'.*?\')', "string"),
            (r"\b\d+(\.\d+)?\b", "number"),
            (r"\b(self|cls)\b", "parameter"),
            (r"\b(True|False|None)\b", "keyword"),
            (r"\b(print|len|range|type|isinstance)\b", "function")
        ]

        for regex, tag in patterns:
            for match in re.finditer(regex, content):
                self._apply_tag(tag, match)

        for kw in PYTHON_KEYWORDS:
            for match in re.finditer(rf"\b{kw}\b", content):
                self._apply_tag("keyword", match)

        for match in re.finditer(r"\bdef\s+(\w+)", content):
            self._apply_tag("function", match, group=1)
            
        for match in re.finditer(r"\bclass\s+(\w+)", content):
            self._apply_tag("class", match, group=1)

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
            self.file_label.config(text=os.path.basename(path))
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
            self.file_label.config(text=os.path.basename(path))
            self.save_file()

    def run_code(self):
        self._on_run_button_press()
        self.after(100, self._on_run_button_release)
        
        code = self.text.get("1.0", tk.END)
        self.output_console.config(state="normal")
        self.output_console.delete("1.0", tk.END)
        try:
            with open("temp_run.py", "w", encoding="utf-8") as f:
                f.write(code)
            result = subprocess.run(["python", "temp_run.py"], capture_output=True, text=True)
            output = result.stdout + ("\n" + result.stderr if result.stderr else "")
            self.output_console.insert("1.0", output)
        except Exception as e:
            self.output_console.insert("1.0", f"Error: {str(e)}")
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
                        background="#424242",
                        troughcolor="#2b2b2b",
                        bordercolor="#2b2b2b",
                        arrowcolor="#888888",
                        relief="flat", 
                        width=12,
                        borderwidth=0)
        style.map("Custom.Vertical.TScrollbar",
                  background=[("active", "#5e5e5e")])

        style.configure("Custom.Horizontal.TScrollbar",
                        background="#424242",
                        troughcolor="#2b2b2b",
                        bordercolor="#2b2b2b",
                        arrowcolor="#888888",
                        relief="flat", 
                        height=12,
                        borderwidth=0)
        style.map("Custom.Horizontal.TScrollbar",
                  background=[("active", "#5e5e5e")])

if __name__ == "__main__":
    CodeEditor().mainloop()
