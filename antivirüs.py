import sys
import os
import hashlib
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QFileDialog, QListWidget, QMessageBox, QProgressBar,
                             QComboBox, QDialog, QTimeEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QTime
from PyQt5.QtGui import QFont, QIcon

know_virus_signatures = [
    'd41d8cd98f00b204e9800998ecf8427e',
    '5d41402abc4b2a76b9719d911017c592'
]

scheduled_scans = []

class ScanThread(QThread):
    progress = pyqtSignal(int)
    result = pyqtSignal(str)
    finished = pyqtSignal()
    def __init__(self,path,scan_type='directory'):
        super().__init__()
        self.path = path
        self.scan_type = scan_type
    def run(self):
        if self.scan_type == 'file':
            files = [self.path]
        elif self.scan_type == 'directory':
            files = self.get_files_in_directory(self.path)
        elif self.scan_type == 'full_system':
            files = self.get_files_in_directory("/")

        total_files = len(files)
        for index, file_path in enumerate(files):
            result = scan_file(file_path)
            self.result.emit(result)
            progress_percent = int((index + 1) / total_files * 100)
            self.progress.emit(progress_percent)
        self.finished.emit()
    def get_files_in_directory(self,path):
        all_files = []
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root,file)
                all_files.append(file_path)
        return all_files

