

from pprint import pprint
from colorama import init, Fore, Back, Style

# Initialize colorama for cross-platform support
init(autoreset=True)

def hello_team(team_name=None, color=None, style=None):
    """
    Prints a colorful hello message to a team using colorama.
    
    Args:
        team_name (str, optional): The name of the team. Defaults to "World".
        color (str, optional): Color for the message. Options: 'blue', 'green', 'cyan', 'yellow', 'red', 'magenta', 'white'. Defaults to 'green'.
        style (str, optional): Style for the message. Options: 'bright', 'dim', 'normal'. Defaults to 'normal'.
    
    Example:
        >>> hello_team("Python", "blue", "bright")
        'Hello Python Team' (in bright blue)
        
        >>> hello_team()
        'Hello World Team' (in green)
    """
    if team_name is None:
        team_name = "World"
    
    if color is None:
        color = "green"
        
    if style is None:
        style = "normal"
    
    # Map color names to colorama Fore colors
    color_map = {
        'blue': Fore.BLUE,
        'green': Fore.GREEN,
        'cyan': Fore.CYAN,
        'yellow': Fore.YELLOW,
        'red': Fore.RED,
        'magenta': Fore.MAGENTA,
        'white': Fore.WHITE,
        'black': Fore.BLACK
    }
    
    # Map style names to colorama Style
    style_map = {
        'bright': Style.BRIGHT,
        'dim': Style.DIM,
        'normal': Style.NORMAL
    }
    
    color_code = color_map.get(color.lower(), Fore.GREEN)
    style_code = style_map.get(style.lower(), Style.NORMAL)
    message = f"Hello {team_name} Team"
    
    # colorama automatically resets after each print when autoreset=True
    colored_message = f"{style_code}{color_code}{message}"
    
    print(colored_message)
    return message


if __name__ == "__main__":
    print("Testing colorama-powered hello_team function:")
    print("=" * 50)
    
    # Basic colors
    hello_team()  # Default green
    hello_team("Python", "blue")
    hello_team("DevOps", "cyan")
    hello_team("Design", "magenta")
    hello_team("QA", "yellow")
    
    # With styles
    print("\nWith styles:")
    hello_team("Backend", "red", "bright")
    hello_team("Frontend", "blue", "bright")
    hello_team("Mobile", "green", "dim")
