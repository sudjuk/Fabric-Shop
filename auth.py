from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox)
from PySide6.QtCore import Qt
import psycopg2
from manager import ManagerWindow
from seller import SellerWindow

class AuthWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Заголовок
        title = QLabel("Вход в систему")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)
        
        # Поля ввода
        form_layout = QVBoxLayout()
        
        # Логин
        login_layout = QHBoxLayout()
        login_label = QLabel("Логин:")
        self.login_input = QLineEdit()
        login_layout.addWidget(login_label)
        login_layout.addWidget(self.login_input)
        form_layout.addLayout(login_layout)
        
        # Пароль
        password_layout = QHBoxLayout()
        password_label = QLabel("Пароль:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        form_layout.addLayout(password_layout)
        
        layout.addLayout(form_layout)
        
        # Кнопка входа
        login_button = QPushButton("Войти")
        login_button.clicked.connect(self.try_login)
        login_button.setMinimumHeight(40)
        layout.addWidget(login_button)
        
        self.setLayout(layout)
        
    def try_login(self):
        login = self.login_input.text()
        password = self.password_input.text()
        
        try:
            # Подключение к базе данных
            conn = psycopg2.connect(
                dbname="fabric_shop",
                user="postgres",
                password="lol132kek",  # Замените на ваш пароль
                host="localhost",
                port="5432"
            )
            
            cursor = conn.cursor()
            
            # Проверка учетных данных
            cursor.execute("""
                SELECT role_name 
                FROM roles 
                WHERE role_name = %s AND password = %s
            """, (login, password))
            
            result = cursor.fetchone()
            
            if result:
                role = result[0]
                self.open_role_window(role)
            else:
                QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")
            
            cursor.close()
            conn.close()
            
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка подключения к базе данных: {e}")
    
    def open_role_window(self, role):
        # Создаем соответствующее окно в зависимости от роли
        if role == 'manager':
            window = ManagerWindow(self.main_window)
        elif role == 'seller':
            window = SellerWindow(self.main_window)
        
        # Добавляем окно в стек и переключаемся на него
        self.main_window.stacked_widget.addWidget(window)
        self.main_window.stacked_widget.setCurrentWidget(window) 