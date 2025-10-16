"""
WikiTree API Python Client
__main__.py

Command-line interface entry point for the WikiTree API client.
Allows direct API interaction from the shell using explicit named parameters.
Copyright (c) 2025 Steven Harris
License: GPL-3.0-only
"""

import sys
import json
import inspect
from .session import WikiTreeSession
from .fields_reference import describe_fields


def print_global_help():
    """Display top-level help."""
    print("WikiTree API Python Client\n")
    print("Usage:")
    print("  wikitree-cli <action> param=value [param=value ...]")
    print("  wikitree-cli <action> --help")
    print()
    print("Examples:")
    print("  wikitree-cli getProfile key=Clemens-1 fields=Name,FirstName")
    print("  wikitree-cli getAncestors key=Clemens-1 depth=5")
    print()
    print("Use `wikitree-cli <action> --help` for detailed documentation about a specific API action.")
    sys.exit(0)


def print_action_help(action: str, wt: WikiTreeSession):
    """Display help for a specific API wrapper."""
    method = getattr(wt, action, None)
    if method is None:
        print(f"No action found: {action}")
        sys.exit(2)

    if action.lower() == "fields":
        print(describe_fields())
        sys.exit(0)

    doc = inspect.getdoc(method)
    if not doc:
        print(f"No documentation available for '{action}'.")
    else:
        print(f"\nHelp for {action}:\n")
        print(doc)
    sys.exit(0)


def main():
    """Command-line entry point for the WikiTree API client."""
    wt = WikiTreeSession()

    # no arguments → short usage message
    if len(sys.argv) == 1:
        print("wikitree-cli <action> <key> - see `wikitree-cli --help` for more information")
        sys.exit(1)

    command = sys.argv[1]

    # global help
    if command == "--help":
        print_global_help()

    # handle per-action help
    if len(sys.argv) == 3 and sys.argv[2] == "--help":
        print_action_help(command, wt)

    # otherwise: treat as API request
    args = dict(arg.split("=", 1) for arg in sys.argv[2:] if "=" in arg)

    try:
        result = wt.request(command, **args)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
