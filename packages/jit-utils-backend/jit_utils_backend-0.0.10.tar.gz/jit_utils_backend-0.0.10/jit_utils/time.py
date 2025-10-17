# -*-coding:utf-8-*-
"""
Created on 2023/9/25

@author: 臧韬

@desc: 默认描述
"""
import arrow
import datetime
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from dateutil.tz import tz
from operator import eq, ge, gt, le, lt, ne

import time
from .workday_constants import holidayDict, workdayDict

ONE_DAY_SECONDS = 24 * 60 * 60
ONE_WEEK_MSECONDS = 7 * 24 * 60 * 60
ONE_DAY_MSECONDS = 24 * 60 * 60 * 1000
HALF_MONTH_MSECONDS = 60 * 60 * 24 * 1000 * 15
ONE_MONTH_MSECONDS = 60 * 60 * 24 * 1000 * 30
ONE_YEAR_MSECONDS = 60 * 60 * 24 * 1000 * 365

timeZone = tz.tzlocal()


def get(date):
    return arrow.get(date, tzinfo=timeZone)


def now():
    """
    当前时间
    :return:
    """
    return arrow.now(tz=timeZone).naive


def today():
    """
    今天
    :return:
    """
    return now().floor("day").naive


def dayShift(date, days):
    """
    日期偏移
    :param date:
    :param days:
    :return:
    """
    return get(date).shift(days=days).naive


def monday():
    """
    本周一
    :return:
    """
    return now().floor("week").naive


def weekShift(date, weeks):
    """
    星期偏移
    :return:
    """
    return get(date).shift(weeks=weeks).naive


def monthStart():
    """
    月初
    :return:
    """
    return now().floor("month").naive


def monthShift(date, months):
    """
    月偏移
    :return:
    """
    return get(date).shift(months=months).naive


def quarterStart():
    """
    本季度
    :return:
    """
    return now().floor("quarter").naive


def quarterShift(date, quarters):
    """
    季度偏移
    :param date:
    :param quarters:
    :return:
    """
    return get(date).shift(quarters=quarters).naive


def yearStart():
    """
    本年
    :return:
    """
    return now().floor("year").naive


def yearShift(date, years):
    """
    年偏移
    :param date:
    :param years:
    :return:
    """
    return get(date).shift(years=years).naive


def getTimestamp():
    return int(time.time() * 1000)


def timeStampToDateTime(ts):
    # 带微秒需要去掉后三位
    if ts >= 10 ** 10:
        ts //= 10 ** 3
    dt = datetime.datetime.fromtimestamp(ts)
    return dt


def strToTimestamp(dateStr, arrowFmt="YYYY-MM-DD HH:mm:ss", datetimeFmt="%Y-%m-%d %H:%M:%S"):
    """
    字符串转时间戳
    """
    if isinstance(dateStr, datetime.datetime):
        dateStr = datetime.datetime.strftime(dateStr, datetimeFmt)
    return arrow.get(dateStr, arrowFmt).timestamp()


def timeStampToDate(ts):
    return timeStampToDateTime(ts).date()


def datetime2string(dt, fmt="%Y-%m-%d"):
    if isinstance(dt, datetime.datetime):
        return datetime.datetime.strftime(dt, fmt)
    else:
        return ""


def currentTimedelta(*args, **kwargs):
    return datetime.datetime.now() + datetime.timedelta(*args, **kwargs)


def nowNoMicrosecond():
    """获取不包含毫秒时间的当前时间"""
    return datetime.datetime.now().replace(microsecond=0)


def formatNow(fmt="%Y-%m-%d"):
    return datetime.datetime.strftime(datetime.datetime.now(), fmt)


def getNowTimestampFmt(fmt):
    nowStr = formatNow(fmt=fmt)
    dt = string2datetime(nowStr, fmt=fmt)
    return datetime2timestamp(dt)


def datetime2timestamp(dt):
    if not isinstance(dt, datetime.datetime):
        return dt
    return int(time.mktime(dt.timetuple()) * 1000)


def dateTimestamps(day=0):
    """生成账单日期 为前一天"""
    dt = datetime.date.today() + datetime.timedelta(days=-day)
    return int(time.mktime(dt.timetuple()) * 1000)


def timestamp2date(timeStamp):
    """timestamp date 转换"""
    dt = datetime.datetime.fromtimestamp(timeStamp)
    return dt.strftime("%Y-%m-%d")


