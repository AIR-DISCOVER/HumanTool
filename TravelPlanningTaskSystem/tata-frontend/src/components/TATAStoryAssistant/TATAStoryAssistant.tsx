import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Settings } from 'lucide-react'; // 🎯 添加设置图标
import { Message, ThinkingStep, ToolCall, DraftContent, AgendaSummary } from './types';
import { generateSessionId } from './utils/messageUtils';
import { useStreamHandler } from './hooks/useStreamHandler';
import { useChatManager } from './hooks/useChatManager';

// 组件导入
import { StatusBar } from './components/StatusBar';
import { MessageList } from './components/MessageList';
import { InputArea } from './components/InputArea';
import { AgendaPanel } from './components/AgendaPanel';
import { AccountSelector } from './components/AccountSelector'; // 🎯 添加账号选择器

import '../TATAStoryAssistant.css';

// 旅游信息面板组件定义
interface TravelInfoPanelProps {
  currentConfig: {user_profile: string; travel_query: string} | null;
}

interface AccommodationData {
  city: string;
  hotels: {
    name: string;
    type: string;
    price: string;
    rating: number;
    address?: string;
    maxOccupancy: number;
    minNights: number;
    houseRules?: string;
    reviewRateNumber?: number;
  }[];
}

interface AttractionData {
  city: string;
  attractions: {
    name: string;
    nameEn: string;
    type: string;
    description: string;
    address: string;
    phone?: string;
    website?: string;
  }[];
}

interface RestaurantData {
  city: string;
  restaurants: {
    name: string;
    nameEn: string;
    cuisine: string;
    avgCost: number;
    rating: number;
  }[];
}

interface TransportData {
  route: string;
  routeEn: string;
  options: {
    type: string;
    typeEn: string;
    duration: string;
    price: string;
    description: string;
  }[];
}

