import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ASSIST.settings')
django.setup()

import json
from hello.views import _get_faculty_response_data
from django.contrib.auth.models import User

u = User.objects.get(email='msnbaldonado@tip.edu.ph')

class FakeRequest:
    user = u
    def build_absolute_uri(self, path):
        return f'http://127.0.0.1:8000{path}'

data = _get_faculty_response_data(FakeRequest())
print(json.dumps(data, indent=2))