def getEveryDate(beginDate, endDate):
    """获取 2个日期之间的所有日期"""
    beginDate = timestamp2date(int(float(beginDate / 1000)))
    endDate = timestamp2date(int(float(endDate / 1000)))
    dateList = []
    beginDate = datetime.datetime.strptime(beginDate, "%Y-%m-%d")
    endDate = datetime.datetime.strptime(endDate, "%Y-%m-%d")
    while beginDate <= endDate:
        dateStr = int(time.mktime(beginDate.timetuple()))  # beginDate.strftime("%Y-%m-%d")
        dateList.append(dateStr)
        beginDate += datetime.timedelta(days=1)
    return dateList


def getXDayBefore(x, tsFlag=False):
    """获取x天前日期  tsFlag为True则返回时间戳"""
    dt = datetime.datetime.now() - datetime.timedelta(days=x)
    if tsFlag:
        return int(dt.timestamp() * 1000)
    return dt


def datetime2special(dt, days, hmstr):
    """
    2018-11-22 21:11:25
    @param days: 天数 1
    @param hmstr: '09:00'
    @return: 2018-11-23 09:00:00
    """
    if days:
        dt = dt + datetime.timedelta(days=days)
    if hmstr:
        hmList = hmstr.split(":")
        dt = datatypes.replace(hour=int(hmList[0]))
        dt = datatypes.replace(minute=int(hmList[-1]))
        dt = datatypes.replace(second=0)
    return dt


def string2datetime(dtStr, fmt="%Y-%m-%d"):
    if dtStr:
        return datetime.datetime.strptime(dtStr, fmt)
    else:
        return None


def string2date(dtStr, splitStr="-"):
    """splitStr 分割符，默认样式是 2020-10-05"""
    if dtStr:
        return datetime.date(*map(int, dtStr.split(splitStr)))
    else:
        return None


def datetimeYymmdd():
    return str(datetime.datetime.now()).replace(" ", "").replace(":", "").replace(".", "").replace("-", "")[:-12]


def datetimeYymmddhhmmss():
    return str(datetime.datetime.now()).replace(" ", "").replace(":", "").replace(".", "").replace("-", "")[:-6]


def specialYymmddhhmmss(ts):
    dt = timestamp2datetime(ts)
    return str(dt).replace(" ", "").replace(":", "").replace(".", "").replace("-", "")


def getZeroTimestamp(ts=None):
    """获取今天0点的时间戳"""
    ts = ts or getTimestamp()
    dt = timestamp2datetime(ts)
    return datetime2timestamp(datetime.datetime(dt.year, dt.month, dt.day, 0, 0, 0))


def getNextZeroTimestamp(ts=None):
    ts = ts or getTimestamp()
    dt = timestamp2datetime(ts) + datetime.timedelta(days=1)
    return datetime2timestamp(datetime.datetime(dt.year, dt.month, dt.day, 0, 0, 0))


def getNextMonthDay(ts=None):
    ts = ts or getTimestamp()
    date = timestamp2datetime(ts)
    nextDt = date + relativedelta(months=1)
    return datetime2timestamp(nextDt)


def getPrevMonthDay(ts=None):
    ts = ts or getTimestamp()
    date = timestamp2datetime(ts)
    nextDt = date + relativedelta(months=-1)
    return datetime2timestamp(nextDt)


def getPrevZeroTimestamp(ts=None):
    """获取昨天0点的时间戳"""
    ts = ts or getTimestamp()
    dt = timestamp2datetime(ts) + datetime.timedelta(days=-1)
    return datetime2timestamp(datetime.datetime(dt.year, dt.month, dt.day, 0, 0, 0))


def getMonthStartTimestamp(ts=None):
    ts = ts or getTimestamp()
    dt = timestamp2datetime(ts)
    dt = datetime.datetime(dt.year, dt.month, 1, 0, 0, 0)
    return datetime2timestamp(dt)


def getNextMonthStartTimestamp(ts=None):
    ts = ts or getTimestamp()
    dt = timestamp2datetime(ts)
    dt = dt + relativedelta(months=1)
    dt = datetime.datetime(dt.year, dt.month, 1, 0, 0, 0)
    return datetime2timestamp(dt)


def getReduceTimestamp(standTime):
    return time.time() * 10 - standTime


