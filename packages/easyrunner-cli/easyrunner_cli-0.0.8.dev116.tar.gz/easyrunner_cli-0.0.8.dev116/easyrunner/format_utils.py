# ANSI color codes for terminal output
green = "\033[92m"  # Green for success
red = "\033[91m"    # Red for failure
reset = "\033[0m"   # Reset color

# Unicode tick and cross symbols
tick_char = "✓"
cross_char = "✗"

def convert_bool_to_emoji(value: bool) -> str:
    """Convert a boolean value to a tick or cross character."""
    if value:
        return f"{green}{tick_char}{reset}"  # Green tick for True
    else:
        return f"{red}{cross_char}{reset}"  # Red cross for False