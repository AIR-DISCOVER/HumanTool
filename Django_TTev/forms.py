from django import forms
from .models import EvaluationResult


class EvaluationForm(forms.ModelForm):
    """评估表单"""
    
    class Meta:
        model = EvaluationResult
        fields = ['user_name', 'user_group', 'submitted_text']
        widgets = {
            'user_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入您的姓名',
                'required': True,
            }),
            'user_group': forms.Select(attrs={
                'class': 'form-control',
                'required': True,
            }),
            'submitted_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 15,
                'placeholder': '请将您和TATA协作生成的文本内容粘贴到这里...',
                'required': True,
            }),
        }
        labels = {
            'user_name': '姓名',
            'user_group': '组别',
            'submitted_text': '文本内容',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置组别选择的空选项
        self.fields['user_group'].empty_label = "请选择组别"