def getTimestampSecond():
    return int(time.time())


def getTodayStr():
    return str(datetime.date.today())


def getSecondTimestamp(afterSeconds=0):
    """afterSeconds 多少秒后的时间"""
    return int(time.time()) + afterSeconds


def getMinuteTimestamp():
    now = datetime.datetime.now()
    return int(time.mktime(now.timetuple())) - now.second


def timestamp2datetime(ts):
    strSt = str(ts)
    if len(strSt) > 10:
        ts = int(strSt[:-3])
    dt = datetime.datetime.fromtimestamp(ts)
    return dt


def getNextMonthZeroTs(ts):
    dt = timestamp2datetime(ts)
    if dt.month == 12:
        nextMonthDate = datetime.datetime(dt.year + 1, 1, 1)
    else:
        nextMonthDate = datetime.datetime(dt.year, dt.month + 1, 1)
    return datetime2timestamp(nextMonthDate)


def timestamp2string(ts, fmt="%Y-%m-%d %H:%M:%S"):
    dt = timestamp2datetime(ts)
    return datetime2string(dt, fmt)


def cmpTsSameDay(ts1, ts2):
    dt1 = timestamp2datetime(ts1)
    dt2 = timestamp2datetime(ts2)

    dtstr1 = datetime2string(dt1)
    dtstr2 = datetime2string(dt2)

    if dtstr1 and dtstr2 and dtstr1 == dtstr2:
        return True
    return False


def cmpTsMinutes(ts1, ts2):
    return int((ts2 - ts1) / (1000 * 60))


def formatStr(jsfmtstr):
    return (
        jsfmtstr.replace("YYYY", "%Y")
        .replace("MM", "ppp")
        .replace("M", "%m")
        .replace("DD", "ooo")
        .replace("D", "%d")
        .replace("HH", "%H")
        .replace("mm", "%M")
        .replace("ss", "%S")
        .replace("ppp", "%m")
        .replace("ooo", "%d")
    )


def formatMysqlStr(pyFmtStr):
    return (
        pyFmtStr.replace("YYYY", "%Y")
        .replace("MM", "ppp")
        .replace("M", "%m")
        .replace("DD", "ooo")
        .replace("D", "%d")
        .replace("HH", "%H")
        .replace("mm", "%i")
        .replace("ss", "%S")
        .replace("ppp", "%m")
        .replace("ooo", "%d")
    )


def nowYyyymmddhhmmss():
    """
    @return: 当天时间 如 2018-12-12 20:57:43
    """
    dtstr = str(datetime.datetime.now())
    return dtstr.split(".")[0]


def nowYyyymmddhhmm():
    """
    @return: 当天时间 如 2018-12-12 20:57
    """
    dtstr = str(datetime.datetime.now())
    return dtstr.rsplit(":", 1)[0]


def string2timestamp(string, fmt="%Y-%m-%d"):
    return int(time.mktime(string2datetime(string, fmt=fmt).timetuple())) * 1000


def deltaTime(ts1, ts2):
    """
    ts1 和 ts2 的时间差
    """
    if len("%s" % ts1) == 13:
        ts1 = ts1 / 1000.0
    if len("%s" % ts2) == 13:
        ts2 = ts2 / 1000.0
    t1 = datetime.datetime.fromtimestamp(ts1)
    t2 = datetime.datetime.fromtimestamp(ts2)
    return t1 - t2


def isWorkday(dt):
    dtStr = str(dt).rsplit(" ", 1)[0]
    return bool(dtStr in workdayDict.keys() or (dt.weekday() <= 4 and dtStr not in holidayDict.keys()))


def getNextWorkTs(ts, splitDays):
    d = 0
    while d < splitDays:
        ts += 24 * 60 * 60 * 1000
        while not isWorkday(ts):
            ts += 24 * 60 * 60 * 1000
        d += 1
    return ts


