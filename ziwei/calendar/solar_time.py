"""
真太阳时校正系统 — True Solar Time Correction

紫微斗数以出生地真太阳时为准:
- 中国统一使用北京时间(UTC+8, 120°E), 但国土横跨约60个经度
- 每差1个经度, 真太阳时差约4分钟
- 乌鲁木齐(87°E)与北京(116°E)相差约116分钟, 时辰完全不同
- 此外还需考虑均时差(Equation of Time, ±16分钟)

校正公式:
  真太阳时 = 钟表时间 - 时区偏移 + (经度 - 120°) × 4分钟 + 均时差
"""

import math
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict

# ──────────────────────────────────────
# 中国主要城市经纬度数据库
# ──────────────────────────────────────

CITY_DATABASE: Dict[str, Tuple[float, float, str]] = {
    # 直辖市
    "北京": (116.40, 39.90, "北京市"),
    "上海": (121.47, 31.23, "上海市"),
    "天津": (117.20, 39.13, "天津市"),
    "重庆": (106.54, 29.59, "重庆市"),
    
    # 省会城市
    "哈尔滨": (126.63, 45.75, "黑龙江"),
    "长春": (125.35, 43.88, "吉林"),
    "沈阳": (123.38, 41.80, "辽宁"),
    "呼和浩特": (111.65, 40.82, "内蒙古"),
    "乌鲁木齐": (87.62, 43.82, "新疆"),
    "拉萨": (91.13, 29.65, "西藏"),
    "西宁": (101.78, 36.62, "青海"),
    "兰州": (103.73, 36.03, "甘肃"),
    "银川": (106.27, 38.47, "宁夏"),
    "西安": (108.95, 34.27, "陕西"),
    "太原": (112.53, 37.87, "山西"),
    "石家庄": (114.51, 38.04, "河北"),
    "济南": (117.00, 36.65, "山东"),
    "郑州": (113.65, 34.76, "河南"),
    "南京": (118.78, 32.04, "江苏"),
    "合肥": (117.27, 31.86, "安徽"),
    "武汉": (114.31, 30.52, "湖北"),
    "长沙": (112.97, 28.23, "湖南"),
    "南昌": (115.89, 28.68, "江西"),
    "杭州": (120.19, 30.26, "浙江"),
    "福州": (119.30, 26.08, "福建"),
    "台北": (121.52, 25.03, "台湾"),
    "广州": (113.23, 23.16, "广东"),
    "南宁": (108.33, 22.84, "广西"),
    "海口": (110.35, 20.02, "海南"),
    "香港": (114.17, 22.28, "香港"),
    "澳门": (113.55, 22.19, "澳门"),
    "成都": (104.07, 30.67, "四川"),
    "贵阳": (106.71, 26.57, "贵州"),
    "昆明": (102.73, 25.04, "云南"),
    
    # 重要地级市
    "大连": (121.62, 38.92, "辽宁"),
    "青岛": (120.38, 36.07, "山东"),
    "厦门": (118.08, 24.48, "福建"),
    "深圳": (114.07, 22.55, "广东"),
    "珠海": (113.55, 22.22, "广东"),
    "三亚": (109.51, 18.25, "海南"),
    "桂林": (110.28, 25.29, "广西"),
    "苏州": (120.60, 31.30, "江苏"),
    "无锡": (120.29, 31.59, "江苏"),
    "宁波": (121.54, 29.87, "浙江"),
    "温州": (120.70, 28.00, "浙江"),
    "秦皇岛": (119.57, 39.93, "河北"),
    "烟台": (121.39, 37.53, "山东"),
    "威海": (122.12, 37.51, "山东"),
    "洛阳": (112.44, 34.70, "河南"),
    "开封": (114.35, 34.79, "河南"),
    "宜昌": (111.29, 30.69, "湖北"),
    "襄阳": (112.14, 32.04, "湖北"),
    "岳阳": (113.09, 29.37, "湖南"),
    "株洲": (113.16, 27.83, "湖南"),
    "汕头": (116.68, 23.35, "广东"),
    "湛江": (110.36, 21.27, "广东"),
    "柳州": (109.41, 24.32, "广西"),
    "绵阳": (104.73, 31.48, "四川"),
    "遵义": (106.90, 27.70, "贵州"),
    "大理": (100.23, 25.61, "云南"),
    "丽江": (100.23, 26.88, "云南"),
    "延吉": (129.51, 42.91, "吉林"),
    "齐齐哈尔": (123.97, 47.33, "黑龙江"),
    "牡丹江": (129.58, 44.60, "黑龙江"),
    "包头": (109.84, 40.66, "内蒙古"),
    "大同": (113.30, 40.12, "山西"),
    "喀什": (75.99, 39.47, "新疆"),
    "伊犁": (81.32, 43.92, "新疆"),
    "徐州": (117.20, 34.27, "江苏"),
    "常州": (119.95, 31.79, "江苏"),
    "南通": (120.86, 32.01, "江苏"),
    "扬州": (119.42, 32.39, "江苏"),
    "镇江": (119.44, 32.20, "江苏"),
    "绍兴": (120.58, 30.01, "浙江"),
    "嘉兴": (120.76, 30.77, "浙江"),
    "金华": (119.64, 29.08, "浙江"),
    "台州": (121.42, 28.66, "浙江"),
    "泉州": (118.58, 24.93, "福建"),
    "漳州": (117.66, 24.51, "福建"),
    "东莞": (113.75, 23.04, "广东"),
    "佛山": (113.12, 23.03, "广东"),
    "惠州": (114.42, 23.11, "广东"),
    "中山": (113.38, 22.52, "广东"),
    "江门": (113.08, 22.58, "广东"),
    "肇庆": (112.47, 23.05, "广东"),
    "清远": (113.01, 23.70, "广东"),
    "韶关": (113.60, 24.80, "广东"),
    "梅州": (116.12, 24.28, "广东"),
    "潮州": (116.63, 23.68, "广东"),
    "揭阳": (116.35, 23.55, "广东"),
    "汕尾": (115.36, 22.79, "广东"),
    "河源": (114.70, 23.73, "广东"),
    "阳江": (111.95, 21.85, "广东"),
    "茂名": (110.92, 21.66, "广东"),
    "云浮": (112.04, 22.93, "广东"),
    "北海": (109.12, 21.49, "广西"),
    "防城港": (108.35, 21.70, "广西"),
    "钦州": (108.65, 21.96, "广西"),
    "贵港": (109.60, 23.11, "广西"),
    "玉林": (110.14, 22.63, "广西"),
    "百色": (106.62, 23.90, "广西"),
    "贺州": (111.57, 24.41, "广西"),
    "河池": (108.06, 24.70, "广西"),
    "来宾": (109.22, 23.73, "广西"),
    "崇左": (107.37, 22.40, "广西"),
    "三亚": (109.51, 18.25, "海南"),
    "儋州": (109.58, 19.52, "海南"),
    "文昌": (110.80, 19.61, "海南"),
    "万宁": (110.40, 18.80, "海南"),
    "五指山": (109.52, 18.78, "海南"),
    "德阳": (104.40, 31.13, "四川"),
    "广元": (105.83, 32.44, "四川"),
    "乐山": (103.77, 29.57, "四川"),
    "南充": (106.11, 30.80, "四川"),
    "宜宾": (104.64, 28.77, "四川"),
    "达州": (107.47, 31.21, "四川"),
    "遂宁": (105.57, 30.53, "四川"),
    "泸州": (105.44, 28.87, "四川"),
    "内江": (105.06, 29.58, "四川"),
    "攀枝花": (101.72, 26.58, "四川"),
    "六盘水": (104.83, 26.59, "贵州"),
    "安顺": (105.95, 26.25, "贵州"),
    "毕节": (105.29, 27.30, "贵州"),
    "铜仁": (109.19, 27.72, "贵州"),
    "曲靖": (103.80, 25.50, "云南"),
    "玉溪": (102.55, 24.35, "云南"),
    "保山": (99.18, 25.12, "云南"),
    "昭通": (103.72, 27.34, "云南"),
    "临沧": (100.09, 23.88, "云南"),
    "楚雄": (101.55, 25.04, "云南"),
    "红河": (103.40, 23.37, "云南"),
    "文山": (104.24, 23.37, "云南"),
    "西双版纳": (100.80, 22.01, "云南"),
    "德宏": (98.58, 24.43, "云南"),
    "怒江": (98.85, 25.85, "云南"),
    "迪庆": (99.70, 27.83, "云南"),
    "日喀则": (88.89, 29.27, "西藏"),
    "昌都": (97.18, 31.14, "西藏"),
    "林芝": (94.36, 29.65, "西藏"),
    "山南": (91.77, 29.24, "西藏"),
    "那曲": (92.06, 31.48, "西藏"),
    "阿里": (80.10, 32.50, "西藏"),
    "天水": (105.72, 34.58, "甘肃"),
    "酒泉": (98.50, 39.71, "甘肃"),
    "张掖": (100.45, 38.93, "甘肃"),
    "武威": (102.64, 37.93, "甘肃"),
    "平凉": (106.67, 35.54, "甘肃"),
    "庆阳": (107.64, 35.71, "甘肃"),
    "定西": (104.62, 35.58, "甘肃"),
    "陇南": (104.92, 33.40, "甘肃"),
    "固原": (106.28, 36.00, "宁夏"),
    "石嘴山": (106.39, 39.04, "宁夏"),
    "吴忠": (106.20, 37.99, "宁夏"),
    "中卫": (105.18, 37.51, "宁夏"),
    "格尔木": (94.90, 36.42, "青海"),
    "海东": (102.12, 36.50, "青海"),
    "玉树": (97.01, 33.00, "青海"),
    "延安": (109.49, 36.60, "陕西"),
    "汉中": (107.02, 33.07, "陕西"),
    "榆林": (109.73, 38.29, "陕西"),
    "安康": (109.02, 32.70, "陕西"),
    "商洛": (109.94, 33.87, "陕西"),
    "宝鸡": (107.15, 34.38, "陕西"),
    "咸阳": (108.71, 34.33, "陕西"),
    "渭南": (109.50, 34.50, "陕西"),
    "铜川": (109.11, 34.90, "陕西"),
}


