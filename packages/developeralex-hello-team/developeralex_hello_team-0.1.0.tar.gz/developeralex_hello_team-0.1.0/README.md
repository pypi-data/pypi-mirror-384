# Hello Team 🎨

A colorful Python package that greets teams with style using colorama!

## Installation

```bash
pip install hello-team
```

## Usage

### Basic Usage

```python
from hello_team import hello_team

# Greet with default green color
hello_team("Python")
# Output: 'Hello Python Team' (in green)

# Greet with default team name
hello_team()
# Output: 'Hello World Team' (in green)
```

### Using Colors

```python
# Greet with different colors
hello_team("DevOps", "blue")
hello_team("Security", "red")
hello_team("Data Science", "magenta")
hello_team("Frontend", "cyan")
```

### Using Styles

```python
# Greet with colors and styles
hello_team("Backend", "green", "bright")
hello_team("QA", "yellow", "dim")
hello_team("Mobile", "blue", "normal")
```

## Available Options

### Colors
- `blue` - Blue text
- `green` - Green text (default)
- `cyan` - Cyan text
- `yellow` - Yellow text
- `red` - Red text
- `magenta` - Magenta text
- `white` - White text
- `black` - Black text

### Styles
- `normal` - Regular text (default)
- `bright` - Bold/bright text
- `dim` - Dimmed text

## Features

- 🎨 Colorful terminal output with colorama
- 🖥️ Cross-platform support (Windows, macOS, Linux)
- ✨ Multiple color and style options
- 🔧 Simple and easy to use API
- 📦 Lightweight with minimal dependencies

## Development

To install in development mode:

```bash
pip install -e .
```

To build the package:

```bash
python -m build
```

## License

MIT
