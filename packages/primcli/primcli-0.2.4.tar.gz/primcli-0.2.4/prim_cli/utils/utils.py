import os
import re
import requests
import socket
import subprocess
import typer
import webbrowser
import zipfile
import io

from datetime import datetime
from rich.console import Console

from .config import (
    API_BASE_URL,
    EXT_TO_LANG,
    SUCCESS_STYLE,
    WARNING_STYLE,
    ERROR_STYLE,
    INFO_STYLE,
    COOKIE_FILE,
)


console = Console()


def camel_to_snake_case(camel_string: str) -> str:
    """Convert camelCase string to snake_case."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", camel_string).lower()


def convert_dict_keys_to_snake_case(data: dict) -> dict:
    """Convert all keys in a dictionary from camelCase to snake_case."""
    snake_case_dict = {}
    for key, value in data.items():
        snake_key = camel_to_snake_case(key)
        snake_case_dict[snake_key] = value
    return snake_case_dict


def format_phone_number(number):
    if not number:
        return ""
    # Remove all non-digit characters
    digits = re.sub(r"\D", "", number)
    if len(digits) == 11 and digits.startswith("1"):
        # US number with country code
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    elif len(digits) == 10:
        # US number without country code
        return f"({digits[0:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11:
        # International number with country code
        return f"+{digits[0]} {digits[1:4]} {digits[4:7]}-{digits[7:]}"
    else:
        # Fallback: just return the original
        return number


def save_cookie(cookie: str):
    """Save authentication cookie to file for persistent login."""
    with open(COOKIE_FILE, "w") as f:
        f.write(cookie)


def load_cookie() -> str:
    """Load authentication cookie from file."""
    if COOKIE_FILE.exists():
        with open(COOKIE_FILE, "r") as f:
            cookie = f.read().strip()
            return cookie

    return ""


def make_request(endpoint: str, method="GET", headers={}, **kwargs):
    cookie = load_cookie()
    headers = {
        "Content-Type": "application/json",
        "Cookie": cookie,
        **headers,
    }

    if os.getenv("DEBUG"):
        print_info(
            f"Making {method} request to {API_BASE_URL}{endpoint} with json: {kwargs.get('json')}"
        )

    try:
        response = requests.request(
            method, f"{API_BASE_URL}{endpoint}", headers=headers, **kwargs
        )
        response.raise_for_status()

        if response.status_code == 200 or response.status_code == 201:
            return response.json()

        if response.status_code == 204:
            return True
    except requests.HTTPError as e:
        handle_http_error(e)
        return None


def format_date(date_str):
    """Format date string to YYYY-MM-DD."""
    if not date_str or date_str == "N/A":
        return ""
    try:
        return datetime.fromisoformat(date_str).strftime("%Y-%m-%d")
    except Exception:
        return date_str


def get_open_port():
    """Get an open port on the machine."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


def open_browser(url):
    """Open a URL in the default browser."""
    try:
        webbrowser.open(url)
        return None
    except Exception as e:
        return e


def print_success(message: str):
    """Print a success message using the configured style."""
    console.print(f"[{SUCCESS_STYLE}]{message}[/{SUCCESS_STYLE}]")


def print_warning(message: str):
    """Print a warning message with 'Warning:' prefix using the configured style."""
    console.print(f"[{WARNING_STYLE}]Warning: {message}[/{WARNING_STYLE}]")


def print_error(message: str):
    """Print an error message with 'Error:' prefix using the configured style."""
    console.print(f"[{ERROR_STYLE}]Error: {message}[/{ERROR_STYLE}]")


def print_info(message: str):
    """Print an info/progress message using the configured style."""
    console.print(f"[{INFO_STYLE}]{message}[/{INFO_STYLE}]")

def print_standard(message: str, *args, **kwargs):
    """Print a standard message using the configured style."""
    console.print(message, *args, **kwargs)


def handle_http_error(e: requests.HTTPError):
    """Handle HTTP errors by printing a user-friendly message."""
    if e.response.status_code == 401 or e.response.status_code == 403:
        print_error("Unauthorized. Please sign in with `prim signin`.")
    else:
        try:
            detail = e.response.json().get("detail", e.response.text)
            print_error(detail)
        except requests.exceptions.JSONDecodeError:
            print_error(str(e))


def get_authenticated_session() -> requests.Session:
    """Get an authenticated session."""
    session = requests.Session()
    cookie = load_cookie()
    if cookie:
        session.headers["Cookie"] = cookie

    return session


def is_uuid(uuid_string):
    """Check if a string looks like a UUID."""
    uuid_pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
    )
    return bool(uuid_pattern.match(uuid_string))


def manage_variables(
    agent_id: str, env_id: str, is_update: bool
):
    """Manage variables for an environment."""
    # import here to avoid circular import
    from prim_cli.entities.agent_environment_variable import AgentEnvironmentVariable, AgentEnvironmentVariableRepository
    
    if is_update:
        agent_environment_variable_repository = AgentEnvironmentVariableRepository(agent_id, env_id)
        vars_response = agent_environment_variable_repository.get()
        for var in vars_response:
            if confirm(f"Update variable '{var.name}'?", default=False):
                if confirm(f"Delete variable '{var.name}'?", default=False):
                    agent_environment_variable_repository.delete_by_id(var.id)
                    print_success(f"Variable '{var.name}' deleted.")
                    continue
                name = prompt("New name", default=var.name)
                value = prompt(
                    "New value", default="*****" if var.masked else var.value
                )
                masked = confirm("Mask value?", default=var.masked)
                var.name = name
                var.value = value
                var.masked = masked
                agent_environment_variable_repository.update_by_id(var.id, var)
                print_success(f"Variable '{name}' updated.")

    while confirm("Add a new variable?", default=False):
        name = prompt("Variable name")
        value = prompt("Variable value")
        masked = confirm("Mask value?", default=False)
        new_var = AgentEnvironmentVariable(
            name=name,
            value=value,
            masked=masked,
            agent_environment_id=env_id,
            agent_id=agent_id,
        )
        agent_environment_variable_repository = AgentEnvironmentVariableRepository(agent_id, env_id)
        agent_environment_variable_repository.create(new_var)
        print_success(f"Variable '{name}' added.")