# ──────────────────────────────────────
# 真太阳时计算
# ──────────────────────────────────────

def find_city(query: str) -> Optional[Tuple[float, float, str]]:
    """根据城市名或省份名模糊搜索经纬度."""
    query = query.strip()
    if not query:
        return None
    
    # 精确匹配
    if query in CITY_DATABASE:
        return CITY_DATABASE[query]
    
    # 部分匹配
    for city, (lon, lat, prov) in CITY_DATABASE.items():
        if query in city or city in query:
            return lon, lat, prov
    
    # 模糊搜索 (前2字匹配)
    for city, (lon, lat, prov) in CITY_DATABASE.items():
        if len(query) >= 2 and city[:2] == query[:2]:
            return lon, lat, prov
    
    return None


def equation_of_time(day_of_year: int) -> float:
    """
    均时差 (Equation of Time)
    
    太阳日与平太阳日之差, 由地球轨道椭圆度和黄赤交角产生.
    范围约 ±16分钟.
    
    Args:
        day_of_year: 一年中的第几天 (1-365)
    
    Returns:
        均时差 (分钟)
    """
    # 简化公式: 用正弦波近似均时差
    # 更精确的可使用 Meeus 天文算法, 但此简化对时辰判断精度已足够
    B = 2 * math.pi * (day_of_year - 81) / 365.0
    eot = 9.87 * math.sin(2 * B) - 7.53 * math.cos(B) - 1.5 * math.sin(B)
    return eot  # 分钟


