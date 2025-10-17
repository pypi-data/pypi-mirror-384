import asyncio
from datetime import datetime
import os
import tempfile
import base64
import typer

from pathlib import Path
from rich.table import Table

from prim_cli.entities.phone_number import PhoneNumberRepository

from ..commands.debug import run_debugger

from ..entities.agent import AgentRepository
from ..entities.agent_function import AgentFunction, AgentFunctionRepository
from ..entities.agent_environment import AgentEnvironment, AgentEnvironmentRepository

from ..utils.config import (
    DEBUG_ENV_NAME,
    EXT_TO_LANG,
    TITLE_STYLE,
    ID_STYLE,
    PATH_STYLE,
    UNNAMED,
    NOT_AVAILABLE,
)
from ..utils.utils import (
    format_date,
    format_phone_number,
    package_function,
    print_standard,
    print_success,
    print_error,
    print_warning,
    print_info,
    prompt,
    confirm,
)

app = typer.Typer()
agent_repository = AgentRepository()


# TODO: fix error handling so it doesn't say success when it fails
@app.command("list")
def func_list(agent_name_or_id: str = typer.Argument(..., help="Agent name or ID.")):
    """List all functions for an agent. Provide agent name or ID."""
    print_info(f"Getting functions for {agent_name_or_id}...")

    agent = agent_repository.get_by_name_or_id(agent_name_or_id)
    if not agent:
        print_error(f"Agent '{agent_name_or_id}' not found.")
        return

    agent_function_repository = AgentFunctionRepository(agent.id)
    functions = agent_function_repository.get()

    table = Table(
        "Name",
        "Display Name",
        "Language",
        "Updated",
        "ID",
        show_header=True,
        header_style=TITLE_STYLE,
    )

    for func in functions:
        table.add_row(
            func.name,
            func.display_name or NOT_AVAILABLE,
            func.language or NOT_AVAILABLE,
            format_date(func.updated_at),
            f"[{ID_STYLE}]{func.id}[/{ID_STYLE}]",
        )

    print_standard(table)


@app.command("info")
def func_info(
    agent_name_or_id: str = typer.Argument(..., help="Agent name or ID."),
    function_name_or_id: str = typer.Argument(..., help="Function name or ID."),
):
    """Show detailed information about a function. Provide agent name or ID and function name or ID."""
    agent = agent_repository.get_by_name_or_id(agent_name_or_id)
    if not agent:
        print_error(f"Agent '{agent_name_or_id}' not found.")
        return

    agent_function_repository = AgentFunctionRepository(agent.id)
    function = agent_function_repository.get_by_name_or_id(function_name_or_id)
    if not function:
        print_error(f"Function '{function_name_or_id}' not found.")
        return

    table = Table(show_header=False, show_lines=False, box=None, pad_edge=False)
    table.add_row(
        f"[{TITLE_STYLE}]Function Name[/{TITLE_STYLE}]",
        f"{function.name or UNNAMED}",
    )
    table.add_row(
        f"[{TITLE_STYLE}]Display Name[/{TITLE_STYLE}]",
        f"{function.display_name or NOT_AVAILABLE}",
    )
    table.add_row(
        f"[{TITLE_STYLE}]ID[/{TITLE_STYLE}]",
        f"[{ID_STYLE}]{function.id}[/{ID_STYLE}]",
    )
    table.add_row(
        f"[{TITLE_STYLE}]Agent[/{TITLE_STYLE}]",
        f"{agent.name or UNNAMED}",
    )
    table.add_row(
        f"[{TITLE_STYLE}]Agent ID[/{TITLE_STYLE}]",
        f"[{ID_STYLE}]{agent.id}[/{ID_STYLE}]",
    )
    table.add_row(
        f"[{TITLE_STYLE}]Created[/{TITLE_STYLE}]",
        f"{format_date(function.created_at)}",
    )
    table.add_row(
        f"[{TITLE_STYLE}]Updated[/{TITLE_STYLE}]",
        f"{format_date(function.updated_at)}",
    )
    table.add_row(
        f"[{TITLE_STYLE}]Deleted[/{TITLE_STYLE}]",
        f"{format_date(function.deleted_at) or NOT_AVAILABLE}",
    )
    table.add_row(
        f"[{TITLE_STYLE}]Language[/{TITLE_STYLE}]",
        f"{function.language or NOT_AVAILABLE}",
    )
    print_standard(table)

    if confirm("View function code?", default=False):
        code = function.code
        if code:
            # Check if this is zip bytes or plain text
            is_zip = function.code_path is not None

            if is_zip:
                print_info(
                    "This function uses zip file storage. The code is stored as base64-encoded zip bytes."
                )
                if confirm("Save zip file to disk?", default=False):
                    zip_filename = f"function_{function.id}.zip"
                    try:
                        zip_bytes = base64.b64decode(code)
                        with open(zip_filename, "wb") as f:
                            f.write(zip_bytes)
                        print_info(
                            f"Zip file saved as: [{PATH_STYLE}]{zip_filename}[/{PATH_STYLE}] in current directory"
                        )
                    except Exception as e:
                        print_error(f"Failed to save zip file: {e}")
            else:
                print_info("This function uses plain text storage.")
                language = function.language.lower()
                ext = next(
                    (k for k, v in EXT_TO_LANG.items() if v.lower() == language),
                    language or "txt",
                )
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=f".{ext}", mode="w", encoding="utf-8"
                ) as tmp:
                    tmp.write(code)
                    tmp_path = tmp.name
                print_info(
                    f"Temporary file created at: [{PATH_STYLE}]{tmp_path}[/{PATH_STYLE}]"
                )
                if confirm("Remove temporary file?", default=True):
                    os.remove(tmp_path)
        else:
            print_warning("No code found for this function.")


