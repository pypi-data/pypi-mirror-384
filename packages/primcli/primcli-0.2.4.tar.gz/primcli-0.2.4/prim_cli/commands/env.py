from datetime import datetime

import requests
import typer
from rich.table import Table
import asyncio

from ..entities.agent import AgentRepository
from ..entities.agent_environment import AgentEnvironment, AgentEnvironmentRepository
from ..entities.agent_environment_variable import AgentEnvironmentVariableRepository
from ..entities.agent_function import AgentFunctionRepository

from ..utils.config import (
    TITLE_STYLE,
    TRUE_STYLE,
    FALSE_STYLE,
    ID_STYLE,
    UNNAMED,
    NOT_AVAILABLE
)
from ..utils.utils import (
    format_date,
    format_phone_number,
    handle_http_error,
    manage_variables,
    print_error,
    print_standard,
    print_success,
    print_info,
    print_warning,
    prompt,
    confirm
)
from .debug import run_debugger

app = typer.Typer()
agent_repository = AgentRepository()

@app.command("list")
def agent_env_list(
    agent_name_or_id: str = typer.Argument(..., help="Agent name or ID.")
):
    """List all environments for an agent. Provide agent name or ID."""
    print_info(f"Getting environments for {agent_name_or_id}...")
    agent = agent_repository.get_by_name_or_id(agent_name_or_id)
    if not agent:
        print_error(f"Agent '{agent_name_or_id}' not found.")
        return
    agent_environment_repository = AgentEnvironmentRepository(agent.id)
    environments = agent_environment_repository.get()
    table = Table(
        "Name", "Phone", "Function", "Updated", "ID",
        show_header=True, header_style=TITLE_STYLE
    )
    agent_function_repository = AgentFunctionRepository(agent.id)
    functions = agent_function_repository.get()
    for env in environments:
        func_name = next(
            (f.name for f in functions if f.id == env.function_id), ""
        )
        table.add_row(
            f"{env.name}",
            f"{format_phone_number(env.phone_number) or NOT_AVAILABLE}",
            f"{func_name or NOT_AVAILABLE}",
            f"{format_date(env.updated_at)}",
            f"[{ID_STYLE}]{env.id}[/{ID_STYLE}]",
        )
    print_standard(table)