def getNextDatetime(n, unit, skipHoliday=False):
    """
    获取下一个执行时间
    dt: datetime.datetime
    n: 天数 整数
    skipHoliday: 是否跳过节假日
    """
    startTime = datetime.datetime.now()
    timeMap = {
        "D": "days",
        "H": "hours",
        "M": "minutes",
    }
    if unit != "D":
        timeOffset = datetime.timedelta(**{timeMap[unit]: n})
        startTime = startTime + timeOffset
        if skipHoliday and not isWorkday(startTime):
            start = 1
            while start < 100:
                startTime += datetime.timedelta(days=1)
                if isWorkday(startTime):
                    break
                start += 1
    else:
        if skipHoliday:
            d = 0
            while d < n:
                if isWorkday(startTime):
                    startTime += datetime.timedelta(days=1)
                    d += 1
                else:
                    startTime += datetime.timedelta(days=1)

        else:
            startTime += datetime.timedelta(days=n)
    return startTime


def lastDayOfMonth(anyDay=datetime.date.today()):
    """获取月末最后一天， 返回date类型"""
    nextMonth = anyDay.replace(day=28) + datetime.timedelta(days=4)
    return nextMonth - datetime.timedelta(days=nextMonth.day)


def getXMonthZeroDt(ts, x):
    """获取x月后的第一天"""
    for _ in range(x):
        nextTs = getNextMonthZeroTs(ts)
        ts = nextTs
    return timestamp2datetime(ts)


def getFirstWorkday(dt):
    """获取当月第一个工作日"""
    firstDt = datatypes.replace(day=1)
    firstDs = datetime2timestamp(firstDt)
    while not isWorkday(firstDs):
        firstDt += relativedelta(days=1)
        firstDs = datetime2timestamp(firstDt)
    return firstDt


def getLastWorkday(dt):
    """获取当月最后一个工作日"""
    lastDay = lastDayOfMonth(dt)
    lastDt = datatypes.replace(day=lastDay.day)
    lastTs = datetime2timestamp(lastDt)
    while not isWorkday(lastTs):
        lastDt -= relativedelta(days=1)
        lastTs = datetime2timestamp(lastDt)
    return lastDt


def getDeltaDayTime(t1, t2, unit=rrule.DAILY, fmt="YYYY-MM-DD HH:mm:ss"):
    """
    获取时间差值 t2 - t1, 单位: day
    param t1: 时间1, 字符串 或者 datetime
    param t2: 时间2, 字符串 或者 datetime
    param t2: 时间2, 字符串 或者 datetime
    param unit: 差值的具体单位, 默认为 day
    return 具体的unit数, 向上兼容
        ex:
            1. t2 < t1时, 返回0
            2. t2 - t1 小于1年时, 返回1;
            2. t2 - t1 大于等于1年时, 返回 n + 1;
    """
    # 将输入转换为 Arrow 对象
    if isinstance(t1, str):
        t1 = arrow.get(t1, fmt)
    elif isinstance(t1, datetime.datetime):
        t1 = arrow.get(t1)
    if isinstance(t2, str):
        t2 = arrow.get(t2, fmt)
    elif isinstance(t2, datetime.datetime):
        t2 = arrow.get(t2)
    # 根据unit返回具体的差值
    return rrule.rrule(freq=unit, dtstart=t1, until=t2).count()


def compareDatetime(dt1, op, dt2):
    """
    比较两个datetime格式: 针对于两个datetime时区不同的情况

    dt1 op dt2
    :param dt1: 时间1(datetime格式1)
    :param op: 比较符
    :param dt2: 时间2(datetime格式2)
    """
    # 定义比较操作符字典
    ops = {
        "==": eq,
        "!=": ne,
        "<": lt,
        ">": gt,
        "<=": le,
        ">=": ge,
    }
    # 确保给定的操作符有效
    if op not in ops:
        raise ValueError("无效的比较操作符")
    # 将两个datetime都转换为UTC时间
    if dt1.tzinfo is not None and dt1.tzinfo.utcoffset(dt1) is not None:
        dt1 = dt1.astimezone(datetime.timezone.utc)
    else:
        dt1 = dt1.replace(tzinfo=datetime.timezone.utc)

    if dt2.tzinfo is not None and dt2.tzinfo.utcoffset(dt2) is not None:
        dt2 = dt2.astimezone(datetime.timezone.utc)
    else:
        dt2 = dt2.replace(tzinfo=datetime.timezone.utc)
    # 使用提供的操作符进行比较
    return ops[op](dt1, dt2)


