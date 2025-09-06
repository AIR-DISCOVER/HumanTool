import json
import sys
import os
import argparse
from datetime import datetime
from tqdm import tqdm

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, 'agents'))

# 更改工作目录到agents目录
os.chdir(os.path.join(current_dir, 'agents'))

# 导入必要的模块
try:
    from tool_agents import ReactAgent
except ImportError as e:
    print(f"Import error: {e}")
    print("Trying alternative import...")
    from agents.tool_agents import ReactAgent

# 定义测试查询
TEST_QUERIES = [
    {
        "idx": 41,
        "query": "Can you help construct a travel plan that begins in Philadelphia and includes visits to 3 different cities in Virginia? The trip duration is for 7 days, from March 15th to March 21st, 2022, with a total budget of $1,800."
    },
    {
        "idx": 120,
        "query": "Can you assist in creating a travel itinerary departing Baton Rouge and heading to Dallas for a duration of 3 days, from March 25th to March 27th, 2022? The plan will be for a group of 4 people and will have a total budget of $5,500. It's crucial for us to find accommodations where smoking is permitted as that's one of our requirements."
    },
    {
        "idx": 121,
        "query": "I need to organize a 3-day trip for a group of 3, departing from Asheville and arriving in Minneapolis. We will be traveling from March 7th to March 9th, 2022, with a total budget of $2,300. We require accommodations that allow pets and provide entire rooms. Regarding meals, our group enjoys a variety of cuisines, including Indian, Chinese, Mediterranean, and American."
    }
]

def run_single_query(query_data, model_name='gpt-4o', max_steps=50):
    """
    运行单个查询
    """
    idx = query_data['idx']
    query = query_data['query']
    
    print(f"\n{'='*80}")
    print(f"PROCESSING QUERY {idx}")
    print(f"{'='*80}")
    print(f"Query: {query}")
    print(f"Model: {model_name}")
    print(f"Max steps: {max_steps}")
    
    # 设置环境变量检查
    if not os.getenv('OPENAI_API_KEY'):
        print("Warning: OPENAI_API_KEY not set in environment variables")
        return {
            "idx": idx,
            "query": query,
            "error": "OpenAI API key not set",
            "success": False,
            "model_name": model_name
        }
    
    # 定义工具列表
    tools_list = ["notebook", "flights", "attractions", "accommodations", "restaurants", "googleDistanceMatrix", "planner", "cities"]
    
    try:
        # 创建ReactAgent实例
        agent = ReactAgent(
            args=None,
            tools=tools_list,
            max_steps=max_steps,
            react_llm_name=model_name,
            planner_llm_name=model_name
        )
        
        print("Starting Two-stage Mode planning...")
        
        # 运行ReactAgent
        planner_results, scratchpad, action_log = agent.run(query)
        
        print(f"Agent execution completed:")
        print(f"- Planner results length: {len(str(planner_results)) if planner_results else 0}")
        print(f"- Scratchpad length: {len(scratchpad) if scratchpad else 0}")
        print(f"- Total actions: {len(action_log) if action_log else 0}")
        
        # 检查是否有结果
        has_valid_results = (
            planner_results is not None and 
            planner_results != '' and 
            planner_results != 'Max Token Length Exceeded.' and
            'Invalid Action' not in str(planner_results)
        )
        
        # 如果没有结果，尝试从scratchpad提取信息
        if not has_valid_results and scratchpad:
            print("No planner results found, trying to extract from scratchpad...")
            if "plan" in scratchpad.lower() or "itinerary" in scratchpad.lower():
                lines = scratchpad.split('\n')
                plan_lines = []
                for line in lines:
                    if any(keyword in line.lower() for keyword in ['day', 'march', 'hotel', 'restaurant', 'flight', 'attraction']):
                        plan_lines.append(line.strip())
                
                if plan_lines:
                    planner_results = '\n'.join(plan_lines[-30:])  # 取最后30行相关内容
                    has_valid_results = True
                    print("Extracted plan from scratchpad")
        
        # 构建结果
        result = {
            "idx": idx,
            "query": query,
            "planner_results": planner_results,
            "scratchpad": scratchpad,
            "action_log": action_log,
            "success": has_valid_results,
            "model_name": model_name,
            "total_steps": len(action_log) if action_log else 0
        }
        
        return result
        
    except Exception as e:
        print(f"Error occurred during planning: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "idx": idx,
            "query": query,
            "error": str(e),
            "success": False,
            "model_name": model_name
        }