@app.command("create")
def func_create(
    agent_name_or_id: str = typer.Argument(..., help="Agent name or ID."),
    directory: str = typer.Option(
        None, "--dir", help="Directory path to the function code"
    ),
    display_name: str = typer.Option(
        None, "--display-name", help="Display name for the function"
    ),
):
    """Create a new function for an agent. Provide agent name or ID and file path to the function code zip file."""
    agent = agent_repository.get_by_name_or_id(agent_name_or_id)
    if not agent:
        print_error(f"Agent '{agent_name_or_id}' not found.")
        return

    if not display_name and not directory:
        agent_function_repository = AgentFunctionRepository(agent.id)
        functions = agent_function_repository.get()
        func_display_names = [f.display_name for f in functions if f.display_name]
        while True:
            display_name = prompt("Enter function display name")
            if display_name not in func_display_names:
                break
            print_error(
                f"Function display name '{display_name}' is already taken. Please choose a different name."
            )
        print_info("You need to provide a directory path for the function code.")
        directory = prompt("Enter directory path")
        directory = Path(directory).expanduser()
        if not directory.exists():
            print_error(
                f"Directory not found at '[{PATH_STYLE}]{directory}[/{PATH_STYLE}]'"
            )
            return

    directory_full_path = Path(directory).expanduser()
    if not directory_full_path.exists():
        print_error(
            f"File not found at '[{PATH_STYLE}]{directory_full_path}[/{PATH_STYLE}]'"
        )
        return

    zip_bytes, code_lang = package_function(directory_full_path)

    code = base64.b64encode(zip_bytes).decode("utf-8")

    agent_function = AgentFunction(
        agent_id=agent.id,
        code=code,
        is_multifile=True,
        language=code_lang,
        display_name=display_name,
    )

    agent_function_repository = AgentFunctionRepository(agent.id)
    created_function = agent_function_repository.create(agent_function)

    if created_function:
        print_success(
            f"Function '{created_function.get_display_name()}' created successfully."
        )
    else:
        print_error(f"Failed to create function for agent '{agent_name_or_id}'.")


