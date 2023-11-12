import pytz
from datetime import datetime
from app.config import TIMEZONE


def tz_now():
    tz = pytz.timezone(TIMEZONE)
    return datetime.now(tz)