@app.command("info")
def agent_env_info(
    agent_name_or_id: str = typer.Argument(..., help="Agent name or ID."),
    env_name_or_id: str = typer.Argument(..., help="Environment name or ID."),
):
    """Show detailed information about an environment. Provide agent name or ID and environment name or ID."""
    agent = agent_repository.get_by_name_or_id(agent_name_or_id)
    if not agent:
        print_error(f"Agent '{agent_name_or_id}' not found.")
        return
    agent_environment_repository = AgentEnvironmentRepository(agent.id)
    env = agent_environment_repository.get_by_name_or_id(env_name_or_id)
    if not env:
        print_error(f"Environment '{env_name_or_id}' not found.")
        return
    if env.function_id:
        agent_function_repository = AgentFunctionRepository(agent.id)
        func = agent_function_repository.get_by_id(env.function_id)
        if not func:
            return
    else:
        func = None

    table = Table(
        show_header=False, 
        show_lines=False, 
        box=None, 
        pad_edge=False
    )
    table.add_row(
        f"[{TITLE_STYLE}]Environment[/{TITLE_STYLE}]", 
        f"{env.name or UNNAMED}"
    )
    table.add_row(
        f"[{TITLE_STYLE}]ID[/{TITLE_STYLE}]", 
        f"[{ID_STYLE}]{env.id}[/{ID_STYLE}]"
    )
    table.add_row(
        f"[{TITLE_STYLE}]Agent[/{TITLE_STYLE}]", 
        f"{agent.name or UNNAMED}"
    )
    table.add_row(
        f"[{TITLE_STYLE}]Agent ID[/{TITLE_STYLE}]", 
        f"[{ID_STYLE}]{agent.id}[/{ID_STYLE}]"
    )
    table.add_row(
        f"[{TITLE_STYLE}]Function[/{TITLE_STYLE}]", 
        f"{func.name if func else NOT_AVAILABLE}"
    )
    table.add_row(
        f"[{TITLE_STYLE}]Function ID[/{TITLE_STYLE}]", 
        f"[{ID_STYLE}]{func.id if func else NOT_AVAILABLE}[/{ID_STYLE}]"
    )
    table.add_row(
        f"[{TITLE_STYLE}]Is Debug[/{TITLE_STYLE}]", 
        f"[{TRUE_STYLE}]Yes[/{TRUE_STYLE}]" if env.is_debug
        else f"[{FALSE_STYLE}]No[/{FALSE_STYLE}]"
    )
    table.add_row(
        f"[{TITLE_STYLE}]Created[/{TITLE_STYLE}]", 
        f"{format_date(env.created_at)}"
    )
    table.add_row(
        f"[{TITLE_STYLE}]Updated[/{TITLE_STYLE}]", 
        f"{format_date(env.updated_at)}"
    )
    table.add_row(
        f"[{TITLE_STYLE}]Deleted[/{TITLE_STYLE}]", 
        f"{format_date(env.deleted_at) or NOT_AVAILABLE}"
    )
    table.add_row(
        f"[{TITLE_STYLE}]Phone[/{TITLE_STYLE}]", 
        f"{format_phone_number(env.phone_number) or NOT_AVAILABLE}"
    )
    table.add_row(
        f"[{TITLE_STYLE}]Recording[/{TITLE_STYLE}]", 
        f"[{TRUE_STYLE}]On[/{TRUE_STYLE}]" if env.recording_enabled
        else f"[{FALSE_STYLE}]Off[/{FALSE_STYLE}]"
    )
    table.add_row(
        f"[{TITLE_STYLE}]Redaction[/{TITLE_STYLE}]", 
        f"[{TRUE_STYLE}]On[/{TRUE_STYLE}]" if env.redaction_enabled 
        else f"[{FALSE_STYLE}]Off[/{FALSE_STYLE}]"
    )
    table.add_row(
        f"[{TITLE_STYLE}]STT Language[/{TITLE_STYLE}]", 
        f"{'English' if env.stt_language == 'en' else env.stt_language or NOT_AVAILABLE}"
    )
    table.add_row(
        f"[{TITLE_STYLE}]STT Keywords[/{TITLE_STYLE}]", 
        f"{env.stt_prompt or NOT_AVAILABLE}"
    )
    agent_environment_variable_repository = AgentEnvironmentVariableRepository(agent.id, env.id)
    vars_response = agent_environment_variable_repository.get()
    if vars_response:
        table.add_row(f"[{TITLE_STYLE}]Variables[/{TITLE_STYLE}]", "")
        vars_table = Table(
            "Name", "Value", "Masked", 
            show_header=True, 
            header_style=TITLE_STYLE, 
            box=None, 
            show_edge=False
        )
        for var in vars_response:
            masked = var.masked
            value = "*****" if masked else var.value
            vars_table.add_row(
                var.name,
                value,
                f"[{TRUE_STYLE}]Yes[/{TRUE_STYLE}]" if masked 
                else f"[{FALSE_STYLE}]No[/{FALSE_STYLE}]"
            )
        table.add_row("", vars_table)
    print_standard(table)


@app.command("create")
def agent_env_create(
    agent_name_or_id: str = typer.Argument(..., help="Agent name or ID.")
):
    """Create a new environment for an agent. Provide agent name or ID."""
    agent = agent_repository.get_by_name_or_id(agent_name_or_id)
    if not agent:
        print_error(f"Agent '{agent_name_or_id}' not found.")
        return
    agent_environment_repository = AgentEnvironmentRepository(agent.id)
    environments = agent_environment_repository.get()
    env_names = [e.name for e in environments]
    while True:
        env_name = prompt("Enter environment name")
        if env_name not in env_names:
            break
        print_error(f"Environment name '{env_name}' is already taken. Please choose a different name.")
    phone = confirm("Add phone number?", default=False)
    recording = confirm("Enable recording?", default=False)
    redaction = confirm("Enable redaction?", default=False)
    stt_language_is_english = confirm(
        "Use English for STT language? (select No for Multi-Lingual)", 
        default=True
    )
    stt_language = "en" if stt_language_is_english else "multi"
    stt_prompt = prompt(
        "Enter STT keywords (comma-separated)", 
        default="", 
        validation=None
    )
    deploy = confirm("Deploy function to environment?", default=False)
    if deploy:
        agent_function_repository = AgentFunctionRepository(agent.id)
        while True:
            func = prompt("Function (name or ID)")
            function = agent_function_repository.get_by_name_or_id(func)
            if function:
                func = function.id
                break
    else:
        func = ""
    new_env = AgentEnvironment(
        name=env_name,
        agent_id=agent.id,
        function_id=func,
        phone_number=None,
        recording_enabled=recording,
        redaction_enabled=redaction,
        stt_language=stt_language,
        stt_prompt=stt_prompt,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        deleted_at=None,
    )
    agent_environment_repository = AgentEnvironmentRepository(agent.id)
    env = agent_environment_repository.create(new_env)
    manage_variables(agent.id, env.id, False)
    if phone:
        phone_env = agent_environment_repository.configure_phone(env.id, phone)
        if not phone_env:
            print_error(f"Failed to configure phone number for environment '{env.name}'")
            return
        print_info(f"Phone number '{format_phone_number(phone_env.phone_number)}' configured for environment '{env.name}'")
    print_success(
        f"Environment '{env_name}' created successfully (ID: '{env.id}')"
    )


