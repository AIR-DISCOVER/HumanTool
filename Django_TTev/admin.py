from django.contrib import admin
from django.db.models import Avg
from django.contrib.auth.models import User
from django.utils import timezone
from .models import EvaluationResult, METRIC_FIELDS


@admin.register(EvaluationResult)
class EvaluationResultAdmin(admin.ModelAdmin):
    """评估结果管理界面"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 动态生成列表显示字段
        self.list_display = [
            'user_name',
            'user_group',
            'total_score',
        ]
        # 添加所有指标的分数字段
        for field_name in METRIC_FIELDS.keys():
            self.list_display.append(f'{field_name}_score')
        self.list_display.append('created_at')

        # 动态生成列表过滤器
        self.list_filter = [
            'user_group',
            'created_at',
        ]
        # 添加所有指标的分数字段到过滤器
        for field_name in METRIC_FIELDS.keys():
            self.list_filter.append(f'{field_name}_score')

        # 动态生成只读字段
        self.readonly_fields = [
            'created_at',
            'total_score',
            'ai_response',
            'overall_summary',
        ]
        # 添加所有指标的分数和解释字段
        for field_name in METRIC_FIELDS.keys():
            self.readonly_fields.extend([
                f'{field_name}_score',
                f'{field_name}_justification'
            ])

        # 动态生成字段分组
        self.fieldsets = [
            ('用户信息', {
                'fields': ('user_name', 'user_group', 'created_at')
            }),
            ('提交内容', {
                'fields': ('submitted_text',),
                'classes': ('collapse',)
            }),
            ('整体评估', {
                'fields': ('overall_summary', 'total_score')
            }),
        ]
        
        # 为每个指标添加字段分组
        for field_name, verbose_name in METRIC_FIELDS.items():
            self.fieldsets.append((
                verbose_name, {
                    'fields': (f'{field_name}_score', f'{field_name}_justification'),
                    'classes': ('collapse',)
                }
            ))
        
        # 添加AI完整回复字段分组
        self.fieldsets.append((
            'AI完整回复', {
                'fields': ('ai_response',),
                'classes': ('collapse',)
            }
        ))

    # 搜索字段
    search_fields = ['user_name', 'submitted_text']

    # 排序
    ordering = ['-created_at']

    # 每页显示数量
    list_per_page = 20

    # 禁止添加和删除
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    # 自定义显示方法
    def get_queryset(self, request):
        """只有超级用户可以查看所有结果"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.none()  # 非超级用户看不到任何结果

    def save_model(self, request, obj, form, change):
        """保存时自动计算总分"""
        obj.calculate_total_score()
        super().save_model(request, obj, form, change)


# 自定义Admin站点配置
admin.site.site_header = 'TATA评估系统管理后台'
admin.site.site_title = 'TATA评估系统'
admin.site.index_title = '欢迎来到TATA评估系统管理后台'

# 自定义Admin首页上下文
def admin_index_context(request):
    """为Admin首页添加统计数据"""
    total_evaluations = EvaluationResult.objects.count()
    today = timezone.now().date()
    today_evaluations = EvaluationResult.objects.filter(created_at__date=today).count()
    total_users = User.objects.count()

    # 平均分
    avg_score = EvaluationResult.objects.exclude(total_score=0).aggregate(
        avg=Avg('total_score')
    )['avg']

    return {
        'total_evaluations': total_evaluations,
        'today_evaluations': today_evaluations,
        'total_users': total_users,
        'avg_score': round(avg_score, 1) if avg_score else 0,
    }

# 重写Admin站点的index方法
original_index = admin.site.index

def custom_index(request, extra_context=None):
    extra_context = extra_context or {}
    extra_context.update(admin_index_context(request))
    return original_index(request, extra_context)

admin.site.index = custom_index