def calculate_md5(path):
    hash_md5 = hashlib.md5()
    try:
        with open(path,"rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        return None

def scan_file(path):
    file_hash = calculate_md5(path)
    if file_hash in know_virus_signatures:
        return f"Tehlikeli dosya bulundu: {path}"
    else:
        return f"Temiz dosya: {path}"

class AntivirusApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Antivirüs Uygulaması')
        self.setWindowIcon(QIcon('icon.ico'))
        self.setGeometry(100,100,700,500)
        main_layout = QVBoxLayout()
        self.setStyleSheet("""
        QWidget {
        background-color: #2C3E50;
        color: white;
        }
        QPushButton {
        background-color: #8E44AD;
        color: white;
        border-radius: 5px;
        padding: 10px;
        }
        QPushButton:hover{
        background-color: #9B59B6;
        }
        QProgressBar{
        border: 2px solid #8E44AD;
        border-radius: 5px;
        text-align: center;
        }
        QProgressBar::chunk {
        background-color: #9B59B6;
        width: 10px;
        }
        QListWidget {
        background-color: #34495E;
        border: 1px solid #8E44AD;
        padding: 10px;
        }
        """)
        self.label = QLabel('Antivirüs Taraması Sonuçları',self)
        self.label.setFont(QFont('Arial',14,QFont.Bold))
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet('margin_bottom: 15px;')
        main_layout.addWidget(self.label)

        self.result_list = QListWidget(self)
        self.result_list.setFont(QFont('Courier',10))
        main_layout.addWidget(self.result_list)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        self.schedule_button = QPushButton("Günlük Tarama Zamanla",self)
        self.schedule_button.clicked.connect(self.open_schedule_dialog)
        main_layout.addWidget(self.schedule_button)

        button_layout = QHBoxLayout()
        button_font = QFont('Arial',12)
        self.scan_file_button = QPushButton('Dosya Tara',self)
        self.scan_file_button.setFont(button_font)
        self.scan_file_button.clicked.connect(self.scan_file)
        button_layout.addWidget(self.scan_file_button)
        self.scan_directory_button = QPushButton('Dizin Tara',self)
        self.scan_directory_button.setFont(button_font)
        self.scan_directory_button.clicked.connect(self.scan_directory)
        button_layout.addWidget(self.scan_directory_button)
        self.scan_full_system_button = QPushButton('Tüm Bilgisayarı Tara',self)
        self.scan_full_system_button.setFont(button_font)
        self.scan_full_system_button.clicked.connect(self.scan_full_system)
        button_layout.addWidget(self.scan_full_system_button)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self.daily_timer = QTimer()
    def start_scan(self,path,scan_type,daily=False):
        self.result_list.clear()
        self.progress_bar.setValue(0)
        self.thread = ScanThread(path,scan_type)
        self.thread.progress.connect(self.update_progress)
        self.thread.result.connect(self.add_result)
        self.thread.finished.connect(self.show_notification)
        if daily:
            self.thread.finished.connect(self.reschedule_daily_scan)
        self.thread.start()
    def update_progress(self,value):
        self.progress_bar.setValue(value)
    def add_result(self,result):
        self.result_list.addItem(result)
    def show_notification(self):
        QMessageBox.information(self,"Tarama Tamamlandı","Tarama başarıyla tamamlandı!")
    def scan_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self,'Dosya Seç','','Tüm Dosyalar (*)')
        if file_path:
            self.start_scan(file_path,scan_type='file')
    def scan_directory(self):
        directory_path = QFileDialog.getExistingDirectory(self,'Dizin Seç')
        if directory_path:
            self.start_scan(directory_path,scan_type='directory')
    def scan_full_system(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle(self.windowTitle())
        msg_box.setWindowIcon(QIcon('icon.ico'))
        msg_box.setText('Tüm bilgisayarı taramak uzun sürebilir, emin misiniz?')
        yes_button = msg_box.addButton("Evet",QMessageBox.YesRole)
        no_button = msg_box.addButton("Hayır",QMessageBox.NoRole)
        result = msg_box.exec()

        if msg_box.clickedButton() ==yes_button:
            self.start_scan("/",scan_type='full_system')
    def open_schedule_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Günlük Tarama Zamanla")
        dialog.setGeometry(250,250,300,300)
        layout = QVBoxLayout()
        time_label = QLabel("Saat Seçin:",dialog)
        layout.addWidget(time_label)

        self.time_edit = QTimeEdit(dialog)
        self.time_edit.setTime(QTime.currentTime())
        self.time_edit.setDisplayFormat("HH:mm")
        layout.addWidget(self.time_edit)

        scan_type_label = QLabel("Tarama Tipi Seçin:",dialog)
        layout.addWidget(scan_type_label)

        self.scan_type_combo = QComboBox(dialog)
        self.scan_type_combo.addItems(["Tam Tarama","Dizin Tarama"])
        self.scan_type_combo.currentIndexChanged.connect(self.on_scan_type_changed)
        layout.addWidget(self.scan_type_combo)

        self.directory_label = QLabel("Tarama Dizini Seçin:",dialog)
        self.directory_label.setVisible(False)

        layout.addWidget(self.directory_label)

        self.directory_button = QPushButton("Dizin Seç",dialog)
        self.directory_button.setVisible(False)
        self.directory_button.clicked.connect(self.select_directory)
        layout.addWidget(self.directory_button)

        ok_button = QPushButton("Tamam",dialog)
        ok_button.clicked.connect(lambda: self.schedule_daily_scan(dialog))
        layout.addWidget(ok_button)

        settings_label = QLabel("Ayarlanmış Taramalar:",dialog)
        layout.addWidget(settings_label)
        self.schedule_scans_list = QListWidget(dialog)
        layout.addWidget(self.schedule_scans_list)
        self.display_scheduled_scans()
        dialog.setLayout(layout)
        dialog.exec()
    def on_scan_type_changed(self):
        if self.scan_type_combo.currentText()=="Dizin Tarama":
            self.directory_label.setVisible(True)
            self.directory_button.setVisible(True)
        else:
            self.directory_label.setVisible(False)
            self.directory_button.setVisible(False)
    def select_directory(self):
        self.selected_directory = QFileDialog.getExistingDirectory(self,"Tarama Dizini Seç")
        self.directory_label.setText(f'Seçilen Dizin: {self.selected_directory}')
    def schedule_daily_scan(self,dialog):
        selected_time = self.time_edit.time()
        now = QTime.currentTime()
        interval = now.msecsTo(selected_time)
        if interval<0:
            interval += 24*60*60*1000
        QTimer.singleShot(interval,self.start_scheduled_scan)
        scan_type = self.scan_type_combo.currentText()
        if scan_type=="Dizin Tarama" and hasattr(self,'selected_directory'):
            scheduled_scan = f'{selected_time.toString("HH:mm")} - Dizin Tarama - {self.selected_directory}'
        else:
            scheduled_scan = f'{selected_time.toString("HH:mm")} - Tam Tarama '
        scheduled_scans.append(scheduled_scan)
        self.display_scheduled_scans()
        QMessageBox.information(self,"Günlük Tarama","Günlük tarama zamanlandı!")
        dialog.accept()
    def display_scheduled_scans(self):
        self.schedule_scans_list.clear()
        if scheduled_scans:
            self.schedule_scans_list.addItems(scheduled_scans)
        else:
            self.schedule_scans_list.addItem("Herhangi bir tarama ayarlanmadı")
    def start_scheduled_scan(self):
        scan_type = self.scan_type_combo.currentText()
        if scan_type == "Tam Tarama":
            self.start_scan("/",scan_type='full_system',daily=True)
        elif scan_type == "Dizin Tarama" and hasattr(self,'selected_directory'):
            self.start_scan(self.selected_directory, scan_type='directory',daily=True)
    def reschedule_daily_scan(self):
        QTimer.singleShot(24*60*60*1000,self.start_scheduled_scan)
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AntivirusApp()
    window.show()
    sys.exit(app.exec_())