@app.command("update")
def agent_env_update(
    agent_name_or_id: str = typer.Argument(..., help="Agent name or ID"),
    env_name_or_id: str = typer.Argument(..., help="Environment name or ID"),
):
    """Update an environment. Provide agent name or ID and environment name or ID."""
    agent = agent_repository.get_by_name_or_id(agent_name_or_id)
    if not agent:
        print_error(f"Agent '{agent_name_or_id}' not found.")
        return
    agent_environment_repository = AgentEnvironmentRepository(agent.id)
    env = agent_environment_repository.get_by_name_or_id(env_name_or_id)
    if not env:
        print_error(f"Environment '{env_name_or_id}' not found.")
        return
    environments = agent_environment_repository.get()
    env_names = [e.name for e in environments if e.id != env.id]
    while True:
        env_name = prompt(
            "Enter new environment name", 
            default=env.name
        )
        if env_name not in env_names:
            break
        print_error(f"Environment name '{env_name}' is already taken. Please choose a different name.")
    phone = False
    if not env.phone_number:
        phone = confirm("Add phone number?", default=False)
    recording = confirm(
        "Enable recording?", 
        default=env.recording_enabled
    )
    redaction = confirm(
        "Enable redaction?", 
        default=env.redaction_enabled
    )
    stt_language_is_english = confirm(
        "Use English for STT language? (select No for Multi-Lingual)",
        default=(env.stt_language == "en"),
    )
    stt_language = "en" if stt_language_is_english else "multi"
    stt_prompt = prompt(
        "Enter new STT keywords (comma-separated)",
        default=env.stt_prompt,
        validation=None,
    )
    deploy_prompt = env.function_id or "N/A"
    if confirm(
        f"Deploy function to environment (Current: '{deploy_prompt}')?",
        default=False,
    ):
        agent_function_repository = AgentFunctionRepository(agent.id)
        while True:
            func = prompt("Function (name or ID)")
            function = agent_function_repository.get_by_name_or_id(func)
            if function:
                func = function.id
                break
    else:
        func = ""
    env.name = env_name
    env.function_id = func
    env.recording_enabled = recording
    env.redaction_enabled = redaction
    env.stt_language = stt_language
    env.stt_prompt = stt_prompt
    env.updated_at = datetime.now().isoformat()
    agent_environment_repository.update_by_id(env.id, env)
    print_info(f"Updating environment variables...")
    manage_variables(agent.id, env.id, True)
    if phone and not env.phone_number:
        phone_env = agent_environment_repository.configure_phone(env.id, phone)
        if not phone_env:
            print_error(f"Failed to configure phone number for environment '{env.name}'")
            return
        print_info(f"Phone number '{format_phone_number(phone_env.phone_number)}' configured for environment '{env.name}'")
    print_success(f"Environment '{env_name}' updated successfully")


@app.command("delete")
def agent_env_delete(
    agent_name_or_id: str = typer.Argument(..., help="Agent name or ID."),
    env_name_or_id: str = typer.Argument(..., help="Environment name or ID."),
):
    """Delete an environment. Provide agent name or ID and environment name or ID."""
    agent = agent_repository.get_by_name_or_id(agent_name_or_id)
    if not agent:
        print_error(f"Agent '{agent_name_or_id}' not found.")
        return
    agent_environment_repository = AgentEnvironmentRepository(agent.id)
    env = agent_environment_repository.get_by_name_or_id(env_name_or_id)
    if not env:
        print_error(f"Environment '{env_name_or_id}' not found.")
        return
    if env.is_debug:
        print_error(f"You cannot delete the debug environment '{env.name}'.")
        return
    if confirm(f"Are you sure you want to delete environment '{env.name}'?"):
        agent_environment_repository.delete_by_id(env.id)
        print_success(f"Environment '{env.name}' deleted successfully.")


