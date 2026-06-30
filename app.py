import argparse
import json
import sys

from config import load_api_key
from writer import create_client, ArthurWriter

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    # Rich is optional - the app still works with plain print() if it's
    # not installed.
    RICH_AVAILABLE = False
    console = None




SLASH_COMMANDS = {
    "story":     ("Write a short story",            "generate_story",     "Story idea"),
    "improve":   ("Improve a piece of writing",      "improve_text",       "Text to improve"),
    "continue":  ("Continue a story/chapter",        "continue_story",     "Story so far"),
    "brainstorm": ("Brainstorm ideas",               "brainstorm",         "Topic"),
    "character": ("Generate a character",            "generate_character", "Character description"),
    "world":     ("Build a fictional world",         "build_world",        "World/setting idea"),
    "poem":      ("Write a poem",                    "write_poem",         "Poem topic"),
    "proofread": ("Proofread text",                  "proofread",          "Text to proofread"),
    "technique": ("Explain a writing technique",     "explain_technique",  "Technique name"),
    "outline":   ("Generate a book outline",         "generate_outline",   "Book idea"),
}



# Output helpers

def print_banner():
    """Print the app title banner."""
    if RICH_AVAILABLE:
        console.print(Panel.fit(
            "[bold cyan]Arthur[/bold cyan] — AI Writing Mentor CLI\n"
            "[dim]Type /help for commands, or just start chatting.[/dim]",
            border_style="cyan"
        ))
    else:
        print("=" * 56)
        print(" Arthur — AI Writing Mentor CLI")
        print(" Type /help for commands, or just start chatting.")
        print("=" * 56)


def print_response(response: str, label: str = "Arthur"):
    """Display Arthur's response, nicely formatted if Rich is available."""
    if RICH_AVAILABLE:
        console.print(Panel(Markdown(response), title=label, border_style="green"))
    else:
        print(f"\n[{label}]\n{response}\n")


def print_help():
    """Print the list of available slash commands."""
    lines = ["Available commands:", ""]
    for name, (desc, _, _) in SLASH_COMMANDS.items():
        lines.append(f"  /{name:<12} {desc}")
    lines.append(f"  {'/help':<13} Show this help message")
    lines.append(f"  {'/clear':<13} Clear conversation history")
    lines.append(f"  {'/quit':<13} Exit (also: /exit, Ctrl+C)")
    lines.append("")
    lines.append("Anything not starting with / is sent to Arthur as a normal")
    lines.append("chat message, with the conversation history kept for context.")
    text = "\n".join(lines)

    if RICH_AVAILABLE:
        console.print(Panel(text, title="Help", border_style="yellow"))
    else:
        print("\n" + text + "\n")


def get_multiline_input(prompt_text: str) -> str:
    """
    Get longer text input from the user (e.g. a paragraph to improve).
    User types their text, then types END on its own line to finish.
    """
    print(f"{prompt_text} (type END on a new line when finished, "
          f"or leave blank + END to cancel)")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines)



# Interactive mode

def handle_slash_command(arthur: ArthurWriter, command: str, rest: str) -> bool:
    """
    Handle a single slash command typed in the interactive session.

    Args:
        arthur: The ArthurWriter instance.
        command: The command name without the leading slash (e.g. "story").
        rest: Any text typed after the command on the same line.

    Returns:
        bool: False if the session should exit, True to keep looping.
    """
    if command in ("quit", "exit"):
        print("\nFarewell, and happy writing!")
        return False

    if command == "help":
        print_help()
        return True

    if command == "clear":
        arthur.reset_history()
        print("\n[Conversation history cleared.]\n")
        return True

    if command in SLASH_COMMANDS:
        desc, method_name, prompt_label = SLASH_COMMANDS[command]

        # Multi-turn-text commands benefit from multiline paste input;
        # short ones just take the rest of the line or a quick prompt.
        if command in ("improve", "continue", "proofread"):
            text = rest.strip() or get_multiline_input(f"{prompt_label}:")
        else:
            text = rest.strip() or input(f"{prompt_label}: ").strip()

        if not text:
            print("\n[No input provided, cancelled.]\n")
            return True

        method = getattr(arthur, method_name)

        # brainstorm() also accepts an optional count, e.g. "/brainstorm 5 dragons"
        if command == "brainstorm":
            parts = text.split(maxsplit=1)
            if parts and parts[0].isdigit() and len(parts) > 1:
                count, topic = int(parts[0]), parts[1]
            else:
                count, topic = 10, text
            response = method(topic, count)
        else:
            response = method(text)

        print_response(response, label=f"Arthur — {desc}")
        return True

    print(f"\n[Unknown command: /{command}. Type /help for the full list.]\n")
    return True


def run_interactive(arthur: ArthurWriter):
    """Run the persistent interactive CLI session."""
    print_banner()
    print()

    while True:
        try:
            raw = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nFarewell, and happy writing!")
            break

        if not raw:
            continue

        try:
            if raw.startswith("/"):
                # Split "/story a lighthouse keeper" into command + rest.
                body = raw[1:]
                parts = body.split(maxsplit=1)
                command = parts[0].lower() if parts else ""
                rest = parts[1] if len(parts) > 1 else ""
                should_continue = handle_slash_command(arthur, command, rest)
                if not should_continue:
                    break
            else:
                # Free-text chat - keeps conversation history for context.
                response = arthur.chat(raw, use_history=True)
                print_response(response)

        except KeyboardInterrupt:
            print("\n\n[Interrupted current request.]\n")
        except Exception as e:
            print(f"\n[Unexpected error] {e}\n")



# Headless one-shot mode

def run_headless(arthur: ArthurWriter, prompt: str, output_format: str):
    """
    Run a single prompt non-interactively and print the result, then exit.
    Mirrors `agy -p "..."` style headless invocation.
    """
    if prompt == "-":
        # Read the prompt from stdin, e.g. for piping.
        prompt = sys.stdin.read().strip()

    if not prompt:
        print("[Error] No prompt provided.", file=sys.stderr)
        sys.exit(1)

    response = arthur.chat(prompt)

    if output_format == "json":
        print(json.dumps({"prompt": prompt, "response": response}, indent=2))
    else:
        print(response)



# Argument parsing & entry point

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="app.py",
        description="Arthur — AI Writing Mentor CLI, powered by the Groq API.",
    )
    parser.add_argument(
        "-p", "--prompt",
        metavar="TEXT",
        help="Run a single prompt non-interactively and exit. "
             "Pass '-' to read the prompt from stdin.",
    )
    parser.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="Output format for headless (-p) mode. Default: text.",
    )
    return parser


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    api_key = load_api_key()
    client = create_client(api_key)
    arthur = ArthurWriter(client)

    if args.prompt is not None:
        run_headless(arthur, args.prompt, args.output_format)
    else:
        run_interactive(arthur)


if __name__ == "__main__":
    main()
