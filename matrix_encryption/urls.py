from django.contrib import admin
from django.urls import path
from encrypter import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.matrix_view, name='matrix_encryption'),
]
