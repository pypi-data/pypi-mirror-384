# Bellu Love

A romantic Python library dedicated to Bellu, filled with love messages, 
poems, ASCII art, and romantic utilities.

---

## Table of Contents

1. Installation
2. Quick Start
3. Features Overview
4. Usage Guide
   - Messages Module
   - ASCII Art Module
   - Love Calculator Module
   - Romantic Utils Module
5. Function Reference
6. Examples
7. Requirements
8. Error Handling
9. Contributing
10. License
11. Author

---

## Installation

Install using pip:

```
pip install bellu-love
```

Verify installation:

```
import bellu_love
print(bellu_love.__version__)
```

---

## Quick Start

```
import bellu_love

# Display welcome art
print(bellu_love.bellu_name_art())

# Get a love message
message = bellu_love.daily_love_message()

# Show heart art
art = bellu_love.heart_art()

# Calculate days together (replace with your date)
stats = bellu_love.days_together('2020-01-15')
```

---

## Features Overview

### Messages
- Daily love messages
- Random compliments
- Romantic poems
- Morning and night greetings

### ASCII Art
- Heart designs
- Love banners
- Name art displays

### Love Calculator
- Days together calculator
- Love percentage calculator

### Romantic Utilities
- Love reminders
- Custom love note generator

---

## Usage Guide

### Messages Module

Get romantic messages and greetings for Bellu.

**daily_love_message()**
- Returns a random sweet daily message
- No parameters required
- Returns string

Example:
```
msg = bellu_love.daily_love_message()
# Returns a random love message
```

**random_compliment()**
- Returns a random heartfelt compliment
- No parameters required
- Returns string

Example:
```
compliment = bellu_love.random_compliment()
# Returns a random compliment
```

**love_poem()**
- Returns a romantic poem
- No parameters required
- Returns multi-line string

Example:
```
poem = bellu_love.love_poem()
# Returns a complete romantic poem
```

**good_morning()**
- Returns a good morning message
- No parameters required
- Returns string

Example:
```
morning = bellu_love.good_morning()
# Returns morning greeting
```

**good_night()**
- Returns a good night message
- No parameters required
- Returns string

Example:
```
night = bellu_love.good_night()
# Returns night greeting
```

---

### ASCII Art Module

Display beautiful ASCII art designs.

**heart_art()**
- Returns heart ASCII art
- No parameters required
- Returns formatted string

Example:
```
heart = bellu_love.heart_art()
print(heart)
# Displays heart design with love message
```

**love_banner()**
- Returns a love banner
- No parameters required
- Returns formatted string

Example:
```
banner = bellu_love.love_banner()
print(banner)
# Displays decorative banner
```

**bellu_name_art()**
- Returns BELLU name in large letters
- No parameters required
- Returns formatted string

Example:
```
name_art = bellu_love.bellu_name_art()
print(name_art)
# Displays BELLU in large block letters
```

---

### Love Calculator Module

Calculate romantic statistics and compatibility.

**days_together(start_date)**
- Calculates days together since a special date
- Parameter: start_date (string in 'YYYY-MM-DD' format)
- Returns dictionary with keys:
  - total_days: Total days together (integer)
  - years: Number of complete years (integer)
  - days_after_years: Remaining days (integer)
  - message: Formatted message (string)
- Raises ValueError if date format is invalid or future date

Example:
```
result = bellu_love.days_together('2020-01-15')
# Returns dict with statistics
print(result['message'])
print(result['total_days'])
```

**love_percentage(name1, name2)**
- Calculates love percentage between two names
- Parameters:
  - name1: First name (string, default: "You")
  - name2: Second name (string, default: "Bellu")
- Returns formatted percentage string
- Always returns 100% for Bellu

Example:
```
percentage = bellu_love.love_percentage("Me", "Bellu")
# Returns love percentage result
```

---

### Romantic Utils Module

Utility functions for romantic interactions.

**love_reminder()**
- Returns a random love reminder
- No parameters required
- Returns string

Example:
```
reminder = bellu_love.love_reminder()
# Returns a reminder to show love
```

**create_love_note(custom_message)**
- Creates a formatted love note
- Parameter: custom_message (string, optional)
  - If empty or not provided, uses default message
  - Maximum length: 50 characters (auto-truncated)
- Returns formatted note with date

Example:
```
note = bellu_love.create_love_note("You are amazing!")
print(note)
# Displays formatted love note

note_default = bellu_love.create_love_note()
# Uses default message
```

---

## Function Reference

### Complete Function List

**Messages:**
- daily_love_message() -> str
- random_compliment() -> str
- love_poem() -> str
- good_morning() -> str
- good_night() -> str

