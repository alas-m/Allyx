# 🧠 Allyx — Lightweight Python Code Editor
Allyx is a minimal, fast, and customizable Python code editor built entirely with Tkinter. Inspired by Sublime Text, it brings a modern, dark-themed interface with essential IDE features while remaining lightweight and plugin-free.

# 🚀 Features
🎨 Dark Theme by default

🧠 Syntax highlighting for Python:

```Keywords, strings, comments, numbers, functions```

```Color-coded warnings and errors```

💻 Code runner:

```Run Python files directly via ▶ Run button or Ctrl + B```

🧾 Line numbers for easy code navigation

🔍 Autocomplete suggestions powered by Jedi

```Triggered only at the end of words```

```Suggestions are dismissed on space```

```Press Tab to accept and replace```

📁 File explorer:

```Lists .py files in the project directory```

```Active file highlighted with a pill-shaped marker```

🧰 Custom font support via Google Fonts (Rubik)

🌀 Modern UI elements:

```Smooth scrollbars```

```Rounded buttons```

```Clean, borderless look```

📦 Packaged as a standalone .exe (via PyInstaller)

# 📷 Screenshot
<img width="218" height="411" alt="image" src="https://github.com/user-attachments/assets/1178235a-b7ab-40da-8319-bdf730ea0780" />
<img width="1919" height="982" alt="image" src="https://github.com/user-attachments/assets/ecfcdcab-a4cf-4887-bdf1-55136b6b7b1e" />


# 🛠 Installation
1. Clone the repository:
   
   <pre> bash # Install dependencies pip install jedi # Run the editor python main.py # Build executable pyinstaller main.py --onefile --noconsole --icon=icon.ico </pre>
   
3. Install dependencies:
   
   <pre> bash # pip install jedi </pre>

4. (Optional) Install custom font:

   Add Rubik-VariableFont_wght.ttf and Rubik-Italic-VariableFont_wght.ttf to the /src folder
   
   Or install them system-wide for automatic use

   <pre> python main.py </pre>

# 📦 Build ```.exe``` (Windows)
Make sure you have PyInstaller installed:

<pre> pip install pyinstaller  </pre>
<pre> pyinstaller main.py --onefile --noconsole --icon=icon.ico </pre>

# ‼️ Move main.exe from dist folder to the root folder

# 🧩 Roadmap
 Tabbed files

 Auto-save

 Find/Replace panel

 Mini-map support

# 📄 License
MIT License
