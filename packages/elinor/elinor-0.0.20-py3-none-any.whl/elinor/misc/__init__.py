from datetime import datetime, timezone
from .timer import timer

def o_d(td:int=0, tz:timezone=None):
    if tz is not None:
        return datetime.now(tz)
    if td !=0:
        tz = timezone(datetime.timedelta(hours=td))
        return datetime.now(tz)
    now = datetime.now()
    return now.astimezone()
