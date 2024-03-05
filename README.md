# __Foodgram - продуктовый помощник__

#### сайт доступен по адресу: 
```bash
foodgramhelper.sytes.net
```
#### данные для проверки админ-панели:
```bash
Уникальный юзернейм: AdminFoodgram
пароль: foodgram12345
```

![Github Actions main workflow](https://github.com/Denis-Shtanskiy/foodgram-project-react/actions/workflows/main.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

## Использованные при реализации проекта технологии
 - Docker
 - Django
 - djangorestframework
 - Python
 - Nginx
 - PostgreSQL

## __Как развернуть проект__

### Для установки проекта потребуется выполнить следующие действия:

_Локальная настройка и запуск проекта_

Клонировать репозиторий к себе на компьютер и перейти в директорию с проектом:
```bash
git clone https://github.com/denis-shtanskiy/foodgram-project-react.git
cd foodgram-project-react
```
Для проекта создать и активировать виртуальное окружение, установить зависимости:
__для windows:__
```bash
python -m venv venv
source venv/Scripts/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
cd foodgram
```
__для linux:__
```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
cd foodgram
```
### .env
Для корректной работы backend-части проекта, создайте в корне файл `.env` и заполните его переменными по примеру из файла `.env.example` или по примеру ниже:
```bash
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
DB_NAME=foodgram
DB_HOST=db
DB_PORT=5432
SECRET_KEY=safq12432tdzxqxght_!erks       # стандартный ключ, который создается при старте проекта
DEBUG=True
ALLOWED_HOSTS=['IP_адрес_сервера', '127.0.0.1', 'localhost', 'домен_сервера']
SUPERUSER_USERNAME=AdminFoodgram       # переменные для автоматического создания суперюзера, 
SUPERUSER_PASSWORD=foodgram12345       # если не указать, применятся стандартные из скрипта
SUPERUSER_EMAIL=admin@nothing.not      # вид стандартных переменных ('admin', 'admin@example.com, 'admin12345')
```

Установите [docker compose](https://www.docker.com/) на свой компьютер.
Для запуска проекта на локальной машине достаточно:
* Запустить проект, ключ `-d` запускает проект в фоновом режиме
* выполнить миграции
* собрать статику и скопировать её
* запустить скрипт для создания суперюзера
* запустить менеджмент команду для загрузки базы ингредиентов
```bash
docker compose -f docker-compose.prodauction.yml up --build -d
docker compose -f docker-compose.prodauction.yml exec backend python manage.py migrate
docker compose -f docker-compose.prodauction.yml exec backend python manage.py collectstatic  && \
docker compose -f docker-compose.prodauction.yml exec backend cp -r /app/static_backend/. /backend_static/static/
docker compose -f docker-compose.production.yml exec backend bash create_superuser_script.sh
docker compose -f docker-compose.production.yml exec backend python manage.py import_ingredients ./data/ingredients.csv
```

## Если вы используете удаленный сервер
__Для работы на удаленном сервере потребуется:__
1. Установить Nginx
2. Отредактировать конфигурационный файл:
   ```bash
   server {
    server_name IP_адрес_сервера домен_сервера;

    location / {
        proxy_pass http://127.0.0.1:9000;
    }
   }
   ```
3. Настроить и установить Docker
4. Перенести файл `docker-compose.production.yml с локальной машины на удаленную
5. Запустить контейнеры
6. Выполнить миграции собрать статику и скопировать её, так же как описано для локальной машины
   _Необходимые команды_
```bash
sudo apt install nginx -y                                # устанавливаем Nginx
sudo systemctl start nginx                               # запускаем Nginx
sudo nano /etc/nginx/sites-enabled/default               # заходим редактировать файл конфигурации
sudo nginx -t                                            # проверяем корректность настроек
sudo service nginx reload                                # перезапускаем Nginx
sudo service nginx status                                # проверяем что Nginx запущен и работает без ошибок
sudo apt install snapd && \                              # Устанавливаем certbot для получения SSL-сертификата
sudo snap install core && \                              # Устанавливаем certbot для получения SSL-сертификата
sudo snap refresh core && \                              # Устанавливаем certbot для получения SSL-сертификата
sudo snap install --classic certbot && \                 # Устанавливаем certbot для получения SSL-сертификата
sudo ln -s /snap/bin/certbot /usr/bin/certbot            # Устанавливаем certbot для получения SSL-сертификата
sudo certbot --nginx                                     # Запускаем certbot получаем SSL-сертификат
sudo service nginx reload                                # Сертификат автоматически сохранится в конфигурации Nginx
sudo apt update && sudo apt install curl                 # Устанавливаем Docker
curl -fSl https://get.docker.com -o get-docker.sh        # Устанавливаем Docker
sudo sh ./get-docker.sh                                  # Настраиваем Docker
sudo apt-get install docker-compose-plugin               # Настраиваем Docker
sudo nano docker-compose.production.yml                  # В этот файл перенесем содержимое из файла на локальной машине
sudo docker compose -f docker-compose.production.yml up -d # Запускаем контейнеры на удаленном сервере в фоновом режиме
```
## Автоматизация запуска при изменении в коде

__Workflow__
Для постоянного использования CI/CD интеграции и деплоя в репозитории проекта на GitHub в разделе Actions
перейти `Settings/Secret and variables/Actions` нужно прописать переменные окружения для доступа к сервисам - _Secrets_:

```
DOCKER_USERNAME                # логин в DockerHub
DOCKER_PASSWORD                # пароль пользователя в DockerHub
DOCKER_USER                    # имя пользователя для репозиториев
HOST                           # ip_address сервера
USER                           # имя пользователя
SSH_KEY                        # приватный ssh-ключ (cat ~/.ssh/id_rsa) по выбору: удаленный сервер или локальная машина
PASSPHRASE                     # кодовая фраза (пароль) для ssh-ключа по выбору: удаленный сервер или локальная машина

TELEGRAM_TO                    # id телеграм-аккаунта (можно узнать у @userinfobot, команда /start)
TELEGRAM_TOKEN                 # токен бота (получить токен можно у @BotFather, /token, имя бота)
```
По команде `git push` в репозитории на github отрабатывают сценарии:
* __tests__ - для всех веток проверка кода по стандартам PEP8.
* __build_and_push_to_docker_hub__ - сборка и отправка образов в удаленный репозиторий на DockerHub
* __deploy__ - автоматический деплой проекта
* __send_message__ - отправка соообщения разработчику в Telegram


#### Автор
Denis Shtanskiy
Telegram: @shtanskiy
