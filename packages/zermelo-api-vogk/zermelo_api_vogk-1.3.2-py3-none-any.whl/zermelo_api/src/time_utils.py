from datetime import datetime, timedelta


def get_date(datestring: str = "") -> datetime:
    try:
        date = datetime.strptime(datestring, "%Y-%m-%d")
    except:
        date = datetime.today()
    finally:
        return date


def delta_week(date: datetime, delta: int = 0) -> datetime:
    return date + timedelta(weeks=delta)


def get_year(datestring: str = "") -> int:
    return delta_week(get_date(datestring), -33).strftime("%Y")
