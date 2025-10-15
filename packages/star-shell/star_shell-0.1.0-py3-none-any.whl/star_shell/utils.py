import platform
import json
from pathlib import Path
import typer
from backend import OpenAIGenie, GeminiGenie
from security import secure_storage


def get_os_info():
    oper_sys = platform.system()
    if oper_sys == "Windows" or oper_sys == "Darwin":
        oper_sys = "MacOS" if oper_sys == "Darwin" else "Windows"
        return (oper_sys, platform.platform(aliased=True, terse=True))
    if oper_sys == "Linux":
        return (oper_sys, platform.freedesktop_os_release()["PRETTY_NAME"])
    return (None, None)


def load_config():
    """Load and decrypt configuration from the config file."""
    APP_NAME = ".star_shell"
    app_dir = typer.get_app_dir(APP_NAME)
    config_path = Path(app_dir) / "config.json"
    
    if not config_path.exists():
        raise FileNotFoundError("Configuration file not found. Please run 'star-shell init' first.")
    
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Decrypt API keys if they exist and are encrypted
    if "openai_api_key" in config and config["openai_api_key"]:
        config["openai_api_key"] = secure_storage.decrypt_api_key(config["openai_api_key"])
    
    if "gemini_api_key" in config and config["gemini_api_key"]:
        config["gemini_api_key"] = secure_storage.decrypt_api_key(config["gemini_api_key"])
    
    return config


def get_backend(**config: dict):
    backend_name = config["backend"]
    if backend_name == "openai-gpt-3.5-turbo":
        return OpenAIGenie(
            api_key=config["openai_api_key"],
            os_fullname=config["os_fullname"],
            shell=config["shell"],
        )

    elif backend_name == "gemini-pro":
        return GeminiGenie(
            api_key=config["gemini_api_key"],
            os_fullname=config["os_fullname"],
            shell=config["shell"],
        )
    else:
        raise ValueError(f"Unknown backend: {backend_name}")