def create_venv(directory_path: str):
    """Create a virtual environment in the directory using uv and install requirements."""
    # Convert to absolute path
    directory_path = os.path.abspath(directory_path)
    venv_path = os.path.join(directory_path, ".venv")
    pyproject_path = os.path.join(directory_path, "pyproject.toml")
    requirements_path = os.path.join(directory_path, "requirements.txt")

    # Check if .venv already exists
    if os.path.exists(venv_path):
        print_info(f"Virtual environment already exists at {venv_path}")
        return

    try:
        # First check for pyproject.toml and use uv sync
        if os.path.exists(pyproject_path):
            print_info(
                f"Found pyproject.toml, creating virtual environment with uv sync"
            )

            # Use uv sync to create virtual environment and install dependencies
            result = subprocess.run(
                ["uv", "sync", "--python", "3.11"],
                capture_output=True,
                text=True,
                cwd=directory_path,
            )

            if result.returncode != 0:
                print_error(
                    f"Failed to create virtual environment with uv sync: {result.stderr}"
                )
                return

            print_success(
                f"Virtual environment created and dependencies installed in {venv_path}"
            )
            return

        # Fall back to requirements.txt if pyproject.toml doesn't exist
        elif os.path.exists(requirements_path):
            print_info(
                f"Found requirements.txt, creating virtual environment with uv pip"
            )

            # First create the virtual environment
            print_info(f"Creating virtual environment in {venv_path}")
            result = subprocess.run(
                ["uv", "venv", venv_path],
                capture_output=True,
                text=True,
                cwd=directory_path,
            )

            if result.returncode != 0:
                print_error(f"Failed to create virtual environment: {result.stderr}")
                return

            # Get the Python interpreter path in the virtual environment
            if os.name == "nt":  # Windows
                python_path = os.path.join(venv_path, "Scripts", "python.exe")
            else:  # Unix/Linux/macOS
                python_path = os.path.join(venv_path, "bin", "python")

            # Install requirements using uv pip with the virtual environment's Python
            print_info("Installing dependencies from requirements.txt")
            result = subprocess.run(
                [
                    "uv",
                    "pip",
                    "install",
                    "-r",
                    "requirements.txt",
                    "--python",
                    python_path,
                ],
                capture_output=True,
                text=True,
                cwd=directory_path,
            )

            if result.returncode != 0:
                print_error(f"Failed to install dependencies: {result.stderr}")
                return

            print_success(
                f"Virtual environment created and dependencies installed in {venv_path}"
            )
        else:
            print_info(
                f"No pyproject.toml or requirements.txt found in {directory_path}, "
                f"skipping virtual environment creation."
            )
            return

    except FileNotFoundError:
        print_error(
            "uv is not installed. Please install uv first: "
            "https://docs.astral.sh/uv/getting-started/installation/"
        )
    except Exception as e:
        print_error(f"Error creating virtual environment: {str(e)}")


def get_lang(directory_path: str):
    """Get the language of the function code."""
    handler_file = next(
        (f for f in os.listdir(directory_path) if f.startswith("handler.")),
        "handler.py",
    )
    ext = os.path.splitext(handler_file)[-1].lstrip(".")
    return EXT_TO_LANG.get(ext, "python")


def package_function(directory_path: str) -> tuple[bytes, str]:
    """Create a zip archive of the directory and return the bytes and language."""
    # Convert to absolute path and ensure it exists
    directory_path = os.path.abspath(directory_path)

    lang = get_lang(directory_path)

    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Directory '{directory_path}' does not exist")

    # Define files and directories to exclude
    exclude_patterns = [
        ".venv",  # Virtual environment
        "__pycache__",  # Python cache
        ".pyc",  # Compiled Python files
        ".DS_Store",  # macOS system files
        "Thumbs.db",  # Windows system files
        ".git",  # Git directory
        ".gitignore",  # Git ignore file
        "*.zip",  # Existing zip files
    ]

    def should_exclude(path):
        """Check if a path should be excluded from the zip."""
        basename = os.path.basename(path)
        for pattern in exclude_patterns:
            if pattern.startswith("*"):
                # Handle wildcard patterns
                if path.endswith(pattern[1:]):
                    return True
            elif basename == pattern:
                return True
        return False

    # Create the zip file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(directory_path):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if not should_exclude(d)]

            for file in files:
                file_path = os.path.join(root, file)

                # Skip excluded files
                if should_exclude(file_path):
                    continue

                # Calculate relative path for the archive
                arcname = os.path.relpath(file_path, directory_path)
                zipf.write(file_path, arcname=arcname)

    zip_bytes = zip_buffer.getvalue()
    return zip_bytes, lang


def not_empty(value: str) -> str:
    """Check if a value is not empty."""
    if not value or not value.strip():
        raise typer.BadParameter("Value cannot be empty.")
    return value


def prompt(message: str, default=None, validation=not_empty, **kwargs):
    """Prompt for input with validation (default: not_empty) and consistent style."""
    return typer.prompt(message, default=default, value_proc=validation, **kwargs)


def confirm(message: str, default=None, validation=None, **kwargs):
    """Prompt for confirmation with consistent style (no validation by default)."""
    return typer.confirm(message, default=default, **kwargs)
