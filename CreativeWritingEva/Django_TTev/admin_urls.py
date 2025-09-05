from django.urls import path
from . import admin_views

app_name = 'admin_views'

urlpatterns = [
    # 管理后台仪表板
    path('dashboard/', admin_views.admin_dashboard, name='dashboard'),
    
    # 评估结果管理
    path('evaluations/', admin_views.evaluation_list, name='evaluation_list'),
    path('evaluations/<int:evaluation_id>/', admin_views.evaluation_detail, name='evaluation_detail'),
    path('evaluations/<int:evaluation_id>/delete/', admin_views.delete_evaluation, name='delete_evaluation'),
    path('evaluations/batch-delete/', admin_views.batch_delete, name='batch_delete'),
    
    # 导出功能
    path('export/', admin_views.export_evaluations, name='export_evaluations'),
    path('evaluations/<int:evaluation_id>/export/', admin_views.export_single_evaluation, name='export_single_evaluation'),
]
