from django.shortcuts import render, get_object_or_404, redirect
from . import metrics
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from django.utils import timezone
from .models import EvaluationResult, METRIC_FIELDS
import json
import csv
from datetime import datetime, timedelta


@staff_member_required
def admin_dashboard(request):
    """管理后台仪表板"""
    
    # 统计数据
    total_evaluations = EvaluationResult.objects.count()
    today = timezone.now().date()
    today_evaluations = EvaluationResult.objects.filter(created_at__date=today).count()
    
    # 动态计算平均分
    avg_dict = {'avg_total': Avg('total_score')}
    for field_name in METRIC_FIELDS.keys():
        avg_dict[f'avg_{field_name}'] = Avg(f'{field_name}_score')
    
    avg_scores = EvaluationResult.objects.exclude(total_score=0).aggregate(**avg_dict)
    
    # 按组别统计
    group_stats = EvaluationResult.objects.values('user_group').annotate(
        count=Count('id'),
        avg_score=Avg('total_score')
    ).order_by('user_group')
    
    # 最近的评估记录
    recent_evaluations = EvaluationResult.objects.order_by('-created_at')[:10]
    
    # 动态生成指标名称
    all_metrics = []
    for field_name, verbose_name in METRIC_FIELDS.items():
        all_metrics.append({
            'field_name': field_name,
            'verbose_name': verbose_name,
            'avg_score': avg_scores.get(f'avg_{field_name}', 0)
        })
    
    context = {
        'total_evaluations': total_evaluations,
        'today_evaluations': today_evaluations,
        'avg_scores': avg_scores,
        'group_stats': group_stats,
        'recent_evaluations': recent_evaluations,
        'all_metrics': all_metrics,
    }
    
    return render(request, 'admin/dashboard.html', context)


@staff_member_required
def evaluation_list(request):
    """评估结果列表页面"""
    
    # 获取筛选参数
    search_query = request.GET.get('search', '')
    group_filter = request.GET.get('group', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    score_min = request.GET.get('score_min', '')
    score_max = request.GET.get('score_max', '')
    
    # 构建查询
    evaluations = EvaluationResult.objects.all()
    
    if search_query:
        evaluations = evaluations.filter(
            Q(user_name__icontains=search_query) |
            Q(submitted_text__icontains=search_query)
        )
    
    if group_filter:
        evaluations = evaluations.filter(user_group=group_filter)
    
    if date_from:
        evaluations = evaluations.filter(created_at__date__gte=date_from)
    
    if date_to:
        evaluations = evaluations.filter(created_at__date__lte=date_to)
    
    if score_min:
        evaluations = evaluations.filter(total_score__gte=int(score_min))
    
    if score_max:
        evaluations = evaluations.filter(total_score__lte=int(score_max))
    
    # 排序
    sort_by = request.GET.get('sort', '-created_at')
    evaluations = evaluations.order_by(sort_by)
    
    # 分页
    paginator = Paginator(evaluations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 获取组别选项
    group_choices = EvaluationResult.GROUP_CHOICES
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'group_filter': group_filter,
        'date_from': date_from,
        'date_to': date_to,
        'score_min': score_min,
        'score_max': score_max,
        'sort_by': sort_by,
        'group_choices': group_choices,
        'all_metrics': METRIC_FIELDS,
    }
    
    return render(request, 'admin/evaluation_list.html', context)


@staff_member_required
def evaluation_detail(request, evaluation_id):
    """评估结果详情页面"""
    evaluation = get_object_or_404(EvaluationResult, id=evaluation_id)
    
    # 使用模型的动态方法获取指标数据
    metrics_data = evaluation.get_all_metrics()

    context = {
        'evaluation': evaluation,
        'metrics_data': metrics_data,
    }
    
    return render(request, 'admin/evaluation_detail.html', context)


@staff_member_required
def delete_evaluation(request, evaluation_id):
    """删除评估结果"""
    if request.method == 'POST':
        evaluation = get_object_or_404(EvaluationResult, id=evaluation_id)
        user_name = evaluation.user_name
        evaluation.delete()
        messages.success(request, f'已成功删除用户 {user_name} 的评估结果')
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': '无效的请求方法'})


@staff_member_required
def batch_delete(request):
    """批量删除评估结果"""
    if request.method == 'POST':
        evaluation_ids = request.POST.getlist('evaluation_ids')
        if evaluation_ids:
            deleted_count = EvaluationResult.objects.filter(id__in=evaluation_ids).delete()[0]
            messages.success(request, f'已成功删除 {deleted_count} 条评估结果')
        else:
            messages.warning(request, '请选择要删除的评估结果')
    
    return redirect('admin_views:evaluation_list')


@staff_member_required
def export_evaluations(request):
    """导出评估结果"""
    
    # 获取筛选参数（与列表页面相同）
    search_query = request.GET.get('search', '')
    group_filter = request.GET.get('group', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    score_min = request.GET.get('score_min', '')
    score_max = request.GET.get('score_max', '')
    
    # 构建查询（与列表页面相同逻辑）
    evaluations = EvaluationResult.objects.all()
    
    if search_query:
        evaluations = evaluations.filter(
            Q(user_name__icontains=search_query) |
            Q(submitted_text__icontains=search_query)
        )
    
    if group_filter:
        evaluations = evaluations.filter(user_group=group_filter)
    
    if date_from:
        evaluations = evaluations.filter(created_at__date__gte=date_from)
    
    if date_to:
        evaluations = evaluations.filter(created_at__date__lte=date_to)
    
    if score_min:
        evaluations = evaluations.filter(total_score__gte=int(score_min))
    
    if score_max:
        evaluations = evaluations.filter(total_score__lte=int(score_max))
    
    evaluations = evaluations.order_by('-created_at')
    
    # 创建CSV响应
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="evaluation_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    # 添加BOM以支持Excel中文显示
    response.write('\ufeff')
    
    writer = csv.writer(response)
    
    # 动态生成表头
    headers = ['ID', '用户姓名', '用户组别', '总分']
    for _, verbose_name in METRIC_FIELDS.items():
        headers.append(verbose_name)
    headers.extend(['创建时间', '整体总结'])
    writer.writerow(headers)
    
    # 写入数据
    for evaluation in evaluations:
        row = [
            evaluation.id,
            evaluation.user_name,
            evaluation.get_user_group_display(),
            evaluation.total_score,
        ]
        # 动态添加指标分数
        for field_name in METRIC_FIELDS.keys():
            row.append(getattr(evaluation, f'{field_name}_score'))
        
        row.extend([
            evaluation.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            evaluation.overall_summary[:100] + '...' if len(evaluation.overall_summary) > 100 else evaluation.overall_summary
        ])
        writer.writerow(row)
    
    return response


@staff_member_required
def export_single_evaluation(request, evaluation_id):
    """导出单个评估结果的详细信息"""
    evaluation = get_object_or_404(EvaluationResult, id=evaluation_id)
    
    # 创建JSON响应
    response = HttpResponse(content_type='application/json; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="evaluation_{evaluation.user_name}_{evaluation.id}.json"'
    
    # 准备详细数据
    data = evaluation.to_json()
    
    # 写入JSON
    json.dump(data, response, ensure_ascii=False, indent=2)
    
    return response