// 真实数据 - 住宿信息（基于local_validation_data.json）
const accommodationDataMap: Record<string, AccommodationData[]> = {
  philadelphia_virginia: [
    {
      city: "Richmond 里士满",
      hotels: [
        { name: "Cool Summer Vibes UWS Pent House w/ rooftop", type: "整套房源 Entire home/apt", price: "$498/晚", rating: 4.0, maxOccupancy: 2, minNights: 3, houseRules: "", reviewRateNumber: 4.0 },
        { name: "12 East 86th St full furnished", type: "整套房源 Entire home/apt", price: "$451/晚", rating: 5.0, maxOccupancy: 2, minNights: 30, houseRules: "", reviewRateNumber: 5.0 },
        { name: "Spacious Room with Character in BK", type: "私人房间 Private room", price: "$1032/晚", rating: 3.0, maxOccupancy: 1, minNights: 1, houseRules: "", reviewRateNumber: 3.0 },
        { name: "Gorgeous studio in midtown Manhattan", type: "整套房源 Entire home/apt", price: "$212/晚", rating: 3.0, maxOccupancy: 3, minNights: 30, houseRules: "", reviewRateNumber: 3.0 },
        { name: "Large cozy bedroom close to Times Square 43D4", type: "私人房间 Private room", price: "$403/晚", rating: 4.0, maxOccupancy: 2, minNights: 7, houseRules: "", reviewRateNumber: 4.0 },
        { name: "2 bd 2 bathroom Apartment in Upper East Side", type: "整套房源 Entire home/apt", price: "$285/晚", rating: 5.0, maxOccupancy: 3, minNights: 4, houseRules: "", reviewRateNumber: 5.0 },
        { name: "Large suite with private bathroom (15 min to city)", type: "私人房间 Private room", price: "$764/晚", rating: 3.0, maxOccupancy: 2, minNights: 3, houseRules: "", reviewRateNumber: 3.0 },
        { name: "Inviting Brooklyn Studio", type: "整套房源 Entire home/apt", price: "$398/晚", rating: 5.0, maxOccupancy: 3, minNights: 3, houseRules: "", reviewRateNumber: 5.0 },
        { name: "CB3 BROOKLYN", type: "私人房间 Private room", price: "$1009/晚", rating: 4.0, maxOccupancy: 1, minNights: 6, houseRules: "", reviewRateNumber: 4.0 },
        { name: "East Village 1BR with private patio", type: "整套房源 Entire home/apt", price: "$566/晚", rating: 4.0, maxOccupancy: 4, minNights: 3, houseRules: "", reviewRateNumber: 4.0 },
        { name: "Bright Spacious BK Room with Bath", type: "私人房间 Private room", price: "$204/晚", rating: 1.0, maxOccupancy: 2, minNights: 3, houseRules: "", reviewRateNumber: 1.0 },
        { name: "Centrally Located Beautiful Escape", type: "私人房间 Private room", price: "$828/晚", rating: 5.0, maxOccupancy: 2, minNights: 1, houseRules: "", reviewRateNumber: 5.0 },
        { name: "Luxury NYC 1 Bed w/Gorgeous Views + Pool", type: "整套房源 Entire home/apt", price: "$255/晚", rating: 3.0, maxOccupancy: 3, minNights: 2, houseRules: "", reviewRateNumber: 3.0 }
      ]
    },
    {
      city: "Petersburg 彼得斯堡",
      hotels: [
        { name: "Charming cozy bedroom in Clinton Hill!", type: "私人房间 Private room", price: "$274/晚", rating: 5.0, maxOccupancy: 2, minNights: 3, houseRules: "", reviewRateNumber: 5.0 },
        { name: "Great Studio Apartment, 15-20mins from Downtown", type: "整套房源 Entire home/apt", price: "$595/晚", rating: 3.0, maxOccupancy: 5, minNights: 3, houseRules: "", reviewRateNumber: 3.0 },
        { name: "Grand Central/ United Nations! MASTER Bedroom", type: "私人房间 Private room", price: "$825/晚", rating: 3.0, maxOccupancy: 1, minNights: 30, houseRules: "", reviewRateNumber: 3.0 },
        { name: "Large bedroom in 2BDR apt. in the East Village", type: "私人房间 Private room", price: "$607/晚", rating: 2.0, maxOccupancy: 2, minNights: 3, houseRules: "", reviewRateNumber: 2.0 },
        { name: "Gorgeous sky-lit 2BR", type: "整套房源 Entire home/apt", price: "$725/晚", rating: 2.0, maxOccupancy: 3, minNights: 3, houseRules: "", reviewRateNumber: 2.0 },
        { name: "Penthouse", type: "整套房源 Entire home/apt", price: "$541/晚", rating: 3.0, maxOccupancy: 3, minNights: 4, houseRules: "", reviewRateNumber: 3.0 },
        { name: "cozy and extremely convenient apartment", type: "整套房源 Entire home/apt", price: "$1106/晚", rating: 2.0, maxOccupancy: 4, minNights: 30, houseRules: "", reviewRateNumber: 2.0 },
        { name: "Modern & Artsy, Awesome Location", type: "私人房间 Private room", price: "$384/晚", rating: 2.0, maxOccupancy: 1, minNights: 1, houseRules: "", reviewRateNumber: 2.0 },
        { name: "For Female Cozy Shared Room in Midtown West", type: "共享房间 Shared room", price: "$401/晚", rating: 3.0, maxOccupancy: 1, minNights: 1, houseRules: "", reviewRateNumber: 3.0 },
        { name: "Brooklyn Cultural Chateau: Sunny Private Room", type: "私人房间 Private room", price: "$275/晚", rating: 3.0, maxOccupancy: 2, minNights: 2, houseRules: "", reviewRateNumber: 3.0 },
        { name: "A King Size Bed in private room in NYC!", type: "私人房间 Private room", price: "$446/晚", rating: 3.0, maxOccupancy: 2, minNights: 2, houseRules: "", reviewRateNumber: 3.0 },
        { name: "Quiet & cozy 1 BR/balcony - Graham L in WBURG", type: "整套房源 Entire home/apt", price: "$583/晚", rating: 4.0, maxOccupancy: 3, minNights: 2, houseRules: "", reviewRateNumber: 4.0 },
        { name: "One of a Kind Chinatown 2BR Home w/ HUGE patio", type: "整套房源 Entire home/apt", price: "$431/晚", rating: 3.0, maxOccupancy: 3, minNights: 7, houseRules: "", reviewRateNumber: 3.0 },
        { name: "Modern 1BR Apt in the Heart Of NYC", type: "整套房源 Entire home/apt", price: "$418/晚", rating: 5.0, maxOccupancy: 3, minNights: 7, houseRules: "", reviewRateNumber: 5.0 },
        { name: "Hip FiDi Studio w/ Resident's Bar, Golf Simulator", type: "整套房源 Entire home/apt", price: "$393/晚", rating: 4.0, maxOccupancy: 3, minNights: 30, houseRules: "", reviewRateNumber: 4.0 },
        { name: "Chic & Cosy Lower East Side Apartment", type: "私人房间 Private room", price: "$577/晚", rating: 3.0, maxOccupancy: 1, minNights: 2, houseRules: "", reviewRateNumber: 3.0 },
        { name: "2 BEDROOM GREAT APT ON LEXINGTON AVE MUST SEE", type: "整套房源 Entire home/apt", price: "$808/晚", rating: 3.0, maxOccupancy: 7, minNights: 30, houseRules: "", reviewRateNumber: 3.0 },
        { name: "East Village, private room with free breakfast", type: "私人房间 Private room", price: "$909/晚", rating: 4.0, maxOccupancy: 1, minNights: 1, houseRules: "", reviewRateNumber: 4.0 }
      ]
    },
    {
      city: "Charlottesville 夏洛茨维尔",
      hotels: [
        { name: "Gorgeous natural light in Chelsea photo studio", type: "整套房源 Entire home/apt", price: "$1094/晚", rating: 2.0, maxOccupancy: 8, minNights: 1, houseRules: "", reviewRateNumber: 2.0 },
        { name: "Williamsburg Hidden Gem", type: "整套房源 Entire home/apt", price: "$391/晚", rating: 4.0, maxOccupancy: 2, minNights: 1 },
        { name: "Big Private Room in Perfect Williamsburg Location", type: "私人房间 Private room", price: "$946/晚", rating: 2.0, maxOccupancy: 1, minNights: 2 },
        { name: "Single room in Bushwick w/backyard", type: "私人房间 Private room", price: "$107/晚", rating: 3.0, maxOccupancy: 2, minNights: 1, houseRules: "", reviewRateNumber: 3.0 },
        { name: "Fantastic Value - Quiet Room Seconds from Graham L", type: "私人房间 Private room", price: "$320/晚", rating: 4.0, maxOccupancy: 1, minNights: 28 },
        { name: "Charming Shared Place in East Manhattan", type: "共享房间 Shared room", price: "$350/晚", rating: 4.0, maxOccupancy: 1, minNights: 2 },
        { name: "Comfy Cozy", type: "整套房源 Entire home/apt", price: "$553/晚", rating: 5.0, maxOccupancy: 2, minNights: 2 },
        { name: "One bedroom apartment", type: "整套房源 Entire home/apt", price: "$176/晚", rating: 5.0, maxOccupancy: 2, minNights: 7 },
        { name: "Charismatic Flat in Astoria", type: "私人房间 Private room", price: "$1098/晚", rating: 2.0, maxOccupancy: 2, minNights: 3 },
        { name: "Peaceful Spacious 1 Bdrm Apt in Carroll Gardens", type: "整套房源 Entire home/apt", price: "$611/晚", rating: 5.0, maxOccupancy: 2, minNights: 7 },
        { name: "Comfortable PRIVATE ROOM in a great location", type: "私人房间 Private room", price: "$763/晚", rating: 5.0, maxOccupancy: 2, minNights: 4 },
        { name: "Cozy and sunny Studio", type: "整套房源 Entire home/apt", price: "$154/晚", rating: 2.0, maxOccupancy: 2, minNights: 5 },
        { name: "Sunny spacious room full of good energy", type: "私人房间 Private room", price: "$155/晚", rating: 2.0, maxOccupancy: 1, minNights: 1 },
        { name: "Amazing Private room in LIC minutes to Manhattan", type: "私人房间 Private room", price: "$97/晚", rating: 4.0, maxOccupancy: 2, minNights: 1 },
        { name: "Spacious sun lit Bushwick room", type: "私人房间 Private room", price: "$87/晚", rating: 5.0, maxOccupancy: 1, minNights: 5 }
      ]
    }
  ],
  vegas_santa_maria: [
    {
      city: "Santa Maria 圣玛丽亚",
      hotels: [
        { name: "Big Bright Room ☼ Lower East Side", type: "私人房间 Private room", price: "$474/晚", rating: 5.0, maxOccupancy: 1, minNights: 25, houseRules: "不允许10岁以下儿童 & 不允许宠物 & 不允许聚会", reviewRateNumber: 5.0 },
        { name: "Cozy room in Brooklyn", type: "私人房间 Private room", price: "$906/晚", rating: 3.0, maxOccupancy: 1, minNights: 8, houseRules: "不允许聚会 & 不允许10岁以下儿童", reviewRateNumber: 3.0 },
        { name: "Beautiful Manhattan 1br apartment close to subway!", type: "整套房源 Entire home/apt", price: "$573/晚", rating: 4.0, maxOccupancy: 3, minNights: 3, houseRules: "不允许聚会 & 不允许宠物 & 不允许10岁以下儿童", reviewRateNumber: 4.0 },
        { name: "Large Bedroom on upper west/columbia", type: "私人房间 Private room", price: "$98/晚", rating: 3.0, maxOccupancy: 2, minNights: 1, houseRules: "不允许聚会 & 不允许宠物", reviewRateNumber: 3.0 },
        { name: "Crown Hts Beauty: Quiet and Cozy!", type: "整套房源 Entire home/apt", price: "$1054/晚", rating: 2.0, maxOccupancy: 8, minNights: 7, houseRules: "不允许10岁以下儿童", reviewRateNumber: 2.0 },
        { name: "Cozy apartment near Central Park", type: "整套房源 Entire home/apt", price: "$738/晚", rating: 5.0, maxOccupancy: 6, minNights: 1, houseRules: "不允许宠物", reviewRateNumber: 5.0 },
        { name: "15 Minutes to Manhattan and Safe Neighborhood!", type: "私人房间 Private room", price: "$914/晚", rating: 4.0, maxOccupancy: 2, minNights: 2, houseRules: "不允许10岁以下儿童 & 不允许聚会", reviewRateNumber: 4.0 },
        { name: "Private room in Astoria 10min ride to Central Park", type: "私人房间 Private room", price: "$416/晚", rating: 3.0, maxOccupancy: 2, minNights: 1, houseRules: "不允许访客", reviewRateNumber: 3.0 },
        { name: "Great Room In Brooklyn, The Park, 30 min to MH.", type: "私人房间 Private room", price: "$309/晚", rating: 3.0, maxOccupancy: 2, minNights: 5, houseRules: "不允许宠物 & 不允许聚会 & 不允许吸烟", reviewRateNumber: 3.0 }
      ]
    }
  ],
  ithaca_newark: [
    {
      city: "Newark 纽瓦克",
      hotels: [
        { name: "Large Two Story Loft in the Heart of West Village", type: "整套房源 Entire home/apt", price: "$1127/晚", rating: 4.0, maxOccupancy: 5, minNights: 3, houseRules: "禁止宠物 & 禁止10岁以下儿童", reviewRateNumber: 4.0 },
        { name: "Gramercy One Bedroom w Two Beds", type: "整套房源 Entire home/apt", price: "$485/晚", rating: 2.0, maxOccupancy: 4, minNights: 7, houseRules: "禁止访客 & 禁止10岁以下儿童", reviewRateNumber: 2.0 },
        { name: "AMAZING TIME SQUARE!!BRICK WALLS!!", type: "整套房源 Entire home/apt", price: "$910/晚", rating: 1.0, maxOccupancy: 3, minNights: 30, houseRules: "禁止10岁以下儿童 & 禁止宠物", reviewRateNumber: 1.0 },
        { name: "Huge, Bright, clean Bushwick blocks from train", type: "私人房间 Private room", price: "$814/晚", rating: 4.0, maxOccupancy: 1, minNights: 20, houseRules: "禁止聚会", reviewRateNumber: 4.0 },
        { name: "Contemporary Brooklyn Lifestyle Apt /JFK Airport", type: "整套房源 Entire home/apt", price: "$610/晚", rating: 2.0, maxOccupancy: 6, minNights: 2, houseRules: "禁止宠物", reviewRateNumber: 2.0 },
        { name: "Room 4 -Sunny Cozy Room in Historic Victorian Home", type: "私人房间 Private room", price: "$1196/晚", rating: 4.0, maxOccupancy: 1, minNights: 2, houseRules: "禁止宠物 & 禁止聚会", reviewRateNumber: 4.0 },
        { name: "Large room near Times Square 31C4", type: "私人房间 Private room", price: "$798/晚", rating: 3.0, maxOccupancy: 1, minNights: 7, houseRules: "禁止吸烟", reviewRateNumber: 3.0 },
        { name: "Up to 4 people-Only steps away from Times Square!!", type: "私人房间 Private room", price: "$1046/晚", rating: 2.0, maxOccupancy: 2, minNights: 1, houseRules: "禁止访客 & 禁止吸烟", reviewRateNumber: 2.0 },
        { name: "Rustic Modern Brooklyn Apartment", type: "整套房源 Entire home/apt", price: "$294/晚", rating: 3.0, maxOccupancy: 2, minNights: 30, houseRules: "禁止宠物", reviewRateNumber: 3.0 },
        { name: "Sonder | Stock Exchange | Ideal 1BR + Kitchen", type: "整套房源 Entire home/apt", price: "$903/晚", rating: 4.0, maxOccupancy: 9, minNights: 2, houseRules: "禁止宠物", reviewRateNumber: 4.0 },
        { name: "Sunny Cozy Room Located In Prime East Flatbush", type: "私人房间 Private room", price: "$432/晚", rating: 3.0, maxOccupancy: 2, minNights: 2, houseRules: "禁止聚会 & 禁止访客", reviewRateNumber: 3.0 },
        { name: "Beautiful, Sunny, Artsy apartment in Brooklyn", type: "整套房源 Entire home/apt", price: "$660/晚", rating: 3.0, maxOccupancy: 4, minNights: 21, houseRules: "禁止10岁以下儿童", reviewRateNumber: 3.0 },
        { name: "Spacious 1 bedroom in Prime Williamsburg", type: "整套房源 Entire home/apt", price: "$515/晚", rating: 2.0, maxOccupancy: 5, minNights: 3, houseRules: "禁止宠物 & 禁止访客 & 禁止吸烟", reviewRateNumber: 2.0 },
        { name: "1 Bedroom in UWS Manhattan", type: "整套房源 Entire home/apt", price: "$117/晚", rating: 2.0, maxOccupancy: 3, minNights: 2, houseRules: "禁止聚会 & 禁止吸烟", reviewRateNumber: 2.0 },
        { name: "Prime west village! design 1BR~Best Value", type: "整套房源 Entire home/apt", price: "$1066/晚", rating: 4.0, maxOccupancy: 6, minNights: 30, houseRules: "禁止吸烟", reviewRateNumber: 4.0 }
      ]
    }
  ]
};
// 真实数据 - 景点信息
const attractionDataMap: Record<string, AttractionData[]> = {
  philadelphia_virginia: [
    {
      city: "Richmond 里士满",
      attractions: [
        { name: "弗吉尼亚美术博物馆", nameEn: "Virginia Museum of Fine Arts", type: "博物馆 Museum", description: "丰富的艺术收藏", address: "200 N Arthur Ashe Blvd, Richmond, VA 23220", phone: "(804) 340-1400", website: "https://vmfa.museum/" },
        { name: "梅蒙特公园", nameEn: "Maymont", type: "公园 Park", description: "历史悠久的庄园和花园", address: "1700 Hampton St, Richmond, VA 23220", phone: "(804) 525-9000", website: "https://maymont.org/" },
        { name: "爱伦·坡博物馆", nameEn: "The Poe Museum", type: "博物馆 Museum", description: "纪念著名作家爱伦·坡", address: "1914 E Main St, Richmond, VA 23223", phone: "(804) 648-5523", website: "http://www.poemuseum.org/" },
        { name: "里士满幽灵之旅", nameEn: "Haunts of Richmond - Shadows of Shockoe Tour", type: "旅游活动 Tour", description: "探索城市的鬼魂传说", address: "5 S 20th St, Richmond, VA 23223", phone: "(804) 543-3189", website: "https://hauntsofrichmond.com/" },
        { name: "运河漫步道", nameEn: "Canal Walk", type: "步道 Walkway", description: "沿河休闲步道", address: "1512 Canal Walk, Richmond, VA 23219", website: "https://venturerichmond.com/explore-downtown/riverfront-canal-walk/" },
        { name: "大科学球", nameEn: "The Grand Kugel", type: "科学展品 Science Exhibit", description: "互动科学装置", address: "2500 W Broad St, Richmond, VA 23220", phone: "(804) 864-1400", website: "https://www.atlasobscura.com/places/the-grand-kugel-richmond-virginia" },
        { name: "弗吉尼亚黑人历史博物馆", nameEn: "Black History Museum and Cultural Center of Virginia", type: "历史博物馆 History Museum", description: "非裔美国人历史文化", address: "122 W Leigh St, Richmond, VA 23220", phone: "(804) 780-9093", website: "http://blackhistorymuseum.org/" },
        { name: "弗吉尼亚州议会大厦", nameEn: "Virginia State Capitol", type: "历史建筑 Historic Building", description: "州政府所在地", address: "1000 Bank St, Richmond, VA 23218", phone: "(804) 698-1788", website: "http://www.virginiacapitol.gov/" },
        { name: "情人节博物馆", nameEn: "The Valentine", type: "历史博物馆 History Museum", description: "里士满历史展示", address: "1015 E Clay St, Richmond, VA 23219", phone: "(804) 649-0711", website: "http://www.thevalentine.org/" },
        { name: "美国内战博物馆", nameEn: "American Civil War Museum- Historic Tredegar", type: "战争博物馆 War Museum", description: "内战历史展示", address: "480 Tredegar St, Richmond, VA 23219", phone: "(804) 649-1861", website: "http://www.acwm.org/" },
        { name: "里士满儿童博物馆", nameEn: "Children's Museum of Richmond", type: "儿童博物馆 Children's Museum", description: "儿童互动体验", address: "2626 W Broad St, Richmond, VA 23220", phone: "(804) 474-7000", website: "http://www.cmorva.org/" },
        { name: "利比山公园", nameEn: "Libby Hill Park", type: "公园 Park", description: "城市观景点", address: "2801 E Franklin St, Richmond, VA 23223", phone: "(804) 646-0036" },
        { name: "纪念钟", nameEn: "Memorial Clock", type: "纪念碑 Memorial", description: "历史纪念建筑", address: "1003 E Cary St, Richmond, VA 23219" },
        { name: "弗吉尼亚大屠杀博物馆", nameEn: "Virginia Holocaust Museum", type: "历史博物馆 History Museum", description: "大屠杀历史教育", address: "2000 E Cary St, Richmond, VA 23223", phone: "(804) 257-5400", website: "http://www.vaholocaust.org/" },
        { name: "河滨运河游船", nameEn: "Riverfront Canal Cruises", type: "游船活动 Boat Tour", description: "运河观光游船", address: "139 Virginia St, Richmond, VA 23219", phone: "(804) 649-2800", website: "https://venturerichmond.com/our-services/riverfront-canal-cruises" },
        { name: "玛吉·沃克国家历史遗址", nameEn: "Maggie L Walker National Historic Site", type: "历史遗址 Historic Site", description: "非裔美国人企业家故居", address: "600 N 2nd St, Richmond, VA 23219", phone: "(804) 771-2017", website: "http://www.nps.gov/mawa" },
        { name: "艾格克罗夫特庄园", nameEn: "Agecroft Hall & Gardens", type: "历史庄园 Historic Manor", description: "都铎式建筑和花园", address: "4305 Sulgrave Rd, Richmond, VA 23221", phone: "(804) 353-4241", website: "http://www.agecrofthall.com/" },
        { name: "约翰·马歇尔故居", nameEn: "The John Marshall House", type: "历史建筑 Historic House", description: "首席大法官故居", address: "818 E Marshall St, Richmond, VA 23219", phone: "(804) 648-7998", website: "https://preservationvirginia.org/historic-sites/john-marshall-house/" },
        { name: "里士满国家战场公园游客中心", nameEn: "Richmond National Battlefield Park's Civil War Visitor Center", type: "游客中心 Visitor Center", description: "内战历史信息中心", address: "470 Tredegar St, Richmond, VA 23219", phone: "(804) 771-2145", website: "https://www.nps.gov/rich/planyourvisit/directions.htm" },
        { name: "威尔顿庄园博物馆", nameEn: "Wilton House Museum", type: "历史建筑 Historic House", description: "18世纪乔治亚风格建筑", address: "215 S Wilton Rd, Richmond, VA 23226", phone: "(804) 282-5936", website: "http://www.wiltonhousemuseum.org/" }
      ]
    },
    {
      city: "Petersburg 彼得斯堡",
      attractions: [
        { name: "彼得斯堡国家战场", nameEn: "Petersburg National Battlefield", type: "历史公园 Historic Park", description: "内战历史遗址", address: "Petersburg, VA 23803", phone: "(804) 732-3531", website: "http://www.nps.gov/pete/" },
        { name: "中心山庄园博物馆", nameEn: "Centre Hill Mansion-Museum", type: "博物馆 Museum", description: "历史悠久的庄园", address: "1 Centre Hill Ave, Petersburg, VA 23803", phone: "(804) 733-2401", website: "http://www.museumsofpetersburg.com/" },
        { name: "帕姆林历史公园", nameEn: "Pamplin Historical Park", type: "历史公园 Historic Park", description: "内战历史展示", address: "6125 Boydton Plank Rd, Petersburg, VA 23803", phone: "(804) 861-2408", website: "https://www.pamplinpark.org/" },
        { name: "彼得斯堡国家战场公园步道起点", nameEn: "Petersburg National Battlefield Park Trailhead", type: "步道入口 Trailhead", description: "徒步探索历史战场", address: "5001 Siege Rd, Petersburg, VA 23804", phone: "(804) 732-3531", website: "http://www.nps.gov/pete/index.htm" },
        { name: "士兵雕像", nameEn: "Soldier Statue", type: "纪念碑 Monument", description: "战争纪念雕像", address: "1529-1517, US-301 ALT, Petersburg, VA 23805" },
        { name: "传说公园", nameEn: "Legends Park", type: "公园 Park", description: "历史主题公园", address: "1614 Defense Rd, Petersburg, VA 23805", phone: "(804) 733-2394", website: "http://www.petersburgva.gov/Facilities/Facility/Details/Lee-Memorial-Park-1" },
        { name: "酒馆公园", nameEn: "Tavern Park", type: "公园 Park", description: "城市休闲公园", address: "Petersburg, VA 23803" },
        { name: "巴特西基金会", nameEn: "Battersea Foundation", type: "历史建筑 Historic Building", description: "历史建筑保护", address: "1289 Upper Appomattox St, Petersburg, VA 23803", phone: "(804) 732-9882", website: "http://www.batterseafound.org/" },
        { name: "李将军总部历史标记", nameEn: "General Lee's Headquarters Historical Marker", type: "历史标记 Historical Marker", description: "内战历史标记", address: "Petersburg, VA 23803", website: "https://www.hmdb.org/m.asp?m=17544" },
        { name: "交易所大楼和彼得斯堡游客中心", nameEn: "The Exchange Building and Petersburg Visitors Center", type: "游客中心 Visitor Center", description: "旅游信息服务", address: "15 W Bank St, Petersburg, VA 23803", phone: "(804) 835-9630" },
        { name: "杨树林国家公墓", nameEn: "Poplar Grove National Cemetery", type: "国家公墓 National Cemetery", description: "内战士兵墓地", address: "8005 Vaughan Rd, Petersburg, VA 23805", phone: "(804) 861-2488", website: "https://www.nps.gov/pete/learn/historyculture/poplar-grove-national-cemetery.htm" },
        { name: "机械翅膀涂鸦艺术", nameEn: "Graffiti Art Mechanical Wings", type: "街头艺术 Street Art", description: "当代艺术作品", address: "9 E Bank St, Petersburg, VA 23803" },
        { name: "彼得·琼斯贸易站", nameEn: "Peter Jones Trading Station", type: "历史遗址 Historic Site", description: "早期贸易历史", address: "600-698 N Market St, Petersburg, VA 23803", phone: "(800) 313-1434", website: "http://www.historicpetersburg.org/peter-jones-trading-station/" },
        { name: "布兰福德教堂和墓地游客中心", nameEn: "Blandford Church and Cemetery Visitor's Center", type: "历史教堂 Historic Church", description: "历史教堂和墓地", address: "111 Rochelle Ln, Petersburg, VA 23803", phone: "(804) 733-2396" },
        { name: "彼得斯堡传说历史公园和自然保护区", nameEn: "Petersburg Legends Historical Park and Nature Sanctuary", type: "历史公园 Historic Park", description: "历史和自然结合", address: "1614 Defense Rd, Petersburg, VA 23805" },
        { name: "杨树坪历史街区", nameEn: "Poplar Lawn Historic District", type: "历史街区 Historic District", description: "历史建筑群", address: "Petersburg, VA 23803" },
        { name: "墓碑屋", nameEn: "Tombstone House", type: "历史建筑 Historic Building", description: "独特的历史建筑", address: "1736 Youngs Rd, Petersburg, VA 23803" },
        { name: "紫罗兰银行博物馆", nameEn: "Violet Bank Museum", type: "博物馆 Museum", description: "殖民地时期历史", address: "303 Virginia Ave, Colonial Heights, VA 23834", phone: "(804) 520-9395", website: "https://www.colonialheightsva.gov/499/Violet-Bank" },
        { name: "马托克斯公园步道起点", nameEn: "Matoax Park Trailhead", type: "步道入口 Trailhead", description: "自然步道起点", address: "Petersburg, VA 23803" },
        { name: "埃特里克公园", nameEn: "Ettrick Park", type: "公园 Park", description: "社区休闲公园", address: "20400 Laurel Rd, Petersburg, VA 23803", phone: "(804) 706-2596" }
      ]
    },
    {
      city: "Charlottesville 夏洛茨维尔",
      attractions: [
        { name: "蒙蒂塞洛", nameEn: "Monticello", type: "历史建筑 Historic Site", description: "托马斯·杰斐逊故居", address: "1050 Monticello Loop, Charlottesville, VA 22902", phone: "(434) 984-9800", website: "https://www.monticello.org/" },
        { name: "弗吉尼亚发现博物馆", nameEn: "Virginia Discovery Museum", type: "博物馆 Museum", description: "儿童互动博物馆", address: "524 E Main St, Charlottesville, VA 22902", phone: "(434) 977-1025", website: "https://vadm.org/" },
        { name: "弗拉林艺术博物馆", nameEn: "The Fralin Museum of Art at the University of Virginia", type: "艺术博物馆 Art Museum", description: "弗吉尼亚大学艺术博物馆", address: "155 Rugby Rd, Charlottesville, VA 22904", phone: "(434) 924-3592", website: "https://uvafralinartmuseum.virginia.edu/" },
        { name: "IX艺术公园", nameEn: "Ix Art Park", type: "艺术公园 Art Park", description: "当代艺术和文化空间", address: "522 2nd St SE D, Charlottesville, VA 22902", phone: "(434) 207-2964", website: "https://www.ixartpark.org/" },
        { name: "圆形大厅", nameEn: "The Rotunda", type: "历史建筑 Historic Building", description: "弗吉尼亚大学标志性建筑", address: "1826 University Ave, Charlottesville, VA 22904", phone: "(434) 924-7969", website: "http://rotunda.virginia.edu/" },
        { name: "言论自由墙", nameEn: "Freedom of Speech Wall", type: "公共艺术 Public Art", description: "表达自由的象征", address: "605 E Main St, Charlottesville, VA 22902" },
        { name: "阿尔伯马尔-夏洛茨维尔历史学会", nameEn: "Albemarle Charlottesville Historical Society", type: "历史学会 Historical Society", description: "当地历史文化保护", address: "200 2nd St NE, Charlottesville, VA 22902", phone: "(434) 296-1492", website: "http://www.albemarlehistory.org/" },
        { name: "夏洛茨维尔会议和游客局", nameEn: "Administrative Offices of the Charlottesville Albemarle Convention & Visitors Bureau", type: "游客中心 Visitor Center", description: "旅游信息服务", address: "501 Faulconer Dr, Charlottesville, VA 22903", phone: "(434) 293-6789", website: "http://www.visitcharlottesville.org/" },
        { name: "克鲁格-吕厄原住民艺术收藏馆", nameEn: "Kluge-Ruhe Aboriginal Art Collection of the University of Virginia", type: "艺术博物馆 Art Museum", description: "澳洲原住民艺术", address: "400 Worrell Dr, Charlottesville, VA 22911", phone: "(434) 243-8500", website: "https://kluge-ruhe.org/" },
        { name: "桑德斯-蒙蒂塞洛步道", nameEn: "Saunders-Monticello Trail", type: "步道 Trail", description: "历史徒步路线", address: "503 Thomas Jefferson Pkwy, Charlottesville, VA 22902", phone: "(434) 984-9822", website: "http://www.monticello.org/site/visit/kemper-park" },
        { name: "大草坪", nameEn: "The Lawn", type: "校园地标 Campus Landmark", description: "弗吉尼亚大学历史核心", address: "400 Emmet St S, Charlottesville, VA 22903", phone: "(434) 924-0311", website: "https://housing.virginia.edu/area/1176" },
        { name: "伯克利艺术墙", nameEn: "Berkeley Art Wall", type: "公共艺术 Public Art", description: "社区艺术展示", address: "2118 Dominion Dr, Charlottesville, VA 22901" },
        { name: "麦金太尔公园", nameEn: "McIntire Park", type: "公园 Park", description: "大型城市公园", address: "375 US-250 BYP, Charlottesville, VA 22901", phone: "(434) 970-3589", website: "https://www.charlottesville.gov/Facilities/Facility/Details/McIntire-Park-25" },
        { name: "利安德·麦考密克天文台", nameEn: "Leander McCormick Observatory", type: "天文台 Observatory", description: "天文观测和教育", address: "600 McCormick Rd, Charlottesville, VA 22904", phone: "(434) 243-1885" },
        { name: "蓝岭疗养院", nameEn: "Blue Ridge Sanitarium", type: "历史建筑 Historic Building", description: "废弃的历史建筑", address: "Unnamed Road, Charlottesville, VA 22902" },
        { name: "河景公园", nameEn: "Riverview Park", type: "公园 Park", description: "河边休闲公园", address: "1909 Chesapeake St, Charlottesville, VA 22902", phone: "(434) 970-3333", website: "https://www.charlottesville.gov/facilities/facility/details/Riverview-Park-61" },
        { name: "锯齿山自然保护区", nameEn: "Ragged Mountain Nature Area", type: "自然保护区 Nature Area", description: "徒步和自然观察", address: "1730 Reservoir Rd, Charlottesville, VA 22902", website: "https://www.charlottesville.gov/Facilities/Facility/Details/Ragged-Mountain-Natural-Area-40" },
        { name: "笔公园", nameEn: "Pen Park", type: "公园 Park", description: "运动和休闲设施", address: "1300 Pen Park Rd, Charlottesville, VA 22901", phone: "(434) 970-3589", website: "https://www.charlottesville.gov/Facilities/Facility/Details/Pen-Park-26" },
        { name: "森林山公园", nameEn: "Forest Hills Park", type: "公园 Park", description: "社区休闲公园", address: "1022 Forest Hills Ave, Charlottesville, VA 22903", phone: "(434) 970-3260", website: "https://www.charlottesville.gov/Facilities/Facility/Details/Forest-Hills-Park-23" },
        { name: "绿叶公园", nameEn: "Greenleaf Park", type: "公园 Park", description: "家庭友好公园", address: "1598 Rose Hill Dr, Charlottesville, VA 22903", phone: "(434) 970-3021", website: "https://www.charlottesville.gov/facilities/facility/details/Greenleaf-Park-24" }
      ]
    }
  ],
  vegas_santa_maria: [
    {
      city: "Santa Maria 圣玛丽亚",
      attractions: [
        { name: "圣玛丽亚谷发现博物馆", nameEn: "Santa Maria Valley Discovery Museum", type: "博物馆 Museum", description: "互动式儿童博物馆", address: "705 S McClelland St, Santa Maria, CA 93454", phone: "(805) 928-8414", website: "http://www.smvdiscoverymuseum.org/" },
        { name: "圣玛丽亚飞行博物馆", nameEn: "Santa Maria Museum of Flight", type: "航空博物馆 Aviation Museum", description: "航空历史展示", address: "3015 Airpark Dr, Santa Maria, CA 93455", phone: "(805) 922-8758", website: "https://www.smmuseumofflight.com/" },
        { name: "圣玛丽亚历史博物馆", nameEn: "Santa Maria Historical Museum", type: "历史博物馆 History Museum", description: "当地历史文化", address: "616 S Broadway, Santa Maria, CA 93454", phone: "(805) 922-3130", website: "http://santamariahistory.com/" },
        { name: "自然历史博物馆", nameEn: "Natural History Museum", type: "自然博物馆 Natural History Museum", description: "自然科学展示", address: "412 S McClelland St, Santa Maria, CA 93454", phone: "(805) 614-0806", website: "https://www.smnaturalhistory.org/" },
        { name: "拉塞尔公园", nameEn: "Russell Park", type: "公园 Park", description: "城市休闲公园", address: "1000 W Church St, Santa Maria, CA 93458", phone: "(805) 925-0951" },
        { name: "吉姆·梅公园", nameEn: "Jim May Park", type: "公园 Park", description: "社区运动公园", address: "809 Stanford Dr, Santa Maria, CA 93454", phone: "(805) 925-0951" },
        { name: "洛斯弗洛雷斯牧场公园", nameEn: "Los Flores Ranch Park", type: "牧场公园 Ranch Park", description: "乡村风格公园", address: "6245 Dominion Rd, Santa Maria, CA 93454", phone: "(805) 925-0951" },
        { name: "冒险野生动物园恐龙仓库", nameEn: "Adventure Safaris Dinosaur Warehouse", type: "主题展览 Theme Exhibition", description: "恐龙主题体验", address: "1360 W McCoy Ln #11, Santa Maria, CA 93455", phone: "(805) 588-3353", website: "https://www.centralcoastdinosaurs.com/" },
        { name: "普赖斯克公园", nameEn: "Preisker Park", type: "公园 Park", description: "家庭休闲公园", address: "330 Hidden Pines Way, Santa Maria, CA 93458", phone: "(805) 925-0951" },
        { name: "先锋公园", nameEn: "Pioneer Park", type: "公园 Park", description: "历史主题公园", address: "1150 W Foster Rd, Santa Maria, CA 93455" },
        { name: "普雷斯克酒庄", nameEn: "Presqu'ile Winery", type: "酒庄 Winery", description: "精品葡萄酒庄", address: "5391 Presquile Dr, Santa Maria, CA 93455", phone: "(805) 937-8110", website: "https://www.presquilewine.com/" },
        { name: "圣玛丽亚轰鸣游乐场", nameEn: "Boomers Santa Maria", type: "游乐场 Amusement Park", description: "家庭娱乐中心", address: "2250 Preisker Ln, Santa Maria, CA 93458", phone: "(805) 928-4942", website: "https://boomersparks.com/santamaria" },
        { name: "金色海岸酒庄", nameEn: "Costa de Oro Winery", type: "酒庄 Winery", description: "当地精品酒庄", address: "1331 Nicholson Ave, Santa Maria, CA 93454", phone: "(805) 922-1468", website: "https://www.costadeorowines.com/" },
        { name: "圣玛丽亚市", nameEn: "Santa Maria, CA", type: "城市地标 City Landmark", description: "城市标志", address: "Nipomo, CA 93444" },
        { name: "圣玛丽亚谷历史学会", nameEn: "Santa Maria Valley Historical Society", type: "历史学会 Historical Society", description: "当地历史保护", address: "616 S Broadway, Santa Maria, CA 93454", phone: "(805) 922-3130", website: "https://santamariahistory.com/about.html" },
        { name: "赖斯公园", nameEn: "Rice Park", type: "公园 Park", description: "社区公园", address: "700 E Sunset Ave, Santa Maria, CA 93454", phone: "(805) 925-0951" },
        { name: "奥克利公园", nameEn: "Oakley Park", type: "公园 Park", description: "休闲运动公园", address: "119 010-019, Santa Maria, CA 93458", phone: "(805) 925-0951" }
      ]
    }
  ],
  ithaca_newark: [
    {
      city: "Newark 纽瓦克",
      attractions: [
        { name: "纽瓦克艺术博物馆", nameEn: "The Newark Museum of Art", type: "艺术博物馆 Art Museum", description: "新泽西州最大的博物馆", address: "49 Washington St, Newark, NJ 07102", phone: "(973) 596-6550", website: "http://www.newarkmuseumart.org/" },
        { name: "军事公园", nameEn: "Military Park", type: "公园 Park", description: "市中心历史公园", address: "51 Park Pl, Newark, NJ 07102", phone: "(973) 900-5800" },
        { name: "布兰奇布鲁克公园", nameEn: "Branch Brook Park", type: "公园 Park", description: "樱花盛开的大型公园", address: "Park Avenue, Lake St, Newark, NJ 07104", phone: "(973) 268-3500", website: "http://www.essexcountyparks.org/parks/branch-brook-park" },
        { name: "威奎阿克公园", nameEn: "Weequahic Park", type: "公园 Park", description: "湖边休闲公园", address: "Elizabeth Ave &, Meeker Ave, Newark, NJ 07112", phone: "(973) 268-3500", website: "http://www.essex-countynj.org/p/index.php?section=parks/sites/we#top" },
        { name: "纽瓦克河滨公园橙色棍", nameEn: "Newark Riverfront Park, Orange Sticks", type: "河滨公园 Riverfront Park", description: "河边艺术装置", address: "727 Raymond Blvd, Newark, NJ 07105" },
        { name: "新泽西历史学会", nameEn: "New Jersey Historical Society", type: "历史博物馆 Historical Society", description: "新泽西州历史文化", address: "52 Park Pl, Newark, NJ 07102", phone: "(973) 596-8500", website: "http://www.jerseyhistory.org/" },
        { name: "新泽西犹太博物馆", nameEn: "The Jewish Museum of New Jersey", type: "文化博物馆 Cultural Museum", description: "犹太历史和文化", address: "145 Broadway, Newark, NJ 07104", phone: "(973) 485-2609", website: "http://www.jewishmuseumnj.org/" },
        { name: "纽瓦克河滨公园索姆街入口", nameEn: "Newark Riverfront Park - Somme Street Entrance", type: "公园入口 Park Entrance", description: "河滨公园主入口", address: "709 Raymond Blvd, Newark, NJ 07105", phone: "(201) 341-8311", website: "https://newarkcityparksfoundation.com/" },
        { name: "退伍军人纪念公园", nameEn: "Veterans Memorial Park", type: "纪念公园 Memorial Park", description: "向退伍军人致敬", address: "W Market St & Wickliffe Street, Newark, NJ 07102", phone: "(973) 268-3500", website: "http://www.essexcountyparks.org/parks/veterans-memorial-park" },
        { name: "杰西·艾伦公园", nameEn: "Jesse Allen Park", type: "社区公园 Community Park", description: "社区休闲空间", address: "Muhammad Ali Ave, Newark, NJ 07108", phone: "(973) 733-6454", website: "https://www.newarknj.gov/departments/rcass" },
        { name: "德雷福斯天文馆", nameEn: "Dreyfuss Planetarium", type: "天文馆 Planetarium", description: "天文教育和观察", address: "49 Washington St Dreyfuss Planetarium, Newark, NJ 07102", phone: "(973) 596-6529", website: "https://newarkmuseumart.org/event/planetarium-life" },
        { name: "前保罗·兰迪姆二世之家", nameEn: "Ex-Casa do Paulo Landim II", type: "历史建筑 Historic Building", description: "历史住宅", address: "311 E Kinney St, Newark, NJ 07105" },
        { name: "纽瓦克保护和地标委员会", nameEn: "Newark Preservation & Landmark", type: "保护组织 Preservation Organization", description: "历史建筑保护", address: "69 Washington St, Newark, NJ 07102", phone: "(973) 622-4910", website: "https://www.newarklandmarks.org/" },
        { name: "河岸公园", nameEn: "Riverbank Park", type: "河岸公园 Riverbank Park", description: "河边休闲区", address: "Market St & VanBuren Street, Newark, NJ 07105", phone: "(973) 268-3500", website: "https://www.essexcountyparks.org/parks/riverbank-park" },
        { name: "樱花欢迎中心", nameEn: "Cherry Blossom Welcome Center", type: "游客中心 Welcome Center", description: "樱花节信息中心", address: "Branch Brook Park Dr, Newark, NJ 07104", phone: "(973) 268-3500", website: "http://www.essexcountyparks.org/parks/branch-brook-park" },
        { name: "费根斯潘大厦", nameEn: "The Feigenspan Mansion", type: "历史大厦 Historic Mansion", description: "19世纪豪宅", address: "710 Dr Martin Luther King Jr Blvd, Newark, NJ 07102", phone: "(973) 274-0995", website: "https://www.nj.gov/dca/njht/funded/sitedetails/feigenspan_mansion.shtml" },
        { name: "埃塞克斯县河滨公园", nameEn: "Essex County Riverfront Park", type: "县立公园 County Park", description: "大型河滨公园", address: "1-3 Brill St, Newark, NJ 07105", phone: "(973) 268-3500", website: "https://www.essexcountyparks.org/parks/riverfront-park" },
        { name: "爱丽丝·兰森·德雷福斯纪念花园", nameEn: "Alice Ransom Dreyfuss Memorial Garden", type: "纪念花园 Memorial Garden", description: "纪念花园", address: "Newark, NJ 07102" },
        { name: "保罗·罗伯逊画廊", nameEn: "Paul Robeson Galleries, Rutgers University - Newark", type: "大学画廊 University Gallery", description: "罗格斯大学艺术展览", address: "350 Dr Martin Luther King Jr Blvd, Newark, NJ 07103", phone: "(973) 353-0615", website: "https://paulrobesongalleries.rutgers.edu/" },
        { name: "威奎阿克公园(南区)", nameEn: "Weequahic Park", type: "公园 Park", description: "公园南部区域", address: "1 Thomas Carmichael Dr, Newark, NJ 07114", phone: "(973) 926-2520", website: "http://www.essexcountyparks.org/" }
      ]
    }
  ]
};


