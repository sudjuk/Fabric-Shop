from PySide6.QtWidgets import QVBoxLayout, QPushButton, QWidget, QDialog, QFormLayout, QLineEdit, QComboBox, QDateEdit, QLabel, QHBoxLayout, QMessageBox, QGroupBox, QGridLayout, QTableWidget, QHeaderView, QTableWidgetItem
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QDoubleValidator
from base_role_window import BaseRoleWindow
from database_utils import get_combo_values, get_table_style, create_export_button, export_table_to_excel, get_button_style, get_db_connection
import psycopg2
import datetime

class SellerWindow(BaseRoleWindow):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.setup_content(self.content_layout)

    def get_title(self):
        return "Панель продавца"
    
    def setup_top_panel(self):
        buttons = [
            ("Новая продажа", self.new_sale),
            ("История продаж", self.show_sales_report),
            ("Клиенты", self.show_customers_report),
            ("Каталог тканей", self.show_fabrics_report),
            ("Добавить поставку", self.add_delivery),
            ("Отчет по поставкам", self.show_deliveries_report)
        ]
        for text, slot in buttons:
            button = QPushButton(text)
            button.setMinimumHeight(30)
            button.clicked.connect(slot)
            self.top_panel.addWidget(button)

    def setup_content(self, layout):
        pass

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

    def show_sales_report(self):
        self.clear_content()
        self.content_label.setText("Отчёт по продажам")
        report_container = QWidget()
        report_layout = QVBoxLayout(report_container)
        report_layout.setContentsMargins(0, 0, 0, 0)
        report_layout.setSpacing(0)
        # Фильтры
        filters_group = QGroupBox("Фильтры")
        filters_layout = QGridLayout()
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
        update_button = QPushButton("Обновить отчёт")
        update_button.setStyleSheet(get_button_style())
        update_button.clicked.connect(self.update_sales_report)
        filters_layout.addWidget(update_button, 0, 4)
        filters_group.setLayout(filters_layout)
        report_layout.addWidget(filters_group)
        # Итоги
        summary_group = QGroupBox("Итоги")
        summary_layout = QGridLayout()
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
        # Таблица
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(6)
        self.sales_table.setHorizontalHeaderLabels([
            "Дата продажи", "Клиент", "Товар", "Количество (м)", "Цена за м", "Сумма"
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
            start_date = self.start_date.date().toString("yyyy-MM-dd")
            end_date = self.end_date.date().toString("yyyy-MM-dd")
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(s.total_amount), 0) as total_sales,
                    COUNT(s.sale_id) as sales_count,
                    COALESCE(AVG(s.total_amount), 0) as avg_sale
                FROM sales s
                WHERE s.sale_date::date BETWEEN %s AND %s
            """, (start_date, end_date))
            total_sales, sales_count, avg_sale = cursor.fetchone()
            self.total_sales_label.setText(f"Общая сумма продаж: {total_sales:,.2f} ₽")
            self.sales_count_label.setText(f"Количество продаж: {sales_count}")
            self.avg_sale_label.setText(f"Средний чек: {avg_sale:,.2f} ₽")
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
    def export_sales_report_to_excel(self):
        export_table_to_excel(self.sales_table, "Продажи")

    def show_customers_report(self):
        self.clear_content()
        self.content_label.setText("Отчёт по клиентам")
        report_container = QWidget()
        report_layout = QVBoxLayout(report_container)
        report_layout.setContentsMargins(0, 0, 0, 0)
        report_layout.setSpacing(0)
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
        self.customers_table = QTableWidget()
        self.customers_table.setColumnCount(7)
        self.customers_table.setHorizontalHeaderLabels([
            "ФИО", "Телефон", "E-mail", "Кол-во покупок", "Сумма покупок", "Первая покупка", "Последняя покупка"
        ])
        self.customers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.customers_table.setStyleSheet(get_table_style())
        report_layout.addWidget(self.customers_table)
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
        filters_group = QGroupBox("Фильтры")
        filters_layout = QGridLayout()
        category_label = QLabel("Категория:")
        self.fabric_category_combo = QComboBox()
        self.fabric_category_combo.addItem("Все", None)
        for val, text in get_combo_values('fabric_categories', 'name'):
            self.fabric_category_combo.addItem(str(text), val)
        supplier_label = QLabel("Поставщик:")
        self.fabric_supplier_combo = QComboBox()
        self.fabric_supplier_combo.addItem("Все", None)
        for val, text in get_combo_values('suppliers', 'company_name'):
            self.fabric_supplier_combo.addItem(str(text), val)
        stock_label = QLabel("Остаток <")
        self.fabric_stock_edit = QLineEdit()
        self.fabric_stock_edit.setPlaceholderText("например, 10")
        date_label = QLabel("С даты поступления:")
        self.fabric_date_edit = QDateEdit()
        self.fabric_date_edit.setDate(QDate.currentDate().addMonths(-1))
        self.fabric_date_edit.setCalendarPopup(True)
        update_button = QPushButton("Обновить отчёт")
        update_button.setStyleSheet(get_button_style())
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
        self.fabrics_table = QTableWidget()
        self.fabrics_table.setColumnCount(9)
        self.fabrics_table.setHorizontalHeaderLabels([
            "Название", "Категория", "Цвет", "Плотность", "Ширина (см)", "Цена за м", "Остаток (м)", "Поставщик", "Дата поступления"
        ])
        self.fabrics_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.fabrics_table.setStyleSheet(get_table_style())
        report_layout.addWidget(self.fabrics_table)
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
            category_id = self.fabric_category_combo.currentData()
            supplier_id = self.fabric_supplier_combo.currentData()
            stock_limit = self.fabric_stock_edit.text()
            arrival_date = self.fabric_date_edit.date().toString("yyyy-MM-dd")
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

    def new_sale(self):
        dlg = NewSaleDialog(self)
        dlg.exec()

    def add_delivery(self):
        dlg = AddDeliveryDialog(self)
        dlg.exec()

    def show_deliveries_report(self):
        # Используем отчёт менеджера
        from manager import ManagerWindow
        mw = ManagerWindow(self)
        mw.show_deliveries_report()
        self.clear_content()
        for i in range(mw.content_layout.count()):
            item = mw.content_layout.itemAt(i)
            if item.widget():
                self.content_layout.addWidget(item.widget())
            elif item.layout():
                self.content_layout.addLayout(item.layout())
        self.content_label.setText("Отчёт по поставкам")

class NewSaleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Новая продажа")
        self.setMinimumWidth(700)
        self.layout = QVBoxLayout(self)

        # --- Клиент ---
        client_layout = QHBoxLayout()
        self.client_combo = QComboBox()
        self.reload_clients()
        add_client_btn = QPushButton("+")
        add_client_btn.setToolTip("Добавить клиента")
        add_client_btn.setFixedWidth(32)
        add_client_btn.clicked.connect(self.add_client)
        client_layout.addWidget(QLabel("Клиент:"))
        client_layout.addWidget(self.client_combo)
        client_layout.addWidget(add_client_btn)
        self.layout.addLayout(client_layout)

        # --- Таблица позиций ---
        self.items_table = QTableWidget(0, 4)
        self.items_table.setHorizontalHeaderLabels(["Ткань", "Количество (м)", "Цена за м", "Сумма"])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.items_table)

        add_item_btn = QPushButton("Добавить позицию")
        add_item_btn.clicked.connect(self.add_item_row)
        self.layout.addWidget(add_item_btn)

        # --- Итог, оплата, дата ---
        bottom_layout = QHBoxLayout()
        self.total_label = QLabel("Итого: 0 ₽")
        bottom_layout.addWidget(self.total_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(QLabel("Способ оплаты:"))
        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["Наличные", "Карта", "Перевод"])
        bottom_layout.addWidget(self.payment_combo)
        bottom_layout.addWidget(QLabel("Дата:"))
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        bottom_layout.addWidget(self.date_edit)
        self.layout.addLayout(bottom_layout)

        # --- Кнопки ---
        btns = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")
        save_btn.clicked.connect(self.save)
        cancel_btn.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        self.layout.addLayout(btns)

        self.items_table.cellChanged.connect(self.recalc_total)
        self.fabric_data = self.load_fabrics()

    def reload_clients(self):
        self.client_combo.clear()
        from database_utils import get_combo_values
        for val, text in get_combo_values('customers', 'full_name'):
            self.client_combo.addItem(str(text), val)

    def load_fabrics(self):
        from database_utils import get_combo_values
        # Получаем id, name, stock, price
        import psycopg2
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT fabric_id, name, stock_meters, price_per_meter FROM fabrics ORDER BY name")
            data = cursor.fetchall()
            cursor.close()
            conn.close()
            return {row[0]: {'name': row[1], 'stock': row[2], 'price': row[3]} for row in data}
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки тканей: {e}")
            return {}

    def add_client(self):
        dialog = AddClientDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.reload_clients()
            self.client_combo.setCurrentIndex(self.client_combo.count()-1)

    def add_item_row(self):
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        # Ткань (ComboBox)
        fabric_combo = QComboBox()
        for fid, f in self.fabric_data.items():
            fabric_combo.addItem(f["name"], fid)
        fabric_combo.currentIndexChanged.connect(lambda _, r=row: self.update_price_for_row(r))
        self.items_table.setCellWidget(row, 0, fabric_combo)
        # Количество
        qty_edit = QLineEdit("1")
        qty_edit.setValidator(QDoubleValidator(0.01, 9999, 2))
        qty_edit.textChanged.connect(lambda _: self.recalc_total())
        self.items_table.setCellWidget(row, 1, qty_edit)
        # Цена за м (авто, не редактируется)
        price_item = QTableWidgetItem()
        price_item.setFlags(price_item.flags() ^ Qt.ItemIsEditable)
        self.items_table.setItem(row, 2, price_item)
        # Сумма (авто, не редактируется)
        sum_item = QTableWidgetItem()
        sum_item.setFlags(sum_item.flags() ^ Qt.ItemIsEditable)
        self.items_table.setItem(row, 3, sum_item)
        self.update_price_for_row(row)
        self.recalc_total()

    def update_price_for_row(self, row):
        fabric_combo = self.items_table.cellWidget(row, 0)
        if not fabric_combo: return
        fabric_id = fabric_combo.currentData()
        price = self.fabric_data.get(fabric_id, {}).get('price', 0)
        price_item = self.items_table.item(row, 2)
        if price_item:
            price_item.setText(str(price))
        self.recalc_total()

    def recalc_total(self):
        total = 0
        for row in range(self.items_table.rowCount()):
            qty_edit = self.items_table.cellWidget(row, 1)
            price_item = self.items_table.item(row, 2)
            sum_item = self.items_table.item(row, 3)
            try:
                qty = float(qty_edit.text()) if qty_edit else 0
                price = float(price_item.text()) if price_item else 0
                s = qty * price
                if sum_item:
                    sum_item.setText(f"{s:.2f}")
                total += s
            except Exception:
                if sum_item:
                    sum_item.setText("")
        self.total_label.setText(f"Итого: {total:,.2f} ₽")

    def save(self):
        from database_utils import get_db_connection
        import psycopg2
        client_id = self.client_combo.currentData()
        sale_date = self.date_edit.date().toString("yyyy-MM-dd")
        payment = self.payment_combo.currentText()
        positions = []
        for row in range(self.items_table.rowCount()):
            fabric_combo = self.items_table.cellWidget(row, 0)
            qty_edit = self.items_table.cellWidget(row, 1)
            price_item = self.items_table.item(row, 2)
            sum_item = self.items_table.item(row, 3)
            fabric_id = fabric_combo.currentData() if fabric_combo else None
            try:
                qty = float(qty_edit.text()) if qty_edit else 0
                price = float(price_item.text()) if price_item else 0
                s = float(sum_item.text()) if sum_item else 0
            except Exception:
                QMessageBox.warning(self, "Ошибка", "Некорректные данные в позициях!")
                return
            if not fabric_id or qty <= 0:
                QMessageBox.warning(self, "Ошибка", "Заполните все позиции корректно!")
                return
            # Проверка остатка
            stock = self.fabric_data.get(fabric_id, {}).get('stock', 0)
            if qty > stock:
                QMessageBox.warning(self, "Ошибка", f"Недостаточно ткани '{self.fabric_data[fabric_id]['name']}' (остаток: {stock})!")
                return
            positions.append((fabric_id, qty, price, s))
        if not positions:
            QMessageBox.warning(self, "Ошибка", "Добавьте хотя бы одну позицию!")
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Добавляем продажу
            cursor.execute("INSERT INTO sales (sale_date, employee_id, customer_id, total_amount, payment_method, notes) VALUES (%s, %s, %s, %s, %s, %s) RETURNING sale_id", (
                sale_date, 1, client_id, sum([p[3] for p in positions]), payment, ""
            ))
            sale_id = cursor.fetchone()[0]
            # Добавляем позиции
            for fabric_id, qty, price, s in positions:
                cursor.execute("INSERT INTO sale_items (sale_id, fabric_id, quantity_meters, price_per_meter, total_amount) VALUES (%s, %s, %s, %s, %s)",
                    (sale_id, fabric_id, qty, price, s))
                # Обновляем остаток ткани
                cursor.execute("UPDATE fabrics SET stock_meters = stock_meters - %s WHERE fabric_id = %s", (qty, fabric_id))
            conn.commit()
            cursor.close()
            conn.close()
            QMessageBox.information(self, "Успех", "Продажа успешно добавлена!")
            self.accept()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении продажи: {e}")

class AddClientDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить клиента")
        layout = QFormLayout(self)
        self.name_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.address_edit = QLineEdit()
        layout.addRow("ФИО:", self.name_edit)
        layout.addRow("Телефон:", self.phone_edit)
        layout.addRow("E-mail:", self.email_edit)
        layout.addRow("Адрес:", self.address_edit)
        btns = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")
        save_btn.clicked.connect(self.save)
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addRow(btns)
    def save(self):
        from database_utils import get_db_connection
        import psycopg2
        name = self.name_edit.text().strip()
        phone = self.phone_edit.text().strip()
        email = self.email_edit.text().strip()
        address = self.address_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите ФИО клиента!")
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO customers (full_name, phone, email, address) VALUES (%s, %s, %s, %s)",
                (name, phone, email, address))
            conn.commit()
            cursor.close()
            conn.close()
            self.accept()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении клиента: {e}")

class AddDeliveryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить поставку")
        self.setMinimumWidth(700)
        layout = QVBoxLayout(self)
        # --- Поставщик, сотрудник, дата ---
        top = QHBoxLayout()
        self.supplier_combo = QComboBox()
        for val, text in get_combo_values('suppliers', 'company_name'):
            self.supplier_combo.addItem(str(text), val)
        self.employee_combo = QComboBox()
        for val, text in get_combo_values('employees', 'full_name'):
            self.employee_combo.addItem(str(text), val)
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        top.addWidget(QLabel("Поставщик:"))
        top.addWidget(self.supplier_combo)
        top.addWidget(QLabel("Сотрудник:"))
        top.addWidget(self.employee_combo)
        top.addWidget(QLabel("Дата:"))
        top.addWidget(self.date_edit)
        layout.addLayout(top)
        # --- Таблица позиций ---
        self.items_table = QTableWidget(0, 4)
        self.items_table.setHorizontalHeaderLabels(["Ткань", "Количество (м)", "Цена за м", "Добавить новую ткань"])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.items_table)
        add_item_btn = QPushButton("Добавить позицию")
        add_item_btn.clicked.connect(self.add_item_row)
        layout.addWidget(add_item_btn)
        # --- Кнопки ---
        btns = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")
        save_btn.clicked.connect(self.save)
        cancel_btn.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)
        self.fabric_data = self.load_fabrics_full()

    def load_fabrics_full(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT fabric_id, name, price_per_meter FROM fabrics ORDER BY name")
            data = cursor.fetchall()
            cursor.close()
            conn.close()
            return {row[0]: {'name': row[1], 'price': row[2]} for row in data}
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки тканей: {e}")
            return {}

    def add_item_row(self):
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        # Ткань (ComboBox)
        fabric_combo = QComboBox()
        for fid, f in self.fabric_data.items():
            fabric_combo.addItem(f["name"], fid)
        fabric_combo.currentIndexChanged.connect(lambda _, r=row: self.update_price_for_row(r))
        self.items_table.setCellWidget(row, 0, fabric_combo)
        # Количество
        qty_edit = QLineEdit("1")
        qty_edit.setValidator(QDoubleValidator(0.01, 9999, 2))
        self.items_table.setCellWidget(row, 1, qty_edit)
        # Цена за м (авто для существующих, редактируемо только для новой)
        price_edit = QLineEdit()
        price_edit.setValidator(QDoubleValidator(0.01, 999999, 2))
        price_edit.setReadOnly(True)
        self.items_table.setCellWidget(row, 2, price_edit)
        # Кнопка добавить новую ткань
        add_fabric_btn = QPushButton("...")
        add_fabric_btn.setToolTip("Добавить новую ткань")
        add_fabric_btn.clicked.connect(lambda _, r=row: self.add_new_fabric(r))
        self.items_table.setCellWidget(row, 3, add_fabric_btn)
        self.update_price_for_row(row)

    def update_price_for_row(self, row):
        fabric_combo = self.items_table.cellWidget(row, 0)
        price_edit = self.items_table.cellWidget(row, 2)
        if not fabric_combo or not price_edit:
            return
        fabric_id = fabric_combo.currentData()
        if fabric_id not in self.fabric_data:
            price_edit.setReadOnly(False)
            price_edit.setText("")
        else:
            price = self.fabric_data.get(fabric_id, {}).get('price', "")
            price_edit.setReadOnly(True)
            price_edit.setText(str(price))

    def check_new_fabric(self, row):
        fabric_combo = self.items_table.cellWidget(row, 0)
        if fabric_combo.currentData() == -1:
            self.add_new_fabric(row)

    def add_new_fabric(self, row):
        dlg = AddFabricDialog(self)
        if dlg.exec() == QDialog.Accepted:
            # Обновить список тканей во всех строках
            self.fabric_data = self.load_fabrics_full()
            for r in range(self.items_table.rowCount()):
                combo = self.items_table.cellWidget(r, 0)
                current = combo.currentData()
                combo.clear()
                for fid, f in self.fabric_data.items():
                    combo.addItem(f["name"], fid)
                if current in self.fabric_data:
                    combo.setCurrentIndex(list(self.fabric_data.keys()).index(current))
                self.update_price_for_row(r)

    def save(self):
        supplier_id = self.supplier_combo.currentData()
        employee_id = self.employee_combo.currentData()
        date = self.date_edit.date().toString("yyyy-MM-dd")
        positions = []
        for row in range(self.items_table.rowCount()):
            fabric_combo = self.items_table.cellWidget(row, 0)
            qty_edit = self.items_table.cellWidget(row, 1)
            price_edit = self.items_table.cellWidget(row, 2)
            fabric_id = fabric_combo.currentData() if fabric_combo else None
            try:
                qty = float(qty_edit.text()) if qty_edit else 0
                price = float(price_edit.text()) if price_edit else 0
            except Exception:
                QMessageBox.warning(self, "Ошибка", "Некорректные данные в позициях!")
                return
            if not fabric_id or qty <= 0 or price <= 0:
                QMessageBox.warning(self, "Ошибка", "Заполните все позиции корректно!")
                return
            positions.append((fabric_id, qty, price))
        if not positions:
            QMessageBox.warning(self, "Ошибка", "Добавьте хотя бы одну позицию!")
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Добавляем поставку
            cursor.execute("INSERT INTO deliveries (delivery_date, supplier_id, employee_id) VALUES (%s, %s, %s) RETURNING delivery_id", (
                date, supplier_id, employee_id
            ))
            delivery_id = cursor.fetchone()[0]
            # Обновляем остатки и добавляем новые ткани
            for fabric_id, qty, price in positions:
                if fabric_id == -1:
                    QMessageBox.warning(self, "Ошибка", "Добавьте новую ткань через кнопку '...'")
                    return
                cursor.execute("UPDATE fabrics SET stock_meters = stock_meters + %s, price_per_meter = %s WHERE fabric_id = %s", (qty, price, fabric_id))
            conn.commit()
            cursor.close()
            conn.close()
            QMessageBox.information(self, "Успех", "Поставка успешно добавлена!")
            self.accept()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении поставки: {e}")

class AddFabricDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить ткань")
        layout = QFormLayout(self)
        self.name_edit = QLineEdit()
        self.category_combo = QComboBox()
        for val, text in get_combo_values('fabric_categories', 'name'):
            self.category_combo.addItem(str(text), val)
        self.color_edit = QLineEdit()
        self.density_edit = QLineEdit()
        self.width_edit = QLineEdit()
        self.price_edit = QLineEdit()
        self.supplier_combo = QComboBox()
        for val, text in get_combo_values('suppliers', 'company_name'):
            self.supplier_combo.addItem(str(text), val)
        self.arrival_date = QDateEdit(QDate.currentDate())
        self.arrival_date.setCalendarPopup(True)
        layout.addRow("Название:", self.name_edit)
        layout.addRow("Категория:", self.category_combo)
        layout.addRow("Цвет:", self.color_edit)
        layout.addRow("Плотность:", self.density_edit)
        layout.addRow("Ширина (см):", self.width_edit)
        layout.addRow("Цена за м:", self.price_edit)
        layout.addRow("Поставщик:", self.supplier_combo)
        layout.addRow("Дата поступления:", self.arrival_date)
        btns = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")
        save_btn.clicked.connect(self.save)
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addRow(btns)
    def save(self):
        name = self.name_edit.text().strip()
        category_id = self.category_combo.currentData()
        color = self.color_edit.text().strip()
        density = self.density_edit.text().strip()
        width = self.width_edit.text().strip()
        price = self.price_edit.text().strip()
        supplier_id = self.supplier_combo.currentData()
        arrival_date = self.arrival_date.date().toString("yyyy-MM-dd")
        if not name or not price or not width:
            QMessageBox.warning(self, "Ошибка", "Заполните все обязательные поля!")
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO fabrics (name, category_id, color, density, width_cm, price_per_meter, stock_meters, supplier_id, arrival_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (name, category_id, color, density, width, price, 0, supplier_id, arrival_date))
            conn.commit()
            cursor.close()
            conn.close()
            self.accept()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении ткани: {e}") 