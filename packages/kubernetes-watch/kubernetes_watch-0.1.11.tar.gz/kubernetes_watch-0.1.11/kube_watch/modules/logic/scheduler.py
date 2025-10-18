from datetime import datetime
from enum import Enum

from prefect import get_run_logger
logger = get_run_logger()

class IntervalType(Enum):
    MINUTES = 'minutes'
    HOURLY = 'hourly'
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'
    SEMIANNUAL = 'semiannual'
    YEARLY = 'yearly'


def should_run_task(interval_type, interval_value=None, interval_buffer=10, specific_day=None):
    """
    The function `should_run_task` determines whether a task should run based on the specified interval
    type and values.
    
    :param interval_type: The `interval_type` parameter specifies the type of interval at which a task
    should run. It can take on the following values:
    :param interval_value: The `interval_value` parameter represents the specific value associated with
    the interval type. For example, if the interval type is `DAILY`, the `interval_value` would
    represent the specific hour at which the task should run daily. Similarly, for `WEEKLY`, it would
    represent the specific day
    :param interval_buffer: The `interval_buffer` parameter in the `should_run_task` function is a
    default value set to 20 minutes. This provides an acceptable range for a task to get executed. Suitable
    for Daily, Weekly, Monthly, etc. schedules.
    :param specific_day: The `specific_day` parameter represents the day of the week when the task
    should run in the case of a weekly interval. The values for `specific_day` are as follows:
    :return: The function `should_run_task` takes in various parameters related to different interval
    types (such as minutes, hourly, daily, weekly, monthly, quarterly, semiannual, yearly) and checks if
    the current datetime matches the specified interval criteria.
    """

    now = datetime.now()
    # Match the interval type
    if interval_type == IntervalType.MINUTES.value:
        # Runs every 'interval_value' minutes
        return now.minute % interval_value == 0
    
    if interval_type == IntervalType.HOURLY.value:
        # Runs every 'interval_value' hours on the hour
        return now.hour % interval_value == 0 and now.minute < interval_buffer
    
    if interval_type == IntervalType.DAILY.value:
        # Runs once a day at 'interval_value' hour
        return now.hour == interval_value and now.minute < interval_buffer

    if interval_type == IntervalType.WEEKLY.value:
        # Runs once a week on 'specific_day' (0=Monday, 6=Sunday)
        return now.weekday() == specific_day and now.hour == 0 and now.minute < interval_buffer
    
    if interval_type == IntervalType.MONTHLY.value:
        # Runs on the 'interval_value' day of each month
        return now.day == interval_value and now.hour == 0 and now.minute < interval_buffer
    
    if interval_type == IntervalType.QUARTERLY.value:
        # Runs on the first day of each quarter
        return now.month % 3 == 1 and now.day == 1 and now.hour == 0 and now.minute < interval_buffer
    
    if interval_type == IntervalType.SEMIANNUAL.value:
        # Runs on the first day of the 1st and 7th month
        return (now.month == 1 or now.month == 7) and now.day == 1 and now.hour == 0 and now.minute < interval_buffer
    
    if interval_type == IntervalType.YEARLY.value:
        # Runs on the first day of the year
        return now.month == 1 and now.day == 1 and now.hour == 0 and now.minute < interval_buffer

    return False

