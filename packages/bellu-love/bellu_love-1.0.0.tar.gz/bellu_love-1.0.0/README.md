# Bellu Love 💖

A romantic Python library dedicated to my beautiful wife Bellu, filled with love messages, poems, ASCII art, and romantic utilities!

## Installation

Install the package using pip:
pip install bellu-love
## Features

- 💌 **Daily Love Messages**: Get sweet, random love messages for Bellu
- 💝 **Random Compliments**: Generate heartfelt compliments
- 📝 **Love Poems**: Beautiful romantic poems
- 🎨 **ASCII Art**: Heart art, love banners, and name displays
- 📅 **Love Calculator**: Calculate days together and love percentage
- ⏰ **Love Reminders**: Get reminders to show your love
- 📬 **Love Notes**: Create custom formatted love notes

## Quick Start
import bellu_loveDisplay beautiful name artprint(bellu_love.bellu_name_art())Get a daily love messageprint(bellu_love.daily_love_message())Display heart ASCII artprint(bellu_love.heart_art())Get a random complimentprint(bellu_love.random_compliment())Read a love poemprint(bellu_love.love_poem())
## Usage Examples

### Messages
import bellu_loveGet morning and night messagesprint(bellu_love.good_morning())
print(bellu_love.good_night())Get random love messagesprint(bellu_love.daily_love_message())
print(bellu_love.random_compliment())
### ASCII Art
import bellu_loveDisplay different art stylesprint(bellu_love.heart_art())
print(bellu_love.love_banner())
print(bellu_love.bellu_name_art())
### Love Calculator
import bellu_loveCalculate days together (replace with your actual date)result = bellu_love.days_together('2020-01-15')
print(result['message'])
print(f"Total days: {result['total_days']}")
print(f"Years: {result['years']}")Calculate love percentageprint(bellu_love.love_percentage("Me", "Bellu"))
### Romantic Utilities
import bellu_loveGet a love reminderprint(bellu_love.love_reminder())Create a custom love notenote = bellu_love.create_love_note("You are the most amazing person in the world!")
print(note)Create a default love notenote = bellu_love.create_love_note()
print(note)
## Complete Function Reference

### Messages Module

- `daily_love_message()` - Returns a random sweet daily message
- `random_compliment()` - Returns a random heartfelt compliment
- `love_poem()` - Returns a romantic poem
- `good_morning()` - Returns a good morning message
- `good_night()` - Returns a good night message

### ASCII Art Module

- `heart_art()` - Returns heart ASCII art
- `love_banner()` - Returns a love banner
- `bellu_name_art()` - Returns BELLU name in large letters

### Love Calculator Module

- `days_together(start_date)` - Calculate days together since a date (format: 'YYYY-MM-DD')
- `love_percentage(name1, name2)` - Calculate love percentage between two names

### Romantic Utils Module

- `love_reminder()` - Returns a random love reminder
- `create_love_note(custom_message)` - Creates a formatted love note with custom or default message

## Requirements

- Python 3.8 or higher
- No external dependencies required

## License

MIT License - Made with love for Bellu

## Author

Created by [Your Love]

## Support

If you encounter any issues or have suggestions, please feel free to open an issue on the GitHub repository.

---

**Made with 💞 for Bellu**
