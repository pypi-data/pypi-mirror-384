
import shutil
from pathlib import Path
import importlib.resources as pkg_resources

from rich.console import Console
from rich.table import Table

from _yoyo_cli import templates


def get_project_root() -> Path:
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / "main.py").exists() or (parent / ".git").exists():
            return parent
    return current


def remove_keep_files(root: Path) -> None:
    for path in root.rglob("*"):
        if path.is_file() and path.name == ".keep":
            if any(part in ("venv", ".venv", "__pycache__") for part in path.parts):
                continue
            path.unlink()


def init_project(console: Console) -> None:
    dst_path = get_project_root()
    with pkg_resources.path(templates, "project") as template_path:
        shutil.copytree(template_path, dst_path, dirs_exist_ok=True)
        (dst_path / "__init__.py").unlink(missing_ok=True)

    remove_keep_files(dst_path)

    console.print("[green]✅ Project has been created![/green]")


def help_command(console: Console) -> None:
    table = Table(title="🛠 Доступные команды YoYoGram CLI", style="magenta")
    table.add_column("Command", style="cyan3", no_wrap=True)
    table.add_column("Arguments", style="deep_sky_blue1")
    table.add_column("Description", style="white")
    table.add_row("init", "", "Create a new project")
    table.add_row("bot", "bot_name", "Create a new bot")
    table.add_row("router", "name Optional:index Optional:bot_name\nProviding bot_name it will create router by tgbot/bots/bot_name/routers/router_name path\nNot providing bot_name, it established router by the current path\nNot providing index means the last position", "Establish a new router")
    table.add_row("model", "name Optional:bot_name\nWithout bot_name it will create it in tgbot dir, making access for all bots to use the model", "Create a new model")
    console.print(table)


def create_bot(console: Console, bot_name: str) -> None:
    with pkg_resources.path(templates, "bot") as template_path:
        bots_dir = get_project_root() / "tgbot" / "bots" / bot_name

        for item in template_path.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(template_path)
                dst_file = bots_dir / rel_path
                dst_file.parent.mkdir(parents=True, exist_ok=True)

                try:
                    content = item.read_text(encoding="utf-8")
                    content = content.replace("{bot_name}", bot_name)
                    dst_file.write_text(content, encoding="utf-8")
                except UnicodeDecodeError:
                    shutil.copyfile(item, dst_file)

        remove_keep_files(bots_dir)
        (bots_dir / "utils" / "__init__.py").unlink(missing_ok=True)

        console.print(f"[green]✅ {bot_name} has been created by tgbot/bots/{bot_name} directory![/green]")


def establish_router(console: Console, router_name: str, router_index: int = -1, bot_name: str = None) -> None:
    with pkg_resources.path(templates, "router") as template_path:
        if bot_name:
            if (get_project_root() / "tgbot" / "bots" / bot_name).exists():
                router_dir = get_project_root() / "tgbot" / "bots" / bot_name / "routers" / router_name
            else:
                console.print(f"[red]❌ There is no {bot_name} bot![/red]")
        else:
            bots = [p for p in (get_project_root() / "tgbot" / "bots").iterdir() if p.is_dir()]
            if len(bots) == 1:
                router_dir = bots[0] / "routers" / router_name
            else:
                for parent in [Path.cwd()] + list(Path.cwd().parents):
                    if (parent / "routers").exists():
                        router_dir = parent / "routers" / router_name
                        bot_name = parent.name
                        break
                else:
                    console.print("[red]❌ You're not in certain bot, so please provide the bot_name parameter![/red]")
                    return

        for item in template_path.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(template_path)
                dst_file = router_dir / rel_path
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                try:
                    content = item.read_text(encoding="utf-8")
                    content = content.replace("{bot_name}", bot_name)
                    content = content.replace("{router_index}", str(router_index))
                    dst_file.write_text(content, encoding="utf-8")
                except UnicodeDecodeError:
                    shutil.copyfile(item, dst_file)

        console.print(f"[green]✅ {router_name} has been established by tgbot/bots/{bot_name}/routers/{router_name} directory![/green]")


def create_model(console: Console, name: str, bot_name: str = None) -> None:
    if bot_name:
        model_path = get_project_root() / "tgbot" / "bots" / bot_name / "models" / f"{name}.py"
        db_path = f"tgbot/bots/{bot_name}/models/{name}.db"
    else:
        model_path = get_project_root() / "tgbot" / "models" / f"{name}.py"
        db_path = f"tgbot/models/{name}.db"

    name = name.lower()
    capital_name = name[0].upper() + name[1:]

    with pkg_resources.path(templates, "model") as template_path:
        for item in template_path.rglob("model.py"):
            model_path.parent.mkdir(parents=True, exist_ok=True)

            content = item.read_text(encoding="utf-8")
            content = content.replace("{name}", name)
            content = content.replace("{capital_name}", capital_name)
            content = content.replace("{db_path}", db_path)
            model_path.write_text(content, encoding="utf-8")

    if bot_name:
        console.print(f"[green]✅ {capital_name} Model has been created by tgbot/bots/{bot_name}/models directory![/green]")
    else:
        console.print(f"[green]✅ {capital_name} Model has been created by tgbot/models directory![/green]")
