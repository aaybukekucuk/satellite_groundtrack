import math

def cal2jd(year, month, day, hour=0, minute=0, second=0):
    if month <= 2:
        year -= 1
        month += 12

    A = math.floor(year / 100)
    B = 2 - A + math.floor(A / 4)
    
    jd_day = math.floor(365.25 * (year + 4716))
    jd_month = math.floor(30.6001 * (month + 1))
    
    fractional_day = day + (hour / 24.0) + (minute / 1440.0) + (second / 86400.0)
    
    jd = B + jd_day + jd_month + fractional_day - 1524.5
    return jd

def jd2gps(jd):
    GPS_EPOCH_JD = 2444244.5
    
    elapsed_days = jd - GPS_EPOCH_JD
    
    week = math.floor(elapsed_days / 7)
    
    tow = (elapsed_days - (week * 7)) * 86400.0
    
    return week, tow

# Test
if __name__ == "__main__":
    y, m, d = 2025, 12, 9
    jd = cal2jd(y, m, d, 12, 0, 0)
    wk, tow = jd2gps(jd)
    print(f"Date: {y}-{m}-{d} 12:00 -> JD: {jd:.5f} -> GPS Week: {wk}, TOW: {tow:.2f}")


