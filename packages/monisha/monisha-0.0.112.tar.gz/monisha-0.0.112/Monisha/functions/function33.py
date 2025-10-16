import pytz
from datetime import datetime
#===============================================================================

class SchedulER:

    async def get20():
        nowaes = datetime.now(tz=pytz.timezone("Asia/Kolkata"))
        mineed = nowaes.replace(hour=0, minute=0, second=0, microsecond=0)
        return (mineed - nowaes).seconds

#===============================================================================

class Schedules:

    def __init__(self, **kwargs):
        self.moon01 = kwargs.get("hours", 0)
        self.moon02 = kwargs.get("minutes", 0)
        self.moon03 = kwargs.get("seconds", 0)
        self.moon04 = kwargs.get("microsecond", 0)
        self.moon05 = kwargs.get("zone", "Asia/Kolkata")

    def get01(self):
        nowaes = datetime.now(tz=pytz.timezone(self.moon05))
        mineed = nowaes.replace(hour=self.moon01, minute=self.moon02,
                                second=self.moon03, microsecond=self.moon04)
        return (mineed - nowaes).seconds

    async def get02(self):
        nowaes = datetime.now(tz=pytz.timezone(self.moon05))
        mineed = nowaes.replace(hour=self.moon01, minute=self.moon02,
                                second=self.moon03, microsecond=self.moon04)
        return (mineed - nowaes).seconds

#===============================================================================


"""
from datetime import datetime, timedelta

def seconds_until_next_115959():
    now = datetime.now()
    target = datetime(now.year, now.month, now.day, 23, 59, 59)
    
    # If it's already past 11:59:59 PM, move to the next day's 11:59:59 PM
    if now > target:
        target += timedelta(days=1)

    return int((target - now).total_seconds())

remaining_seconds = seconds_until_next_115959()
print("Seconds remaining until next 11:59:59 PM:", remaining_seconds)


import arrow

def seconds_until_next_115959():
    now = arrow.now()
    target = now.replace(hour=23, minute=59, second=59, microsecond=0)

    # If the current time is past 11:59:59 PM, move to the next day's 11:59:59 PM
    if now > target:
        target = target.shift(days=1)

    return (target - now).total_seconds()

remaining_seconds = int(seconds_until_next_115959())
print("Seconds remaining until next 11:59:59 PM:", remaining_seconds)
"""
