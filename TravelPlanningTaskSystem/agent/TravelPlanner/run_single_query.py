import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..")))
from tools.flights.apis import Flights
from tools.accommodations.apis import Accommodations
from tools.restaurants.apis import Restaurants
from tools.googleDistanceMatrix.apis import GoogleDistanceMatrix
from tools.attractions.apis import Attractions
import math
import re
import random

# 初始化API工具
flight = Flights()
accommodations = Accommodations()
restaurants = Restaurants()
googleDistanceMatrix = GoogleDistanceMatrix()
attractions = Attractions()

def get_city_list(days, deparure_city, destination):
    city_list = []
    city_list.append(deparure_city)
    if days == 3:
        city_list.append(destination)
    else:
        city_set = open('../database/background/citySet_with_states.txt').read().split('\n')
        state_city_map = {}
        for unit in city_set:
            city, state = unit.split('\t')
            if state not in state_city_map:
                state_city_map[state] = []
            state_city_map[state].append(city)
        for city in state_city_map[destination]:
            if city != deparure_city:
                city_list.append(city + f"({destination})")
    return city_list

def extract_before_parenthesis(s):
    match = re.search(r'^(.*?)\([^)]*\)', s)
    return match.group(1) if match else s

def get_transportation(org, dest, date):
    transportation_price_info = {'Flight': 1e9, 'Self-driving': 1e9, 'Taxi': 1e9}
    
    # 获取航班信息
    flight_info = flight.run(org, dest, date)
    if type(flight_info) != str and len(flight_info) > 0:
        flight_cost = int(flight_info.sort_values(by=['Price'], ascending=True).iloc[0]['Price'])
        transportation_price_info['Flight'] = flight_cost
    
    # 获取自驾信息
    self_driving_info = googleDistanceMatrix.run_for_evaluation(org, dest, mode='driving')
    if self_driving_info['cost'] != None:
        transportation_price_info['Self-driving'] = self_driving_info['cost'] * math.ceil(1.0 / 5)
    
    # 获取出租车信息
    taxi_info = googleDistanceMatrix.run_for_evaluation(org, dest, mode='taxi')
    if taxi_info['cost'] != None:
        transportation_price_info['Taxi'] = taxi_info['cost'] * math.ceil(1.0 / 4)
    
    sorted_dict = dict(sorted(transportation_price_info.items(), key=lambda item: item[1]))
    transportation = list(sorted_dict.keys())[0]
    
    if transportation_price_info[transportation] == 1e9:
        return False, None
    
    if transportation == 'Flight':
        transportation = f"Flight Number: {flight_info.sort_values(by=['Price'], ascending=True).iloc[0]['Flight Number']}"
    
    return True, transportation

def get_meal(city):
    restaurant = restaurants.run(city)
    if type(restaurant) == str:
        return False, None
    restaurant = restaurant.sort_values(by=["Average Cost"], ascending=True)
    
    for idx in range(len(restaurant)):
        return True, f"{restaurant.iloc[idx]['Name']}, {city}"
    return False, None

def get_attraction(city):
    attraction = attractions.run(city)
    if type(attraction) == str:
        return False, None
    idx = random.choice([i for i in range(len(attraction))])
    return True, f"{attraction.iloc[idx]['Name']}, {city}"

def get_accommodation(city):
    accommodation = accommodations.run(city)
    
    if type(accommodation) == str:
        return False, None
    accommodation = accommodation.sort_values(by=["price"], ascending=True)
    if len(accommodation) == 0:
        return False, None
    
    return True, f"{accommodation.iloc[0]['NAME']}, {city}"

