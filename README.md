# Fabric-Shop

## Описание проекта

Система управления магазином тканей с базой данных PostgreSQL. Приложение предоставляет интерфейс для управления товарами, заказами и пользователями.

## Функциональность

- **Аутентификация пользователей** - система входа с ролями (менеджер, продавец)
- **Управление товарами** - добавление, редактирование, удаление товаров
- **Управление заказами** - создание и обработка заказов
- **Отчетность** - генерация отчетов по продажам и товарам
- **База данных** - интеграция с PostgreSQL

## Структура проекта

- `main.py` - главный файл приложения
- `auth.py` - модуль аутентификации
- `database_utils.py` - утилиты для работы с базой данных
- `manager.py` - интерфейс менеджера
- `seller.py` - интерфейс продавца
- `base_role_window.py` - базовый класс для окон ролей

## Требования

- Python 3.8+
- PostgreSQL
- PySide6 (Qt для GUI)
- psycopg2 (драйвер PostgreSQL)

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Настройте базу данных PostgreSQL

3. Запустите приложение:
```bash
python main.py
```

## Сборка исполняемого файла

Для создания исполняемого файла используйте PyInstaller:
```bash
pyinstaller main.spec
```

## Автор

Горшков Владимир Максимович

<img width="579" height="399" alt="image" src="https://github.com/user-attachments/assets/872e05c1-0465-43ec-b3cc-225a69cdda56" />
<img width="664" height="459" alt="image" src="https://github.com/user-attachments/assets/77c37201-da6d-40bb-8835-bd0bec6a1497" />
<img width="550" height="383" alt="image" src="https://github.com/user-attachments/assets/47a99ba3-066b-412d-a067-c3a8b83376f7" />
<img width="661" height="457" alt="image" src="https://github.com/user-attachments/assets/4d75d577-6099-4a0a-a711-0c5f3a65fe00" />
<img width="676" height="467" alt="image" src="https://github.com/user-attachments/assets/a573a160-8841-4529-9b04-04bc759bdee2" />
<img width="820" height="564" alt="image" src="https://github.com/user-attachments/assets/dd9853ca-71da-4e61-b809-859407d01f30" />
<img width="723" height="379" alt="image" src="https://github.com/user-attachments/assets/09502f47-64d3-4793-b76f-edb10d5bc694" />
<img width="742" height="357" alt="image" src="https://github.com/user-attachments/assets/c01bfd76-77ec-4dce-a0f1-41093745348a" />








