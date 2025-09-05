from typing import Dict, Any, List
import sys
import os
from .prompts import PROMPT_0818, ALL_METRICS  # 确保正确导入提示词

# 添加父目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class CreativityEvaluator:
    """文本创意性评估器"""

    def __init__(self):
        # Dynamically create the criterion mapping from the prompt-defined ALL_METRICS
        # and map them to the first N metric fields defined in models.METRIC_FIELDS.
        # This ensures we only parse/store the metrics that are actually defined in metrics.py
        from .models import METRIC_FIELDS
        from .prompts import ALL_METRICS

        self.criterion_mapping = {}
        field_keys = list(METRIC_FIELDS.keys())
        # Map each defined metric (from ALL_METRICS) to the corresponding model field
        for i, metric in enumerate(ALL_METRICS):
            if i >= len(field_keys):
                # safety: don't create mappings beyond available model fields
                break
            target_field = field_keys[i]
            self.criterion_mapping[i + 1] = {
                'name': metric.get('name', '').strip(),
                'score_field': f'{target_field}_score',
                'justification_field': f'{target_field}_justification'
            }
    
    def get_criterion_names(self) -> List[str]:
        """获取所有指标名称"""
        return [mapping['name'] for mapping in self.criterion_mapping.values()]
    
    def generate_system_prompt(self) -> str:
        """生成系统提示"""
        return PROMPT_0818  # 直接返回从 prompts.py 引用的提示词
    
    def generate_evaluation_prompt(self, text: str) -> str:
        """生成评估提示"""
        #return f"Please evluate the following text:\n\n{text}"
        return f"Please evaluate the following Chinese text and provide your analysis in English:\n\n{text}"

    
    def parse_evaluation_result(self, response: str) -> Dict[str, Any]:
        """
        解析评估结果 - 专门处理CRITERION格式

        Args:
            response: 完整的评估结果文本

        Returns:
            包含整体总结和各指标分数与解释的字典
        """
        import re
        result = {}

        # 标准化换行符，处理不同的换行符格式
        response = response.replace('\r\n', '\n').replace('\r', '\n')

        # 处理JSON转义的换行符
        response = response.replace('\\n', '\n')

        # 解析结构化格式
        return self._parse_criterion_format(response)

    def _parse_criterion_format(self, response: str) -> Dict[str, Any]:
        """解析CRITERION格式的评估结果"""
        import re
        result = {}

        # 提取 Overall Summary
        if '===EVALUATION_START===' in response:
            # 从结构化格式中提取
            eval_pattern = re.compile(r'===EVALUATION_START===(.*?)===EVALUATION_END===', re.DOTALL)
            eval_match = eval_pattern.search(response)
            if eval_match:
                eval_content = eval_match.group(1).strip()
                summary_pattern = re.compile(r'OVERALL_SUMMARY:\s*(.*?)(?=\s*CRITERION_SCORES:|$)', re.DOTALL)
                summary_match = summary_pattern.search(eval_content)
                if summary_match:
                    result['overall_summary'] = summary_match.group(1).strip()
        else:
            # 从普通格式中提取
            summary_pattern = re.compile(r'Overall Summary:\s*(.*?)(?=\n\s*\n|Criterion|CRITERION|$)', re.DOTALL | re.IGNORECASE)
            summary_match = summary_pattern.search(response)
            if summary_match:
                result['overall_summary'] = summary_match.group(1).strip()

        if 'overall_summary' not in result:
            result['overall_summary'] = ''

        # 解析CRITERION行 - 使用你建议的方法
        # 匹配 CRITERION_数字|指标名称|分数|解释 格式
        criterion_pattern = re.compile(r'CRITERION_(\d+)\|([^|]+)\|(\d+)\|(.*?)(?=\nCRITERION_\d+|===EVALUATION_END===|$)', re.DOTALL)
        matches = criterion_pattern.findall(response)

        for match in matches:
            criterion_id = int(match[0])
            criterion_name = match[1].strip()
            score = int(match[2])
            justification = match[3].strip()

            # 根据CRITERION_ID映射到数据库字段
            if criterion_id in self.criterion_mapping:
                mapping = self.criterion_mapping[criterion_id]
                result[mapping['score_field']] = score
                result[mapping['justification_field']] = justification

                # 验证指标名称是否匹配（可选的验证步骤）
                expected_name = mapping['name']
                if criterion_name.lower() != expected_name.lower():
                    print(f"Warning: 指标名称不匹配 - 期望: '{expected_name}', 实际: '{criterion_name}'")
            else:
                print(f"Warning: 未知的CRITERION_ID: {criterion_id}")

        return result



    def save_evaluation_result(self, user_name: str, user_group: str, submitted_text: str, ai_response: str) -> 'EvaluationResult':
        """
        保存评估结果到数据库

        Args:
            user_name: 用户姓名
            user_group: 用户组别
            submitted_text: 提交的文本
            ai_response: AI的完整回复

        Returns:
            保存的EvaluationResult实例
        """
        from .models import EvaluationResult

        # 解析评估结果
        parsed_result = self.parse_evaluation_result(ai_response)

        # 创建评估结果实例
        evaluation_result = EvaluationResult(
            user_name=user_name,
            user_group=user_group,
            submitted_text=submitted_text,
            ai_response=ai_response,
            overall_summary=parsed_result.get('overall_summary', ''),
        )

        # Dynamically set score and justification fields
        for criterion_id, mapping in self.criterion_mapping.items():
            score = parsed_result.get(mapping['score_field'], 0)
            justification = parsed_result.get(mapping['justification_field'], '')
            setattr(evaluation_result, mapping['score_field'], score)
            setattr(evaluation_result, mapping['justification_field'], justification)

        # 计算总分
        evaluation_result.calculate_total_score()

        # 保存到数据库
        evaluation_result.save()

        return evaluation_result
