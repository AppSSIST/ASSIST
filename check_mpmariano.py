import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ASSIST.settings')
django.setup()

from hello.models import Faculty
from django.contrib.auth.models import User

email = 'mpmariano@tip.edu.ph'
facs = Faculty.objects.filter(email__iexact=email)
users = User.objects.filter(email__iexact=email)

print('Faculty count:', facs.count())
print('User count:', users.count())

for f in facs:
    print(f'Faculty ID: {f.id}, Email: {f.email}, First: {f.first_name}, Last: {f.last_name}')

for u in users:
    print(f'User ID: {u.id}, Email: {u.email}, Username: {u.username}')

# Delete all
if facs.count() > 0 or users.count() > 0:
    print("Deleting...")
    facs.delete()
    users.delete()
    print("Done - all records deleted")