def run_single_query():
    # 定义单个查询
    query_data = {
        "idx": 41,
        "query": "Can you help construct a travel plan that begins in Philadelphia and includes visits to 3 different cities in Virginia? The trip duration is for 7 days, from March 15th to March 21st, 2022, with a total budget of $1,800.",
        "org": "Philadelphia",
        "dest": "Virginia", 
        "days": 7,
        "visiting_city_number": 3,
        "date": ["2022-03-15", "2022-03-16", "2022-03-17", "2022-03-18", "2022-03-19", "2022-03-20", "2022-03-21"],
        "people_number": 1,  # 假设默认值
        "budget": 1800
    }
    
    # 运行规划算法
    plan_list = [{'finished': [False, set()]}]
    restaurant_list = []
    attraction_list = []
    finished = False
    city_list = get_city_list(query_data['days'], query_data['org'], query_data['dest'])
    
    # 处理城市列表
    for i, unit in enumerate(city_list):
        city_list[i] = extract_before_parenthesis(unit)
    
    print(f"City list: {city_list}")
    
    # 生成每日计划
    for current_day in range(1, query_data['days'] + 1):
        plan = {key: "-" for key in ['day', 'current_city', 'transportation', 'breakfast', 'lunch', 'dinner', 'attraction', 'accommodation']}
        plan['day'] = current_day
        current_city = None
        
        # 根据当前日期设置城市和交通
        if current_day == 1:
            plan['current_city'] = f'from {city_list[0]} to {city_list[1]}'
            flag, transportation = get_transportation(city_list[0], city_list[1], query_data['date'][0])
            if flag:
                plan['transportation'] = f'{transportation}, from {city_list[0]} to {city_list[1]}'
            else:
                plan_list[0]['finished'][0] = False
                plan_list[0]['finished'][1].add('No valid transportation information.')
        
        elif current_day == 3 and current_day == query_data['days']:
            plan['current_city'] = f'from {city_list[1]} to {city_list[0]}'
            flag, transportation = get_transportation(city_list[1], city_list[0], query_data['date'][2])
            if flag:
                plan['transportation'] = f'{transportation}, from {city_list[1]} to {city_list[0]}'
            else:
                plan_list[0]['finished'][0] = False
                plan_list[0]['finished'][1].add('No valid transportation information.')
        
        elif current_day == 3:
            plan['current_city'] = f'from {city_list[1]} to {city_list[2]}'
            flag, transportation = get_transportation(city_list[1], city_list[2], query_data['date'][2])
            if flag:
                plan['transportation'] = f'{transportation}, from {city_list[1]} to {city_list[2]}'
            else:
                plan_list[0]['finished'][0] = False
                plan_list[0]['finished'][1].add('No valid transportation information.')
        
        elif current_day == 5 and current_day == query_data['days']:
            plan['current_city'] = f'from {city_list[2]} to {city_list[0]}'
            flag, transportation = get_transportation(city_list[2], city_list[0], query_data['date'][4])
            if flag:
                plan['transportation'] = f'{transportation}, from {city_list[2]} to {city_list[0]}'
            else:
                plan_list[0]['finished'][0] = False
                plan_list[0]['finished'][1].add('No valid transportation information.')
        
        elif current_day == 5:
            plan['current_city'] = f'from {city_list[2]} to {city_list[3]}'
            flag, transportation = get_transportation(city_list[2], city_list[3], query_data['date'][4])
            if flag:
                plan['transportation'] = f'{transportation}, from {city_list[2]} to {city_list[3]}'
            else:
                plan_list[0]['finished'][0] = False
                plan_list[0]['finished'][1].add('No valid transportation information.')
        
        elif current_day == 7:
            plan['current_city'] = f'from {city_list[3]} to {city_list[0]}'
            flag, transportation = get_transportation(city_list[3], city_list[0], query_data['date'][6])
            if flag:
                plan['transportation'] = f'{transportation}, from {city_list[3]} to {city_list[0]}'
            else:
                plan_list[0]['finished'][0] = False
                plan_list[0]['finished'][1].add('No valid transportation information.')
        
        # 确定当前城市
        if plan['current_city'] == '-':
            plan['current_city'] = plan_list[-1]['current_city'].split(' to ')[1]
            current_city = plan['current_city']
        else:
            current_city = plan['current_city'].split(' to ')[1]
        
        print(f"Day {current_day}: Current city - {current_city}")
        
        # 获取餐厅信息
        for key in ['breakfast', 'lunch', 'dinner']:
            flag, meal = get_meal(current_city)
            if flag:
                plan[key] = f'{meal}'
                restaurant_list.append(meal)
            else:
                plan_list[0]['finished'][0] = False
                plan_list[0]['finished'][1].add('No valid meal information.')
        
        # 获取景点信息
        flag, attraction = get_attraction(current_city)
        if flag:
            plan['attraction'] = f'{attraction}'
        else:
            plan_list[0]['finished'][0] = False
            plan_list[0]['finished'][1].add('No valid attraction information.')
        
        # 获取住宿信息（最后一天除外）
        if current_day != query_data['days']:
            flag, accommodation = get_accommodation(current_city)
            if flag:
                plan['accommodation'] = f'{accommodation}'
            else:
                plan_list[0]['finished'][0] = False
                plan_list[0]['finished'][1].add('No valid accommodation information.')
        
        plan_list.append(plan)
    
    # 检查是否成功完成
    if plan_list[0]['finished'][1] == set():
        plan_list[0]['finished'] = (True, [])
    
    # 构建最终结果
    result = {
        "idx": query_data["idx"],
        "query": query_data["query"],
        "plan": plan_list[1:]  # 排除第一个元素（状态信息）
    }
    
    return result

if __name__ == "__main__":
    try:
        result = run_single_query()
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()