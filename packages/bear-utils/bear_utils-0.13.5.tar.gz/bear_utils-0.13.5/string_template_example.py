"""Example of using string.Template for logging format strings.

This demonstrates how string.Template could be used as an alternative
to .format() or % formatting for logging templates.
"""

from datetime import datetime
from pathlib import Path
from string import Template

SIMPLE_FORMAT = Template("$message")

VERBOSE_FORMAT = Template("$timestamp |$level| {$filename|$caller_function|$line_number} $message")

CONSOLE_FORMAT = Template("$timestamp <[$level_style]$level[/$level_style]> $message")

JSON_FORMAT = Template(
    '{"time": "$timestamp", "level": "$level", "message": "$message", "function": "$caller_function", "file": "$filename", "line": $line_number}'
)


def main() -> None:
    """Demonstrate string.Template usage for logging formats."""
    # Sample data (like what you'd get from your StackInfo)
    log_data = {
        "timestamp": datetime.now(tz=datetime.now().astimezone().tzinfo).strftime("%Y-%m-%d %H:%M:%S"),
        "level": "INFO",
        "level_style": "green",
        "message": "This is a test log message",
        "caller_function": "main",
        "filename": Path(__file__).name,
        "line_number": 42,
    }

    print("=== String Template Examples ===\n")

    print("Simple format:")
    print(f"  Template: {SIMPLE_FORMAT.template!r}")
    print(f"  Result:   {SIMPLE_FORMAT.substitute(**log_data)}")
    print()

    print("Verbose format:")
    print(f"  Template: {VERBOSE_FORMAT.template!r}")
    print(f"  Result:   {VERBOSE_FORMAT.substitute(**log_data)}")
    print()

    print("Console format:")
    print(f"  Template: {CONSOLE_FORMAT.template!r}")
    print(f"  Result:   {CONSOLE_FORMAT.substitute(**log_data)}")
    print()

    print("JSON-like format:")
    print(f"  Template: {JSON_FORMAT.template!r}")
    print(f"  Result:   {JSON_FORMAT.substitute(**log_data)}")
    print()

    # Demonstrate safe substitution (missing variables)
    print("=== Safe Substitution Example ===\n")
    incomplete_data = {"message": "Only message provided"}

    print("Regular substitute() with missing data:")
    try:
        result = VERBOSE_FORMAT.substitute(**incomplete_data)
        print(f"  Result: {result}")
    except KeyError as e:
        print(f"  Error: {e}")

    print("\nSafe substitute() with missing data:")
    result = VERBOSE_FORMAT.safe_substitute(**incomplete_data)
    print(f"  Result: {result}")
    print("  (Notice the unsubstituted variables remain as $variable)")
    print()

    # Show the comparison with .format() style
    print("=== Comparison with .format() ===\n")

    format_style = "{timestamp} |{level}| {{{filename}|{caller_function}|{line_number}}} {message}"
    template_style = "$timestamp |$level| {$filename|$caller_function|$line_number} $message"

    print("Format style:")
    print(f"  Template: {format_style!r}")
    print(f"  Result:   {format_style.format(**log_data)}")
    print()

    print("Template style:")
    print(f"  Template: {template_style!r}")
    print(f"  Result:   {Template(template_style).substitute(**log_data)}")


if __name__ == "__main__":
    main()
