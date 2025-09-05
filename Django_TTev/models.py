from django.db import models
from django.utils import timezone
import json

# 评估指标元数据 - 定义在类外部以便动态添加字段
METRIC_FIELDS = {
    'character_depth_arc': 'Character Depth & Moral Dilemma Arc',
    'memory_anchors': 'Memory Anchors & Sensory Specificity',
    'intergenerational_span': 'Intergenerational Span & Long-term Causality',
    'ethical_complexity': 'Institutional & Tech Ethical Complexity',
    'investigative_drive': 'Investigative Drive & Clue Architecture',
    'multi_layered_conflict': 'Multi-layered Conflict',
    'value_turns_cohesion': 'Value Turns & Causal Cohesion',
    'hierarchy_beats_design': 'Hierarchy of Beats & Midpoint/Climax Design',
    'emotional_punch_aftershock': 'Emotional Punch & Aftershock',
    'dual_resonance_ending': 'Dual Resonance of Ending: Personal & Public',
}


class EvaluationResult(models.Model):
    """评估结果模型"""

    GROUP_CHOICES = [
        ('writing_a1', '写作 A-1'),
        ('writing_a2', '写作 A-2'),
        ('writing_b1', '写作 B-1'),
        ('writing_b2', '写作 B-2'),
    ]

    # 用户信息
    user_name = models.CharField(max_length=100, verbose_name='用户姓名')
    user_group = models.CharField(max_length=20, choices=GROUP_CHOICES, verbose_name='用户组别')

    # 提交的文本内容
    submitted_text = models.TextField(verbose_name='提交的文本内容')

    # 总分
    total_score = models.IntegerField(default=0, verbose_name='总分')

    # AI完整回复
    ai_response = models.TextField(blank=True, verbose_name='AI完整回复')

    # 创建时间
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')

    # Overall Summary
    overall_summary = models.TextField(blank=True, verbose_name='整体总结')

    class Meta:
        verbose_name = '评估结果'
        verbose_name_plural = '评估结果'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user_name} - {self.get_user_group_display()} - {self.total_score}分"

    def get_scores_dict(self):
        """获取分数字典"""
        scores = {}
        for field, name in METRIC_FIELDS.items():
            scores[name] = getattr(self, f'{field}_score')
        return scores

    def get_justifications_dict(self):
        """获取解释字典"""
        justifications = {}
        for field, name in METRIC_FIELDS.items():
            justifications[name] = getattr(self, f'{field}_justification')
        return justifications

    def calculate_total_score(self):
        """计算总分"""
        total = 0
        for field in METRIC_FIELDS.keys():
            total += getattr(self, f'{field}_score')
        self.total_score = total
        return self.total_score

    def get_all_metrics(self):
        """获取所有指标的名称、分数和解释"""
        metrics = []
        for field, name in METRIC_FIELDS.items():
            metrics.append({
                'name': name,
                'score': getattr(self, f'{field}_score'),
                'justification': getattr(self, f'{field}_justification')
            })
        return metrics

    def to_json(self):
        """转换为JSON格式"""
        return {
            'user_name': self.user_name,
            'user_group': self.user_group,
            'user_group_display': self.get_user_group_display(),
            'submitted_text': self.submitted_text,
            'scores': self.get_scores_dict(),
            'justifications': self.get_justifications_dict(),
            'metrics': self.get_all_metrics(),
            'overall_summary': self.overall_summary,
            'total_score': self.total_score,
            'ai_response': self.ai_response,
            'created_at': self.created_at.isoformat(),
        }


# Dynamically add metric score and justification fields
for field_name, verbose_name in METRIC_FIELDS.items():
    EvaluationResult.add_to_class(f'{field_name}_score', models.IntegerField(default=0, verbose_name=f'{verbose_name} Score'))
    EvaluationResult.add_to_class(f'{field_name}_justification', models.TextField(verbose_name=f'{verbose_name} Justification', blank=True))
