"""tata_evaluation URL Configuration"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('management/', include('Django_TTev.admin_urls')),  # 管理后台
    path('', include('Django_TTev.urls')),  # 使用你的应用的URLs
]
