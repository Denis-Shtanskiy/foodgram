echo "from django.contrib.auth import get_user_model;
import os;
from dotenv import load_dotenv;
load_dotenv();
User = get_user_model();
admin = os.getenv('SUPERUSER_USERNAME', 'admin123');
password = os.getenv('SUPERUSER_PASSWORD', 'admin12345');
email = os.getenv('SUPERUSER_EMAIL', 'admin@examle.com');
User.objects.filter(username='username').exists() or User.objects.create_superuser(username=admin, email=email, password=password)" | python manage.py shell
