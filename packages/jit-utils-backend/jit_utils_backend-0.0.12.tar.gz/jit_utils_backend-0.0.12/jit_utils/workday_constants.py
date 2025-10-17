# -*-coding:utf-8-*-
"""
Created on 2023/10/21

@author: wanjianjun

@desc:
"""
import datetime
from enum import Enum


class Holiday(Enum):
    def __new__(cls, english, chinese, days):
        obj = object.__new__(cls)
        obj._value = english

        obj.chinese = chinese
        obj.days = days
        return obj

    newYearsDay = "New Year's Day", "元旦", 3
    springFestival = "Spring Festival", "春节", 7
    tombSweepingDay = "Tomb-sweeping Day", "清明", 3
    labourDay = "Labour Day", "劳动节", 5
    dragonBoatFestival = "Dragon Boat Festival", "端午", 3
    nationalDay = "National Day", "国庆节", 7
    midAutumnFestival = "Mid-autumn Festival", "中秋", 3


holidayDict = {
    datetime.date(year=2024, month=1, day=1).strftime("%Y-%m-%d"): Holiday.newYearsDay.value,
    datetime.date(year=2024, month=2, day=10).strftime("%Y-%m-%d"): Holiday.springFestival.value,
    datetime.date(year=2024, month=2, day=11).strftime("%Y-%m-%d"): Holiday.springFestival.value,
    datetime.date(year=2024, month=2, day=12).strftime("%Y-%m-%d"): Holiday.springFestival.value,
    datetime.date(year=2024, month=2, day=13).strftime("%Y-%m-%d"): Holiday.springFestival.value,
    datetime.date(year=2024, month=2, day=14).strftime("%Y-%m-%d"): Holiday.springFestival.value,
    datetime.date(year=2024, month=2, day=15).strftime("%Y-%m-%d"): Holiday.springFestival.value,
    datetime.date(year=2024, month=2, day=16).strftime("%Y-%m-%d"): Holiday.springFestival.value,
    datetime.date(year=2024, month=2, day=17).strftime("%Y-%m-%d"): Holiday.springFestival.value,
    datetime.date(year=2024, month=4, day=4).strftime("%Y-%m-%d"): Holiday.tombSweepingDay.value,
    datetime.date(year=2024, month=4, day=5).strftime("%Y-%m-%d"): Holiday.tombSweepingDay.value,
    datetime.date(year=2024, month=4, day=6).strftime("%Y-%m-%d"): Holiday.tombSweepingDay.value,
    datetime.date(year=2024, month=5, day=1).strftime("%Y-%m-%d"): Holiday.labourDay.value,
    datetime.date(year=2024, month=5, day=2).strftime("%Y-%m-%d"): Holiday.labourDay.value,
    datetime.date(year=2024, month=5, day=3).strftime("%Y-%m-%d"): Holiday.labourDay.value,
    datetime.date(year=2024, month=5, day=4).strftime("%Y-%m-%d"): Holiday.labourDay.value,
    datetime.date(year=2024, month=5, day=5).strftime("%Y-%m-%d"): Holiday.labourDay.value,
    datetime.date(year=2024, month=6, day=10).strftime("%Y-%m-%d"): Holiday.dragonBoatFestival.value,
    datetime.date(year=2024, month=9, day=15).strftime("%Y-%m-%d"): Holiday.midAutumnFestival.value,
    datetime.date(year=2024, month=9, day=16).strftime("%Y-%m-%d"): Holiday.midAutumnFestival.value,
    datetime.date(year=2024, month=9, day=17).strftime("%Y-%m-%d"): Holiday.midAutumnFestival.value,
    datetime.date(year=2024, month=10, day=1).strftime("%Y-%m-%d"): Holiday.nationalDay.value,
    datetime.date(year=2024, month=10, day=2).strftime("%Y-%m-%d"): Holiday.nationalDay.value,
    datetime.date(year=2024, month=10, day=3).strftime("%Y-%m-%d"): Holiday.nationalDay.value,
    datetime.date(year=2024, month=10, day=4).strftime("%Y-%m-%d"): Holiday.nationalDay.value,
    datetime.date(year=2024, month=10, day=5).strftime("%Y-%m-%d"): Holiday.nationalDay.value,
    datetime.date(year=2024, month=10, day=6).strftime("%Y-%m-%d"): Holiday.nationalDay.value,
    datetime.date(year=2024, month=10, day=7).strftime("%Y-%m-%d"): Holiday.nationalDay.value,

    datetime.date(year=2025, month=1, day=1).strftime('%Y-%m-%d'): Holiday.newYearsDay.value,
    datetime.date(year=2025, month=1, day=28).strftime('%Y-%m-%d'): Holiday.springFestival.value,
    datetime.date(year=2025, month=1, day=29).strftime('%Y-%m-%d'): Holiday.springFestival.value,
    datetime.date(year=2025, month=1, day=30).strftime('%Y-%m-%d'): Holiday.springFestival.value,
    datetime.date(year=2025, month=1, day=31).strftime('%Y-%m-%d'): Holiday.springFestival.value,
    datetime.date(year=2025, month=2, day=1).strftime('%Y-%m-%d'): Holiday.springFestival.value,
    datetime.date(year=2025, month=2, day=2).strftime('%Y-%m-%d'): Holiday.springFestival.value,
    datetime.date(year=2025, month=2, day=3).strftime('%Y-%m-%d'): Holiday.springFestival.value,
    datetime.date(year=2025, month=2, day=4).strftime('%Y-%m-%d'): Holiday.springFestival.value,
    datetime.date(year=2025, month=4, day=4).strftime('%Y-%m-%d'): Holiday.tombSweepingDay.value,
    datetime.date(year=2025, month=4, day=5).strftime('%Y-%m-%d'): Holiday.tombSweepingDay.value,
    datetime.date(year=2025, month=4, day=6).strftime('%Y-%m-%d'): Holiday.tombSweepingDay.value,
    datetime.date(year=2025, month=5, day=1).strftime('%Y-%m-%d'): Holiday.labourDay.value,
    datetime.date(year=2025, month=5, day=2).strftime('%Y-%m-%d'): Holiday.labourDay.value,
    datetime.date(year=2025, month=5, day=3).strftime('%Y-%m-%d'): Holiday.labourDay.value,
    datetime.date(year=2025, month=5, day=4).strftime('%Y-%m-%d'): Holiday.labourDay.value,
    datetime.date(year=2025, month=5, day=5).strftime('%Y-%m-%d'): Holiday.labourDay.value,
    datetime.date(year=2025, month=5, day=31).strftime('%Y-%m-%d'): Holiday.dragonBoatFestival.value,
    datetime.date(year=2025, month=6, day=1).strftime('%Y-%m-%d'): Holiday.dragonBoatFestival.value,
    datetime.date(year=2025, month=6, day=2).strftime('%Y-%m-%d'): Holiday.dragonBoatFestival.value,
    datetime.date(year=2025, month=10, day=1).strftime('%Y-%m-%d'): Holiday.nationalDay.value,
    datetime.date(year=2025, month=10, day=2).strftime('%Y-%m-%d'): Holiday.nationalDay.value,
    datetime.date(year=2025, month=10, day=3).strftime('%Y-%m-%d'): Holiday.nationalDay.value,
    datetime.date(year=2025, month=10, day=4).strftime('%Y-%m-%d'): Holiday.nationalDay.value,
    datetime.date(year=2025, month=10, day=5).strftime('%Y-%m-%d'): Holiday.nationalDay.value,
    datetime.date(year=2025, month=10, day=6).strftime('%Y-%m-%d'): Holiday.nationalDay.value,
    datetime.date(year=2025, month=10, day=7).strftime('%Y-%m-%d'): Holiday.nationalDay.value,
    datetime.date(year=2025, month=10, day=8).strftime('%Y-%m-%d'): Holiday.nationalDay.value,

}

