"""Love calculator functions with proper error handling"""
from datetime import datetime


def days_together(start_date):
    """
    Calculate days together since a special date

    Args:
        start_date: String in format 'YYYY-MM-DD'

    Returns:
        dict: Dictionary with total days, years, and message

    Raises:
        ValueError: If date format is invalid
    """
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
    except ValueError as e:
        raise ValueError(
            f"Invalid date format. Please use 'YYYY-MM-DD'. Error: {str(e)}"
        )

    today = datetime.now()

    if start > today:
        raise ValueError("Start date cannot be in the future!")

    days = (today - start).days
    years = days // 365
    remaining_days = days % 365

    return {
        'total_days': days,
        'years': years,
        'days_after_years': remaining_days,
        'message': f"We have been together for {days} amazing days! That is {years} years and {remaining_days} days of love!"
    }


def love_percentage(name1="You", name2="Bellu"):
    """
    Calculate love percentage

    Args:
        name1: First name (default: "You")
        name2: Second name (default: "Bellu")

    Returns:
        str: Love percentage message
    """
    if not isinstance(name1, str) or not isinstance(name2, str):
        return "Please provide valid names!"

    if "bellu" in name2.lower():
        return "100% - Perfect Match! True Love Forever!"

    return "100% - True Love Always!"