def run_multiple_queries(queries=None, model_name='gpt-4o', max_steps=50, output_dir='results'):
    """
    运行多个查询
    """
    if queries is None:
        queries = TEST_QUERIES
    
    # 使用绝对路径确保目录创建成功
    if not os.path.isabs(output_dir):
        output_dir = os.path.abspath(output_dir)
    
    # 创建输出目录
    try:
        os.makedirs(output_dir, exist_ok=True)
        print(f"Output directory created/verified: {output_dir}")
    except Exception as e:
        print(f"Error creating output directory: {e}")
        # 回退到当前目录
        output_dir = os.path.join(os.getcwd(), 'results')
        os.makedirs(output_dir, exist_ok=True)
        print(f"Using fallback directory: {output_dir}")
    
    print(f"Running {len(queries)} queries with model {model_name}")
    
    results = []
    summary = {
        "total": len(queries),
        "successful": 0,
        "failed": 0,
        "failed_indices": [],
        "model_name": model_name,
        "timestamp": datetime.now().strftime('%Y%m%d_%H%M%S')
    }
    
    # 处理每个查询
    for i, query_data in enumerate(tqdm(queries, desc="Processing queries")):
        result = run_single_query(query_data, model_name, max_steps)
        results.append(result)
        
        # 更新统计
        if result.get('success', False):
            summary['successful'] += 1
            print(f"✓ Query {result['idx']}: SUCCESS")
        else:
            summary['failed'] += 1
            summary['failed_indices'].append(result['idx'])
            print(f"✗ Query {result['idx']}: FAILED - {result.get('error', 'Unknown error')}")
        
        # 保存单个结果 - 使用更安全的文件名
        try:
            single_result_file = os.path.join(output_dir, f"query_{result['idx']}_{summary['timestamp']}.json")
            print(f"Saving to: {single_result_file}")
            
            with open(single_result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            # 立即保存JSONL格式（用于后处理）
            jsonl_result = {
                "idx": result['idx'],
                "query": result['query'],
                "plan": result.get('planner_results', '')
            }
            
            jsonl_file = os.path.join(output_dir, f"query_{result['idx']}_{summary['timestamp']}.jsonl")
            with open(jsonl_file, 'w', encoding='utf-8') as f:
                f.write(json.dumps(jsonl_result, ensure_ascii=False) + '\n')
                
        except Exception as e:
            print(f"Error saving individual result for query {result['idx']}: {e}")
            # 继续处理其他查询
            continue
    
    # 保存汇总结果
    try:
        batch_results = {
            "summary": summary,
            "results": results
        }
        
        batch_file = os.path.join(output_dir, f"batch_results_{summary['timestamp']}.json")
        with open(batch_file, 'w', encoding='utf-8') as f:
            json.dump(batch_results, f, indent=2, ensure_ascii=False)
        
        # 保存所有结果的JSONL文件
        all_jsonl_file = os.path.join(output_dir, f"all_results_{summary['timestamp']}.jsonl")
        with open(all_jsonl_file, 'w', encoding='utf-8') as f:
            for result in results:
                jsonl_result = {
                    "idx": result['idx'],
                    "query": result['query'],
                    "plan": result.get('planner_results', '')
                }
                f.write(json.dumps(jsonl_result, ensure_ascii=False) + '\n')
                
        print(f"Batch results saved to: {batch_file}")
        print(f"All JSONL results saved to: {all_jsonl_file}")
        
    except Exception as e:
        print(f"Error saving batch results: {e}")
    
    return results, summary

def print_summary(summary, results):
    """
    打印执行总结
    """
    print("\n" + "="*80)
    print("EXECUTION SUMMARY")
    print("="*80)
    print(f"Model: {summary['model_name']}")
    print(f"Total queries: {summary['total']}")
    print(f"Successful: {summary['successful']}")
    print(f"Failed: {summary['failed']}")
    print(f"Success rate: {summary['successful']/summary['total']*100:.1f}%")
    
    if summary['failed_indices']:
        print(f"Failed query indices: {summary['failed_indices']}")
    
    print(f"\nDetailed results:")
    for result in results:
        status = "✓ SUCCESS" if result.get('success', False) else "✗ FAILED"
        plan_length = len(str(result.get('planner_results', '')))
        print(f"  Query {result['idx']}: {status} (Plan length: {plan_length} chars)")

def print_sample_results(results, show_count=1):
    """
    打印样本结果
    """
    print(f"\n" + "="*80)
    print(f"SAMPLE RESULTS (showing first {show_count})")
    print("="*80)
    
    successful_results = [r for r in results if r.get('success', False)]
    
    for i, result in enumerate(successful_results[:show_count]):
        print(f"\nSample {i+1} - Query {result['idx']}:")
        print("-" * 40)
        print(f"Query: {result['query'][:100]}...")
        plan = result.get('planner_results', '')
        if plan:
            print(f"Plan (first 300 chars): {plan[:300]}...")
        else:
            print("No plan generated")
        print("-" * 40)

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='Run Two-stage Mode for multiple queries')
    parser.add_argument('--model_name', type=str, default='gpt-4o',
                        choices=['gpt-3.5-turbo-1106', 'gpt-4-1106-preview', 'gpt-4o', 'gemini'],
                        help='Model name to use')
    parser.add_argument('--max_steps', type=int, default=50,
                        help='Maximum steps for agent execution')
    parser.add_argument('--output_dir', type=str, default='results',
                        help='Output directory')
    parser.add_argument('--queries', type=str, nargs='+', 
                        choices=['all', '41', '120', '121'],
                        default=['all'],
                        help='Which queries to run (default: all)')
    parser.add_argument('--show_samples', type=int, default=1,
                        help='Number of sample results to show')
    parser.add_argument('--custom_query_file', type=str, default=None,
                        help='Path to custom queries JSON file')
    
    args = parser.parse_args()
    
    # 确定要运行的查询
    if args.custom_query_file:
        try:
            with open(args.custom_query_file, 'r', encoding='utf-8') as f:
                queries = json.load(f)
        except Exception as e:
            print(f"Error loading custom query file: {e}")
            return
    else:
        if 'all' in args.queries:
            queries = TEST_QUERIES
        else:
            # 按索引选择查询
            selected_indices = [int(q) for q in args.queries if q.isdigit()]
            queries = [q for q in TEST_QUERIES if q['idx'] in selected_indices]
    
    if not queries:
        print("No queries selected!")
        return
    
    print(f"Two-stage Mode Multiple Queries Runner")
    print(f"Using model: {args.model_name}")
    print(f"Max steps: {args.max_steps}")
    print(f"Output directory: {args.output_dir}")
    print(f"Selected queries: {[q['idx'] for q in queries]}")
    print("="*80)
    
    # 运行查询
    try:
        results, summary = run_multiple_queries(
            queries=queries,
            model_name=args.model_name,
            max_steps=args.max_steps,
            output_dir=args.output_dir
        )
        
        # 打印总结
        print_summary(summary, results)
        
        # 显示样本结果
        if args.show_samples > 0 and summary['successful'] > 0:
            print_sample_results(results, args.show_samples)
        
        print(f"\n✅ All results saved to: {os.path.abspath(args.output_dir)}")
        print(f"📁 Main files:")
        timestamp = summary['timestamp']
        print(f"  - Batch results: batch_results_{timestamp}.json")
        print(f"  - All JSONL: all_results_{timestamp}.jsonl")
        print(f"  - Individual files: query_[idx]_{timestamp}.json/jsonl")
        
    except Exception as e:
        print(f"Fatal error in main execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()