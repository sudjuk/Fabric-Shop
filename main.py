import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import Qt
from auth import AuthWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Магазин тканей")
        self.setMinimumSize(1200, 800)
        
        # Создаем стек виджетов для переключения между окнами
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Создаем окно авторизации
        self.auth_window = AuthWindow(self)
        self.stacked_widget.addWidget(self.auth_window)
        
        # Показываем окно авторизации
        self.stacked_widget.setCurrentWidget(self.auth_window)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 