// 真实数据 - 交通信息
const transportDataMap: Record<string, TransportData> = {
  philadelphia_virginia: {
    route: "费城 - 弗吉尼亚州",
    routeEn: "Philadelphia - Virginia",
    options: [
      // 费城到里士满
      { type: "飞机 ✈️", typeEn: "Flight", duration: "1小时1分", price: "$73-97", description: "费城到里士满直飞，航班号F3728234/F3730367" },
      { type: "自驾 🚗", typeEn: "Self-driving", duration: "4小时2分", price: "$20", description: "费城到里士满，距离407公里" },
      { type: "出租车 🚕", typeEn: "Taxi", duration: "4小时2分", price: "$407", description: "费城到里士满，距离407公里" },
      
      // 里士满到彼得斯堡
      { type: "自驾 🚗", typeEn: "Self-driving", duration: "25分钟", price: "$1", description: "里士满到彼得斯堡，距离38公里" },
      { type: "出租车 🚕", typeEn: "Taxi", duration: "25分钟", price: "$38", description: "里士满到彼得斯堡，距离38公里" },
      
      // 彼得斯堡到夏洛茨维尔
      { type: "自驾 🚗", typeEn: "Self-driving", duration: "1小时30分", price: "$7", description: "彼得斯堡到夏洛茨维尔，距离152公里" },
      { type: "出租车 🚕", typeEn: "Taxi", duration: "1小时30分", price: "$152", description: "彼得斯堡到夏洛茨维尔，距离152公里" },
      
      // 夏洛茨维尔回费城
      { type: "自驾 🚗", typeEn: "Self-driving", duration: "4小时24分", price: "$20", description: "夏洛茨维尔到费城，距离411公里" },
      { type: "出租车 🚕", typeEn: "Taxi", duration: "4小时24分", price: "$411", description: "夏洛茨维尔到费城，距离411公里" }
    ]
  },
  vegas_santa_maria: {
    route: "拉斯维加斯 - 圣玛丽亚",
    routeEn: "Las Vegas - Santa Maria",
    options: [
      // 拉斯维加斯到圣玛丽亚
      { type: "自驾 🚗", typeEn: "Self-driving", duration: "6小时17分", price: "$31", description: "拉斯维加斯到圣玛丽亚，距离634公里" },
      { type: "出租车 🚕", typeEn: "Taxi", duration: "6小时17分", price: "$634", description: "拉斯维加斯到圣玛丽亚，距离634公里" },
      
      // 圣玛丽亚回拉斯维加斯
      { type: "自驾 🚗", typeEn: "Self-driving", duration: "6小时19分", price: "$31", description: "圣玛丽亚到拉斯维加斯，距离636公里" },
      { type: "出租车 🚕", typeEn: "Taxi", duration: "6小时19分", price: "$636", description: "圣玛丽亚到拉斯维加斯，距离636公里" },
      
      // 注意：数据显示没有直飞航班
      { type: "飞机 ✈️", typeEn: "Flight", duration: "暂无直飞", price: "N/A", description: "拉斯维加斯到圣玛丽亚暂无直飞航班" }
    ]
  },
  ithaca_newark: {
    route: "伊萨卡 - 纽瓦克",
    routeEn: "Ithaca - Newark",
    options: [
      // 伊萨卡到纽瓦克
      { type: "飞机 ✈️", typeEn: "Flight", duration: "1小时35分-1小时42分", price: "$62", description: "伊萨卡到纽瓦克，航班号F3924332/F3924359，距离172公里" },
      { type: "自驾 🚗", typeEn: "Self-driving", duration: "3小时38分", price: "$17", description: "伊萨卡到纽瓦克，距离343公里" },
      { type: "出租车 🚕", typeEn: "Taxi", duration: "3小时38分", price: "$343", description: "伊萨卡到纽瓦克，距离343公里" },
      
      // 纽瓦克回伊萨卡
      { type: "飞机 ✈️", typeEn: "Flight", duration: "56分钟-1小时2分", price: "$42-83", description: "纽瓦克到伊萨卡，航班号F3923347/F3923348，距离172公里" },
      { type: "自驾 🚗", typeEn: "Self-driving", duration: "3小时43分", price: "$17", description: "纽瓦克到伊萨卡，距离343公里" },
      { type: "出租车 🚕", typeEn: "Taxi", duration: "3小时43分", price: "$343", description: "纽瓦克到伊萨卡，距离343公里" }
    ]
  }
};