def calculate_true_solar_time(
    year: int, month: int, day: int,
    clock_hour: int, clock_minute: int,
    longitude: float,
    timezone_offset: float = 8.0,  # 中国 UTC+8
) -> Tuple[int, int, float]:
    """
    计算真太阳时.
    
    Args:
        year, month, day: 公历日期
        clock_hour, clock_minute: 钟表时间 (24小时制)
        longitude: 出生地经度 (东经为正)
        timezone_offset: 时区偏移小时 (中国=8)
    
    Returns:
        (校正后小时, 校正后分钟, 总偏差分钟数)
    """
    # 1. 经度差校正: 每偏离120°E 1度差4分钟
    standard_meridian = 120.0  # 北京时间标准经线
    lon_offset = (longitude - standard_meridian) * 4.0  # 分钟
    
    # 2. 时区偏移 (钟表时间统一为UTC+8, 此处已包含在clock_hour中)
    # 中国全境使用北京时间(UTC+8)
    
    # 3. 均时差
    from datetime import date
    doy = date(year, month, day).timetuple().tm_yday
    eot = equation_of_time(doy)
    
    # 总偏差
    total_offset_minutes = lon_offset + eot
    
    # 校正后时间
    total_clock_minutes = clock_hour * 60 + clock_minute
    total_solar_minutes = total_clock_minutes + total_offset_minutes
    
    # 处理跨日
    total_solar_minutes = total_solar_minutes % (24 * 60)
    
    solar_hour = int(total_solar_minutes // 60)
    solar_minute = int(total_solar_minutes % 60)
    
    return solar_hour, solar_minute, total_offset_minutes


def get_chinese_hour_with_correction(
    year: int, month: int, day: int,
    clock_hour: int, clock_minute: int,
    city: str,
) -> Dict:
    """
    根据出生城市获取校正后的时辰.
    
    Args:
        year, month, day: 公历日期
        clock_hour, clock_minute: 钟表时间
        city: 城市名 (如 "乌鲁木齐", "北京", "上海")
    
    Returns:
        {
            "city": str,
            "province": str,
            "longitude": float,
            "latitude": float,
            "clock_time": "HH:MM",
            "true_solar_time": "HH:MM",
            "offset_minutes": float,
            "corrected_hour": int,
            "corrected_minute": int,
            "chinese_hour_before": str,   # 校正前时辰
            "chinese_hour_after": str,    # 校正后时辰
            "hour_changed": bool,         # 时辰是否改变
        }
    """
    from .ganzhi import chinese_hour_from_time
    
    # 查找城市
    city_info = find_city(city)
    if not city_info:
        # 未找到城市, 使用北京时间(无校正)
        ch_hour = chinese_hour_from_time(clock_hour, clock_minute)
        return {
            "city": city,
            "province": "未知",
            "longitude": 120.0,
            "latitude": 35.0,
            "clock_time": f"{clock_hour:02d}:{clock_minute:02d}",
            "true_solar_time": f"{clock_hour:02d}:{clock_minute:02d}",
            "offset_minutes": 0.0,
            "corrected_hour": clock_hour,
            "corrected_minute": clock_minute,
            "chinese_hour_before": ch_hour,
            "chinese_hour_after": ch_hour,
            "hour_changed": False,
        }
    
    lon, lat, prov = city_info
    
    # 计算真太阳时
    solar_h, solar_m, offset = calculate_true_solar_time(
        year, month, day, clock_hour, clock_minute, lon
    )
    
    # 校正前后时辰
    ch_before = chinese_hour_from_time(clock_hour, clock_minute)
    ch_after = chinese_hour_from_time(solar_h, solar_m)
    changed = (ch_before != ch_after)
    
    return {
        "city": city,
        "province": prov,
        "longitude": lon,
        "latitude": lat,
        "clock_time": f"{clock_hour:02d}:{clock_minute:02d}",
        "true_solar_time": f"{solar_h:02d}:{solar_m:02d}",
        "offset_minutes": round(offset, 1),
        "corrected_hour": solar_h,
        "corrected_minute": solar_m,
        "chinese_hour_before": ch_before,
        "chinese_hour_after": ch_after,
        "hour_changed": changed,
    }


def search_cities(query: str, limit: int = 10) -> list:
    """搜索城市, 返回匹配列表."""
    q = query.strip()
    if not q:
        return []
    
    results = []
    for city, (lon, lat, prov) in CITY_DATABASE.items():
        if q in city or city in q:
            results.append({"city": city, "province": prov, "longitude": lon, "latitude": lat})
            if len(results) >= limit:
                break
    
    return results
