from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QTableWidget, 
                             QTableWidgetItem, QHBoxLayout, QLabel, 
                             QLineEdit, QMessageBox, QDialog, QFormLayout, QHeaderView, QComboBox, QDateEdit,
                             QGroupBox, QGridLayout, QFileDialog, QMenu)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from base_role_window import BaseRoleWindow
from database_utils import (TABLES_CONFIG, get_combo_values, load_table_data,
                          add_row_to_table, update_row_in_table, delete_row_from_table, get_db_connection,
                          create_export_button, export_table_to_excel, get_table_style, get_button_style)
import psycopg2
from datetime import datetime, timedelta
import openpyxl

class ManagerWindow(BaseRoleWindow):
    def get_title(self):
        return "Панель менеджера"
    
    def setup_top_panel(self):
        buttons = [
            (TABLES_CONFIG['employees']['title'], lambda: self.manage_table('employees')),
            (TABLES_CONFIG['fabrics']['title'], lambda: self.manage_table('fabrics')),
            (TABLES_CONFIG['fabric_categories']['title'], lambda: self.manage_table('fabric_categories')),
            (TABLES_CONFIG['suppliers']['title'], lambda: self.manage_table('suppliers')),
            (TABLES_CONFIG['deliveries']['title'], lambda: self.manage_table('deliveries')),
            (TABLES_CONFIG['customers']['title'], lambda: self.manage_table('customers')),
            (TABLES_CONFIG['sales']['title'], lambda: self.manage_table('sales')),
            (TABLES_CONFIG['sale_items']['title'], lambda: self.manage_table('sale_items')),
        ]
        for text, slot in buttons:
            button = QPushButton(text)
            button.setMinimumHeight(30)
            button.clicked.connect(slot)
            self.top_panel.addWidget(button)

        # Добавляем кнопку поиска с выпадающим меню
        search_button = QPushButton("Поиск")
        search_button.setMinimumHeight(30)
        search_menu = QMenu(self)
        search_menu.addAction("Поиск клиента", self.show_customer_search)
        search_menu.addAction("Поиск сотрудника", self.show_employee_search)
        search_menu.addAction("Поиск поставщика", self.show_supplier_search)
        search_button.setMenu(search_menu)
        self.top_panel.addWidget(search_button)

        # Добавляем кнопку отчетов
        reports_button = QPushButton("Отчеты")
        reports_button.setMinimumHeight(30)
        reports_button.clicked.connect(self.show_reports)
        self.top_panel.addWidget(reports_button)
    
    def setup_content(self, layout):
        self.content_label = QLabel("Выберите действие в верхнем меню")
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.content_label)
    
    def manage_table(self, table_key):
        config = TABLES_CONFIG[table_key]
        self.clear_content()
        self.content_label.setText(config['title'])
        headers = [h for h in config['headers'] if h != 'ID']
        table = QTableWidget()
        table.setColumnCount(len(headers) + 1)  # +1 для колонки Действия
        table.setHorizontalHeaderLabels(headers + ["Действия"])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setStyleSheet("""
            QTableWidget { background: #232323; color: #fff; font-size: 15px; border-radius: 8px; }
            QHeaderView::section { background: #333; color: #fff; font-weight: bold; font-size: 16px; padding: 6px; border: none; }
            QTableWidget::item { padding: 6px; }
            QTableWidget QTableCornerButton::section { background: #333; border: none; }
        """)
        buttons_layout = QHBoxLayout()
        add_button = QPushButton(f"Добавить {config['title'].split()[0].lower()}")
        add_button.setStyleSheet("""
            QPushButton { background: #0078d7; color: #fff; border-radius: 8px; padding: 8px 18px; font-size: 15px; font-weight: bold; }
            QPushButton:hover { background: #005fa3; }
        """)
        add_button.clicked.connect(lambda: self.add_row(table_key, table))
        buttons_layout.addWidget(add_button)
        self.content_layout.addLayout(buttons_layout)
        self.content_layout.addWidget(table)
        self.load_table(table_key, table)
    
    def clear_content(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())
        layout.deleteLater()
    
    def load_table(self, table_key, table):
        rows = load_table_data(table_key)
        table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, value in enumerate(row[1:]):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                table.setItem(i, j, item)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(0, 0, 0, 0)
            edit_btn = QPushButton("")
            edit_btn.setToolTip("Изменить")
            edit_btn.setFixedWidth(32)
            edit_btn.setStyleSheet("QPushButton { background: #ffc107; color: #232323; border-radius: 6px; padding: 4px; } QPushButton:hover { background: #ffb300; }")
            delete_btn = QPushButton("")
            delete_btn.setToolTip("Удалить")
            delete_btn.setFixedWidth(32)
            delete_btn.setStyleSheet("QPushButton { background: #e53935; color: #fff; border-radius: 6px; padding: 4px; } QPushButton:hover { background: #b71c1c; }")
            edit_btn.clicked.connect(lambda _, r=row: self.edit_row(table_key, table, r))
            delete_btn.clicked.connect(lambda _, pk_val=row[0]: self.delete_row(table_key, table, pk_val))
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_widget.setLayout(actions_layout)
            table.setCellWidget(i, len(row)-1, actions_widget)

    def add_row(self, table_key, table):
        config = TABLES_CONFIG[table_key]
        combos = {}
        fields = config['fields']
        for f in fields:
            if f.get('type') == 'combo':
                combos[f['name']] = get_combo_values(f['combo_table'], f['combo_label'])
        dialog = UniversalEditDialog(self, f"Добавить {config['title'].split()[0].lower()}", fields, combos=combos)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            vals = dialog.get_values()
            if table_key == 'employees':
                if 'hire_date' not in vals or not vals['hire_date']:
                    vals['hire_date'] = datetime.now().date().strftime('%Y-%m-%d')
                if 'hire_date' not in [f['name'] for f in config['fields']]:
                    config['fields'].append({'name': 'hire_date', 'label': 'Дата приёма', 'type': 'date'})
            if add_row_to_table(table_key, vals):
                self.load_table(table_key, table)

    def edit_row(self, table_key, table, row_data):
        config = TABLES_CONFIG[table_key]
        pk = config['pk']
        combos = {}
        for f in config['fields']:
            if f.get('type') == 'combo':
                combos[f['name']] = get_combo_values(f['combo_table'], f['combo_label'])
        values = {f['name']: row_data[i+1] for i, f in enumerate(config['fields'])}
        dialog = UniversalEditDialog(self, f"Изменить {config['title'].split()[0].lower()}", config['fields'], values, combos=combos)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            vals = dialog.get_values()
            if update_row_in_table(table_key, vals, row_data[0]):
                self.load_table(table_key, table)

    def delete_row(self, table_key, table, pk_value):
        reply = QMessageBox.question(self, "Удаление", f"Вы уверены, что хотите удалить запись?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if delete_row_from_table(table_key, pk_value):
                self.load_table(table_key, table)

    def show_reports(self):
        self.clear_content()
        self.content_label.setText("Отчеты")
        
        reports_layout = QVBoxLayout()
        
        # Кнопки для различных отчетов
        reports = [
            ("Отчет по продажам", self.show_sales_report),
            ("Отчет по поставкам", self.show_deliveries_report),
            ("Отчет по клиентам", self.show_customers_report),
            ("Отчет по тканям", self.show_fabrics_report)
        ]
        
        for text, slot in reports:
            button = QPushButton(text)
            button.setMinimumHeight(50)
            button.setStyleSheet("""
                QPushButton { 
                    background: #0078d7; 
                    color: #fff; 
                    border-radius: 8px; 
                    padding: 8px 18px; 
                    font-size: 15px; 
                    font-weight: bold; 
                }
                QPushButton:hover { 
                    background: #005fa3; 
                }
            """)
            button.clicked.connect(slot)
            reports_layout.addWidget(button)
        
        self.content_layout.addLayout(reports_layout)

    def show_sales_report(self):
        self.clear_content()
        self.content_label.setText("Отчёт по продажам")
        
        report_container = QWidget()
        report_layout = QVBoxLayout(report_container)
        report_layout.setContentsMargins(0, 0, 0, 0)
        report_layout.setSpacing(0)

        # Создаем группу фильтров
        filters_group = QGroupBox("Фильтры")
        filters_layout = QGridLayout()
        
        # Добавляем фильтры по датам
        start_date_label = QLabel("Начальная дата:")
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        
        end_date_label = QLabel("Конечная дата:")
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        
        filters_layout.addWidget(start_date_label, 0, 0)
        filters_layout.addWidget(self.start_date, 0, 1)
        filters_layout.addWidget(end_date_label, 0, 2)
        filters_layout.addWidget(self.end_date, 0, 3)
        
        # Кнопка обновления отчёта
        update_button = QPushButton("Обновить отчёт")
        update_button.setStyleSheet("""
            QPushButton { 
                background: #0078d7; 
                color: #fff; 
                border-radius: 8px; 
                padding: 8px 18px; 
                font-size: 15px; 
                font-weight: bold; 
            }
            QPushButton:hover { 
                background: #005fa3; 
            }
        """)
        update_button.clicked.connect(self.update_sales_report)
        filters_layout.addWidget(update_button, 0, 4)
        
        filters_group.setLayout(filters_layout)
        report_layout.addWidget(filters_group)
        
        # Создаем группу с итогами
        summary_group = QGroupBox("Итоги")
        summary_layout = QGridLayout()
        
        # Добавляем метки для итогов
        self.total_sales_label = QLabel("Общая сумма продаж: 0 ₽")
        self.total_sales_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.sales_count_label = QLabel("Количество продаж: 0")
        self.sales_count_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.avg_sale_label = QLabel("Средний чек: 0 ₽")
        self.avg_sale_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        summary_layout.addWidget(self.total_sales_label, 0, 0)
        summary_layout.addWidget(self.sales_count_label, 0, 1)
        summary_layout.addWidget(self.avg_sale_label, 0, 2)
        
        summary_group.setLayout(summary_layout)
        report_layout.addWidget(summary_group)
        
        # Создаем таблицу для деталей продаж
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(6)
        self.sales_table.setHorizontalHeaderLabels([
            "Дата продажи", "Клиент", "Товар", "Количество (м)", 
            "Цена за м", "Сумма"
        ])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.sales_table.setStyleSheet(get_table_style())
        
        report_layout.addWidget(self.sales_table)

        # Кнопка экспорта
        export_button = create_export_button(report_container, self.export_sales_report_to_excel)
        def position_export_btn():
            margin = 16
            x = report_container.width() - export_button.width() - margin
            y = report_container.height() - export_button.height() - margin
            export_button.move(x, y)
        report_container.resizeEvent = lambda event: (position_export_btn(), QWidget.resizeEvent(report_container, event))

        self.content_layout.addWidget(report_container)
        self.update_sales_report()
    
    def update_sales_report(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Получаем даты из фильтров
            start_date = self.start_date.date().toString("yyyy-MM-dd")
            end_date = self.end_date.date().toString("yyyy-MM-dd")
            
            # Запрос для получения итогов
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(s.total_amount), 0) as total_sales,
                    COUNT(s.sale_id) as sales_count,
                    COALESCE(AVG(s.total_amount), 0) as avg_sale
                FROM sales s
                WHERE s.sale_date::date BETWEEN %s AND %s
            """, (start_date, end_date))
            
            total_sales, sales_count, avg_sale = cursor.fetchone()
            
            # Обновляем метки с итогами
            self.total_sales_label.setText(f"Общая сумма продаж: {total_sales:,.2f} ₽")
            self.sales_count_label.setText(f"Количество продаж: {sales_count}")
            self.avg_sale_label.setText(f"Средний чек: {avg_sale:,.2f} ₽")
            
            # Запрос для получения деталей продаж
            cursor.execute("""
                SELECT 
                    s.sale_date,
                    c.full_name as customer_name,
                    f.name as fabric_name,
                    si.quantity_meters,
                    si.price_per_meter,
                    si.total_amount
                FROM sales s
                JOIN customers c ON s.customer_id = c.customer_id
                JOIN sale_items si ON s.sale_id = si.sale_id
                JOIN fabrics f ON si.fabric_id = f.fabric_id
                WHERE s.sale_date::date BETWEEN %s AND %s
                ORDER BY s.sale_date DESC
            """, (start_date, end_date))
            
            rows = cursor.fetchall()
            
            # Обновляем таблицу
            self.sales_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, value in enumerate(row):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                    self.sales_table.setItem(i, j, item)
            
            cursor.close()
            conn.close()
            
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке отчёта: {e}")

    def show_deliveries_report(self):
        self.clear_content()
        self.content_label.setText("Отчёт по поставкам")

        report_container = QWidget()
        report_layout = QVBoxLayout(report_container)
        report_layout.setContentsMargins(0, 0, 0, 0)
        report_layout.setSpacing(0)

        # Фильтры
        filters_group = QGroupBox("Фильтры")
        filters_layout = QGridLayout()
        start_date_label = QLabel("Начальная дата:")
        self.deliv_start_date = QDateEdit()
        self.deliv_start_date.setDate(QDate.currentDate().addMonths(-1))
        self.deliv_start_date.setCalendarPopup(True)
        end_date_label = QLabel("Конечная дата:")
        self.deliv_end_date = QDateEdit()
        self.deliv_end_date.setDate(QDate.currentDate())
        self.deliv_end_date.setCalendarPopup(True)
        filters_layout.addWidget(start_date_label, 0, 0)
        filters_layout.addWidget(self.deliv_start_date, 0, 1)
        filters_layout.addWidget(end_date_label, 0, 2)
        filters_layout.addWidget(self.deliv_end_date, 0, 3)
        update_button = QPushButton("Обновить отчёт")
        update_button.setStyleSheet(get_button_style())
        update_button.clicked.connect(self.update_deliveries_report)
        filters_layout.addWidget(update_button, 0, 4)
        filters_group.setLayout(filters_layout)
        report_layout.addWidget(filters_group)

        # Итоги
        summary_group = QGroupBox("Итоги")
        summary_layout = QGridLayout()
        self.total_deliveries_label = QLabel("Количество поставок: 0")
        self.total_deliveries_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        summary_layout.addWidget(self.total_deliveries_label, 0, 0)
        summary_group.setLayout(summary_layout)
        report_layout.addWidget(summary_group)

        # Таблица
        self.deliveries_table = QTableWidget()
        self.deliveries_table.setColumnCount(3)
        self.deliveries_table.setHorizontalHeaderLabels([
            "Дата поставки", "Поставщик", "Сотрудник"
        ])
        self.deliveries_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.deliveries_table.setStyleSheet(get_table_style())
        report_layout.addWidget(self.deliveries_table)

        # Кнопка экспорта
        export_button = create_export_button(report_container, self.export_deliveries_report_to_excel)
        def position_export_btn():
            margin = 16
            x = report_container.width() - export_button.width() - margin
            y = report_container.height() - export_button.height() - margin
            export_button.move(x, y)
        report_container.resizeEvent = lambda event: (position_export_btn(), QWidget.resizeEvent(report_container, event))

        self.content_layout.addWidget(report_container)
        self.update_deliveries_report()

    def update_deliveries_report(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            start_date = self.deliv_start_date.date().toString("yyyy-MM-dd")
            end_date = self.deliv_end_date.date().toString("yyyy-MM-dd")
            # Итоги
            cursor.execute("""
                SELECT COUNT(d.delivery_id) as total_deliveries
                FROM deliveries d
                WHERE d.delivery_date::date BETWEEN %s AND %s
            """, (start_date, end_date))
            total_deliveries = cursor.fetchone()[0]
            self.total_deliveries_label.setText(f"Количество поставок: {total_deliveries}")
            # Детали
            cursor.execute("""
                SELECT d.delivery_date, s.company_name, e.full_name
                FROM deliveries d
                JOIN suppliers s ON d.supplier_id = s.supplier_id
                JOIN employees e ON d.employee_id = e.employee_id
                WHERE d.delivery_date::date BETWEEN %s AND %s
                ORDER BY d.delivery_date DESC
            """, (start_date, end_date))
            rows = cursor.fetchall()
            self.deliveries_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, value in enumerate(row):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                    self.deliveries_table.setItem(i, j, item)
            cursor.close()
            conn.close()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке отчёта: {e}")

    def export_deliveries_report_to_excel(self):
        export_table_to_excel(self.deliveries_table, "Поставки")

    def show_customers_report(self):
        self.clear_content()
        self.content_label.setText("Отчёт по клиентам")

        report_container = QWidget()
        report_layout = QVBoxLayout(report_container)
        report_layout.setContentsMargins(0, 0, 0, 0)
        report_layout.setSpacing(0)

        # Фильтры
        filters_group = QGroupBox("Фильтры")
        filters_layout = QGridLayout()
        start_date_label = QLabel("С даты первой покупки:")
        self.cust_start_date = QDateEdit()
        self.cust_start_date.setDate(QDate.currentDate().addMonths(-1))
        self.cust_start_date.setCalendarPopup(True)
        end_date_label = QLabel("По дату первой покупки:")
        self.cust_end_date = QDateEdit()
        self.cust_end_date.setDate(QDate.currentDate())
        self.cust_end_date.setCalendarPopup(True)
        filters_layout.addWidget(start_date_label, 0, 0)
        filters_layout.addWidget(self.cust_start_date, 0, 1)
        filters_layout.addWidget(end_date_label, 0, 2)
        filters_layout.addWidget(self.cust_end_date, 0, 3)
        update_button = QPushButton("Обновить отчёт")
        update_button.setStyleSheet(get_button_style())
        update_button.clicked.connect(self.update_customers_report)
        filters_layout.addWidget(update_button, 0, 4)
        filters_group.setLayout(filters_layout)
        report_layout.addWidget(filters_group)

        # Итоги
        summary_group = QGroupBox("Итоги")
        summary_layout = QGridLayout()
        self.total_customers_label = QLabel("Всего клиентов: 0")
        self.total_customers_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.new_customers_label = QLabel("Новых за период: 0")
        self.new_customers_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.avg_customer_check_label = QLabel("Средний чек на клиента: 0 ₽")
        self.avg_customer_check_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        summary_layout.addWidget(self.total_customers_label, 0, 0)
        summary_layout.addWidget(self.new_customers_label, 0, 1)
        summary_layout.addWidget(self.avg_customer_check_label, 0, 2)
        summary_group.setLayout(summary_layout)
        report_layout.addWidget(summary_group)

        # Таблица
        self.customers_table = QTableWidget()
        self.customers_table.setColumnCount(7)
        self.customers_table.setHorizontalHeaderLabels([
            "ФИО", "Телефон", "E-mail", "Кол-во покупок", "Сумма покупок", "Первая покупка", "Последняя покупка"
        ])
        self.customers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.customers_table.setStyleSheet(get_table_style())
        report_layout.addWidget(self.customers_table)

        # Кнопка экспорта
        export_button = create_export_button(report_container, self.export_customers_report_to_excel)
        def position_export_btn():
            margin = 16
            x = report_container.width() - export_button.width() - margin
            y = report_container.height() - export_button.height() - margin
            export_button.move(x, y)
        report_container.resizeEvent = lambda event: (position_export_btn(), QWidget.resizeEvent(report_container, event))

        self.content_layout.addWidget(report_container)
        self.update_customers_report()

    def update_customers_report(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            start_date = self.cust_start_date.date().toString("yyyy-MM-dd")
            end_date = self.cust_end_date.date().toString("yyyy-MM-dd")
            # Итоги
            cursor.execute("""
                SELECT COUNT(*) FROM customers
            """)
            total_customers = cursor.fetchone()[0]
            cursor.execute("""
                SELECT COUNT(DISTINCT c.customer_id)
                FROM customers c
                JOIN sales s ON c.customer_id = s.customer_id
                WHERE s.sale_date::date BETWEEN %s AND %s
            """, (start_date, end_date))
            new_customers = cursor.fetchone()[0]
            cursor.execute("""
                SELECT COALESCE(AVG(total), 0) FROM (
                    SELECT SUM(s.total_amount) as total
                    FROM customers c
                    JOIN sales s ON c.customer_id = s.customer_id
                    GROUP BY c.customer_id
                ) t
            """)
            avg_check = cursor.fetchone()[0]
            self.total_customers_label.setText(f"Всего клиентов: {total_customers}")
            self.new_customers_label.setText(f"Новых за период: {new_customers}")
            self.avg_customer_check_label.setText(f"Средний чек на клиента: {avg_check:,.2f} ₽")
            # Таблица
            cursor.execute("""
                SELECT c.full_name, c.phone, c.email,
                       COUNT(s.sale_id) as sales_count,
                       COALESCE(SUM(s.total_amount), 0) as total_amount,
                       MIN(s.sale_date) as first_sale,
                       MAX(s.sale_date) as last_sale
                FROM customers c
                LEFT JOIN sales s ON c.customer_id = s.customer_id
                GROUP BY c.customer_id, c.full_name, c.phone, c.email
                HAVING MIN(s.sale_date)::date BETWEEN %s AND %s
                ORDER BY total_amount DESC
            """, (start_date, end_date))
            rows = cursor.fetchall()
            self.customers_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, value in enumerate(row):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                    self.customers_table.setItem(i, j, item)
            cursor.close()
            conn.close()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке отчёта: {e}")

    def export_customers_report_to_excel(self):
        export_table_to_excel(self.customers_table, "Клиенты")

    def show_fabrics_report(self):
        self.clear_content()
        self.content_label.setText("Отчёт по тканям")

        report_container = QWidget()
        report_layout = QVBoxLayout(report_container)
        report_layout.setContentsMargins(0, 0, 0, 0)
        report_layout.setSpacing(0)

        # Фильтры
        filters_group = QGroupBox("Фильтры")
        filters_layout = QGridLayout()
        # Категория
        category_label = QLabel("Категория:")
        self.fabric_category_combo = QComboBox()
        self.fabric_category_combo.addItem("Все", None)
        for val, text in get_combo_values('fabric_categories', 'name'):
            self.fabric_category_combo.addItem(str(text), val)
        # Поставщик
        supplier_label = QLabel("Поставщик:")
        self.fabric_supplier_combo = QComboBox()
        self.fabric_supplier_combo.addItem("Все", None)
        for val, text in get_combo_values('suppliers', 'company_name'):
            self.fabric_supplier_combo.addItem(str(text), val)
        # Остаток
        stock_label = QLabel("Остаток <")
        self.fabric_stock_edit = QLineEdit()
        self.fabric_stock_edit.setPlaceholderText("например, 10")
        # Дата поступления
        date_label = QLabel("С даты поступления:")
        self.fabric_date_edit = QDateEdit()
        self.fabric_date_edit.setDate(QDate.currentDate().addMonths(-1))
        self.fabric_date_edit.setCalendarPopup(True)
        # Кнопка
        update_button = QPushButton("Обновить отчёт")
        update_button.setStyleSheet("""
            QPushButton { background: #0078d7; color: #fff; border-radius: 8px; padding: 8px 18px; font-size: 15px; font-weight: bold; }
            QPushButton:hover { background: #005fa3; }
        """)
        update_button.clicked.connect(self.update_fabrics_report)
        filters_layout.addWidget(category_label, 0, 0)
        filters_layout.addWidget(self.fabric_category_combo, 0, 1)
        filters_layout.addWidget(supplier_label, 0, 2)
        filters_layout.addWidget(self.fabric_supplier_combo, 0, 3)
        filters_layout.addWidget(stock_label, 1, 0)
        filters_layout.addWidget(self.fabric_stock_edit, 1, 1)
        filters_layout.addWidget(date_label, 1, 2)
        filters_layout.addWidget(self.fabric_date_edit, 1, 3)
        filters_layout.addWidget(update_button, 0, 4, 2, 1)
        filters_group.setLayout(filters_layout)
        report_layout.addWidget(filters_group)

        # Итоги
        summary_group = QGroupBox("Итоги")
        summary_layout = QGridLayout()
        self.total_fabrics_label = QLabel("Всего видов тканей: 0")
        self.total_fabrics_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.low_stock_label = QLabel("С низким остатком: 0")
        self.low_stock_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.avg_price_label = QLabel("Средняя цена за м: 0 ₽")
        self.avg_price_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        summary_layout.addWidget(self.total_fabrics_label, 0, 0)
        summary_layout.addWidget(self.low_stock_label, 0, 1)
        summary_layout.addWidget(self.avg_price_label, 0, 2)
        summary_group.setLayout(summary_layout)
        report_layout.addWidget(summary_group)

        # Таблица
        self.fabrics_table = QTableWidget()
        self.fabrics_table.setColumnCount(9)
        self.fabrics_table.setHorizontalHeaderLabels([
            "Название", "Категория", "Цвет", "Плотность", "Ширина (см)", "Цена за м", "Остаток (м)", "Поставщик", "Дата поступления"
        ])
        self.fabrics_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.fabrics_table.setStyleSheet(get_table_style())
        report_layout.addWidget(self.fabrics_table)

        # Кнопка экспорта
        export_button = create_export_button(report_container, self.export_fabrics_report_to_excel)
        def position_export_btn():
            margin = 16
            x = report_container.width() - export_button.width() - margin
            y = report_container.height() - export_button.height() - margin
            export_button.move(x, y)
        report_container.resizeEvent = lambda event: (position_export_btn(), QWidget.resizeEvent(report_container, event))

        self.content_layout.addWidget(report_container)
        self.update_fabrics_report()

    def update_fabrics_report(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Фильтры
            category_id = self.fabric_category_combo.currentData()
            supplier_id = self.fabric_supplier_combo.currentData()
            stock_limit = self.fabric_stock_edit.text()
            arrival_date = self.fabric_date_edit.date().toString("yyyy-MM-dd")
            # Формируем WHERE
            where = ["f.arrival_date >= %s"]
            params = [arrival_date]
            if category_id:
                where.append("f.category_id = %s")
                params.append(category_id)
            if supplier_id:
                where.append("f.supplier_id = %s")
                params.append(supplier_id)
            if stock_limit:
                where.append("f.stock_meters < %s")
                params.append(stock_limit)
            where_clause = " AND ".join(where)
            # Итоги
            cursor.execute(f"""
                SELECT COUNT(*),
                       SUM(CASE WHEN f.stock_meters < 10 THEN 1 ELSE 0 END),
                       COALESCE(AVG(f.price_per_meter), 0)
                FROM fabrics f
                WHERE {where_clause}
            """, params)
            total, low_stock, avg_price = cursor.fetchone()
            self.total_fabrics_label.setText(f"Всего видов тканей: {total}")
            self.low_stock_label.setText(f"С низким остатком: {low_stock}")
            self.avg_price_label.setText(f"Средняя цена за м: {avg_price:,.2f} ₽")
            # Таблица
            cursor.execute(f"""
                SELECT f.name, c.name, f.color, f.density, f.width_cm, f.price_per_meter, f.stock_meters, s.company_name, f.arrival_date
                FROM fabrics f
                LEFT JOIN fabric_categories c ON f.category_id = c.category_id
                LEFT JOIN suppliers s ON f.supplier_id = s.supplier_id
                WHERE {where_clause}
                ORDER BY f.name
            """, params)
            rows = cursor.fetchall()
            self.fabrics_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, value in enumerate(row):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                    self.fabrics_table.setItem(i, j, item)
            cursor.close()
            conn.close()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке отчёта: {e}")

    def export_fabrics_report_to_excel(self):
        export_table_to_excel(self.fabrics_table, "Ткани")

    def export_sales_report_to_excel(self):
        export_table_to_excel(self.sales_table, "Продажи")

    def show_customer_search(self):
        self.clear_content()
        self.content_label.setText("Поиск клиента")

        search_container = QWidget()
        search_layout = QVBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(0)

        # Создаем группу поиска
        search_group = QGroupBox("Поиск")
        search_group_layout = QHBoxLayout()
        
        # Поле поиска
        self.customer_search_input = QLineEdit()
        self.customer_search_input.setPlaceholderText("Введите фамилию клиента")
        self.customer_search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                font-size: 14px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)
        
        # Кнопка поиска
        search_button = QPushButton("Найти")
        search_button.setStyleSheet(get_button_style())
        search_button.clicked.connect(self.search_customer)
        
        search_group_layout.addWidget(self.customer_search_input)
        search_group_layout.addWidget(search_button)
        search_group.setLayout(search_group_layout)
        search_layout.addWidget(search_group)

        # Информация о клиенте
        self.customer_info_group = QGroupBox("Информация о клиенте")
        customer_info_layout = QGridLayout()
        
        self.customer_name_label = QLabel("ФИО: ")
        self.customer_phone_label = QLabel("Телефон: ")
        self.customer_email_label = QLabel("Email: ")
        self.customer_total_sales_label = QLabel("Всего покупок: ")
        self.customer_total_amount_label = QLabel("Общая сумма: ")
        
        customer_info_layout.addWidget(self.customer_name_label, 0, 0)
        customer_info_layout.addWidget(self.customer_phone_label, 0, 1)
        customer_info_layout.addWidget(self.customer_email_label, 1, 0)
        customer_info_layout.addWidget(self.customer_total_sales_label, 1, 1)
        customer_info_layout.addWidget(self.customer_total_amount_label, 2, 0)
        
        self.customer_info_group.setLayout(customer_info_layout)
        search_layout.addWidget(self.customer_info_group)
        self.customer_info_group.hide()

        # Таблица покупок
        self.customer_sales_table = QTableWidget()
        self.customer_sales_table.setColumnCount(5)
        self.customer_sales_table.setHorizontalHeaderLabels([
            "Дата покупки", "Товар", "Количество (м)", "Цена за м", "Сумма"
        ])
        self.customer_sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.customer_sales_table.setStyleSheet(get_table_style())
        search_layout.addWidget(self.customer_sales_table)

        self.content_layout.addWidget(search_container)

    def search_customer(self):
        try:
            search_text = self.customer_search_input.text().strip()
            if not search_text:
                QMessageBox.warning(self, "Предупреждение", "Введите фамилию для поиска")
                return

            conn = get_db_connection()
            cursor = conn.cursor()

            # Поиск клиента с точным совпадением фамилии
            cursor.execute("""
                SELECT c.customer_id, c.full_name, c.phone, c.email,
                       COUNT(s.sale_id) as total_sales,
                       COALESCE(SUM(s.total_amount), 0) as total_amount
                FROM customers c
                LEFT JOIN sales s ON c.customer_id = s.customer_id
                WHERE c.full_name ILIKE %s
                GROUP BY c.customer_id, c.full_name, c.phone, c.email
            """, (f'{search_text}%',))
            
            customer = cursor.fetchone()
            
            if customer:
                self.customer_info_group.show()
                self.customer_name_label.setText(f"ФИО: {customer[1]}")
                self.customer_phone_label.setText(f"Телефон: {customer[2]}")
                self.customer_email_label.setText(f"Email: {customer[3]}")
                self.customer_total_sales_label.setText(f"Всего покупок: {customer[4]}")
                self.customer_total_amount_label.setText(f"Общая сумма: {customer[5]:,.2f} ₽")

                # Получаем историю покупок
                cursor.execute("""
                    SELECT s.sale_date, f.name, si.quantity_meters, si.price_per_meter, si.total_amount
                    FROM sales s
                    JOIN sale_items si ON s.sale_id = si.sale_id
                    JOIN fabrics f ON si.fabric_id = f.fabric_id
                    WHERE s.customer_id = %s
                    ORDER BY s.sale_date DESC
                """, (customer[0],))
                
                sales = cursor.fetchall()
                self.customer_sales_table.setRowCount(len(sales))
                for i, sale in enumerate(sales):
                    for j, value in enumerate(sale):
                        item = QTableWidgetItem(str(value))
                        item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                        self.customer_sales_table.setItem(i, j, item)
            else:
                self.customer_info_group.hide()
                self.customer_sales_table.setRowCount(0)
                QMessageBox.information(self, "Информация", "Клиент не найден")

            cursor.close()
            conn.close()

        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при поиске клиента: {e}")

    def show_employee_search(self):
        self.clear_content()
        self.content_label.setText("Поиск сотрудника")

        search_container = QWidget()
        search_layout = QVBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(0)

        # Создаем группу поиска
        search_group = QGroupBox("Поиск")
        search_group_layout = QHBoxLayout()
        
        # Поле поиска
        self.employee_search_input = QLineEdit()
        self.employee_search_input.setPlaceholderText("Введите фамилию сотрудника")
        self.employee_search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                font-size: 14px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)
        
        # Кнопка поиска
        search_button = QPushButton("Найти")
        search_button.setStyleSheet(get_button_style())
        search_button.clicked.connect(self.search_employee)
        
        search_group_layout.addWidget(self.employee_search_input)
        search_group_layout.addWidget(search_button)
        search_group.setLayout(search_group_layout)
        search_layout.addWidget(search_group)

        # Информация о сотруднике
        self.employee_info_group = QGroupBox("Информация о сотруднике")
        employee_info_layout = QGridLayout()
        
        self.employee_name_label = QLabel("ФИО: ")
        self.employee_position_label = QLabel("Должность: ")
        self.employee_hire_date_label = QLabel("Дата приема: ")
        self.employee_total_sales_label = QLabel("Всего продаж: ")
        self.employee_total_deliveries_label = QLabel("Всего поставок: ")
        
        employee_info_layout.addWidget(self.employee_name_label, 0, 0)
        employee_info_layout.addWidget(self.employee_position_label, 0, 1)
        employee_info_layout.addWidget(self.employee_hire_date_label, 1, 0)
        employee_info_layout.addWidget(self.employee_total_sales_label, 1, 1)
        employee_info_layout.addWidget(self.employee_total_deliveries_label, 2, 0)
        
        self.employee_info_group.setLayout(employee_info_layout)
        search_layout.addWidget(self.employee_info_group)
        self.employee_info_group.hide()

        # Таблица продаж
        sales_group = QGroupBox("Продажи")
        sales_layout = QVBoxLayout()
        self.employee_sales_table = QTableWidget()
        self.employee_sales_table.setColumnCount(4)
        self.employee_sales_table.setHorizontalHeaderLabels([
            "Дата продажи", "Клиент", "Сумма", "Количество товаров"
        ])
        self.employee_sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.employee_sales_table.setStyleSheet(get_table_style())
        sales_layout.addWidget(self.employee_sales_table)
        sales_group.setLayout(sales_layout)
        search_layout.addWidget(sales_group)

        # Таблица поставок
        deliveries_group = QGroupBox("Поставки")
        deliveries_layout = QVBoxLayout()
        self.employee_deliveries_table = QTableWidget()
        self.employee_deliveries_table.setColumnCount(2)
        self.employee_deliveries_table.setHorizontalHeaderLabels([
            "Дата поставки", "Поставщик"
        ])
        self.employee_deliveries_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.employee_deliveries_table.setStyleSheet(get_table_style())
        deliveries_layout.addWidget(self.employee_deliveries_table)
        deliveries_group.setLayout(deliveries_layout)
        search_layout.addWidget(deliveries_group)

        self.content_layout.addWidget(search_container)

    def search_employee(self):
        try:
            search_text = self.employee_search_input.text().strip()
            if not search_text:
                QMessageBox.warning(self, "Предупреждение", "Введите фамилию для поиска")
                return

            conn = get_db_connection()
            cursor = conn.cursor()

            # Поиск сотрудника
            cursor.execute("""
                SELECT e.employee_id, e.full_name, e.position, e.hire_date,
                       COUNT(DISTINCT s.sale_id) as total_sales,
                       COUNT(DISTINCT d.delivery_id) as total_deliveries
                FROM employees e
                LEFT JOIN sales s ON e.employee_id = s.employee_id
                LEFT JOIN deliveries d ON e.employee_id = d.employee_id
                WHERE e.full_name ILIKE %s
                GROUP BY e.employee_id, e.full_name, e.position, e.hire_date
            """, (f'{search_text}%',))
            
            employee = cursor.fetchone()
            
            if employee:
                self.employee_info_group.show()
                self.employee_name_label.setText(f"ФИО: {employee[1]}")
                self.employee_position_label.setText(f"Должность: {employee[2]}")
                self.employee_hire_date_label.setText(f"Дата приема: {employee[3]}")
                self.employee_total_sales_label.setText(f"Всего продаж: {employee[4]}")
                self.employee_total_deliveries_label.setText(f"Всего поставок: {employee[5]}")

                # Получаем историю продаж
                cursor.execute("""
                    SELECT s.sale_date, c.full_name, s.total_amount,
                           COUNT(si.sale_item_id) as items_count
                    FROM sales s
                    JOIN customers c ON s.customer_id = c.customer_id
                    JOIN sale_items si ON s.sale_id = si.sale_id
                    WHERE s.employee_id = %s
                    GROUP BY s.sale_id, s.sale_date, c.full_name, s.total_amount
                    ORDER BY s.sale_date DESC
                """, (employee[0],))
                
                sales = cursor.fetchall()
                self.employee_sales_table.setRowCount(len(sales))
                for i, sale in enumerate(sales):
                    for j, value in enumerate(sale):
                        item = QTableWidgetItem(str(value))
                        item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                        self.employee_sales_table.setItem(i, j, item)

                # Получаем историю поставок (только дата и поставщик)
                cursor.execute("""
                    SELECT d.delivery_date, s.company_name
                    FROM deliveries d
                    JOIN suppliers s ON d.supplier_id = s.supplier_id
                    WHERE d.employee_id = %s
                    ORDER BY d.delivery_date DESC
                """, (employee[0],))
                
                deliveries = cursor.fetchall()
                self.employee_deliveries_table.setRowCount(len(deliveries))
                for i, delivery in enumerate(deliveries):
                    for j, value in enumerate(delivery):
                        item = QTableWidgetItem(str(value))
                        item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                        self.employee_deliveries_table.setItem(i, j, item)
            else:
                self.employee_info_group.hide()
                self.employee_sales_table.setRowCount(0)
                self.employee_deliveries_table.setRowCount(0)
                QMessageBox.information(self, "Информация", "Сотрудник не найден")

            cursor.close()
            conn.close()

        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при поиске сотрудника: {e}")

    def show_supplier_search(self):
        self.clear_content()
        self.content_label.setText("Поиск поставщика")

        search_container = QWidget()
        search_layout = QVBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(0)

        # Создаем группу поиска
        search_group = QGroupBox("Поиск")
        search_group_layout = QHBoxLayout()
        
        # Поле поиска
        self.supplier_search_input = QLineEdit()
        self.supplier_search_input.setPlaceholderText("Введите название компании")
        self.supplier_search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                font-size: 14px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)
        
        # Кнопка поиска
        search_button = QPushButton("Найти")
        search_button.setStyleSheet(get_button_style())
        search_button.clicked.connect(self.search_supplier)
        
        search_group_layout.addWidget(self.supplier_search_input)
        search_group_layout.addWidget(search_button)
        search_group.setLayout(search_group_layout)
        search_layout.addWidget(search_group)

        # Информация о поставщике
        self.supplier_info_group = QGroupBox("Информация о поставщике")
        supplier_info_layout = QGridLayout()
        
        self.supplier_name_label = QLabel("Название компании: ")
        self.supplier_contact_label = QLabel("Контактное лицо: ")
        self.supplier_phone_label = QLabel("Телефон: ")
        self.supplier_email_label = QLabel("Email: ")
        self.supplier_total_deliveries_label = QLabel("Всего поставок: ")
        
        supplier_info_layout.addWidget(self.supplier_name_label, 0, 0)
        supplier_info_layout.addWidget(self.supplier_contact_label, 0, 1)
        supplier_info_layout.addWidget(self.supplier_phone_label, 1, 0)
        supplier_info_layout.addWidget(self.supplier_email_label, 1, 1)
        supplier_info_layout.addWidget(self.supplier_total_deliveries_label, 2, 0)
        
        self.supplier_info_group.setLayout(supplier_info_layout)
        search_layout.addWidget(self.supplier_info_group)
        self.supplier_info_group.hide()

        # Таблица поставок
        self.supplier_deliveries_table = QTableWidget()
        self.supplier_deliveries_table.setColumnCount(2)
        self.supplier_deliveries_table.setHorizontalHeaderLabels([
            "Дата поставки", "Сотрудник"
        ])
        self.supplier_deliveries_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.supplier_deliveries_table.setStyleSheet(get_table_style())
        search_layout.addWidget(self.supplier_deliveries_table)

        self.content_layout.addWidget(search_container)

    def search_supplier(self):
        try:
            search_text = self.supplier_search_input.text().strip()
            if not search_text:
                QMessageBox.warning(self, "Предупреждение", "Введите название компании")
                return

            conn = get_db_connection()
            cursor = conn.cursor()

            # Поиск поставщика
            cursor.execute("""
                SELECT s.supplier_id, s.company_name, s.contact_person, s.phone, s.email,
                       COUNT(DISTINCT d.delivery_id) as total_deliveries
                FROM suppliers s
                LEFT JOIN deliveries d ON s.supplier_id = d.supplier_id
                WHERE s.company_name ILIKE %s
                GROUP BY s.supplier_id, s.company_name, s.contact_person, s.phone, s.email
            """, (f'{search_text}%',))
            
            supplier = cursor.fetchone()
            
            if supplier:
                self.supplier_info_group.show()
                self.supplier_name_label.setText(f"Название компании: {supplier[1]}")
                self.supplier_contact_label.setText(f"Контактное лицо: {supplier[2]}")
                self.supplier_phone_label.setText(f"Телефон: {supplier[3]}")
                self.supplier_email_label.setText(f"Email: {supplier[4]}")
                self.supplier_total_deliveries_label.setText(f"Всего поставок: {supplier[5]}")

                # Получаем историю поставок (только дата и сотрудник)
                cursor.execute("""
                    SELECT d.delivery_date, e.full_name
                    FROM deliveries d
                    JOIN employees e ON d.employee_id = e.employee_id
                    WHERE d.supplier_id = %s
                    ORDER BY d.delivery_date DESC
                """, (supplier[0],))
                
                deliveries = cursor.fetchall()
                self.supplier_deliveries_table.setRowCount(len(deliveries))
                for i, delivery in enumerate(deliveries):
                    for j, value in enumerate(delivery):
                        item = QTableWidgetItem(str(value))
                        item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                        self.supplier_deliveries_table.setItem(i, j, item)
            else:
                self.supplier_info_group.hide()
                self.supplier_deliveries_table.setRowCount(0)
                QMessageBox.information(self, "Информация", "Поставщик не найден")

            cursor.close()
            conn.close()

        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при поиске поставщика: {e}")

class UniversalEditDialog(QDialog):
    def __init__(self, parent, title, fields, values=None, combos=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.inputs = {}
        layout = QFormLayout()
        for field in fields:
            field_type = field.get('type', 'str')
            label = field['label']
            name = field['name']
            default = values.get(name) if values else None
            if combos and name in combos:
                combo = QComboBox()
                for val, text in combos[name]:
                    combo.addItem(str(text), val)
                if default is not None:
                    found = False
                    for i in range(combo.count()):
                        if combo.itemData(i) == default:
                            combo.setCurrentIndex(i)
                            found = True
                            break
                    if not found and isinstance(default, str):
                        for i in range(combo.count()):
                            if combo.itemText(i) == default:
                                combo.setCurrentIndex(i)
                                found = True
                                break
                self.inputs[name] = combo
                layout.addRow(label, combo)
            elif field_type == 'date':
                date_edit = QDateEdit()
                date_edit.setCalendarPopup(True)
                if default:
                    date_edit.setDate(QDate.fromString(str(default), "yyyy-MM-dd"))
                else:
                    date_edit.setDate(QDate.currentDate())
                self.inputs[name] = date_edit
                layout.addRow(label, date_edit)
            elif field_type == 'password':
                line = QLineEdit(default if default else "")
                line.setEchoMode(QLineEdit.EchoMode.Password)
                self.inputs[name] = line
                layout.addRow(label, line)
            else:
                line = QLineEdit(str(default) if default is not None else "")
                self.inputs[name] = line
                layout.addRow(label, line)
        buttons = QHBoxLayout()
        save_button = QPushButton("Сохранить")
        cancel_button = QPushButton("Отмена")
        buttons.addWidget(save_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)
        self.setLayout(layout)
        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

    def get_values(self):
        result = {}
        for name, widget in self.inputs.items():
            if isinstance(widget, QLineEdit):
                result[name] = widget.text()
            elif isinstance(widget, QComboBox):
                result[name] = widget.currentData()
            elif isinstance(widget, QDateEdit):
                result[name] = widget.date().toString("yyyy-MM-dd")
        return result 