workdayDict = {
    # 2024年双休日调休
    datetime.date(year=2024, month=2, day=4).strftime("%Y-%m-%d"): Holiday.springFestival.value,
    datetime.date(year=2024, month=2, day=18).strftime("%Y-%m-%d"): Holiday.springFestival.value,
    datetime.date(year=2024, month=4, day=7).strftime("%Y-%m-%d"): Holiday.tombSweepingDay.value,
    datetime.date(year=2024, month=4, day=28).strftime("%Y-%m-%d"): Holiday.labourDay.value,
    datetime.date(year=2024, month=5, day=11).strftime("%Y-%m-%d"): Holiday.labourDay.value,
    datetime.date(year=2024, month=9, day=14).strftime("%Y-%m-%d"): Holiday.midAutumnFestival.value,
    datetime.date(year=2024, month=9, day=29).strftime("%Y-%m-%d"): Holiday.nationalDay.value,
    datetime.date(year=2024, month=10, day=12).strftime("%Y-%m-%d"): Holiday.nationalDay.value,

    datetime.date(year=2025, month=1, day=26).strftime('%Y-%m-%d'): Holiday.springFestival.value,
    datetime.date(year=2025, month=2, day=8).strftime('%Y-%m-%d'): Holiday.springFestival.value,
    datetime.date(year=2025, month=4, day=27).strftime('%Y-%m-%d'): Holiday.labourDay.value,
    datetime.date(year=2025, month=9, day=28).strftime('%Y-%m-%d'): Holiday.nationalDay.value,
    datetime.date(year=2025, month=10, day=11).strftime('%Y-%m-%d'): Holiday.nationalDay.value,
}
