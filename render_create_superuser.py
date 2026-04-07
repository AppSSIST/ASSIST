import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ASSIST.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
u = os.getenv("DJANGO_SUPERUSER_USERNAME")
p = os.getenv("DJANGO_SUPERUSER_PASSWORD")
e = os.getenv("DJANGO_SUPERUSER_EMAIL", "")

print("BUILD-SUPERUSER", bool(u), bool(p), bool(e))

if u and p:
    obj = User.objects.filter(username=u).first()
    print("USER-FOUND", bool(obj))
    if obj:
        obj.set_password(p)
        obj.email = e
        obj.is_staff = True
        obj.is_superuser = True
        obj.save()
        print("SUPERUSER-UPDATED")
    else:
        User.objects.create_superuser(u, e, p)
        print("SUPERUSER-CREATED")
else:
    print("SKIPPED-SUPERUSER-CREATION")