@app.command("update")
def func_update(
    agent_name_or_id: str = typer.Argument(..., help="Agent name or ID"),
    function_name_or_id: str = typer.Argument(..., help="Function name or ID"),
    directory: str = typer.Option(
        None, "--dir", help="Directory path to the function code"
    ),
    display_name: str = typer.Option(
        None, "--display-name", help="Display name for the function"
    ),
):
    """Update a function. Provide agent name or ID. Provide function name or ID. Optionally provide file path to the function code zip file."""
    agent = agent_repository.get_by_name_or_id(agent_name_or_id)
    if not agent:
        print_error(f"Agent '{agent_name_or_id}' not found.")
        return

    agent_function_repository = AgentFunctionRepository(agent.id)
    function = agent_function_repository.get_by_name_or_id(function_name_or_id)
    if not function:
        print_error(f"Function '{function_name_or_id}' not found.")
        return

    agent_environment_repository = AgentEnvironmentRepository(agent.id)
    environments = agent_environment_repository.get()

    env = next((e for e in environments if e.function_id == function.id), None)
    if (
        env and not env.is_debug
    ):  # cannot update function if it's deployed to a non-debug environment
        print_error(
            f"Function '{function.get_display_name()}' is already deployed to environment '{env.name}' and cannot be updated. Create a new function instead."
        )
        return

    if not display_name and not directory:
        agent_function_repository = AgentFunctionRepository(agent.id)
        functions = agent_function_repository.get()
        func_display_names = [
            f.display_name for f in functions if f.id != function.id and f.display_name
        ]
        while True:
            display_name = prompt(
                "Enter new function display name", default=function.display_name or ""
            )
            if display_name not in func_display_names:
                break
            print_error(
                f"Function display name '{display_name}' is already taken. Please choose a different name."
            )
        if confirm("View current function code?", default=False):
            code = function.code
            if code:
                # Check if this is zip bytes or plain text
                is_zip = function.code_path is not None

                if is_zip:
                    print_info(
                        "This function uses zip file storage. The code is stored as base64-encoded zip bytes."
                    )
                    if confirm("Save zip file to disk?", default=False):
                        zip_filename = f"function_{function.id}.zip"
                        try:
                            zip_bytes = base64.b64decode(code)
                            with open(zip_filename, "wb") as f:
                                f.write(zip_bytes)
                            print_info(
                                f"Zip file saved as: [{PATH_STYLE}]{zip_filename}[/{PATH_STYLE}] in current directory"
                            )
                        except Exception as e:
                            print_error(f"Failed to save zip file: {e}")
                else:
                    print_info("This function uses plain text storage.")
                    language = function.language.lower()
                    ext = next(
                        (k for k, v in EXT_TO_LANG.items() if v.lower() == language),
                        language or "txt",
                    )
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=f".{ext}", mode="w", encoding="utf-8"
                    ) as tmp:
                        tmp.write(code)
                        tmp_path = tmp.name
                    print_info(
                        f"Temporary file created at: [{PATH_STYLE}]{tmp_path}[/{PATH_STYLE}]"
                    )
                    if confirm("Remove temporary file?", default=True):
                        os.remove(tmp_path)
            else:
                print_warning("No code found for this function.")
        print_info(
            "Provide a directory path for the function code, or hit enter to keep the same code."
        )
        directory = prompt("Enter directory path", default="", validation=None)
        if not directory:
            # Update only the display name
            function.display_name = display_name
            updated_function = agent_function_repository.update_by_id(
                function.id, function
            )
            if updated_function:
                print_success(
                    f"Function '{updated_function.get_display_name()}' updated successfully."
                )
            else:
                print_error(
                    f"Failed to update function '{function.get_display_name()}'."
                )
            return
        directory = Path(directory).expanduser()
        if not directory.exists():
            print_error(
                f"Directory not found at '[{PATH_STYLE}]{directory}[/{PATH_STYLE}]'"
            )
            return

    zip_bytes, code_lang = package_function(directory)

    code = base64.b64encode(zip_bytes).decode("utf-8")

    function.code = code
    function.language = code_lang
    function.is_multifile = True
    function.display_name = display_name

    updated_function = agent_function_repository.update_by_id(function.id, function)

    if updated_function:
        print_success(
            f"Function '{updated_function.get_display_name()}' updated successfully."
        )
    else:
        print_error(f"Failed to update function '{function_name_or_id}'.")


@app.command("delete")
def func_delete(
    agent_name_or_id: str = typer.Argument(..., help="Agent name or ID."),
    function_name_or_id: str = typer.Argument(..., help="Function name or ID."),
):
    """Delete a function. Provide agent name or ID and function name or ID."""
    agent = agent_repository.get_by_name_or_id(agent_name_or_id)
    if not agent:
        print_error(f"Agent '{agent_name_or_id}' not found.")
        return

    agent_function_repository = AgentFunctionRepository(agent.id)
    function = agent_function_repository.get_by_name_or_id(function_name_or_id)
    if not function:
        print_error(f"Function '{function_name_or_id}' not found.")
        return

    if confirm(
        f"Are you sure you want to delete function '{function.get_display_name()}'?"
    ):
        is_deleted = agent_function_repository.delete_by_id(function.id)
        if is_deleted:
            print_success(
                f"Function '{function.get_display_name()}' deleted successfully."
            )
        else:
            print_error(f"Failed to delete function '{function.get_display_name()}'.")


