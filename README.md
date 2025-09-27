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

## Модель предметной области в нотации DFD.
•	Контекстный уровень
<img width="702" height="520" alt="image" src="https://github.com/user-attachments/assets/ca6a04b4-1528-4224-8eb7-11830d62be30" />
•	Декомпозиция системы
<img width="970" height="478" alt="image" src="https://github.com/user-attachments/assets/0c76ac06-daba-4a63-b3ef-fc883f04c5e1" />
•	Декомпозиции формирования отчета
<img width="557" height="527" alt="image" src="https://github.com/user-attachments/assets/89e1ec43-caef-4678-8f87-b1f8edf3dc4b" />

## Модель предметной области в нотации IDEF0.

<img width="950" height="605" alt="image" src="https://github.com/user-attachments/assets/b19aa674-93d7-4330-9d13-69a3025e8786" />
<img width="957" height="522" alt="image" src="https://github.com/user-attachments/assets/1e07fe9d-7f8c-4328-961c-8c43c77bf0bf" />
<img width="944" height="507" alt="image" src="https://github.com/user-attachments/assets/9c5586d0-ee78-4b18-9849-aaf08a52bfbe" />
<img width="939" height="508" alt="image" src="https://github.com/user-attachments/assets/c1154207-3071-4f27-b172-81e443d5699e" />
<img width="919" height="498" alt="image" src="https://github.com/user-attachments/assets/c5b7d2d5-379d-4b34-8a75-d6619a9140b7" />

## Инфологическая модель предметной области
<img width="1004" height="1072" alt="image" src="https://github.com/user-attachments/assets/aaafc806-5289-456e-979f-b357f9fc107d" />

## Датологическая модель предметной области
<img width="1002" height="706" alt="image" src="https://github.com/user-attachments/assets/087015bd-f38b-4845-b352-b3062a7e9ca8" />





