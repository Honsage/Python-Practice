# Yatube API

RESTful API для Yatube Blog. Реализует логику создания, изменения и удаления постов, комментариев и подписок на других авторов.

## Установка и запуск

1. Склонируйте репозиторий:
```bash
git clone https://github.com/Honsage/Yatube-API
```
2. Создайте и активируйте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Выполните миграции:
```bash
cd yatube_api
python manage.py migrate
```

5. Запустите сервер:
```bash
python manage.py runserver
```

## Документация API

После запуска сервера можно ознакомиться с документацией API по адресу [localhost:8000/redoc/]().