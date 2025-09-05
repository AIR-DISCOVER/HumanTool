from django.urls import path
from . import views

app_name = 'evaluation'

urlpatterns = [
    path('', views.evaluation_form, name='form'),
    path('result/<int:result_id>/', views.evaluation_result, name='result'),
    path('success/<int:result_id>/', views.evaluation_success, name='success'),
    path('download/<int:result_id>/', views.download_result, name='download'),
]
