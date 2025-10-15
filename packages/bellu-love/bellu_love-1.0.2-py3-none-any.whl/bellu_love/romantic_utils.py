"""Romantic utility functions"""
import random
from datetime import datetime


def love_reminder():
    """Generate a random love reminder"""
    reminders = [
        "Reminder: Tell Bellu you love her!",
        "Do not forget to give Bellu a hug today!",
        "Time to send Bellu a sweet message!",
        "How about surprising Bellu with something special?",
        "Maybe make Bellu her favorite drink?",
        "Remember to make Bellu smile today!"
    ]
    return random.choice(reminders)


def create_love_note(custom_message=""):
    """
    Create a formatted love note

    Args:
        custom_message: Custom message for the note (optional)

    Returns:
        str: Formatted love note
    """
    if not custom_message or not isinstance(custom_message, str):
        custom_message = "You are the love of my life!"

    # Limit message length to prevent formatting issues
    if len(custom_message) > 50:
        custom_message = custom_message[:47] + "..."

    current_date = datetime.now().strftime('%B %d, %Y')

    note = f"""
========================================
        LOVE NOTE FOR BELLU
========================================

    {custom_message}

        Forever Yours,
        {current_date}

========================================
    """
    return note.strip()