// 真实数据 - 完整餐厅信息（修正版本）
const restaurantDataMap: Record<string, RestaurantData[]> = {
  philadelphia_virginia: [
    {
      city: "Richmond 里士满",
      restaurants: [
        { name: "广州中餐厅", nameEn: "Guang Zhou Chinese Restaurant", cuisine: "中式茶点 Chinese Tea", avgCost: 84, rating: 3.9 },
        { name: "沙丘鸟餐厅酒廊", nameEn: "Sandpiper Restaurant & Lounge", cuisine: "海鲜茶饮 Seafood Tea", avgCost: 20, rating: 3.6 },
        { name: "天堂餐厅", nameEn: "Paradise", cuisine: "意式披萨 Italian Pizza", avgCost: 80, rating: 3.6 },
        { name: "欢迎餐厅", nameEn: "Welcome", cuisine: "法式印度菜 French Indian", avgCost: 86, rating: 2.9 },
        { name: "完美烘焙", nameEn: "Perfect Bake", cuisine: "美式烘焙 American Bakery", avgCost: 33, rating: 3.5 },
        { name: "妈妈厨房", nameEn: "Mother's Kitchen", cuisine: "中式墨西哥菜 Chinese Mexican", avgCost: 46, rating: 0.0 },
        { name: "整夜吃", nameEn: "Eat All Nite", cuisine: "中式快餐 Chinese Fast Food", avgCost: 55, rating: 3.2 },
        { name: "糖艺工坊", nameEn: "Sugarcraft Patisserie", cuisine: "法式甜品 French Desserts", avgCost: 38, rating: 3.3 },
        { name: "索娜中餐", nameEn: "Sona Chinese", cuisine: "咖啡披萨 Cafe Pizza", avgCost: 79, rating: 2.8 },
        { name: "你！中国", nameEn: "Yo! China", cuisine: "美式地中海 American Mediterranean", avgCost: 36, rating: 3.5 },
        { name: "引用-折衷酒吧", nameEn: "Quote - The Eclectic Bar and Lounge", cuisine: "披萨快餐 Pizza Fast Food", avgCost: 49, rating: 3.5 },
        { name: "防务烘焙店", nameEn: "Defence Bakery", cuisine: "烧烤海鲜 BBQ Seafood", avgCost: 36, rating: 4.1 },
        { name: "31号餐厅", nameEn: "Number 31", cuisine: "中式墨西哥菜 Chinese Mexican", avgCost: 97, rating: 4.2 },
        { name: "米尔奇玛萨拉咖啡", nameEn: "Mirch Masala MM Cafe", cuisine: "印度海鲜 Indian Seafood", avgCost: 32, rating: 3.7 },
        { name: "克里希纳果汁角", nameEn: "Krishna Juice & Shakes Corner", cuisine: "茶饮烘焙 Tea Bakery", avgCost: 29, rating: 0.0 },
        { name: "美食角", nameEn: "Nice Food Corner", cuisine: "海鲜快餐 Seafood Fast Food", avgCost: 90, rating: 0.0 },
        { name: "松饼", nameEn: "Muffins", cuisine: "中式披萨 Chinese Pizza", avgCost: 83, rating: 1.9 },
        { name: "塔卡餐厅", nameEn: "Takkar Dhaba", cuisine: "印度海鲜 Indian Seafood", avgCost: 45, rating: 2.6 },
        { name: "品质孟加拉甜品", nameEn: "Kwality Bengali Sweets", cuisine: "茶饮甜品 Tea Desserts", avgCost: 36, rating: 2.9 },
        { name: "现场", nameEn: "The Spot", cuisine: "印度烧烤 Indian BBQ", avgCost: 17, rating: 3.5 },
        { name: "大龙中餐厅", nameEn: "Big Dragon", cuisine: "中式美式 Chinese American", avgCost: 72, rating: 3.1 },
        { name: "奇丹巴拉姆新马德拉斯酒店", nameEn: "Chidambaram's New Madras Hotel", cuisine: "中式烧烤 Chinese BBQ", avgCost: 33, rating: 3.8 },
        { name: "南印度快餐", nameEn: "South Indian Fast Food", cuisine: "中式烧烤 Chinese BBQ", avgCost: 83, rating: 3.3 },
        { name: "纯净厨房", nameEn: "The Pure Kitchen", cuisine: "意式中式 Italian Chinese", avgCost: 91, rating: 0.0 },
        { name: "蒂普苏丹鸡肉点", nameEn: "Tipu Sultan Chicken Point", cuisine: "中式意式 Chinese Italian", avgCost: 63, rating: 3.2 },
        { name: "安纳普尔纳食品点", nameEn: "Annapurna Food Point", cuisine: "地中海烧烤 Mediterranean BBQ", avgCost: 27, rating: 0.0 },
        { name: "萨加拉特纳", nameEn: "Sagar Ratna", cuisine: "法式披萨 French Pizza", avgCost: 27, rating: 2.7 },
        { name: "杰阿奥杰乔勒巴图雷", nameEn: "Jee Aao Jee Chole Bhature", cuisine: "披萨烘焙 Pizza Bakery", avgCost: 99, rating: 0.0 },
        { name: "杰作咖啡", nameEn: "The Masterpiece Cafe", cuisine: "墨西哥快餐 Mexican Fast Food", avgCost: 82, rating: 3.5 },
        { name: "布达佩斯厨房酒吧", nameEn: "Budapest Kitchen & Bar", cuisine: "地中海甜品 Mediterranean Desserts", avgCost: 65, rating: 3.0 },
        { name: "阿尔塔杰沙明鸡肉点", nameEn: "Al-Taj Shamim Chicken Point", cuisine: "地中海海鲜 Mediterranean Seafood", avgCost: 81, rating: 0.0 },
        { name: "圣吉米尼亚诺帝国", nameEn: "San Gimignano - The Imperial", cuisine: "美式海鲜 American Seafood", avgCost: 78, rating: 3.7 },
        { name: "沙希穆拉达巴迪鸡肉饭", nameEn: "Shahi Muradabadi Chicken Biryani", cuisine: "墨西哥披萨 Mexican Pizza", avgCost: 55, rating: 0.0 },
        { name: "卷王", nameEn: "RollsKing", cuisine: "美式快餐 American Fast Food", avgCost: 54, rating: 3.9 },
        { name: "查克纳", nameEn: "Chakna", cuisine: "美式烧烤 American BBQ", avgCost: 96, rating: 2.7 },
        { name: "诺伊达蛋糕在线", nameEn: "Noida Cakes Online", cuisine: "海鲜甜品 Seafood Desserts", avgCost: 92, rating: 3.0 },
        { name: "狂牛辣冲", nameEn: "Raging Bull - The Spicy Punch", cuisine: "地中海茶饮 Mediterranean Tea", avgCost: 72, rating: 0.0 },
        { name: "悬挂蝙蝠", nameEn: "The Hanging Bat", cuisine: "意式海鲜 Italian Seafood", avgCost: 51, rating: 3.5 }
      ]
    },
    {
      city: "Petersburg 彼得斯堡",
      restaurants: [
        { name: "5只小猪", nameEn: "5 Little Pigs", cuisine: "法式甜品 French Desserts", avgCost: 46, rating: 4.1 },
        { name: "J的家常菜", nameEn: "J's Homestyle Cooking", cuisine: "快餐烧烤 Fast Food BBQ", avgCost: 63, rating: 3.6 },
        { name: "逗我茶屋", nameEn: "Tea'se Me - Rooftop Tea Boutique", cuisine: "茶饮甜品 Tea Desserts", avgCost: 49, rating: 4.2 },
        { name: "茶点", nameEn: "Chai Point", cuisine: "咖啡披萨 Cafe Pizza", avgCost: 76, rating: 3.7 },
        { name: "烘焙宝贝", nameEn: "Bake-a-boo", cuisine: "茶饮烧烤 Tea BBQ", avgCost: 40, rating: 3.7 },
        { name: "银冠", nameEn: "Silver Crown", cuisine: "印度海鲜 Indian Seafood", avgCost: 54, rating: 2.5 },
        { name: "拉朱瓦什诺阿姆利萨里餐厅", nameEn: "Raju Vaishno Amritsari Dhaba", cuisine: "地中海海鲜 Mediterranean Seafood", avgCost: 83, rating: 0.0 },
        { name: "午夜经文", nameEn: "Midnight Sutra", cuisine: "印度甜品 Indian Desserts", avgCost: 65, rating: 3.0 },
        { name: "柠檬鸡", nameEn: "Lemon Chick", cuisine: "中式海鲜 Chinese Seafood", avgCost: 34, rating: 0.0 },
        { name: "零食吧", nameEn: "Snack Bar", cuisine: "法式印度咖啡 French Indian Cafe", avgCost: 82, rating: 3.0 },
        { name: "我的酒吧餐厅", nameEn: "My Bar Lounge & Restaurant", cuisine: "法式印度海鲜 French Indian Seafood", avgCost: 37, rating: 2.7 },
        { name: "17度食品服务", nameEn: "17 Degree Food Service", cuisine: "海鲜快餐 Seafood Fast Food", avgCost: 66, rating: 0.0 },
        { name: "奈韦德亚姆", nameEn: "Naivedyam", cuisine: "中式烧烤 Chinese BBQ", avgCost: 49, rating: 3.6 },
        { name: "卡蒂卷屋", nameEn: "Kati Roll Cottage", cuisine: "烘焙海鲜 Bakery Seafood", avgCost: 60, rating: 3.5 },
        { name: "拉杰南印度食品", nameEn: "Raj South Indian Food", cuisine: "法式墨西哥 French Mexican", avgCost: 67, rating: 3.0 },
        { name: "顺便说一下", nameEn: "BTW", cuisine: "咖啡快餐 Cafe Fast Food", avgCost: 90, rating: 3.3 },
        { name: "食物思考", nameEn: "Food For Thought", cuisine: "茶饮甜品 Tea Desserts", avgCost: 24, rating: 3.8 },
        { name: "阿曼瓦什诺餐厅", nameEn: "Aman Vaishno Dhaba", cuisine: "烘焙海鲜 Bakery Seafood", avgCost: 71, rating: 0.0 },
        { name: "阿努潘酒店", nameEn: "Anupam Hotel", cuisine: "意式烧烤 Italian BBQ", avgCost: 81, rating: 0.0 },
        { name: "管道与炒作", nameEn: "Pipes & Hipes", cuisine: "意式印度 Italian Indian", avgCost: 22, rating: 3.0 },
        { name: "阿普尼拉索伊", nameEn: "Apni Rasoi", cuisine: "地中海烧烤 Mediterranean BBQ", avgCost: 94, rating: 0.0 },
        { name: "奥贝罗伊比尔亚尼", nameEn: "Oberoi Biryani", cuisine: "法式美式 French American", avgCost: 96, rating: 2.6 },
        { name: "加尔比斯特罗咖啡", nameEn: "Ghar Bistro Cafe", cuisine: "咖啡披萨 Cafe Pizza", avgCost: 83, rating: 4.4 },
        { name: "哈根达斯", nameEn: "Häagen-Dazs", cuisine: "美式甜品 American Desserts", avgCost: 23, rating: 4.0 },
        { name: "金先生", nameEn: "Mr. Gold", cuisine: "法式地中海 French Mediterranean", avgCost: 36, rating: 0.0 },
        { name: "鸡肉烧烤", nameEn: "Chick N Grills", cuisine: "意式快餐 Italian Fast Food", avgCost: 63, rating: 0.0 },
        { name: "里克酒吧-泰姬陵酒店", nameEn: "Ricks Bar - The Taj Mahal Hotel", cuisine: "地中海快餐 Mediterranean Fast Food", avgCost: 29, rating: 3.6 },
        { name: "必胜客", nameEn: "Pizza Hut", cuisine: "法式烧烤 French BBQ", avgCost: 56, rating: 2.4 },
        { name: "黑马中餐", nameEn: "Hema Chinese Foods", cuisine: "意式海鲜 Italian Seafood", avgCost: 68, rating: 3.3 },
        { name: "亚洲七快车", nameEn: "Asia Seven Express", cuisine: "法式地中海 French Mediterranean", avgCost: 76, rating: 0.0 },
        { name: "巴斯金罗宾斯", nameEn: "Baskin Robbins", cuisine: "地中海海鲜 Mediterranean Seafood", avgCost: 56, rating: 0.0 },
        { name: "B巴瓦奇餐厅", nameEn: "B Bawarchi Restaurant", cuisine: "意式烧烤 Italian BBQ", avgCost: 85, rating: 0.0 },
        { name: "纳泽尔食品", nameEn: "Nazeer Foods", cuisine: "墨西哥披萨 Mexican Pizza", avgCost: 58, rating: 2.3 },
        { name: "热辣", nameEn: "Hot & Spicy", cuisine: "咖啡快餐 Cafe Fast Food", avgCost: 12, rating: 2.9 },
        { name: "橄榄餐厅", nameEn: "Olive", cuisine: "意式烧烤 Italian BBQ", avgCost: 85, rating: 4.2 },
        { name: "扎克餐厅", nameEn: "Zaoq", cuisine: "中式美式 Chinese American", avgCost: 24, rating: 4.2 }
      ]
    },
    {
      city: "Charlottesville 夏洛茨维尔",
      restaurants: [
        { name: "妈妈鱼屋", nameEn: "Mama's Fish House", cuisine: "茶饮披萨 Tea Pizza", avgCost: 63, rating: 4.9 },
        { name: "安德烈餐厅", nameEn: "Restaurant Andre", cuisine: "茶饮烧烤 Tea BBQ", avgCost: 250, rating: 3.8 },
        { name: "达美乐披萨", nameEn: "Domino's Pizza", cuisine: "中式印度烧烤 Chinese Indian BBQ", avgCost: 53, rating: 2.8 },
        { name: "高松餐厅", nameEn: "Takamaka", cuisine: "茶饮披萨 Tea Pizza", avgCost: 72, rating: 3.9 },
        { name: "达瓦特伊什克", nameEn: "Dawat-e-Ishq", cuisine: "意式烧烤 Italian BBQ", avgCost: 26, rating: 3.3 },
        { name: "萤火虫餐厅", nameEn: "Firefly", cuisine: "披萨烘焙 Pizza Bakery", avgCost: 30, rating: 0.0 },
        { name: "舌头扭转者", nameEn: "The Tongue Twister", cuisine: "法式海鲜 French Seafood", avgCost: 81, rating: 3.4 },
        { name: "56弗雷斯卡", nameEn: "56 Fresca", cuisine: "法式印度海鲜 French Indian Seafood", avgCost: 95, rating: 3.7 },
        { name: "茶壶", nameEn: "Tpot", cuisine: "墨西哥烧烤 Mexican BBQ", avgCost: 35, rating: 0.0 },
        { name: "卡姆德努家庭角", nameEn: "Kamdhenu Family Corner", cuisine: "法式披萨烧烤 French Pizza BBQ", avgCost: 69, rating: 2.8 },
        { name: "博阿村", nameEn: "Boa Village", cuisine: "意式海鲜 Italian Seafood", avgCost: 46, rating: 4.0 },
        { name: "蛋糕中央", nameEn: "Cake Central - Premier Cake Design Studio", cuisine: "美式烧烤 American BBQ", avgCost: 21, rating: 3.4 },
        { name: "瓦什诺素食餐厅", nameEn: "A Vaishno Bhojnalaya", cuisine: "地中海披萨 Mediterranean Pizza", avgCost: 32, rating: 3.1 },
        { name: "蓝牛咖啡", nameEn: "Blue Bull Cafe", cuisine: "法式披萨 French Pizza", avgCost: 12, rating: 2.8 },
        { name: "达巴尔阿瓦德", nameEn: "Darbar E Awadh", cuisine: "法式烧烤 French BBQ", avgCost: 63, rating: 3.2 },
        { name: "桑贾楚拉宝贝达", nameEn: "Sanjha Chulah Babe Da", cuisine: "地中海烘焙 Mediterranean Bakery", avgCost: 76, rating: 0.0 },
        { name: "烘焙坏蛋", nameEn: "Baking Bad", cuisine: "美式海鲜 American Seafood", avgCost: 22, rating: 3.8 },
        { name: "吉亚尼", nameEn: "Giani", cuisine: "咖啡海鲜 Cafe Seafood", avgCost: 54, rating: 3.3 },
        { name: "马德拉斯咖啡", nameEn: "Madras Cafe", cuisine: "披萨快餐 Pizza Fast Food", avgCost: 15, rating: 3.2 },
        { name: "PS中泰餐厅", nameEn: "P.S. Chinese & Thai Food", cuisine: "中式烧烤 Chinese BBQ", avgCost: 81, rating: 0.0 },
        { name: "卷王", nameEn: "RollsKing", cuisine: "中式披萨烧烤 Chinese Pizza BBQ", avgCost: 63, rating: 3.5 },
        { name: "咖啡咖啡日", nameEn: "Cafe Coffee Day", cuisine: "法式烘焙 French Bakery", avgCost: 50, rating: 2.6 },
        { name: "朋友咖啡", nameEn: "The Friends Cafe", cuisine: "美式地中海 American Mediterranean", avgCost: 62, rating: 0.0 },
        { name: "沙希鸡肉角", nameEn: "Shahi Chicken Corner", cuisine: "咖啡海鲜 Cafe Seafood", avgCost: 85, rating: 0.0 },
        { name: "天使中国西藏食品", nameEn: "Anjel China & Tibetian Food", cuisine: "中式烧烤 Chinese BBQ", avgCost: 48, rating: 0.0 },
        { name: "毕加索屋顶", nameEn: "Picasso Roof Top", cuisine: "意式墨西哥烧烤 Italian Mexican BBQ", avgCost: 63, rating: 3.1 },
        { name: "卡斯巴", nameEn: "Kasba", cuisine: "印度烧烤 Indian BBQ", avgCost: 91, rating: 0.0 },
        { name: "阿姆利萨里库尔查", nameEn: "Amritsari Kulcha", cuisine: "法式地中海 French Mediterranean", avgCost: 49, rating: 3.1 },
        { name: "查瓦拉坦杜里快车", nameEn: "Chawla's Tandoori Xpress", cuisine: "地中海披萨 Mediterranean Pizza", avgCost: 75, rating: 3.2 },
        { name: "前沿", nameEn: "Frontier", cuisine: "茶饮烧烤 Tea BBQ", avgCost: 34, rating: 0.0 },
        { name: "里亚兹比尔亚尼角", nameEn: "Riyaz Biryani Corner", cuisine: "中式印度海鲜 Chinese Indian Seafood", avgCost: 17, rating: 0.0 },
        { name: "D食品", nameEn: "D Food", cuisine: "美式地中海 American Mediterranean", avgCost: 93, rating: 0.0 },
        { name: "沙阿烘焙坊", nameEn: "Shah Bakery", cuisine: "美式海鲜 American Seafood", avgCost: 20, rating: 3.0 },
        { name: "马吉利斯穆加尔", nameEn: "Majlis-e-Mughal", cuisine: "法式披萨 French Pizza", avgCost: 95, rating: 3.5 },
        { name: "阿普尼拉索伊", nameEn: "Apni Rasoi", cuisine: "法式地中海 French Mediterranean", avgCost: 76, rating: 2.6 },
        { name: "阿拉姆比尔亚尼中心", nameEn: "Alam Biryani Center", cuisine: "墨西哥海鲜 Mexican Seafood", avgCost: 91, rating: 0.0 },
        { name: "DND", nameEn: "DND", cuisine: "法式烧烤 French BBQ", avgCost: 64, rating: 3.5 },
        { name: "基文特斯", nameEn: "Keventers", cuisine: "地中海披萨 Mediterranean Pizza", avgCost: 90, rating: 0.0 },
        { name: "传说与烈酒", nameEn: "Tales & Spirits", cuisine: "墨西哥烧烤 Mexican BBQ", avgCost: 91, rating: 4.1 }
      ]
    },
  ],
  vegas_santa_maria: [
    {
      city: "Santa Maria 圣玛丽亚",
      restaurants: [
        { name: "天生印式", nameEn: "Indian By Nature", cuisine: "地中海烧烤 Mediterranean BBQ", avgCost: 45, rating: 4.3 },
        { name: "烧烤海盗", nameEn: "Pirates of Grill", cuisine: "美式地中海 American Mediterranean", avgCost: 90, rating: 4.0 },
        { name: "纳什塔", nameEn: "Nashta", cuisine: "中式地中海 Chinese Mediterranean", avgCost: 13, rating: 3.7 },
        { name: "拉朱哈尔瓦伊", nameEn: "Raju Halwai", cuisine: "烧烤甜品 BBQ Desserts", avgCost: 40, rating: 3.1 },
        { name: "45号", nameEn: "#45", cuisine: "茶饮烧烤 Tea BBQ", avgCost: 14, rating: 3.6 },
        { name: "河岸餐厅酒吧", nameEn: "RiverDine Restaurant & Bar", cuisine: "中式烧烤 Chinese BBQ", avgCost: 71, rating: 3.5 },
        { name: "纳里亚尔咖啡", nameEn: "Nariyal Cafe", cuisine: "茶饮烧烤 Tea BBQ", avgCost: 14, rating: 4.2 },
        { name: "库瑞马冰淇淋", nameEn: "Kuremal Mohan Lal Kulfi Wale", cuisine: "意式美式 Italian American", avgCost: 84, rating: 4.5 },
        { name: "埃塔尔酒廊酒吧", nameEn: "Etal The Lounge Bar", cuisine: "印度烧烤 Indian BBQ", avgCost: 71, rating: 3.2 },
        { name: "吃喝", nameEn: "Eat & Gulp", cuisine: "地中海意式 Mediterranean Italian", avgCost: 52, rating: 0.0 },
        { name: "佩沙瓦里美黑尔", nameEn: "Peshawari Mehel", cuisine: "披萨烧烤 Pizza BBQ", avgCost: 50, rating: 0.0 },
        { name: "莫蒂玛哈尔豪华", nameEn: "Moti Mahal Delux", cuisine: "美式意式 American Italian", avgCost: 94, rating: 2.6 },
        { name: "茶点", nameEn: "Tea Point", cuisine: "美式甜品 American Desserts", avgCost: 42, rating: 0.0 },
        { name: "中国食品角", nameEn: "Chinese Food Corner", cuisine: "美式茶饮 American Tea", avgCost: 21, rating: 0.0 },
        { name: "蛋糕篮", nameEn: "The Cake Basket", cuisine: "茶饮烧烤 Tea BBQ", avgCost: 98, rating: 0.0 },
        { name: "日历卡纳劳", nameEn: "Calendar Khana Laao", cuisine: "印度茶饮 Indian Tea", avgCost: 91, rating: 4.2 },
        { name: "清真披萨乐趣", nameEn: "Halal Pizza Fun", cuisine: "地中海快餐 Mediterranean Fast Food", avgCost: 14, rating: 3.1 },
        { name: "烤肉", nameEn: "Kabab", cuisine: "茶饮甜品 Tea Desserts", avgCost: 35, rating: 3.2 },
        { name: "伦敦街厨房", nameEn: "London Street Kitchen", cuisine: "中式海鲜 Chinese Seafood", avgCost: 90, rating: 4.2 },
        { name: "宾堂甜蜜惊喜", nameEn: "Bintang Sweet Thrills", cuisine: "地中海披萨 Mediterranean Pizza", avgCost: 86, rating: 3.5 },
        { name: "醉酒屋", nameEn: "The Drunk House", cuisine: "美式地中海 American Mediterranean", avgCost: 91, rating: 4.2 },
        { name: "旁遮普拉索伊", nameEn: "Punjabi Rasoi", cuisine: "美式海鲜 American Seafood", avgCost: 11, rating: 2.8 },
        { name: "肚子笑话", nameEn: "The Belly Giggles", cuisine: "美式地中海 American Mediterranean", avgCost: 27, rating: 3.0 },
        { name: "食品迷", nameEn: "Food Junkies", cuisine: "地中海烧烤 Mediterranean BBQ", avgCost: 70, rating: 3.2 },
        { name: "城市食堂", nameEn: "The Urban Canteen", cuisine: "墨西哥披萨 Mexican Pizza", avgCost: 37, rating: 0.0 },
        { name: "巴贝迪哈蒂", nameEn: "Bhappe Di Hatti", cuisine: "地中海烧烤 Mediterranean BBQ", avgCost: 50, rating: 3.1 },
        { name: "安娜", nameEn: "The Anna", cuisine: "披萨快餐 Pizza Fast Food", avgCost: 68, rating: 2.8 },
        { name: "漂浮蛋糕", nameEn: "Floating Cakes", cuisine: "法式墨西哥 French Mexican", avgCost: 79, rating: 2.8 },
        { name: "丛林月亮舞餐厅", nameEn: "Jungli Moon Dance Restaurant", cuisine: "咖啡海鲜 Cafe Seafood", avgCost: 70, rating: 3.1 },
        { name: "帕帕里奇", nameEn: "PappaRich", cuisine: "意式法式海鲜 Italian French Seafood", avgCost: 26, rating: 4.0 }
      ]
    }
  ],
  ithaca_newark: [
    {
      city: "Newark 纽瓦克",
      restaurants: [
        { name: "艺术餐厅", nameEn: "Artistry", cuisine: "咖啡披萨 Cafe Pizza", avgCost: 79, rating: 3.8 },
        { name: "安吉蒂餐厅", nameEn: "Angeethi Restaurant", cuisine: "法式烧烤 French BBQ", avgCost: 12, rating: 3.3 },
        { name: "幻影餐厅酒吧", nameEn: "Mirage Restro Bar", cuisine: "美式甜品 American Desserts", avgCost: 51, rating: 2.4 },
        { name: "哈曼餐厅", nameEn: "Harmann Restaurant", cuisine: "美式茶饮 American Tea", avgCost: 57, rating: 0.0 },
        { name: "逃脱露台酒吧厨房", nameEn: "Escape Terrace Bar Kitchen", cuisine: "中式海鲜 Chinese Seafood", avgCost: 100, rating: 3.4 },
        { name: "美洲豹", nameEn: "Jaguar", cuisine: "法式海鲜 French Seafood", avgCost: 38, rating: 2.8 },
        { name: "漂流者咖啡", nameEn: "Drifters Cafe", cuisine: "茶饮烧烤 Tea BBQ", avgCost: 24, rating: 4.1 },
        { name: "水壶和小桶", nameEn: "Kettle & Kegs", cuisine: "地中海意式 Mediterranean Italian", avgCost: 67, rating: 0.0 },
        { name: "伯纳多餐厅", nameEn: "Bernardo's", cuisine: "美式地中海 American Mediterranean", avgCost: 84, rating: 4.0 },
        { name: "阿奈查食品联合", nameEn: "Anaicha's Food Joint", cuisine: "墨西哥海鲜 Mexican Seafood", avgCost: 43, rating: 3.6 },
        { name: "夏威夷阿达", nameEn: "Hawai Adda", cuisine: "茶饮披萨 Tea Pizza", avgCost: 17, rating: 3.5 },
        { name: "艾姆德里咖啡", nameEn: "Aim Delhi Cafe", cuisine: "茶饮烧烤 Tea BBQ", avgCost: 87, rating: 3.4 },
        { name: "贝萨克咖啡", nameEn: "Cafe Bethak", cuisine: "地中海海鲜 Mediterranean Seafood", avgCost: 100, rating: 3.4 },
        { name: "鸡肉共和国", nameEn: "Republic of Chicken", cuisine: "咖啡甜品 Cafe Desserts", avgCost: 42, rating: 2.9 },
        { name: "关于食物的一切", nameEn: "All About Food", cuisine: "美式海鲜 American Seafood", avgCost: 47, rating: 0.0 },
        { name: "苏鲁奇", nameEn: "Suruchee", cuisine: "中式烧烤 Chinese BBQ", avgCost: 44, rating: 3.4 },
        { name: "通达伊卡巴比", nameEn: "Tunday Kababi", cuisine: "美式印度 American Indian", avgCost: 10, rating: 2.2 },
        { name: "奶油创作", nameEn: "Creamy Creation", cuisine: "墨西哥披萨 Mexican Pizza", avgCost: 44, rating: 0.0 },
        { name: "迪利达巴鸡肉点", nameEn: "Dilli Darbar Chicken Point", cuisine: "法式烧烤 French BBQ", avgCost: 87, rating: 0.0 },
        { name: "桑吉塔餐厅", nameEn: "Sangeeta Dhaba", cuisine: "美式茶饮 American Tea", avgCost: 47, rating: 0.0 },
        { name: "阿加瓦尔比卡内里甜品", nameEn: "Aggarwal Bikaneri Sweets", cuisine: "法式地中海 French Mediterranean", avgCost: 76, rating: 0.0 },
        { name: "莫甘博餐厅", nameEn: "Mogambo Khush Hua", cuisine: "地中海甜品 Mediterranean Desserts", avgCost: 39, rating: 3.8 },
        { name: "巧克雷托蛋糕设计工作室", nameEn: "Chokoreto - The Cake Design Studio", cuisine: "咖啡烧烤 Cafe BBQ", avgCost: 96, rating: 0.0 },
        { name: "新花园小屋", nameEn: "New Garden Hut", cuisine: "茶饮快餐 Tea Fast Food", avgCost: 12, rating: 0.0 },
        { name: "阿普尼拉索伊", nameEn: "Apni Rasoi", cuisine: "墨西哥海鲜 Mexican Seafood", avgCost: 42, rating: 3.0 },
        { name: "阿普基拉索伊", nameEn: "Aapki Rasoi", cuisine: "意式披萨 Italian Pizza", avgCost: 98, rating: 0.0 },
        { name: "乔希食屋", nameEn: "Joshi Eating House", cuisine: "印度披萨 Indian Pizza", avgCost: 52, rating: 0.0 },
        { name: "德夫汉堡", nameEn: "Dev Burger", cuisine: "意式快餐 Italian Fast Food", avgCost: 31, rating: 2.9 },
        { name: "南印度小屋", nameEn: "South Indian Hut", cuisine: "茶饮烧烤 Tea BBQ", avgCost: 47, rating: 0.0 },
        { name: "南印度咖啡", nameEn: "South Indian Cafe", cuisine: "印度甜品 Indian Desserts", avgCost: 83, rating: 3.3 },
        { name: "必胜客", nameEn: "Pizza Hut", cuisine: "印度甜品 Indian Desserts", avgCost: 70, rating: 0.0 },
        { name: "艾哈迈德", nameEn: "Ahmed's", cuisine: "茶饮海鲜 Tea Seafood", avgCost: 36, rating: 0.0 },
        { name: "巴斯金罗宾斯", nameEn: "Baskin Robbins", cuisine: "意式烧烤 Italian BBQ", avgCost: 77, rating: 0.0 }
      ]
    }
  ]
};


