import json

def check_test_file():
    file_path = r"C:\AIRelief\HUMANTOOL\bench\TravelPlanner\test_evaluation.jsonl"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"文件内容长度: {len(content)}")
            print(f"文件内容预览: {repr(content[:200])}")
            
            if not content.strip():
                print("❌ 文件是空的!")
                return False
            
            lines = content.strip().split('\n')
            print(f"文件行数: {len(lines)}")
            
            for i, line in enumerate(lines):
                if line.strip():
                    try:
                        data = json.loads(line)
                        print(f"第 {i+1} 行解析成功:")
                        print(f"  idx: {data.get('idx', 'MISSING')}")
                        print(f"  有 plan: {'是' if data.get('plan') else '否'}")
                        print(f"  plan 类型: {type(data.get('plan'))}")
                        if data.get('plan'):
                            print(f"  plan 长度: {len(data['plan']) if isinstance(data['plan'], list) else 'N/A'}")
                        return True
                    except json.JSONDecodeError as e:
                        print(f"❌ 第 {i+1} 行 JSON 解析错误: {e}")
                        print(f"  内容: {repr(line)}")
                        return False
            
    except FileNotFoundError:
        print(f"❌ 文件未找到: {file_path}")
        return False
    except Exception as e:
        print(f"❌ 读取文件时出错: {e}")
        return False
    
    return False

if __name__ == "__main__":
    check_test_file()