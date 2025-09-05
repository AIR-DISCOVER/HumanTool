from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.utils import timezone
from .models import EvaluationResult
from .forms import EvaluationForm
from .evaluation import CreativityEvaluator
from api_client import api_call
import json
import os
import logging

logger = logging.getLogger(__name__)


def evaluation_form(request):
    """评估表单视图"""
    if request.method == 'POST':
        form = EvaluationForm(request.POST)
        if form.is_valid():
            try:
                # 保存基本信息
                evaluation_result = form.save(commit=False)

                # 创建评估器实例
                evaluator = CreativityEvaluator()

                # 生成系统提示词和用户提示词
                system_prompt = evaluator.generate_system_prompt()
                user_prompt = evaluator.generate_evaluation_prompt(evaluation_result.submitted_text)

                # 调用API获取评估结果
                logger.info(f"开始评估用户 {evaluation_result.user_name} 的文本")
                ai_response = api_call(user_prompt, system_prompt=system_prompt)
                logger.info(f"API响应: {ai_response}")

                # 使用新的保存方法，它会自动解析和保存所有字段
                evaluation_result = evaluator.save_evaluation_result(
                    user_name=evaluation_result.user_name,
                    user_group=evaluation_result.user_group,
                    submitted_text=evaluation_result.submitted_text,
                    ai_response=ai_response
                )

                # 保存到JSON文件
                save_result_to_json(evaluation_result)

                logger.info(f"评估完成，总分: {evaluation_result.total_score}")

                # 重定向到成功页面
                return redirect('evaluation:success', result_id=evaluation_result.id)

            except Exception as e:
                logger.error(f"评估过程中出错: {e}")
                messages.error(request, f'评估过程中出现错误: {str(e)}')
        else:
            messages.error(request, '请检查表单信息是否填写正确')
    else:
        form = EvaluationForm()

    return render(request, 'evaluation/form.html', {'form': form})


def evaluation_success(request, result_id):
    """评估成功页面"""
    result = get_object_or_404(EvaluationResult, id=result_id)
    return render(request, 'evaluation/success.html', {
        'result': result,
        'result_id': result_id
    })


from . import metrics

def evaluation_result(request, result_id):
    """评估结果详情页面"""
    result = get_object_or_404(EvaluationResult, id=result_id)
    
    # 使用模型方法获取所有指标数据
    all_metrics = result.get_all_metrics()

    context = {
        'result': result,
        'all_metrics': all_metrics,
    }
    return render(request, 'evaluation/result.html', context)


def save_result_to_json(evaluation_result):
    """将评估结果保存为JSON文件"""
    try:
        # 创建结果目录
        results_dir = settings.EVALUATION_RESULTS_DIR
        results_dir.mkdir(exist_ok=True)
        
        # 生成文件名
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"evaluation_{evaluation_result.user_name}_{timestamp}.json"
        filepath = results_dir / filename
        
        # 准备JSON数据
        json_data = evaluation_result.to_json()
        
        # 保存到文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"评估结果已保存到: {filepath}")
        
    except Exception as e:
        logger.error(f"保存JSON文件时出错: {e}")


def download_result(request, result_id):
    """下载评估结果"""
    result = get_object_or_404(EvaluationResult, id=result_id)
    
    # 准备JSON数据
    json_data = result.to_json()
    
    # 创建HTTP响应
    response = HttpResponse(
        json.dumps(json_data, ensure_ascii=False, indent=2),
        content_type='application/json; charset=utf-8'
    )
    
    # 设置下载文件名
    filename = f"evaluation_result_{result.user_name}_{result.created_at.strftime('%Y%m%d_%H%M%S')}.json"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response
