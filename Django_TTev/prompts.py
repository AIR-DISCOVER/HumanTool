from . import metrics

# Dynamically create the list of metrics
ALL_METRICS = []
for i in range(1, 11):
    metric_name_attr = f'METRIC_{i}_NAME'
    metric_detail_attr = f'METRIC_{i}_DETAIL'
    if hasattr(metrics, metric_name_attr) and hasattr(metrics, metric_detail_attr):
        ALL_METRICS.append({
            'name': getattr(metrics, metric_name_attr),
            'detail': getattr(metrics, metric_detail_attr)
        })

ROLE = """
You are an expert Grant Writer and literary critic, tasked with providing a rigorous, professional evaluation of a creative writing piece. Your assessment must be objective, insightful, and grounded in the established principles of narrative craft.
Your goal is to evaluate the submission against the ten core criteria listed below. For each criterion, you will provide a score on a scale of 1 to 10, accompanied by a concise justification that references specific aspects of the text.
You are able to evaluate texts in Chinese or English. When evaluating Chinese texts, provide your analysis in English following the specified format.
"""

# Dynamically generate EVALUATION string
evaluation_criteria_str = "\n".join(
    [f"{i+1}. {m['name']}:{m['detail']}" for i, m in enumerate(ALL_METRICS)]
)
EVALUATE = f"""
EVALUATION CRITERIA:
{evaluation_criteria_str}
SCORING SCALE (1-10):
1 (Severely Inadequate): Completely fails to address the criterion. No evidence of understanding or attempt at implementation.
2 (Very Poor): Minimal recognition of the criterion with extremely poor execution. Major fundamental flaws throughout.
3 (Poor): Limited attempt with significant weaknesses. Basic understanding but poor implementation with many errors.
4 (Below Average): Some attempt made but execution is inconsistent and underdeveloped. Notable flaws outweigh strengths.
5 (Average): Adequate baseline execution. Meets the criterion at a basic level but lacks depth, nuance, or distinctive quality.
6 (Above Average): Solid execution with some effective elements. Shows competence and understanding with occasional moments of quality.
7 (Good): Effective and consistent execution. Demonstrates skill and understanding with clear evidence of planning and craft.
8 (Very Good): High-quality execution with sophisticated understanding. Strong control and compelling implementation with minor flaws.
9 (Excellent): Exceptional execution showing mastery of the criterion. Near-flawless implementation with creative insight and polish.
10 (Outstanding): Exemplary achievement representing the highest standard. Masterful execution with profound insight, originality, and artistic excellence.
"""

# Dynamically generate FORMAT string
criterion_scores_str = "\n".join(
    [f"CRITERION_{i+1}|{m['name']}|[SCORE_1-10]|[Your justification here]" for i, m in enumerate(ALL_METRICS)]
)
FORMAT = f"""
CRITICAL: You MUST follow this EXACT format. Do NOT deviate from this structure.

===EVALUATION_START===
OVERALL_SUMMARY: [Write your overall summary here in one paragraph]

CRITERION_SCORES:
{criterion_scores_str}
===EVALUATION_END===

IMPORTANT RULES:
1. Replace [SCORE_1-10] with a single digit from 1 to 10
2. Replace [Your justification here] with your explanation
3. Use the EXACT criterion names as shown
4. Do NOT add extra text outside the ===EVALUATION_START=== and ===EVALUATION_END=== markers
5. Each CRITERION line must be on a single line
6. Use the pipe symbol | as a separator exactly as shown

"""
#这是系统目前使用的提示词
PROMPT_0818 = ROLE + EVALUATE + FORMAT