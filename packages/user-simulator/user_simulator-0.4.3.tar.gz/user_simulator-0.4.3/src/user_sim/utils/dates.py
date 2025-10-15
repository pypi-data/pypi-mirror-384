import re
import random
from user_sim.utils.exceptions import *
from datetime import datetime, timedelta


def get_random_date() -> str:
    """
    Generate a random valid date string in the format "day/month/year".

    The function randomly selects a year between 0 and 3000,
    a month between 1 and 12, and then picks a valid day for that month.
    February accounts for leap years, using the Gregorian rule:
    - Leap year if divisible by 4.
    - Except years divisible by 100, unless divisible by 400.

    Returns:
        str: A date string in the format "DD/MM/YYYY".
    """
    year = random.randint(0, 3000)
    month = random.randint(1, 12)

    if month in [1, 3, 5, 7, 8, 10, 12]:
        day = random.randint(1, 31)
    elif month == 2:
        if year % 4 == 0:
            day = random.randint(1, 29)
        else:
            day = random.randint(1, 28)
    else:
        day = random.randint(1, 30)

    return f"{day}/{month}/{year}"


def get_date_range(start, end, step, date_type) -> list[str]:
    """
    Generate a list of date strings between two given dates, based on the specified method.

    Args:
        start (datetime): The starting date.
        end (datetime): The ending date.
        step (int): The step size, meaning depends on `date_type`.
        date_type (str): Defines how the date range is generated. Supported options:
            - "linspace": Divide the interval [start, end] into `step` equally spaced dates.
            - "day": Increment dates by `step` days until reaching or passing `end`.
            - "month": Increment dates by `step` months (approximated as 30 days each).
            - "year": Increment dates by `step` years (approximated as 365 days each).
            - "random": Select `step` random dates between `start` and `end`.

    Returns:
        list[str]: List of date strings formatted as "DD/MM/YYYY".

    Raises:
        InvalidFormat: If `date_type` is not one of the supported options.
    """
    if 'linspace' in date_type:
        total_seconds = (end - start).total_seconds()
        interval_seconds = total_seconds / (step - 1) if step > 1 else 0
        range_date_list = [(start + timedelta(seconds=interval_seconds * i)).strftime('%d/%m/%Y') for i in range(step)]

    elif date_type in ['day', 'month', 'year']:
        if 'month' in date_type:
            step = 30 * step
        elif 'year' in date_type:
            step = 365 * step

        range_date_list = [start.strftime('%d/%m/%Y')]
        while end > start:
            start = start + timedelta(days=step)
            range_date_list.append(start.strftime('%d/%m/%Y'))

    elif 'random' in date_type:
        delta = end - start
        random_dates = [
            (start + timedelta(days=random.randint(0, delta.days))).strftime('%d/%m/%Y') for _ in range(step)
        ]
        return random_dates

    else:
        raise InvalidFormat(f"The following parameter does not belong to date range field: {date_type}")

    return range_date_list


def get_fake_date() -> str:
    """
    Generate a fake (invalid) date string.

    This function deliberately produces dates that cannot exist in a real calendar,
    for example:
    - Days greater than 28 for February or greater than 31 in general.
    - Months greater than 12.
    - Years within a fixed range (2000–2099), but combined with invalid days/months.

    The purpose is typically for testing validation functions that should reject
    malformed or impossible dates.

    Returns:
        str: A string representing a fake date in the format "DD/MM/YYYY".
    """
    fake_day = random.randint(29, 99)
    fake_month = random.randint(13, 99)
    fake_year = random.randint(2000, 2099)

    return f"{fake_day}/{fake_month}/{fake_year}"


