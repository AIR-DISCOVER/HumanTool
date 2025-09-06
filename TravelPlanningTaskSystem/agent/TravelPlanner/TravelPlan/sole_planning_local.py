import os
import re
import sys

# 获取当前文件目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录 (TravelPlanner)
project_root = os.path.dirname(current_dir) # c:\AIRelief\HUMANTOOL\TATA\agent\TravelPlanner
# 获取 agent 根目录
agent_root = os.path.dirname(project_root) # c:\AIRelief\HUMANTOOL\TATA\agent

# 打印初始 sys.path，用于调试
print("--- Initial sys.path ---")
for i, p_item in enumerate(sys.path):
    print(f"{i}: {p_item}")
print("------------------------")

# --- sys.path MANIPULATION ---
# Start with a clean slate relevant to the project for sys.path
# Keep essential Python paths (like anaconda3 paths)
# Add project_root and agent_root with high priority.
# The order matters: project_root first, then agent_root, then others.

essential_paths = [p for p in sys.path if 'anaconda3' in p.lower() or 'python311' in p.lower()] # Adjust if your python path is different
new_sys_path = []

# 1. Add project_root (TravelPlanner)
if project_root not in new_sys_path:
    new_sys_path.append(project_root)

# 2. Add agent_root (agent)
if agent_root not in new_sys_path:
    new_sys_path.append(agent_root)

# Add back the essential Python paths
for p in essential_paths:
    if p not in new_sys_path:
        new_sys_path.append(p)

# Add current script's directory if it's not already covered
# (though usually covered by project_root or agent_root if structured well)
if current_dir not in new_sys_path and current_dir != project_root and current_dir != agent_root:
    new_sys_path.insert(2, current_dir) # Insert after project_root and agent_root

sys.path = new_sys_path
# --- END sys.path MANIPULATION ---


# 设置工作目录为 project_root (TravelPlanner)
os.chdir(project_root)
print(f"Changed CWD to: {os.getcwd()}")


print("--- Modified sys.path (before problematic imports) ---")
for i, p_item in enumerate(sys.path):
    print(f"{i}: {p_item}")
print("-----------------------------------------------------")


from dotenv import load_dotenv
# Specify path to .env if it's not in CWD or its parent after chdir
# By default, load_dotenv looks for .env in the current working directory (project_root)
# or its parents. If your .env is elsewhere (e.g., agent_root), specify its path.
dotenv_path = os.path.join(project_root, '.env') # Assuming .env is in TravelPlanner
if not os.path.exists(dotenv_path) and os.path.exists(os.path.join(agent_root, '.env')):
    dotenv_path = os.path.join(agent_root, '.env') # Fallback to .env in agent root
    print(f"Using .env file from agent_root: {dotenv_path}")
elif not os.path.exists(dotenv_path):
    print(f"Warning: .env file not found at {dotenv_path} or in agent_root.")
    dotenv_path = None

if dotenv_path:
    load_dotenv(dotenv_path=dotenv_path)
    print(f"Loaded .env from: {dotenv_path}")
else:
    load_dotenv() # Try default behavior
    print("Attempted to load .env using default behavior (CWD or parents).")


# 现在使用正确的导入
try:
    print("Attempting to import 'agents.prompts'...")
    from agents.prompts import planner_agent_prompt, cot_planner_agent_prompt, react_planner_agent_prompt, react_reflect_planner_agent_prompt, reflect_prompt
    print("Successfully imported 'agents.prompts'")
    
    print("Attempting to import 'tools.planner.apis'...")
    # 修改这行：从 tools.planner.apis 导入，而不是从 TravelPlan.apis
    from tools.planner.apis import Planner, ReactPlanner, ReactReflectPlanner
    print("Successfully imported 'tools.planner.apis'")

except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print("--- sys.path at time of error ---")
    for i, p_item in enumerate(sys.path):
        print(f"{i}: {p_item}")
    print("---------------------------------")
    
    if 'env' in str(e):
        print("\n--- Diagnosing 'env' import issue ---")
        print("Checking for 'env.py' or 'env' package in sys.path locations:")
        for p_dir in sys.path:
            potential_env_py = os.path.join(p_dir, 'env.py')
            potential_env_pkg = os.path.join(p_dir, 'env', '__init__.py')
            if os.path.exists(potential_env_py):
                print(f"  Found 'env.py' at: {potential_env_py}")
            if os.path.exists(potential_env_pkg):
                print(f"  Found 'env' package at: {os.path.dirname(potential_env_pkg)}")
        print("Please ensure 'tools.planner.apis.py' is not trying to 'import env' if it means to use environment variables loaded by python-dotenv.")
        print("Environment variables should be accessed via 'os.environ.get(\"VAR_NAME\")'.")

    sys.exit(1)

import json
import time
from tqdm import tqdm
import argparse

# 修复langchain导入警告
try:
    from langchain_community.callbacks import get_openai_callback
except ImportError:
    try:
        from langchain.callbacks import get_openai_callback
    except ImportError:
        print("Failed to import get_openai_callback. Please install langchain-community:")
        print("pip install langchain-community")
        sys.exit(1)

try:
    import openai
except ImportError:
    print("OpenAI not found. Please install: pip install openai")
    sys.exit(1)

def load_local_data(data_file):
    """加载本地数据文件"""
    # 如果是相对路径，基于项目根目录解析
    if not os.path.isabs(data_file):
        data_file = os.path.join(project_root, data_file)
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Loaded {len(data)} queries from {data_file}")
        return data
    except FileNotFoundError:
        print(f"Error: Data file {data_file} not found!")
        print("Please run extract_specific_queries.py first to create the local data file.")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file {data_file}: {e}")
        return []