def getDelayTime(dateStr, count, unit="days", fmt="YYYY-MM-DD HH:mm:ss"):
    """
    获取时间增加后的时间
    param dateStr: 时间字符串
    param count: 数值
    param unit: 时间单位 (days, hours, minutes, seconds, 等)
    param fmt: 时间格式字符串
    返回后延的具体时间: 时间格式datetime.datetime
    """
    # 使用 Arrow 解析输入的时间字符串
    arrowT1 = arrow.get(dateStr, fmt)
    # 将单位转换为 Arrow 支持的格式
    unitSet = {"years", "quarters", "months", "weeks", "days", "hours", "minutes", "seconds"}
    arrowUnit = unit if unit in unitSet else "days"
    # 计算后延的时间并返回
    delayedArrow = arrowT1.shift(**{arrowUnit: count})
    return delayedArrow.datetime


def getDelayMonthTime(t1, months, fmt="%Y-%m-%d %H:%M:%S"):
    """
    获取时间增加的天数值
    param t1: datetime格式时间或字符串或者时间戳
    param months: 月份
    param fmt: 时间格式字符串
    返回后延的具体时间: 时间格式datetime
    """
    if isinstance(t1, datetime.datetime):
        delayedTime = t1 + relativedelta(months=months)
    elif isinstance(t1, str):
        delayedTime = datetime.datetime.strptime(t1, fmt) + relativedelta(months=months)
    elif isinstance(t1, int):
        delayedTime = datetime.datetime.fromtimestamp(t1) + relativedelta(months=months)
    else:
        raise ValueError("不支持的时间格式")
    return delayedTime


def getValidPeriodTime(expireTime, months, fmt="%Y-%m-%d %H:%M:%S"):
    """
    获取生效的时间段
    param t1: datetime格式时间或字符串或者时间戳
    param expireTime: 过期时间, 字符串, 格式: "%Y-%m-%d %H:%M:%S"
    param months: 月份
    return startTime, endTime, 都是fmt格式的字符串
    """
    startTime = expireTime
    expireTime = string2datetime(expireTime, fmt=fmt)
    currTime = datetime.datetime.now()
    if expireTime < currTime:
        # 如果过期时间比当前时间小(已过期), 直接从当前时间开始计算具体的生效时间
        startTime = datetime2string(currTime, fmt=fmt)
        endTime = datetime2string(getDelayMonthTime(currTime, months), fmt=fmt)
    else:
        # 如果过期时间比当前时间大(未过期), 需要从实际过期时间进行计算
        endTime = datetime2string(getDelayMonthTime(expireTime, months), fmt=fmt)
    return startTime, endTime


def deltaArrowTime(arrowDate, count, unit="minute"):
    """
    时间推迟: 具体的时间按传入值, 推迟到指定时间
    :param arrowDate: arrow对象
    :param count: 推迟数值
    :param unit: 具体单位
    :return datetime.datetime格式
    """
    # 定义时间单位映射关系
    unitMapping = {
        "second": "seconds",
        "minute": "minutes",
        "hour": "hours",
        "day": "days",
        "week": "weeks",
        "month": "months",
        "year": "years",
    }
    # 确保单位是有效的
    if unit not in unitMapping:
        raise ValueError("无效的时间单位")
    # 将单位转换为 Arrow 支持的格式
    arrowUnit = unitMapping[unit]
    # 使用 shift() 方法进行时间推迟
    delayedArrow = arrowDate.shift(**{arrowUnit: count})
    # 将 Arrow 对象转换为 datetime.datetime 格式
    return delayedArrow.datetime


def datetimeToStr(dt, fmt="YYYY-MM-DD"):
    """
    将 datetime 对象转换为指定格式的字符串
    :param dt: datetime 对象
    :param fmt: 时间格式字符串
    :return: 格式化后的字符串
    """
    if isinstance(dt, datetime.datetime):
        # 使用 Arrow 格式化日期时间
        arrowDt = arrow.get(dt)
        formattedStr = arrowDt.format(fmt)
        return formattedStr
    else:
        return ""


def addYearsToDate(currDate, years, fmt="%Y-%m-%d %H:%M:%S"):
    """
    给指定日期增加年数的日期
    :param currDate: 指定日期, 字符串
    :param years: 指定增加的年数
    :param fmt: 日期格式
    :return 日期
    """
    # 使用 Arrow 解析输入的日期字符串
    arrow_date = arrow.get(currDate, fmt)

    # 添加指定年数
    new_date = arrow_date.shift(years=years)

    # 返回新日期对象的格式化字符串
    return new_date.format(fmt)
