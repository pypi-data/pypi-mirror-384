from datetime import time


def format_time(ftime: time) -> str:
    """
    Converts a time object to calibsun api's format.

    :param time: The time object to be formatted.
    :return: The formatted time string.
    """
    try:
        strime = ftime.strftime("%H%M")
        return strime
    except ValueError as e:
        raise ValueError(f"Error formatting time: {e}")
