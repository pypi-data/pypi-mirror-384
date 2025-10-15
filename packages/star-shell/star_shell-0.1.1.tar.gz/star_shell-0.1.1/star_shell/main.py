import json
import os
import subprocess
from pathlib import Path

import pyperclip
import typer
from rich import print
from rich.prompt import Confirm, Prompt

from star_shell.utils import get_backend, get_os_info, load_config
from star_shell.security import secure_storage
from star_shell.context import ContextProvider
from star_shell.command_executor import CommandExecutor
from star_shell.session_manager import SessionManager

APP_NAME = ".star_shell"
app = typer.Typer()


@app.command()
def init():

    backend = Prompt.ask(
        "Select backend:", choices=["openai-gpt-3.5-turbo", "gemini-pro"]
    )
    additional_params = {}

    if backend == "openai-gpt-3.5-turbo":
        openai_api_key = Prompt.ask("Enter a OpenAI API key")
        # Encrypt the API key before storing
        additional_params["openai_api_key"] = secure_storage.encrypt_api_key(openai_api_key)

    if backend == "gemini-pro":
        gemini_api_key = Prompt.ask("Enter a Gemini Pro API key")
        
        # Basic API key validation for Gemini
        print("[yellow]Validating Gemini API key...[/yellow]")
        try:
            from star_shell.backend import GeminiGenie
            test_genie = GeminiGenie(gemini_api_key, "test", "test")
            if test_genie.validate_credentials():
                print("[green]✓ Gemini API key is valid[/green]")
                # Encrypt the API key before storing
                additional_params["gemini_api_key"] = secure_storage.encrypt_api_key(gemini_api_key)
            else:
                print("[red]✗ Invalid Gemini API key. Please check your key and try again.[/red]")
                return
        except Exception as e:
            print(f"[red]✗ Error validating Gemini API key: {e}[/red]")
            return


    os_family, os_fullname = get_os_info()

    if os_family:
        if not Confirm.ask(f"Is your OS {os_fullname}?"):
            os_fullname = Prompt.ask("What is your OS and version? (e.g. MacOS 13.1)")
    else:
        os_fullname = Prompt.ask("What is your OS and version? (e.g. MacOS 13.1)")

    if os_family == "Windows":
        shell = Prompt.ask(
            "What shell are you using?",
            choices=["cmd", "powershell"],
        )

    if os_family in ("Linux", "MacOS"):
        shell_str = os.environ.get("SHELL") or ""
        if "bash" in shell_str:
            shell = "bash"
        elif "zsh" in shell_str:
            shell = "zsh"
        elif "fish" in shell_str:
            shell = "fish"
        else:
            typer.prompt("What shell are you using?")

    config = {
        "backend": backend,
        "os": os_family,
        "os_fullname": os_fullname,
        "shell": shell,
    } | additional_params

    app_dir = typer.get_app_dir(APP_NAME)
    config_path: Path = Path(app_dir) / "config.json"

    print("The following configuration will be saved:")
    print(config)

    config_path.parent.mkdir(parents=True, exist_ok=True)

    if config_path.exists():
        overwrite = Confirm.ask(
            "A config file already exists. Do you want to overwrite it?"
        )
        if not overwrite:
            print("Did not overwrite config file.")
            return

    with open(config_path, "w") as f:
        json.dump(config, f)

    print(f"[bold green]Config file saved at {config_path}[/bold green]")


@app.command()
def ask(
    wish: str = typer.Argument(..., help="What do you want to do?"),
    explain: bool = False,
):
    try:
        config = load_config()
    except FileNotFoundError as e:
        print(f"[red]Error: {e}[/red]")
        return

    # Create context provider and gather context
    context_provider = ContextProvider()
    context = context_provider.build_context()

    genie = get_backend(**config)
    try:
        command, description = genie.ask(wish, explain, context)
    except Exception as e:
        print(f"[red]Error: {e}[/red]")
        return

    # Create command executor for enhanced display and execution
    executor = CommandExecutor()

    if config["os"] == "Windows" and config["shell"] == "powershell":
        # For PowerShell, just display and copy to clipboard
        executor.display_command(command, description)
        pyperclip.copy(command)
        print("[green]Command copied to clipboard.[/green]")
    else:
        # For other systems, use the enhanced execution flow
        command_executed = executor.handle_command_execution(command, description)
        
        # Send feedback to the backend (currently only used by some backends)
        genie.post_execute(
            wish=wish,
            explain=explain,
            command=command,
            description=description,
            feedback=False,
        )


@app.command()
def chat():
    """Start an interactive chat session with Star Shell."""
    try:
        config = load_config()
    except FileNotFoundError as e:
        print(f"[red]Error: {e}[/red]")
        return

    # Create context provider and genie
    context_provider = ContextProvider()
    genie = get_backend(**config)
    
    # Create and start session manager
    session_manager = SessionManager(genie, context_provider)
    session_manager.start_conversation()


if __name__ == "__main__":
    app()