def catch_openai_api_error():
    error = sys.exc_info()[0]
    try:
        if hasattr(openai, 'error'):
            if error == openai.error.APIConnectionError:
                print("APIConnectionError")
            elif error == openai.error.RateLimitError:
                print("RateLimitError")
                time.sleep(60)
            elif error == openai.error.APIError:
                print("APIError")
            elif error == openai.error.AuthenticationError:
                print("AuthenticationError")
            else:
                print("API error:", error)
        else:
            print("OpenAI error:", error)
    except Exception:
        print("Unknown API error:", error)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_file", type=str, default="TravelPlan/local_validation_data.json", 
                        help="Local data file path")
    parser.add_argument("--model_name", type=str, default="gpt-4o")
    parser.add_argument("--output_dir", type=str, default="./TravelPlan/local_results")
    parser.add_argument("--strategy", type=str, default="direct", 
                        choices=['direct', 'cot', 'react', 'reflexion'])
    parser.add_argument("--query_indices", type=int, nargs='+', default=None,
                        help="Specific query indices to run (1-based)")
    
    args = parser.parse_args()
    
    print(f"Project root: {project_root}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Data file: {args.data_file}")
    
    # 加载本地数据
    query_data_list = load_local_data(args.data_file)
    
    if not query_data_list:
        print("No data loaded. Exiting...")
        sys.exit(1)
    
    # 确定要运行的查询
    if args.query_indices:
        numbers = [i for i in args.query_indices if 1 <= i <= len(query_data_list)]
        if not numbers:
            print(f"Error: Invalid query indices. Available range: 1-{len(query_data_list)}")
            sys.exit(1)
    else:
        numbers = [i for i in range(1, len(query_data_list) + 1)]
    
    print(f"Will process {len(numbers)} queries: {numbers}")
    
    # 创建输出目录
    if not os.path.isabs(args.output_dir):
        output_dir = os.path.join(project_root, args.output_dir)
    else:
        output_dir = args.output_dir
    
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")
    
    # 初始化规划器
    try:
        if args.strategy == 'direct':
            planner = Planner(model_name=args.model_name, agent_prompt=planner_agent_prompt)
        elif args.strategy == 'cot':
            planner = Planner(model_name=args.model_name, agent_prompt=cot_planner_agent_prompt)
        elif args.strategy == 'react':
            planner = ReactPlanner(model_name=args.model_name, agent_prompt=react_planner_agent_prompt)
        elif args.strategy == 'reflexion':
            planner = ReactReflectPlanner(model_name=args.model_name, agent_prompt=react_reflect_planner_agent_prompt, reflect_prompt=reflect_prompt)
    except Exception as e:
        print(f"Error initializing planner: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # 运行规划
    results = []
    
    with get_openai_callback() as cb:
        for number in tqdm(numbers, desc="Processing queries"):
            query_data = query_data_list[number - 1]
            reference_information = query_data['reference_information']
            
            print(f"\nProcessing Query {number} (idx: {query_data.get('idx', 'N/A')}):")
            print(f"Query: {query_data['query'][:100]}...")
            
            # 重试机制
            max_retries = 3
            retry_count = 0
            planner_results = None
            scratchpad = None
            
            while retry_count < max_retries:
                try:
                    if args.strategy in ['react', 'reflexion']:
                        planner_results, scratchpad = planner.run(reference_information, query_data['query'])
                    else:
                        planner_results = planner.run(reference_information, query_data['query'])
                    
                    if planner_results is not None:
                        break
                        
                except Exception as e:
                    print(f"Error on attempt {retry_count + 1}: {e}")
                    catch_openai_api_error()
                    
                retry_count += 1
                if retry_count < max_retries:
                    print(f"Retrying... (attempt {retry_count + 1}/{max_retries})")
                    time.sleep(5)
            
            if planner_results is None:
                print(f"Failed to generate plan for query {number} after {max_retries} attempts")
                continue
            
            print(f"Generated plan length: {len(str(planner_results))}")
            
            # 构建结果
            result = {
                "query_number": number,
                "original_idx": query_data.get('idx'),
                "query": query_data['query'],
                f"{args.model_name}_{args.strategy}_sole-planning_results": planner_results
            }
            
            if args.strategy in ['react', 'reflexion'] and scratchpad:
                result[f"{args.model_name}_{args.strategy}_sole-planning_results_logs"] = scratchpad
            
            results.append(result)
            
            # 保存单个结果
            # single_result_file = os.path.join(output_dir, f"generated_plan_{number}.json")
            # with open(single_result_file, 'w', encoding='utf-8') as f:
            #     json.dump([result], f, indent=4, ensure_ascii=False)
            
            # print(f"Saved result to: {single_result_file}")
    
    # 保存所有结果
    all_results_file = os.path.join(output_dir, f"all_results_{args.strategy}_{args.model_name}.json")
    with open(all_results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    
    # 保存JSONL格式
    jsonl_file = os.path.join(output_dir, f"results_{args.strategy}_{args.model_name}.jsonl")
    with open(jsonl_file, 'w', encoding='utf-8') as f:
        for result in results:
            jsonl_item = {
                "idx": result["original_idx"],
                "query": result["query"],
                "plan": result[f"{args.model_name}_{args.strategy}_sole-planning_results"]
            }
            f.write(json.dumps(jsonl_item, ensure_ascii=False) + '\n')
    
    print(f"\nAll results saved:")
    print(f"- JSON format: {all_results_file}")
    print(f"- JSONL format: {jsonl_file}")
    print(f"\nTotal cost: {cb}")