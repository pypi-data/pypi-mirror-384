# 🎲 WheelSpin Library

Create beautiful animated spinning wheel GIFs for games, contests, decision-making, and more!

![WheelSpin Example](simple_example.gif)

## 📁 Project Structure

```
wheelspin-gif-python/
├── wheelspin/           # Main library package
│   ├── __init__.py
│   ├── wheelspin_lib.py
│   └── wheel_generator.py
├── examples/            # Usage examples
│   ├── simple_example.py
│   └── demo.py
├── tests/               # Test files
├── main.py             # Original development script
└── README.md           # This file
```

## ✨ Features

- 🎯 **Simple API** - Create wheels with just one function call
- 🎨 **Customizable** - Colors, sizes, fonts, animation speed
- 📱 **Smart Layout** - Automatically positions text for optimal readability
- 🎬 **Smooth Animation** - Cubic easing for natural spinning motion
- 🔄 **Adaptive Duration** - Animation length scales with number of segments
- 💎 **High Quality** - Clean, professional-looking output
- 🌍 **Unicode & Emoji Support** - Full UTF-8 support including emoji, Cyrillic, Chinese, Japanese, Arabic, and more!

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/mmenzyns/wheelspin-gif-python
cd wheelspin-gif-python

# Install dependencies (Pillow)
pip install Pillow
```

### Basic Usage

```python
from wheelspin import create_spinning_wheel

# Simple example
names = ["Alice", "Bob", "Charlie", "Diana"]
winner = create_spinning_wheel(names, "my_wheel.gif")
print(f"The winner is: {winner}!")
```

### Run Examples

```bash
# Simple example
python examples/simple_example.py

# Complete demo
python examples/demo.py
```

## 📚 API Reference

### `create_spinning_wheel(segments, output_file, size, colors)`

Creates a spinning wheel GIF with automatic settings.

**Parameters:**
- `segments` (List[str]): List of segment names
- `output_file` (str): Output filename (default: 'wheel.gif')  
- `size` (int): Image size in pixels (default: 500)
- `colors` (List[str], optional): Custom hex colors

**Returns:** `str` - The winning segment name

### `create_spinning_wheel_advanced(segments, **options)`

Advanced wheel creation with full customization.

**Additional Parameters:**
- `start_rotation` (float): Fixed starting angle (random if None)
- `font_size` (int): Text size (default: 11)
- `animation_speed` (float): Speed multiplier (default: 1.0)

**Returns:** `Tuple[str, dict]` - Winner name and detailed info

### `quick_spin(names, filename)`

Quick decision maker with minimal setup.

### `decision_wheel(options, question)`

Context-aware decision making wheel.

## 🎨 Examples

### Basic Usage
```python
from wheelspin_lib import create_spinning_wheel

contestants = ["Team A", "Team B", "Team C", "Team D"]
winner = create_spinning_wheel(contestants, "contest.gif")
```

### Custom Colors
```python
from wheelspin import create_spinning_wheel_advanced

teams = ["Red", "Blue", "Green", "Yellow"]
colors = ["#e74c3c", "#3498db", "#2ecc71", "#f1c40f"]

winner, info = create_spinning_wheel_advanced(
    segments=teams,
    output_file="colorful_wheel.gif",
    size=600,
    colors=colors,
    font_size=14,
    animation_speed=1.5
)
```

### Decision Making
```python
from wheelspin import decision_wheel

lunch_options = ["Pizza", "Sushi", "Burgers", "Salad"]
choice = decision_wheel(lunch_options, "What should we have for lunch?")
```

### Quick Coin Flip
```python
from wheelspin import quick_spin

result = quick_spin(["Heads", "Tails"], "coinflip.gif")
```

### Unicode Support 🌍
```python
from wheelspin import create_spinning_wheel

# International cities
cities = ["Paris", "東京", "Москва", "北京", "Cairo"]
winner = create_spinning_wheel(cities, "cities.gif")

# Multilingual greetings
greetings = ["Hello", "Bonjour", "こんにちは", "你好", "مرحبا"]
winner = create_spinning_wheel(greetings, "greetings.gif")

# Accented names
names = ["José", "François", "Søren", "Łukasz"]
winner = create_spinning_wheel(names, "names.gif")
```

**Supported Unicode:**
- ✅ Cyrillic (Москва, Привет, Київ)
- ✅ Chinese (北京, 你好, 上海)
- ✅ Japanese (東京, こんにちは, 大阪)
- ✅ Arabic (مرحبا, شكرا)
- ✅ Accented Latin (Café, José, Zürich)
- ✅ Special Symbols (★ ♥ ♪ ☀ ☁ ⚡)

See `examples/unicode_demo.py` for more Unicode examples!

**Supported Unicode:**
- ✅ Cyrillic (Москва, Привет, Київ)
- ✅ Chinese (北京, 你好, 上海)
- ✅ Japanese (東京, こんにちは, 大阪)
- ✅ Arabic (مرحبا, شكرا)
- ✅ Accented Latin (Café, José, Zürich)
- ✅ Special Symbols (★ ♥ ♪ ☀ ☁ ⚡)
- ⚠️ Emoji (render as black/white outlined symbols due to PIL limitations)

See `examples/unicode_demo.py` for more Unicode examples!

## 🎯 Use Cases

- **Games & Contests** - Fair random selection of winners
- **Decision Making** - When you can't decide between options
- **Teaching** - Classroom activities and random selection
- **Events** - Prize wheels and giveaways  
- **Daily Life** - Choosing restaurants, activities, etc.

## 🛠️ Advanced Features

### Automatic Text Positioning
The library automatically determines the best text position:
- **Inner ring** for wheels with few, short labels
- **Outer ring** for wheels with many or long labels
- **Consistent alignment** - all text uses the same position

### Smart Animation Duration
- **8 segments**: ~3 seconds
- **50 segments**: ~5 seconds  
- **100 segments**: ~10 seconds
- Scales automatically for optimal viewing

### High-Quality Output
- Clean transparent backgrounds
- Smooth curves and edges
- Professional color schemes
- Readable fonts at any size

## 📁 Generated Files

All functions create standard GIF files that work everywhere:
- ✅ Web browsers
- ✅ Social media platforms  
- ✅ Presentations
- ✅ Mobile devices
- ✅ Email attachments

## 🔧 Requirements

- Python 3.7+
- Pillow (PIL) library

## 📝 Complete Example

```python
#!/usr/bin/env python3
from wheelspin import create_spinning_wheel_advanced

# Restaurant picker with custom styling
restaurants = [
    "Italian Bistro", "Sushi Bar", "Burger Joint", 
    "Taco Palace", "Pizza Corner", "Thai Garden"
]

# Warm color scheme
colors = ["#ff6b6b", "#ee5a24", "#feca57", "#48cae4", "#023047", "#8ecae6"]

winner, details = create_spinning_wheel_advanced(
    segments=restaurants,
    output_file="dinner_choice.gif",
    size=700,
    colors=colors,
    font_size=13,
    animation_speed=1.2
)

print(f"🍽️ Tonight's dinner: {winner}")
print(f"📊 Details: {details}")
```

See more examples in the `examples/` directory!

## 🎉 Have Fun!

The WheelSpin library makes it easy to add interactive decision-making to your projects. Whether you're building a game, making life decisions, or just having fun, spin that wheel! 🎲