// 从travel_query中提取旅游类型
const extractTravelType = (travelQuery: string): string => {
  if (travelQuery.includes('Philadelphia') && travelQuery.includes('Virginia')) {
    return 'philadelphia_virginia';
  } else if (travelQuery.includes('Las Vegas') && travelQuery.includes('Santa Maria')) {
    return 'vegas_santa_maria';
  } else if (travelQuery.includes('Ithaca') && travelQuery.includes('Newark')) {
    return 'ithaca_newark';
  }
  return '';
};

const TravelInfoPanel: React.FC<TravelInfoPanelProps> = ({ currentConfig }) => {
  const [activeTab, setActiveTab] = useState<'accommodation' | 'attractions' | 'restaurants' | 'transport'>('accommodation');

  if (!currentConfig) {
    return (
      <div className="panel-window travel-info-panel">
        <div className="panel-header">
          <h3>🗺️ 旅游信息 Travel Info</h3>
        </div>
        <div className="panel-content">
          <div className="empty-state small">
            <div className="empty-icon">🗺️</div>
            <h4>等待任务配置 Waiting for Configuration</h4>
            <p>请先选择旅游场景以查看详细信息<br/>Please select a travel scenario to view details</p>
          </div>
        </div>
      </div>
    );
  }

  const travelType = extractTravelType(currentConfig.travel_query);
  const accommodationData = accommodationDataMap[travelType];
  const attractionData = attractionDataMap[travelType];
  const restaurantData = restaurantDataMap[travelType];
  const transportData = transportDataMap[travelType];

  if (!accommodationData) {
    return (
      <div className="panel-window travel-info-panel">
        <div className="panel-header">
          <h3>🗺️ 旅游信息 Travel Info</h3>
        </div>
        <div className="panel-content">
          <div className="config-info">
            <h4>当前配置 Current Configuration</h4>
            <p><strong>用户档案 User Profile:</strong> {currentConfig.user_profile}</p>
            <p><strong>暂无旅游数据 No travel data available</strong></p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="panel-window travel-info-panel">
      <div className="panel-header">
        <h3>🗺️ 旅游信息 Travel Info</h3>
      </div>
      
      {/* 标签切换 */}
      <div className="tab-switcher">
        <button 
          className={`tab-button ${activeTab === 'accommodation' ? 'active' : ''}`}
          onClick={() => setActiveTab('accommodation')}
        >
          🏨 住宿<br/>Stay
        </button>
        <button 
          className={`tab-button ${activeTab === 'attractions' ? 'active' : ''}`}
          onClick={() => setActiveTab('attractions')}
        >
          🎯 景点<br/>Sights
        </button>
        <button 
          className={`tab-button ${activeTab === 'restaurants' ? 'active' : ''}`}
          onClick={() => setActiveTab('restaurants')}
        >
          🍽️ 餐厅<br/>Dining
        </button>
        <button 
          className={`tab-button ${activeTab === 'transport' ? 'active' : ''}`}
          onClick={() => setActiveTab('transport')}
        >
          🚗 交通<br/>Transit
        </button>
      </div>

      <div className="panel-content">
        {/* 住宿信息 */}
        {activeTab === 'accommodation' && accommodationData.map((cityData, cityIndex) => (
          <div key={cityIndex} className="city-section">
            <h4 className="city-title">📍 {cityData.city}</h4>
            
            <table className="info-table">
              <thead>
                <tr>
                  <th>住宿名称<br/>Accommodation</th>
                  <th>类型<br/>Type</th>
                  <th>价格<br/>Price</th>
                  {/* <th>评分<br/>Rating</th> */}
                  <th>详情<br/>Details</th>
                </tr>
              </thead>
              <tbody>
                {cityData.hotels.map((hotel, hotelIndex) => (
                  <tr key={hotelIndex}>
                    <td>
                      <div className="item-name">{hotel.name}</div>
                    </td>
                    <td>{hotel.type}</td>
                    <td className="price">{hotel.price}</td>
                    {/* <td> */}
                      {/* <div className="rating">
                        <span className="rating-number">{hotel.rating}</span>
                        <span className="rating-stars">
                          {'★'.repeat(Math.floor(hotel.rating))}
                          {hotel.rating % 1 !== 0 && '☆'}
                        </span>
                      </div> */}
                    {/* </td> */}
                    <td>
                      <div className="house-rules">
                        {hotel.houseRules ? hotel.houseRules : "无特殊限制"}
                      </div>
                    </td>
                    <td>
                      <div className="hotel-details">
                        <div>最多 {hotel.maxOccupancy} 人</div>
                        <div>最少 {hotel.minNights} 晚</div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}

        {/* 景点信息 */}
        {activeTab === 'attractions' && attractionData && attractionData.map((cityData, cityIndex) => (
          <div key={cityIndex} className="city-section">
            <h4 className="city-title">📍 {cityData.city}</h4>
            
            <table className="info-table">
              <thead>
                <tr>
                  <th>景点名称<br/>Attraction</th>
                  <th>类型<br/>Type</th>
                  <th>地址<br/>Address</th>
                  <th>联系方式<br/>Contact</th>
                </tr>
              </thead>
              <tbody>
                {cityData.attractions.map((attraction, index) => (
                  <tr key={index}>
                    <td>
                      <div className="item-name">{attraction.name}</div>
                      <div className="item-name-en">{attraction.nameEn}</div>
                      <div className="item-description">{attraction.description}</div>
                    </td>
                    <td>{attraction.type}</td>
                    <td className="attraction-address">{attraction.address}</td>
                    <td>
                      <div className="contact-info">
                        {attraction.phone && <div>📞 {attraction.phone}</div>}
                        {attraction.website && (
                          <div className="website-link">
                            <a 
                              href={attraction.website} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="website-url"
                            >
                              🌐 网站 Website
                            </a>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}

        {/* 餐厅信息 */}
        {activeTab === 'restaurants' && restaurantData && restaurantData.map((cityData, cityIndex) => (
          <div key={cityIndex} className="city-section">
            <h4 className="city-title">📍 {cityData.city}</h4>
            
            <table className="info-table">
              <thead>
                <tr>
                  <th>餐厅名称<br/>Restaurant</th>
                  <th>菜系<br/>Cuisine</th>
                  <th>均价<br/>Avg Cost</th>
                  <th>评分<br/>Rating</th>
                </tr>
              </thead>
              <tbody>
                {cityData.restaurants.map((restaurant, index) => (
                  <tr key={index}>
                    <td>
                      <div className="item-name">{restaurant.name}</div>
                      <div className="item-name-en">{restaurant.nameEn}</div>
                    </td>
                    <td>{restaurant.cuisine}</td>
                    <td className="price">${restaurant.avgCost}</td>
                    <td>
                      <div className="rating">
                        <span className="rating-number">{restaurant.rating}</span>
                        <span className="rating-stars">
                          {'★'.repeat(Math.floor(restaurant.rating))}
                          {restaurant.rating % 1 !== 0 && '☆'}
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}

        {/* 交通信息 */}
        {activeTab === 'transport' && transportData && (
          <div className="transport-section">
            <h4 className="section-title">🚗 {transportData.route}</h4>
            <h5 className="section-subtitle">{transportData.routeEn}</h5>
            
            <table className="info-table">
              <thead>
                <tr>
                  <th>交通方式<br/>Transport</th>
                  <th>时长<br/>Duration</th>
                  <th>价格<br/>Price</th>
                  <th>说明<br/>Description</th>
                </tr>
              </thead>
              <tbody>
                {transportData.options.map((option, index) => (
                  <tr key={index}>
                    <td>
                      <div className="item-name">{option.type}</div>
                      <div className="item-name-en">{option.typeEn}</div>
                    </td>
                    <td>{option.duration}</td>
                    <td className="price">{option.price}</td>
                    <td className="item-description">{option.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        
        {/* 用户档案信息 */}
        {/* <div className="user-profile-info">
          <h4>👤 当前用户 Current User</h4>
          <div className="profile-badge">
            {currentConfig.user_profile}
          </div>
        </div> */}
      </div>
    </div>
  );
};

interface TATAStoryAssistantProps {
  initialMessages?: any[];
  initialSessionId?: string | null;
  currentConfig?: {user_profile: string; travel_query: string} | null;
}

export function TATAStoryAssistant({ 
  initialMessages = [], 
  initialSessionId = null,
  currentConfig: externalConfig = null
}: TATAStoryAssistantProps) {
  // 基础状态
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [sessionId, setSessionId] = useState<string>(initialSessionId || `session_${Date.now()}`);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('disconnected');
  
  // 🎯 账号选择相关状态
  const [currentAccount, setCurrentAccount] = useState('user_main'); // 默认账号
  const [showAccountSelector, setShowAccountSelector] = useState(false);
  
  // 数据状态
  const [currentThinkingSteps, setCurrentThinkingSteps] = useState<ThinkingStep[]>([]);
  const [currentToolCalls, setCurrentToolCalls] = useState<ToolCall[]>([]);
  const [currentAgenda, setCurrentAgenda] = useState<AgendaSummary | null>(null);
  const [currentConfig, setCurrentConfig] = useState<{user_profile: string; travel_query: string} | null>(externalConfig);

  // refs - 修正类型定义以允许null
  const chatEndRef = useRef<HTMLDivElement>(null);
  const messageInputRef = useRef<HTMLTextAreaElement>(null);

  // 调试信息状态
  const [debugInfo, setDebugInfo] = useState<string[]>([]);
  const [showDebug, setShowDebug] = useState(false);
 
  // 自定义hooks
  const { handleStreamResponse } = useStreamHandler({
    setMessages,
    setCurrentThinkingSteps,
    setCurrentToolCalls,
    setCurrentAgenda,
    setIsProcessing,
    setDebugInfo,
    currentThinkingSteps,
    currentToolCalls,
    messageInputRef,
    chatEndRef
  });

  const { handleSendMessage } = useChatManager({
    sessionId,
    messages,
    setMessages,
    currentMessage,
    setCurrentMessage,
    isProcessing,
    setIsProcessing,
    setCurrentThinkingSteps,
    setCurrentToolCalls,
    setDebugInfo,
    handleStreamResponse,
    setConnectionStatus, // 🎯 传递连接状态setter
    currentAccount // 🎯 传递当前账号
  });

  // 🎯 账号切换处理
  const handleAccountChange = useCallback((accountId: string) => {
    setCurrentAccount(accountId);
    setDebugInfo(prev => [...prev, `👤 账号已切换到: ${accountId}`]);
    console.log('✅ 账号已切换到:', accountId);
  }, [setDebugInfo]);

  // 监听外部配置变化
  useEffect(() => {
    if (externalConfig) {
      setCurrentConfig(externalConfig);
    }
  }, [externalConfig]);

  // 键盘事件
  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    // 🎯 优化：支持 Shift+Enter 换行
    if (e.key === 'Enter') {
      if (e.shiftKey) {
        // Shift+Enter: 允许换行，不发送消息
        return;
      } else {
        // Enter: 发送消息
        e.preventDefault();
        if (!isProcessing && currentMessage.trim()) {
          handleSendMessage();
        }
      }
    }
  }, [currentMessage, isProcessing, handleSendMessage]);

  // 切换调试面板快捷键
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'D') {
        setShowDebug(prev => !prev);
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // 在 TATAStoryAssistant 组件中添加 useEffect
  useEffect(() => {
    const checkInitialConnection = async () => {
      try {
        const apiBaseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
        const response = await fetch(`${apiBaseURL}/api/health`, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' }
        });
        
        if (response.ok) {
          setConnectionStatus('connected');
          console.log('✅ 初始连接检查成功');
        } else {
          setConnectionStatus('disconnected');
          console.log('❌ 初始连接检查失败:', response.status);
        }
      } catch (error) {
        setConnectionStatus('disconnected');
        console.log('❌ 初始连接检查错误:', error);
      }
    };
    
    checkInitialConnection();
  }, []); // 空依赖数组，只在组件挂载时执行一次

  // 🎯 修复：当接收到新的初始消息时更新状态
  useEffect(() => {
    if (initialMessages.length > 0) {
      setMessages(initialMessages);
    }
  }, [initialMessages]);
  
  useEffect(() => {
    if (initialSessionId) {
      setSessionId(initialSessionId);
    }
  }, [initialSessionId]);

  return (
    <div className="tata-container">
      {/* 调试信息面板 - 开发时使用 */}
      {showDebug && process.env.NODE_ENV === 'development' && debugInfo.length > 0 && (
        <div style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          background: 'rgba(0,0,0,0.8)',
          color: 'white',
          padding: '10px',
          borderRadius: '8px',
          fontSize: '12px',
          maxWidth: '400px',
          maxHeight: '200px',
          overflow: 'auto',
          zIndex: 1000
        }}>
          {/* 添加关闭按钮 */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '5px' }}>
            <span style={{ fontWeight: 'bold' }}>🔍 调试信息:</span>
            <button 
              onClick={() => setShowDebug(false)} 
              style={{ background: 'none', border: 'none', color: 'white', cursor: 'pointer' }}
            >
              ✕
            </button>
          </div>
          {debugInfo.map((info, index) => (
            <div key={index} style={{ marginBottom: '2px' }}>{info}</div>
          ))}
        </div>
      )}
    
      {/* 状态栏 */}
      <StatusBar 
        sessionId={sessionId}
        connectionStatus={connectionStatus}
        messageCount={messages.length}
        currentAccount={currentAccount} // 🎯 传递当前账号
        onSettingsClick={() => setShowAccountSelector(true)} // 🎯 设置按钮点击处理
      />

      {/* 🎯 账号选择弹窗 */}
      <AccountSelector
        isOpen={showAccountSelector}
        onClose={() => setShowAccountSelector(false)}
        currentAccount={currentAccount}
        onAccountChange={handleAccountChange}
      />

      {/* 主内容区域 - 左侧旅游信息面板 + 右侧聊天 */}
      <div className="main-content">
        {/* 左侧旅游信息面板 */}
        <div className="left-panels">
          <TravelInfoPanel currentConfig={currentConfig} />
        </div>

        {/* 右侧聊天面板 */}
        <div className="chat-panel">
          <div className="chat-window">
            <div className="panel-header">
              <h3>💬 对话交流 Chat</h3>
            </div>
            <div className="panel-content">
              <MessageList messages={messages} chatEndRef={chatEndRef} />
              <InputArea
                currentMessage={currentMessage}
                setCurrentMessage={setCurrentMessage}
                isProcessing={isProcessing}
                onSendMessage={handleSendMessage}
                onKeyPress={handleKeyPress}
                messageInputRef={messageInputRef}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TATAStoryAssistant;
