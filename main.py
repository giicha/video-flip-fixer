import os
import sys
import traceback
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QRadioButton, 
                             QButtonGroup, QFileDialog, QTextEdit, QProgressBar, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

import core

def exception_hook(exctype, value, tb):
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    print(error_msg)
    QMessageBox.critical(None, "Critical Error", f"Application crashed:\n\n{error_msg}")
    sys.exit(1)

sys.excepthook = exception_hook

class ProcessThread(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal()

    def __init__(self, files, mode, output_folder):
        super().__init__()
        self.files = [str(f) for f in files]
        self.mode = str(mode)
        self.output_folder = str(output_folder) if output_folder else ""

    def run(self):
        try:
            total_files = len(self.files)
            if total_files == 0:
                self.finished_signal.emit()
                return

            for index, file_path in enumerate(self.files):
                core.process_video(
                    file_path=file_path, 
                    mode=self.mode, 
                    output_folder=self.output_folder, 
                    log_callback=self.log_signal.emit
                )
                
                progress = int(((index + 1) / total_files) * 100)
                self.progress_signal.emit(progress)
        except Exception as e:
            self.log_signal.emit(f"Thread error: {e}")
        
        self.finished_signal.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lossless Video Rotator Fixer")
        self.setMinimumSize(600, 450)
        self.setAcceptDrops(True)

        # Smart path resolution for the icon file inside standalone .exe
        if getattr(sys, 'frozen', False):
            # If running inside compiled .exe, PyInstaller extracts resources to sys._MEIPASS
            icon_path = os.path.join(sys._MEIPASS, "icon.ico")
        else:
            # Local fallback for running raw script in VS Code
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")

        from PyQt6.QtGui import QIcon
        self.setWindowIcon(QIcon(icon_path))

        self.input_files = []
        self.selected_output_folder = ""

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.drop_label = QLabel("Drag & Drop video files or folders here\nor use the buttons below")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setStyleSheet("""
            QLabel { border: 2px dashed #aaa; border-radius: 10px; padding: 30px; background-color: #f9f9f9; font-size: 14px; color: #555; }
        """)
        main_layout.addWidget(self.drop_label)

        btn_layout = QHBoxLayout()
        self.btn_add_files = QPushButton("Add Files")
        self.btn_add_folder = QPushButton("Add Folder")
        self.btn_clear = QPushButton("Clear List")
        btn_layout.addWidget(self.btn_add_files)
        btn_layout.addWidget(self.btn_add_folder)
        btn_layout.addWidget(self.btn_clear)
        main_layout.addLayout(btn_layout)

        main_layout.addWidget(QLabel("<b>Save Options:</b>"))
        
        self.radio_overwrite = QRadioButton("Overwrite original files")
        self.radio_copy_near = QRadioButton("Create copies nearby (with _fixed suffix)")
        self.radio_copy_folder = QRadioButton("Copy to specific folder:")
        self.radio_copy_near.setChecked(True)

        self.btn_select_folder = QPushButton("Browse...")
        self.btn_select_folder.setEnabled(False)
        self.lbl_folder_path = QLabel("No folder selected")
        self.lbl_folder_path.setStyleSheet("color: gray;")

        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.radio_copy_folder)
        folder_layout.addWidget(self.btn_select_folder)
        folder_layout.addWidget(self.lbl_folder_path)
        folder_layout.addStretch()

        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.radio_overwrite)
        self.mode_group.addButton(self.radio_copy_near)
        self.mode_group.addButton(self.radio_copy_folder)

        main_layout.addWidget(self.radio_overwrite)
        main_layout.addWidget(self.radio_copy_near)
        main_layout.addLayout(folder_layout)

        main_layout.addWidget(QLabel("<b>Process Log:</b>"))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        main_layout.addWidget(self.log_output)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        bottom_layout = QHBoxLayout()
        self.btn_start.setStyleSheet("""
            QPushButton {
                font-weight: bold; 
                background-color: #4CAF50; 
                color: white; 
                height: 35px; 
                width: 150px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:disabled {
                background-color: #A0A0A0; 
                color: #E0E0E0;
            }
        """)
        
        self.lbl_status = QLabel('<a href="https://github.com/giicha/video-flip-fixer" style="color: #2481cc; text-decoration: none; font-style: italic;">https://github.com/giicha/video-flip-fixer</a>')
        self.lbl_status.setOpenExternalLinks(True)  
        self.lbl_status.setCursor(Qt.CursorShape.PointingHandCursor)  
        
        bottom_layout.addWidget(self.btn_start)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.lbl_status)
        main_layout.addLayout(bottom_layout)

        self.btn_add_files.clicked.connect(self.choose_files)
        self.btn_add_folder.clicked.connect(self.choose_folder)
        self.btn_clear.clicked.connect(self.clear_all)
        self.radio_copy_folder.toggled.connect(self.toggle_folder_button)
        self.btn_select_folder.clicked.connect(self.choose_output_folder)
        self.btn_start.clicked.connect(self.start_processing)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isdir(path):
                self.add_folder_files(path)
            elif os.path.isfile(path):
                if path not in self.input_files:
                    self.input_files.append(path)
        self.update_drop_label()

    def choose_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Video Files", "", "Videos (*.mp4 *.mov *.avi *.mkv)")
        for f in files:
            if f not in self.input_files:
                self.input_files.append(f)
        self.update_drop_label()

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder with Videos")
        if folder:
            self.add_folder_files(folder)
            self.update_drop_label()

    def add_folder_files(self, folder_path):
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                    full_path = os.path.join(root, file)
                    if full_path not in self.input_files:
                        self.input_files.append(full_path)

    def clear_all(self):
        self.input_files.clear()
        self.update_drop_label()
        self.progress_bar.setValue(0)

    def update_drop_label(self):
        if self.input_files:
            self.drop_label.setText(f"Selected files for processing: {len(self.input_files)}")
        else:
            self.drop_label.setText("Drag & Drop video files or folders here\nor use the buttons below")

    def toggle_folder_button(self, checked):
        self.btn_select_folder.setEnabled(checked)

    def choose_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.selected_output_folder = folder
            self.lbl_folder_path.setText(os.path.basename(folder))

    def append_log(self, text):
        self.log_output.append(str(text))

    def start_processing(self):
        if not self.input_files:
            self.append_log("Error: File queue is empty!")
            return

        mode = "copy_near"
        if self.radio_overwrite.isChecked():
            mode = "overwrite"
        elif self.radio_copy_folder.isChecked():
            mode = "copy_to_folder"
            if not self.selected_output_folder:
                self.append_log("Error: Output folder not selected!")
                return

        self.btn_start.setEnabled(False)
        self.progress_bar.setValue(0)
        self.append_log("=== Batch processing started ===")

        self.process_thread = ProcessThread(self.input_files, mode, self.selected_output_folder)
        self.process_thread.log_signal.connect(self.append_log)
        self.process_thread.progress_signal.connect(self.progress_bar.setValue)
        self.process_thread.finished_signal.connect(self.processing_finished)
        self.process_thread.start()

    def processing_finished(self):
        self.btn_start.setEnabled(True)
        self.input_files.clear()
        self.update_drop_label()
        self.append_log("=== Batch processing completed successfully ===")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
