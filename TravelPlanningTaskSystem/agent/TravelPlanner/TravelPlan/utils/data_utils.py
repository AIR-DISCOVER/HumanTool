from datasets import load_dataset
import json

def load_small_sample_data(set_type='validation', sample_size=20):
    """加载小样本数据"""
    # 加载完整数据集
    data = load_dataset('osunlp/TravelPlanner', set_type)[set_type]
    
    # 取前N个样本
    small_data = data.select(range(min(sample_size, len(data))))
    
    return small_data

def save_small_sample_to_file(set_type='validation', sample_size=20, output_file='small_sample.jsonl'):
    """将小样本保存到文件"""
    data = load_small_sample_data(set_type, sample_size)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"已保存{len(data)}个样本到 {output_file}")

if __name__ == "__main__":
    # 生成20个样本的小数据集
    save_small_sample_to_file(sample_size=20)