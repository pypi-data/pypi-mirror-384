from datetime import timezone, timedelta, datetime
import holidayskr

def is_korean_holiday(holiday_name: str, *, tz: timezone = None) -> bool:
    """
    a function that detects that if today is a holiday or not

    default tz is UTF+9 (South Korea)
    """
    if tz == None:
        tz = timezone(timedelta(hours=9))
    today = datetime.now(tz).date()
    holidays = holidayskr.year_holidays(str(today.year))
    for holiday, name in holidays:
        if holiday == today:
            return name == holiday_name
    return False