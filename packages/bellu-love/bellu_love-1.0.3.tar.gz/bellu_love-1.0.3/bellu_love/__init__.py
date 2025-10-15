"""
Bellu Love - A romantic Python library dedicated to Bellu
==========================================================

A collection of romantic functions including love messages, poems,
ASCII art, and love calculators.

Quick Start
-----------
>>> import bellu_love
>>> bellu_love.quick_start()  # View full documentation
>>> print(bellu_love.daily_love_message())
>>> print(bellu_love.heart_art())

For more information, use help(bellu_love)
"""

__version__ = "1.0.3"
__author__ = "BITANU"

from .messages import (
    daily_love_message,
    random_compliment,
    love_poem,
    good_morning,
    good_night
)
from .ascii_art import heart_art, love_banner, bellu_name_art
from .love_calculator import days_together, love_percentage
from .romantic_utils import love_reminder, create_love_note


def quick_start(show_examples=True):
    """
    Display comprehensive documentation for Bellu Love package

    Args:
        show_examples: If True, shows usage examples (default: True)
    """
    # ANSI color codes for terminal formatting
    PINK = '\u001B[95m'
    RED = '\u001B[91m'
    GREEN = '\u001B[92m'
    YELLOW = '\u001B[93m'
    BLUE = '\u001B[94m'
    CYAN = '\u001B[96m'
    BOLD = '\u001B[1m'
    UNDERLINE = '\u001B[4m'
    RESET = '\u001B[0m'

    doc = f"""
{PINK}{BOLD}{'='*70}
                        BELLU LOVE
         A Romantic Python Library Dedicated to Bellu
{'='*70}{RESET}

{GREEN}Author : BITANU {RESET}
{CYAN}{BOLD}TABLE OF CONTENTS{RESET}
{YELLOW}1.{RESET} Installation
{YELLOW}2.{RESET} Quick Start
{YELLOW}3.{RESET} Features Overview
{YELLOW}4.{RESET} Function Reference
{YELLOW}5.{RESET} Usage Examples
{YELLOW}6.{RESET} Getting Help

{PINK}{'─'*70}{RESET}

{CYAN}{BOLD}INSTALLATION{RESET}

Install using pip:
    {GREEN}pip install bellu-love{RESET}

Verify installation:
    {GREEN}import bellu_love{RESET}
    {GREEN}print(bellu_love.__version__){RESET}

{PINK}{'─'*70}{RESET}

{CYAN}{BOLD}QUICK START{RESET}

{GREEN}import bellu_love{RESET}

# Display welcome art
{GREEN}print(bellu_love.bellu_name_art()){RESET}

# Get a love message
{GREEN}message = bellu_love.daily_love_message(){RESET}

# Show heart art
{GREEN}art = bellu_love.heart_art(){RESET}

# Calculate days together
{GREEN}stats = bellu_love.days_together('2020-01-15'){RESET}

{PINK}{'─'*70}{RESET}

{CYAN}{BOLD}FEATURES OVERVIEW{RESET}

{YELLOW}📧 MESSAGES MODULE{RESET}
  • daily_love_message() - Get random daily love messages
  • random_compliment() - Get random compliments
  • love_poem() - Read romantic poems
  • good_morning() - Morning greetings
  • good_night() - Night greetings

{YELLOW}🎨 ASCII ART MODULE{RESET}
  • heart_art() - Display heart designs
  • love_banner() - Show love banners
  • bellu_name_art() - Display BELLU name art

{YELLOW}💯 LOVE CALCULATOR MODULE{RESET}
  • days_together(date) - Calculate days since special date
  • love_percentage(name1, name2) - Calculate compatibility

{YELLOW}⏰ ROMANTIC UTILS MODULE{RESET}
  • love_reminder() - Get love reminders
  • create_love_note(message) - Create custom love notes

{PINK}{'─'*70}{RESET}

{CYAN}{BOLD}FUNCTION REFERENCE{RESET}

{BOLD}Messages Functions:{RESET}

  {GREEN}daily_love_message(){RESET}
    Returns a random sweet daily message
    Parameters: None
    Returns: string

  {GREEN}random_compliment(){RESET}
    Returns a random heartfelt compliment
    Parameters: None
    Returns: string

  {GREEN}love_poem(){RESET}
    Returns a romantic poem
    Parameters: None
    Returns: multi-line string

  {GREEN}good_morning(){RESET}
    Returns a good morning message
    Parameters: None
    Returns: string

  {GREEN}good_night(){RESET}
    Returns a good night message
    Parameters: None
    Returns: string

{BOLD}ASCII Art Functions:{RESET}

  {GREEN}heart_art(){RESET}
    Returns heart ASCII art
    Parameters: None
    Returns: formatted string

  {GREEN}love_banner(){RESET}
    Returns a love banner
    Parameters: None
    Returns: formatted string

  {GREEN}bellu_name_art(){RESET}
    Returns BELLU name in large letters
    Parameters: None
    Returns: formatted string

{BOLD}Love Calculator Functions:{RESET}

  {GREEN}days_together(start_date){RESET}
    Calculates days together since a special date
    Parameters: start_date (string, format: 'YYYY-MM-DD')
    Returns: dictionary with:
      - total_days: integer
      - years: integer
      - days_after_years: integer
      - message: string
    Raises: ValueError if invalid date

  {GREEN}love_percentage(name1='You', name2='Bellu'){RESET}
    Calculates love percentage between two names
    Parameters: name1, name2 (strings, optional)
    Returns: formatted percentage string

{BOLD}Utility Functions:{RESET}

  {GREEN}love_reminder(){RESET}
    Returns a random love reminder
    Parameters: None
    Returns: string

  {GREEN}create_love_note(custom_message=''){RESET}
    Creates a formatted love note
    Parameters: custom_message (string, optional, max 50 chars)
    Returns: formatted note with date

{PINK}{'─'*70}{RESET}
"""

    print(doc)

    if show_examples:
        examples = f"""
{CYAN}{BOLD}USAGE EXAMPLES{RESET}

{YELLOW}Example 1: Daily Love Routine{RESET}

{GREEN}import bellu_love

# Morning routine
print(bellu_love.good_morning())
print(bellu_love.daily_love_message())

# Evening routine
print(bellu_love.good_night()){RESET}

{PINK}{'─'*70}{RESET}

{YELLOW}Example 2: Special Occasion Display{RESET}

{GREEN}import bellu_love

# Display name art
print(bellu_love.bellu_name_art())

# Show heart
print(bellu_love.heart_art())

# Read poem
print(bellu_love.love_poem()){RESET}

{PINK}{'─'*70}{RESET}

{YELLOW}Example 3: Anniversary Celebration{RESET}

{GREEN}import bellu_love

# Calculate time together (replace with your date)
stats = bellu_love.days_together('2020-01-15')

print(stats['message'])
print(f"Total days: {{stats['total_days']}}")
print(f"Years: {{stats['years']}}")

# Check compatibility
print(bellu_love.love_percentage("Me", "Bellu")){RESET}

{PINK}{'─'*70}{RESET}

{YELLOW}Example 4: Create Custom Love Note{RESET}

{GREEN}import bellu_love

# Custom message
note = bellu_love.create_love_note("You light up my world!")
print(note)

# Default message
note_default = bellu_love.create_love_note()
print(note_default){RESET}

{PINK}{'─'*70}{RESET}

{YELLOW}Example 5: Random Love Expressions{RESET}

{GREEN}import bellu_love

print(bellu_love.random_compliment())
print(bellu_love.love_reminder())
print(bellu_love.love_banner()){RESET}

{PINK}{'─'*70}{RESET}
"""
        print(examples)

    help_section = f"""
{CYAN}{BOLD}GETTING HELP{RESET}

View detailed documentation:
    {GREEN}help(bellu_love){RESET}

View function-specific help:
    {GREEN}help(bellu_love.days_together){RESET}
    {GREEN}help(bellu_love.create_love_note){RESET}

List all functions:
    {GREEN}print(dir(bellu_love)){RESET}

Check version:
    {GREEN}print(bellu_love.__version__){RESET}

Read function documentation:
    {GREEN}print(bellu_love.days_together.__doc__){RESET}

{PINK}{'─'*70}{RESET}

{CYAN}{BOLD}ERROR HANDLING{RESET}

{YELLOW}Common Errors:{RESET}

{RED}ValueError: Invalid date format{RESET}
  Solution: Use 'YYYY-MM-DD' format
  Example: {GREEN}bellu_love.days_together('2020-01-15'){RESET}

{RED}ValueError: Start date cannot be in the future{RESET}
  Solution: Use only past dates
  Example: {GREEN}bellu_love.days_together('2020-01-15'){RESET}

{PINK}{'─'*70}{RESET}

{CYAN}{BOLD}REQUIREMENTS{RESET}

• Python 3.8 or higher
• No external dependencies required
• Works on all platforms (Windows, macOS, Linux)

{PINK}{'─'*70}{RESET}

{PINK}{BOLD}Made with ❤️  for Bellu{RESET}

Version: {__version__}
For more information: {BLUE}https://pypi.org/project/bellu-love/{RESET}

{PINK}{'='*70}{RESET}
"""

    print(help_section)


def readme():
    """
    Display the complete README documentation
    Alias for quick_start()
    """
    quick_start(show_examples=True)


__all__ = [
    'daily_love_message',
    'random_compliment',
    'love_poem',
    'good_morning',
    'good_night',
    'heart_art',
    'love_banner',
    'bellu_name_art',
    'days_together',
    'love_percentage',
    'love_reminder',
    'create_love_note',
    'quick_start',
    'readme'
]