**ASCII Art:**
- heart_art() -> str
- love_banner() -> str
- bellu_name_art() -> str

**Love Calculator:**
- days_together(start_date: str) -> dict
- love_percentage(name1: str, name2: str) -> str

**Utilities:**
- love_reminder() -> str
- create_love_note(custom_message: str) -> str

---

## Examples

### Example 1: Daily Love Routine

```
import bellu_love

# Morning routine
print(bellu_love.good_morning())
print(bellu_love.daily_love_message())

# Evening routine
print(bellu_love.good_night())
```

### Example 2: Special Occasion Display

```
import bellu_love

# Display name art
print(bellu_love.bellu_name_art())

# Show heart
print(bellu_love.heart_art())

# Read poem
print(bellu_love.love_poem())
```

### Example 3: Anniversary Celebration

```
import bellu_love

# Calculate time together
anniversary_date = '2020-01-15'  # Replace with your date
stats = bellu_love.days_together(anniversary_date)

print(stats['message'])
print(f"Total days: {stats['total_days']}")
print(f"Years: {stats['years']}")

# Check compatibility
print(bellu_love.love_percentage("Me", "Bellu"))
```

### Example 4: Create Custom Love Note

```
import bellu_love

# Custom message
note = bellu_love.create_love_note("You light up my world!")
print(note)

# Default message
note_default = bellu_love.create_love_note()
print(note_default)
```

### Example 5: Random Love Expressions

```
import bellu_love

# Get random expressions
print(bellu_love.random_compliment())
print(bellu_love.love_reminder())
print(bellu_love.love_banner())
```

---

## Requirements

- Python 3.8 or higher
- No external dependencies required
- Works on all platforms (Windows, macOS, Linux)

---

## Error Handling

### Common Errors and Solutions

**ValueError: Invalid date format**
- Cause: Incorrect date format in days_together()
- Solution: Use 'YYYY-MM-DD' format (e.g., '2020-01-15')

Example:
```
# Correct
result = bellu_love.days_together('2020-01-15')

# Incorrect (will raise error)
# result = bellu_love.days_together('01/15/2020')
```

**ValueError: Start date cannot be in the future**
- Cause: Provided date is later than today
- Solution: Use a past date only

Example:
```
# Use only dates in the past
result = bellu_love.days_together('2020-01-15')
```

---

## Getting Help

### View Documentation in Python

```
import bellu_love

# General help
help(bellu_love)

# Function-specific help
help(bellu_love.days_together)
help(bellu_love.create_love_note)

# List all functions
print(dir(bellu_love))
```

### Common Usage Patterns

**Check version:**
```
print(bellu_love.__version__)
```

**List available functions:**
```
print([f for f in dir(bellu_love) if not f.startswith('_')])
```

**Read function documentation:**
```
print(bellu_love.days_together.__doc__)
```

---

## Contributing

This package is a personal project dedicated to Bellu. 
Suggestions and improvements are welcome!

---

## License

MIT License

Copyright (c) 2025 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files, to deal in the Software
without restriction, including without limitation the rights to use, copy,
modify, merge, publish, distribute, sublicense, and/or sell copies of the
Software, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

---

## Author

Created with love by BITANU

For Bellu - the love of my life

---

## Version History

### 1.0.0 --> 1.0.1 (2025-10-14)
- Initial release
- Messages module with 5 functions
- ASCII art module with 3 functions
- Love calculator module with 2 functions
- Romantic utilities module with 2 functions

---

**Made with ❤️ for Bellu**

For more information, visit: https://pypi.org/project/bellu-love/
```

## Why This README is Comprehensive

**Easy to print in Python** - Uses simple text formatting without complex markdown[1][2]

**Terminal-friendly** - Readable in any text viewer or terminal[1][5]

**Table of Contents** - Easy navigation to find specific information[2][4]

**Descriptive without spoilers** - Explains what functions do without revealing exact outputs[1][2]

**Clear examples** - Shows usage patterns without output clutter[2][3]

**Error handling guide** - Helps users troubleshoot common issues[2]

**Function signatures** - Shows expected parameters and return types[1][2]

**Multiple access methods** - Explains how to use help(), dir(), and __doc__[6][7]

**Version history** - Tracks changes over time[2][4]

**Structured sections** - Organized logically for easy reading[1][2][4]

Users can read this with

```python
import bellu_love
import pathlib
readme = pathlib.Path(bellu_love.__file__).parent.parent / 'README.md'
print(readme.read_text())
```

This README follows all PyPI best practices and is optimized for both web viewing and terminal reading.
