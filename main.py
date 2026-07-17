import sys
import os
import subprocess
import importlib.util

from PyQt6.QtGui import QFont, QShortcut, QKeySequence, QFileSystemModel
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, \
    QSplitter, QListWidget, QTreeView, QLabel, QLineEdit
from PyQt6.QtCore import Qt, QModelIndex
from PyQt6.QtWidgets import QListWidget, QMessageBox
from extension_manager import ExtensionManager


class ExtensionAPI:
    def __init__(self, ide):
        self.ide = ide
        self.commands = {}
    def register_command(self, name, function):
        self.commands[name] = function
    def run_command(self, name):
        if name in self.commands:
            self.commands[name]()
    def print_terminal(self, text):
        self.ide.terminal.append(text)
    def add_button(self, text, function):
        button = QPushButton(text)
        button.clicked.connect(function)
        self.ide.toolbar_layout.addWidget(button)
    def file_opened(self, callback):
        self.ide.file_open_callbacks.append(callback)

class IDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IDE")
        self.setGeometry(300, 300, 1500, 800)

        self.current_file_path = None

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        toolbar_layout = QHBoxLayout()

        self.toolbar_layout = toolbar_layout
        self.file_open_callbacks = []

        self.extension_api = ExtensionAPI(self)
        self.extension_manager = ExtensionManager(self)

        market_button = QPushButton(
            "Extensions"
        )
        market_button.clicked.connect(
            self.open_marketplace
        )
        toolbar_layout.addWidget(
            market_button
        )

        self.run_button = QPushButton("▶ Run Code")
        self.run_button.clicked.connect(self.run_current_code)
        toolbar_layout.addWidget(self.run_button)

        toolbar_layout.addSpacing(50)

        toolbar_layout.addWidget(QLabel("pip install "))

        self.package_input = QLineEdit()
        self.package_input.setPlaceholderText("Enter Package Name (example: requests, numpy)")
        self.package_input.setFixedWidth(250)
        self.package_input.returnPressed.connect(self.run_pip_install)
        toolbar_layout.addWidget(self.package_input)

        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        user_home_dir = os.path.expanduser("~")

        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(user_home_dir)

        self.sidebar = QTreeView()
        self.sidebar.setModel(self.file_model)
        self.sidebar.setRootIndex(self.file_model.index(user_home_dir))

        for i in range(4, 0, -1):
            self.sidebar.setColumnHidden(i, True)

        self.sidebar.doubleClicked.connect(self.handle_sidebar_double_click)

        main_splitter.addWidget(self.sidebar)

        self.font_up = QPushButton("Increase font size")
        self.font_up.clicked.connect(self.increase_font)
        toolbar_layout.addWidget(self.font_up)

        self.font_down = QPushButton("Decrease font size")
        self.font_down.clicked.connect(self.decrease_font)
        toolbar_layout.addWidget(self.font_down)

        toolbar_layout.addStretch()
        main_layout.addLayout(toolbar_layout)

        splitter = QSplitter(Qt.Orientation.Vertical)

        self.current_font_size = 12
        self.editor = QTextEdit()
        self.editor.setFont(QFont("Consolas", self.current_font_size))
        self.editor.setPlainText("print('Hello from IDE!')\nprint(10 + 20)")
        splitter.addWidget(self.editor)

        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setFont(QFont("Consolas", self.current_font_size))
        self.terminal.setPlaceholderText("Terminal:")
        splitter.addWidget(self.terminal)

        splitter.setSizes([250, 100])
        main_splitter.addWidget(splitter)
        main_splitter.setSizes([150, 650])
        main_layout.addWidget(main_splitter)

        self.set_shortcuts()
        self.load_extensions()

    def run_current_code(self):
        code_text = self.editor.toPlainText()
        if self.current_file_path and self.current_file_path.endswith(".py"):
            temp_file = self.current_file_path
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(code_text)
            is_temporary = False
        else:
            temp_file = "temp_run.py"
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(code_text)
            is_temporary = True

        self.terminal.setText("Running code...\n")

        try:
            current_python_exe = sys.executable

            result = subprocess.run(
                [current_python_exe, temp_file],
                capture_output=True,
                text=True,
                encoding="utf-8"
            )

            if result.stdout:
                self.terminal.append(result.stdout)
                self.terminal.append("\nCODE ENDED: Exit code 0")
            if result.stderr:
                self.terminal.append(f"\nERROR: {result.stderr}")

        except Exception as e:
            self.terminal.append(f"\nERROR: {str(e)}")

        if is_temporary and os.path.exists(temp_file):
            os.remove(temp_file)

    def set_font_size(self, size):
        self.current_font_size = size
        font = QFont("Consolas", self.current_font_size)
        self.editor.setFont(font)
        self.terminal.setFont(font)

    def increase_font(self):
        self.set_font_size(self.current_font_size + 2)

    def decrease_font(self):
        self.set_font_size(self.current_font_size - 2)

    def set_shortcuts(self):
        QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Equal), self, self.increase_font)
        QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Minus), self, self.decrease_font)

    def open_selected_file(self, file_path: str):
        text_extensions = ('.py', '.cpp', '.c', '.h', '.txt', '.json', '.html', '.css', '.md')
        if not file_path.lower().endswith(text_extensions):
            self.terminal.setText(f"Unsupported language: {os.path.basename(file_path)}")
            return

        self.current_file_path = file_path

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                file_content = f.read()

            self.editor.setPlainText(file_content)
            self.setWindowTitle(f"[{os.path.basename(file_path)}]")
            self.terminal.setText(f"Successfully opened: {file_path}")

        except Exception as e:
            self.terminal.setText(f"ERROR OPENING FILE: {str(e)}")

    def handle_sidebar_double_click(self, index: QModelIndex):
        if not index.isValid():
            return

        try:
            target_path = self.file_model.filePath(index)

            if not target_path:
                return
            if self.file_model.isDir(index):
                if self.sidebar.isExpanded(index):
                    self.sidebar.collapse(index)
                else:
                    self.sidebar.expand(index)
            else:
                self.open_selected_file(target_path)

        except Exception as e:
            self.terminal.setText(f"ERROR WHILE FINDING FILE: {str(e)}")

    def run_pip_install(self):
        package_name = self.package_input.text().strip()

        if not package_name:
            self.terminal.setText("ERROR: Enter package name please\n")
            return

        current_python_exe = sys.executable

        self.terminal.setText(f"Starting package download: pip install {package_name}\n")
        self.terminal.append("Downloading library please wait\n")

        QApplication.processEvents()

        try:
            cmd = [current_python_exe, "-m", "pip", "install", package_name]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore"
            )

            if result.stdout:
                self.terminal.append(result.stdout)

            if result.stderr:
                self.terminal.append(f"\nDownload log: {result.stderr}")

            if result.returncode == 0:
                self.terminal.append(f"\nSuccess! Package downloaded: '{package_name}'")
                self.package_input.clear()
            else:
                self.terminal.append(f"\nError! Download failed: (Exit Code: {result.returncode})")

        except Exception as e:
            self.terminal.append(f"\nError! Failed to call package: {str(e)}")

    def load_extensions(self):
        extension_folder = "extensions"
        if not os.path.exists(extension_folder):
            os.mkdir(extension_folder)
        for file in os.listdir(extension_folder):
            if file.endswith(".py"):
                path = os.path.join(extension_folder, file)
                try:
                    spec = importlib.util.spec_from_file_location(
                        file,
                        path
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, "activate"):
                        module.activate(
                            self.extension_api
                        )
                        self.terminal.append(
                            f"Loaded extension: {file}"
                        )
                except Exception as e:

                    self.terminal.append(
                        f"Extension error {file}: {e}"
                    )

    def open_marketplace(self):

        window = QWidget()

        layout = QVBoxLayout(window)

        list_widget = QListWidget()

        extensions = self.extension_manager.get_extensions()

        for ext in extensions:
            list_widget.addItem(
                ext["name"]
                +
                " - "
                +
                ext["description"]
            )

        install = QPushButton(
            "Install Selected"
        )

        def install_extension():
            item = list_widget.currentItem()
            if item:
                name = item.text().split(" - ")[0]
                if self.extension_manager.install(name):
                    QMessageBox.information(
                        window,
                        "Installed",
                        name
                        +
                        " installed!"
                    )
        install.clicked.connect(
            install_extension
        )
        layout.addWidget(list_widget)
        layout.addWidget(install)
        window.setWindowTitle(
            "Extension Marketplace"
        )
        window.resize(
            500,
            400
        )
        window.show()
        self.market_window = window

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IDE()
    window.show()
    sys.exit(app.exec())