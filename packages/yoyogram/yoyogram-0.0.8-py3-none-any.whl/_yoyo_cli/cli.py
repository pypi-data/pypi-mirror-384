
import argparse

from rich.console import Console

from _yoyo_cli.core import init_project, help_command, create_bot, establish_router, create_model


def main():
    # Initializing custom Console by rich module
    console = Console()

    # Creating parser and subparsers for CLI
    parser = argparse.ArgumentParser(prog="yoyo", description="🛠 YoYoGram CLI — Generate Templates")
    subparsers = parser.add_subparsers(dest="command")

    # Help Command
    subparsers.add_parser("help", help="Show list of available commands")

    # Init Command
    subparsers.add_parser("init", help="Create a new project")

    # Bot Command
    bot_parser = subparsers.add_parser("bot", help="Create a new bot")
    bot_parser.add_argument("name", help="The name of the bot")

    # Router Command
    router_parser = subparsers.add_parser("router", help="Establish a new router")
    router_parser.add_argument("name", help="The name of the router")
    router_parser.add_argument("index", nargs='?', help="The index of the router", default=-1)
    router_parser.add_argument("bot_name", nargs='?', help="The name of the bot", default=None)

    # Model Command
    model_parser = subparsers.add_parser("model", help="Create a new model")
    model_parser.add_argument("name", help="The name of the model")
    model_parser.add_argument("bot_name", nargs='?', help="The name of the bot to which model will be created", default=None)

    # Get Request
    args = parser.parse_args()

    # Handle Request
    if args.command == "init":
        init_project(console)
    elif args.command == "bot":
        create_bot(console, args.name)
    elif args.command == "router":
        establish_router(console, args.name, args.index, args.bot_name)
    elif args.command == "model":
        create_model(console, args.name, args.bot_name)
    elif args.command == "help" or args.command is None:
        help_command(console)
    else:
        help_command(console)