def get_date_list(date: dict) -> list:
    """
    Generate a list of dates based on different strategies defined in the input dictionary.

    This function supports multiple ways of generating date values:

    - **custom**: Uses predefined dates provided by the user.
      Example: {"custom": ["01/01/2025", "15/02/2025"]}

    - **random**: Generates a given number of random valid dates in the range
      year=0–3000.
      Example: {"random": 3}

    - **set**: Generates dates relative to today's date.
        * ">today(N)" → N random future dates (within 365 days from today).
        * "<today(N)" → N random past dates (within 365 days from today).
      Example: {"set": "today(5)>today"}

    - **range**: Generates dates between a start and end date.
        * With **step**:
            - `"linspace(N)"` → evenly spaced N dates between start and end.
            - `"day(N)"`, `"month(N)"`, `"year(N)"` → increments of N days/months/years.
        * With **random**: Generates a number of random dates in the given range.
      Example:
        {
            "range": {
                "min": "01/01/2020",
                "max": "01/01/2025",
                "step": "day(10)"
            }
        }

    - **fake**: Generates intentionally invalid dates (days > 31, months > 12).
      Useful for testing validation.
      Example: {"fake": 5}

    Args:
        date (dict): Dictionary specifying one or more strategies for date generation.

    Returns:
        list: A list of date strings in format "DD/MM/YYYY".

    Raises:
        InvalidFormat: If an unsupported step type is provided in the "range" field.

    Example:
        >>> get_date_list({"custom": "01/01/2025"})
        ['01/01/2025']

        >>> get_date_list({"random": 2})
        ['14/07/1580', '29/03/2521']

        >>> get_date_list({
        ...   "range": {"min": "01/01/2020", "max": "01/01/2021", "step": "month(2)"}
        ... })
        ['01/01/2020', '01/03/2020', '01/05/2020', '01/07/2020', '01/09/2020', '01/11/2020', '01/01/2021']
    """
    custom_dates = []
    generated_dates = []
    if 'custom' in date:
        if isinstance(date['custom'], list):
            custom_dates = date['custom']
        else:
            custom_dates = [date['custom']]

    if 'random' in date:
        value = date['random']
        random_dates = []
        for i in range(value):
            str_date = get_random_date()
            random_dates.append(str_date)
        generated_dates += random_dates

    if 'set' in date:
        value = int(re.findall(r'today\((.*?)\)', date['set'])[0])

        if '>today' in date['set']:
            today = datetime.now()
            next_dates = [
                (today + timedelta(days=random.randint(1, 365))).strftime('%d/%m/%Y') for _ in range(value)
            ]
            generated_dates += next_dates

        elif '<today' in date['set']:
            today = datetime.now()
            previous_dates = [
                (today - timedelta(days=random.randint(1, 365))).strftime('%d/%m/%Y') for _ in range(value)
            ]
            generated_dates += previous_dates

    if 'range' in date:
        start = datetime.strptime(date['range']['min'], '%d/%m/%Y')
        end = datetime.strptime(date['range']['max'], '%d/%m/%Y')
        if 'step' in date['range']:
            step_value = int(re.findall(r'\((.*?)\)', date['range']['step'])[0])

            if 'linspace' in date['range']['step']:
                list_of_dates = get_date_range(start, end, step_value, 'linspace')
                generated_dates += list_of_dates

            elif 'day' in date['range']['step']:
                list_of_dates = get_date_range(start, end, step_value, 'day')
                generated_dates += list_of_dates

            elif 'month' in date['range']['step']:
                list_of_dates = get_date_range(start, end, step_value, 'month')
                generated_dates += list_of_dates

            elif 'year' in date['range']['step']:
                list_of_dates = get_date_range(start, end, step_value, 'year')
                generated_dates += list_of_dates
            else:
                raise InvalidFormat(f"The following parameter does not belong "
                                    f"to date range field: {date['range']['step']}")

        elif 'random' in date['range']:
            value = date['range']['random']
            list_of_dates = get_date_range(start, end, value, 'random')
            generated_dates += list_of_dates

    if 'fake' in date:
        num_dates = date["fake"]

        fake_date_list = []
        while len(fake_date_list) < num_dates:
            fake_date = get_fake_date()
            if fake_date not in fake_date_list:
                fake_date_list.append(get_fake_date())

        generated_dates += fake_date_list

    final_date_list = generated_dates + custom_dates
    return final_date_list