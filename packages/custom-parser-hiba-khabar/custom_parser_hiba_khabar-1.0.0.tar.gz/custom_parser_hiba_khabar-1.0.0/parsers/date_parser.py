import re

DATE_RE = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")

def _valid_calendar_date(day: int, month: int, year: int) -> bool:
    if not (1 <= year <= 9999 and 1 <= month <= 12 and 1 <= day <= 31):
        return False
    month_days = {
        1: 31, 2: 28 + (1 if (year % 400 == 0 or (year % 4 == 0 and year % 100 != 0)) else 0),
        3: 31, 4: 30, 5: 31, 6: 30,
        7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
    }
    return day <= month_days[month]

def parse_date(date_string: str) -> dict:
    m = DATE_RE.match(date_string.strip())
    if not m:
        return {}
    day, month, year = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    if not _valid_calendar_date(day, month, year):
        return {}
    return {"day": day, "month": month, "year": year}