@app.command("deploy")
def func_deploy(
    agent_name_or_id: str = typer.Argument(..., help="Agent name or ID"),
    function_name_or_id: str = typer.Argument(..., help="Function name or ID"),
    env_name_or_id: str = typer.Option(None, "--env", help="Environment name or ID"),
):
    """Deploy a function to an environment. Provide agent name or ID and function name or ID. Optionally provide environment name or ID."""
    agent = agent_repository.get_by_name_or_id(agent_name_or_id)
    if not agent:
        print_error(f"Agent '{agent_name_or_id}' not found.")
        return

    agent_function_repository = AgentFunctionRepository(agent.id)
    function = agent_function_repository.get_by_name_or_id(function_name_or_id)
    if not function:
        print_error(f"Function '{function_name_or_id}' not found.")
        return

    env_name_or_id = env_name_or_id or prompt("Enter environment name or ID")
    agent_environment_repository = AgentEnvironmentRepository(agent.id)
    environment = agent_environment_repository.get_by_name_or_id(env_name_or_id)
    if not environment:
        print_error(f"Environment '{env_name_or_id}' not found.")
        return

    if environment.is_debug:
        print_warning(
            f"You are deploying to the debug environment. The function will still be editable. DO NOT use this environment for production."
        )
        if not confirm("Continue?"):
            print_info("Deployment cancelled.")
            return

    environment.function_id = function.id
    if confirm(
        f"Deploy function '{function.get_display_name()}' to environment '{environment.name}'?",
        default=True,
    ):
        updated_environment = agent_environment_repository.update_by_id(
            environment.id, environment
        )
        if updated_environment:
            print_success(
                f"Function '{function.get_display_name()}' deployed to environment '{environment.name}' successfully."
            )
        else:
            print_error(
                f"Failed to deploy function '{function.get_display_name()}' to environment '{environment.name}'."
            )
    else:
        print_info("Deployment cancelled.")


@app.command("debug")
def func_debug(
    agent_name_or_id: str = typer.Argument(..., help="Agent name or ID"),
    function_name_or_id: str = typer.Argument(..., help="Function name or ID"),
    env_name_or_id: str = typer.Option(None, "--env", help="Environment name or ID"),
    phone_only: bool = typer.Option(False, "--phone", help="Phone number"),
):
    """Debug a function. Provide agent name or ID and function name or ID. Optionally provide environment name or ID to deploy to an existing environment. If no environment is provided, a temporary environment will be created."""
    agent = agent_repository.get_by_name_or_id(agent_name_or_id)
    if not agent:
        print_error(f"Agent '{agent_name_or_id}' not found.")
        return

    agent_function_repository = AgentFunctionRepository(agent.id)
    function = agent_function_repository.get_by_name_or_id(function_name_or_id)
    if not function:
        print_error(f"Function '{function_name_or_id}' not found.")
        return

    agent_environment_repository = AgentEnvironmentRepository(agent.id)

    environment = None

    if env_name_or_id:
        environment = agent_environment_repository.get_by_name_or_id(env_name_or_id)
        if not environment:
            print_error(f"Environment '{env_name_or_id}' not found.")
            return

        if not environment.function_id == function.id:
            print_error(
                f"Environment '{env_name_or_id}' is not associated with function '{function.get_display_name()}'. "
                f"Deploy function '{function.get_display_name()}' to environment '{env_name_or_id}' first, "
                f"or run func debug without --env to use the debug environment."
            )
            return
    else:
        environment = agent_environment_repository.get_debug_environment()

    if not environment:
        print_error("Environment not found.")
        return

    if phone_only:
        print_info("Starting debugger in phone-only mode...")
        # use environment phone number if available
        if environment.phone_number:
            phone = environment.phone_number

        # use user phone number if environment phone number is not available
        else:
            phone_number_repository = PhoneNumberRepository()
            phone_number = phone_number_repository.get()
            if not phone_number:
                print_error("No phone number found.")
                return False
            if not phone_number_repository.debug(agent, environment, function):
                print_error("Failed to start debugging with phone number.")
                return False
            phone = phone_number.phone_number
        print_info(
            f"Call {format_phone_number(phone)} to debug function '{function.get_display_name()}' in environment '{environment.name}'"
        )
        return

    print_info(
        f"Running function '{function.get_display_name()}' in environment '{environment.name}'..."
    )
    asyncio.run(run_debugger(agent, environment, function))
