from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea
from PySide6.QtCore import Qt

class BaseRoleWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout()
        
        # Верхняя панель с кнопками
        self.top_panel = QHBoxLayout()
        self.setup_top_panel()
        
        # Добавляем растягивающийся элемент слева
        self.top_panel.addStretch()
        
        # Кнопка выхода справа
        logout_button = QPushButton("Выйти")
        logout_button.clicked.connect(self.logout)
        self.top_panel.addWidget(logout_button)
        
        main_layout.addLayout(self.top_panel)
        
        # Заголовок
        self.content_label = QLabel(self.get_title())
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        main_layout.addWidget(self.content_label)
        
        # Область контента
        self.content_area = QScrollArea()
        self.content_area.setWidgetResizable(True)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_area.setWidget(self.content_widget)
        main_layout.addWidget(self.content_area)
        
        self.setLayout(main_layout)
    
    def get_title(self):
        return "Базовая роль"
    
    def setup_top_panel(self):
        pass
    
    def setup_content(self, layout):
        pass
    
    def logout(self):
        # Возвращаемся к окну авторизации
        self.main_window.stacked_widget.setCurrentIndex(0)
        # Очищаем поля ввода
        auth_window = self.main_window.auth_window
        auth_window.login_input.clear()
        auth_window.password_input.clear() 