from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from hello import views

urlpatterns = [
    # Custom admin login - MUST be first!
    path('admin/login/', views.admin_login, name='admin_login'),

    # Root URL should go to login so users land on the login page
    path('', views.admin_login, name='home'),
    
    # Django default admin (different URL)
    path('django-admin/', admin.site.urls),
    
    # Include hello app URLs
    path('', include('hello.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)