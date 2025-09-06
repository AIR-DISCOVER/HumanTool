import json
from datasets import load_dataset
from tqdm import tqdm

def extract_specific_queries():
    """提取特定的查询数据到本地"""
    
    # 目标查询列表
    target_queries = [
        "Can you help construct a travel plan that begins in Philadelphia and includes visits to 3 different cities in Virginia? The trip duration is for 7 days, from March 15th to March 21st, 2022, with a total budget of $1,800.",
        "Could you help design a 3-day trip for a group of 4 from Las Vegas to Santa Maria from March 10th to March 12th, 2022? We have a budget of $3,700. We have a preference for American and Mediterranean cuisines.",
        "Can you design a 3-day travel itinerary for 2 people, departing from Ithaca and heading to Newark from March 18th to March 20th, 2022? Our budget is set at $1,200, and we require our accommodations to be entire rooms and visitor-friendly. Please note that we prefer not to drive ourselves during this trip."
    ]
    
    print("Loading dataset from HuggingFace...")
    # 加载验证集数据
    dataset = load_dataset('osunlp/TravelPlanner', 'validation')
    validation_data = dataset['validation']
    
    extracted_data = []
    found_queries = set()
    
    print("Searching for target queries...")
    for i, data_point in enumerate(tqdm(validation_data)):
        query = data_point['query'].strip()
        
        # 检查是否匹配目标查询
        for target_query in target_queries:
            if query == target_query.strip():
                print(f"Found query {len(extracted_data) + 1}: {query[:50]}...")
                
                # 提取完整数据
                extracted_item = {
                    "idx": data_point.get('idx', i),
                    "query": query,
                    "reference_information": data_point['reference_information'],
                    "original_index": i
                }
                
                extracted_data.append(extracted_item)
                found_queries.add(target_query)
                break
    
    print(f"\nExtraction completed:")
    print(f"- Target queries: {len(target_queries)}")
    print(f"- Found queries: {len(found_queries)}")
    print(f"- Extracted data points: {len(extracted_data)}")
    
    # 保存到本地JSON文件
    output_file = 'local_validation_data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(extracted_data, f, indent=2, ensure_ascii=False)
    
    print(f"Data saved to: {output_file}")
    
    # 显示找到的查询
    print("\nFound queries:")
    for i, item in enumerate(extracted_data, 1):
        print(f"{i}. Query {item['idx']}: {item['query'][:80]}...")
    
    # 检查是否有未找到的查询
    missing_queries = set(target_queries) - found_queries
    if missing_queries:
        print("\nMissing queries:")
        for query in missing_queries:
            print(f"- {query[:80]}...")
    
    return extracted_data

if __name__ == "__main__":
    extracted_data = extract_specific_queries()