@app.command("deploy")
def agent_env_deploy(
    agent_name_or_id: str = typer.Argument(..., help="Agent name or ID"),
    env_name_or_id: str = typer.Argument(..., help="Environment name or ID"),
    func_name_or_id: str = typer.Option(
        None, "--func", help="Function name or ID"
    ),
):
    """Deploy a function to an environment. Provide agent name or ID and environment name or ID. Optionally provide function name or ID."""
    try:
        agent = agent_repository.get_by_name_or_id(agent_name_or_id)
        if not agent:
            print_error(f"Agent '{agent_name_or_id}' not found.")
            return
        agent_environment_repository = AgentEnvironmentRepository(agent.id)
        env = agent_environment_repository.get_by_name_or_id(env_name_or_id)
        if not env:
            print_error(f"Environment '{env_name_or_id}' not found.")
            return
        
        if env.is_debug:
            print_warning(f"You are deploying to the debug environment. The function will still be editable. DO NOT use this environment for production.")
            if not confirm("Continue?"):
                print_info("Deployment cancelled.")
                return
        
        agent_function_repository = AgentFunctionRepository(agent.id)
        while True:
            func = func_name_or_id or prompt("Function (name or ID)")
            function = agent_function_repository.get_by_name_or_id(func)
            if function:
                func = function.id
                break
            func_name_or_id = None
        
        env.function_id = func
        env.updated_at = datetime.now().isoformat()
        
        if not confirm(
            f"Deploy function '{function.name}' "
            f"to environment '{env.name}'?"
        ):
            return
            
        agent_environment_repository.update_by_id(env.id, env)
        print_success(
            f"Function '{function.name}' deployed to "
            f"environment '{env.name}' successfully"
        )
    except requests.HTTPError as e:
        handle_http_error(e)


@app.command("undeploy")
def agent_env_undeploy(
    agent_name_or_id: str = typer.Argument(..., help="Agent name or ID"), 
    env_name_or_id: str = typer.Argument(..., help="Environment name or ID")
):
    """Remove a function from an environment. Provide agent name or ID and environment name or ID."""
    try:
        agent = agent_repository.get_by_name_or_id(agent_name_or_id)
        if not agent:
            print_error(f"Agent '{agent_name_or_id}' not found.")
            return
        agent_environment_repository = AgentEnvironmentRepository(agent.id)
        env = agent_environment_repository.get_by_name_or_id(env_name_or_id)
        if not env:
            print_error(f"Environment '{env_name_or_id}' not found.")
            return
        
        current_func_id = env.function_id
        if not current_func_id:
            print_warning(
                f"No function currently deployed to environment '{env.name}'"
            )
            return
        
        env.function_id = ""
        env.updated_at = datetime.now().isoformat()
        
        if not confirm(f"Remove function from environment '{env.name}'?"):
            return
            
        agent_environment_repository.update_by_id(env.id, env)
        print_success(
            f"Function removed from environment '{env.name}' successfully"
        )
    except requests.HTTPError as e:
        handle_http_error(e)


@app.command("debug")
def env_debug(
    agent_name_or_id: str = typer.Argument(..., help="Agent name or ID"), 
    environment_name_or_id: str = typer.Argument(..., help="Environment name or ID")
):
    """Debug a function. Provide agent name or ID and function name or ID."""
    try:
        agent = agent_repository.get_by_name_or_id(agent_name_or_id)
        if not agent:
            print_error(f"Agent '{agent_name_or_id}' not found.")
            return
        agent_environment_repository = AgentEnvironmentRepository(agent.id)
        environment = agent_environment_repository.get_by_name_or_id(environment_name_or_id)
        if not environment:
            print_error(f"Environment '{environment_name_or_id}' not found.")
            return
        function_id = environment.function_id
        if not function_id:
            print_warning(
                f"No function deployed to environment '{environment.name}'"
            )
            return
        agent_function_repository = AgentFunctionRepository(agent.id)
        function = agent_function_repository.get_by_id(function_id)
        if not function:
            return
        print_info(
            f"Debugging function '{function.name}' in environment '{environment.name}'"
        )
        asyncio.run(run_debugger(agent, environment, function))
    except requests.HTTPError as e:
        handle_http_error(e)
