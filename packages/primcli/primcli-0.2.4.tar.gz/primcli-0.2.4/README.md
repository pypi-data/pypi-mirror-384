# primvoices-cli

A comprehensive command-line interface for interacting with the Prim Voices API. This CLI tool provides easy access to manage agents, functions, environments, and authentication.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Install from PyPI](#install-from-pypi)
- [Install from Source](#install-from-source)
- [Development Setup](#development-setup)
- [Quick Start](#quick-start)
- [Authentication](#authentication)
- [Agent Management](#agent-management)
- [Agent Functions](#agent-functions)
- [Agent Environments](#agent-environments)
- [Features](#features)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Requirements](#requirements)
- [Dependencies](#dependencies)
- [Support](#support)
- [CLI Output Conventions](#cli-output-conventions)
- [Developer Notes](#developer-notes)
- [Phone Number Management](#phone-number-management)

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

If you do not have a uv virtual environment, you can create one with:
```bash
uv venv --python 3.12
```

**Note:** We recommend using uv to install the package due to the incredible speed of the package manager. The package can still be installed via pip directly, but it will be slower.

## Installation

### Install from PyPI

The easiest way to install primvoices-cli is from PyPI:

```bash
pip install primcli
```

### Install from Source

To install from source (for development or latest features):

```bash
uv pip install .
```

## Development Setup

### Environment

To switch target platform environment, update:
`prim_cli/tools/config.py` : `API_BASE_URL` + `FRONTEND_URL`

### Git Hooks
This project includes git hooks to ensure code quality. To set up the git hooks:

```bash
python setup_hooks.py
```

This will create a pre-commit hook that automatically runs black on Python files before each commit.

## Quick Start

1. **Sign in to your account:**
   ```bash
   prim signin
   ```

2. **List your agents:**
   ```bash
   prim list
   ```

## Authentication

### Sign In
```bash
prim signin
```
This command offers two authentication methods:
- **Direct authentication**: Enter email and password directly in the terminal
- **Web authentication**: Opens a browser to login through the PrimVoices website (recommended for enhanced security via Stytch)

When using web authentication, the CLI will open a login URL in your browser and poll for completion. Upon successful login, your session is securely stored locally.

### Sign Out
```bash
prim signout
```
Clears your authentication session and removes stored credentials.

## Agent Management

### List Agents
```bash
prim list [--all]
```
- `--all`: Show detailed information including creation dates and IDs

### Agent Information
```bash
prim info <agent_name_or_id>
```

### Create Agent
```bash
prim create
```
Interactive command that prompts for:
- Agent name (required)
- Description (required)
- Default voice (by name or ID, required)

### Update Agent
```bash
prim update <agent_name_or_id>
```
Interactive command to modify agent properties.

### Delete Agent
```bash
prim delete <agent_name_or_id>
```
Deletes an agent after confirmation.

## Agent Functions

### List Functions
```bash
prim func list <agent_name_or_id>
```

### Function Information
```bash
prim func info <agent_name_or_id> <function_name_or_id>
```

### Create Function
```bash
prim func create <agent_name_or_id> --dir <directory_path>
```
Creates a new function from a directory. Supports multiple programming languages:
- Python (.py)
- JavaScript (.js)

### Update Function
```bash
prim func update <agent_name_or_id> <function_name_or_id> [--dir <directory_path>]
```
- `--dir`: Path to the updated code directory
- Without `--dir`: Creates a temporary file for editing
- e.g. from URL: https://app.primvoices.com/agents/<agent_name_or_id>/function?f=<function_name_or_id>

### Delete Function
```bash
prim func delete <agent_name_or_id> <function_name_or_id>
```

### Deploy Function
```bash
prim func deploy <agent_name_or_id> <function_name_or_id>
```

### Debug Functions

**NEW**: Debug functions interactively using the command-line debugger, with support for phone and advanced audio features:

```bash
prim func debug <agent_name_or_id> <function_name_or_id> [--env <environment_name_or_id>] [--phone]
```
- `--phone`: Start debugging via phone call (uses environment or user phone number)

#### Debugger Features

The CLI debugger provides the same functionality as the web UI debugger, plus:

- **Real-time WebSocket communication** with the agent
- **Send text messages** to the agent
- **View agent responses** including text-to-speech events
- **Monitor debug events** and logs
- **Track conversation turns** and performance
- **Start/stop microphone recording** (`listen`/`stop` commands)
- **Connect/disconnect phone number** (`phone` command)
- **Advanced audio system**: Echo cancellation, interruption detection, and dynamic echo alignment for seamless voice interaction

#### Debugger Commands

Once in the debugger, you can use these commands:

- `send <text>` - Send a text message to the agent
- `listen` - Start microphone recording (voice input)
- `stop` - Stop microphone recording
- `phone` - Connect or disconnect a phone number for call-based debugging
- `status` - Show connection status and debug summary
- `messages` - Show all debug messages
- `clear` - Clear debug messages
- `help` - Show available commands
- `quit` - Exit debugger

#### Prerequisites

Before using the debugger, make sure:

1. **PrimVoices Agent Server** is running on `localhost:7860`
   ```bash
   # In the primvoices-agents directory
   python src/main.py
   ```

2. **WebSocket dependency** is installed:
   ```bash
   pip install websockets
   ```

3. **Agent and function** exist and are properly configured

#### Example Debug Session

```bash
$ prim func debug my-agent my-function

Starting debugger for agent: my-agent, function: my-function

Debug Configuration:
Agent: My Agent (agent-123)
Function: My Function (func-456)
Environment: Development (env-789)
Language: python

Starting interactive debugger...
Connecting to WebSocket server at ws://localhost:7860/ws
✓ Connected to ws://localhost:7860/ws

PrimVoices CLI Debugger
Type 'help' for available commands, 'quit' to exit

debug> send Hello, how are you?
→ Sent: Hello, how are you?
🤖 Agent (nova): Hello! I'm doing well, thank you for asking. How can I help you today?

debug> status

Debug Summary:
Total messages: 3
Current turn: 1
Connection: Connected
Listening: No

Recent Messages:
  text (input)
  text_to_speech (output)
  turn_end (system)

debug> quit
Disconnected
```

## Agent Environments

### List Environments
```bash
prim env list <agent_name_or_id>
```

### Environment Information
```bash
prim env info <agent_name_or_id> <environment_name_or_id>
```

### Create Environment
```bash
prim env create <agent_name_or_id>
```
Interactive command that prompts for:
- Environment name (required)
- Phone number (optional)
- Recording settings
- Redaction settings
- STT language (English or Multi-lingual)
- STT keywords (optional)
- Function deployment (optional)
- Environment variables (names required, values optional)

If you choose to add a phone number, the CLI will guide you through associating a number with the environment. This enables phone-based debugging and agent interaction.

### Update Environment
```bash
prim env update <agent_name_or_id> <environment_name_or_id>
```
Interactive command to modify environment properties and variables.

### Delete Environment
```bash
prim env delete <agent_name_or_id> <environment_name_or_id>
```

### Deploy to Environment
```bash
prim env deploy <agent_name_or_id> <environment_name_or_id>
```

### Debug Functions

**NEW**: Debug functions interactively using the command-line debugger:

```bash
prim env debug <agent_name_or_id> <environment_name_or_id>
```

#### Debugger Features

The CLI debugger provides the same functionality as the web UI debugger:

- **WebSocket Communication**: Real-time bidirectional communication with PrimVoices agents
- **Audio Processing**: Capture microphone input and play agent responses
- **Text Messaging**: Send text messages to agents
- **Debug Monitoring**: Real-time display of debug messages and conversation turns
- **Audio Statistics**: Monitor audio levels and speech detection
- **Session Management**: Automatic session ID generation and management
- **Configuration**: Environment-based configuration with custom parameters
- **Phone Integration**: Connect to a phone number for call-based debugging and agent interaction

#### Debugger Commands

Once in the debugger, you can use these commands:

- `help` - Show help information
- `status` - Show connection status
- `config` - Show running agent, environment, and function
- `messages` - Show recent debug messages
- `debug <ID>` - Show detailed debugging info for a specific message
- `clear` - Clear message history
- `quit`, `exit`, `q`, or `x` - Exit debugger
- `send <text>` - Send a text message to an agent (also runs when typing any text that's not a command)
- `listen` - Start microphone recording
- `stop` - Stop microphone recording
- `phone` - Connect or disconnect a phone number

#### Example Debug Session

```bash
$ prim env debug my-agent my-environment

Debugging function 'my-agent' in environment 'my-environment'
PrimVoices Debugger
Type 'help' for available commands, or 'quit' to exit
⠼ Connected!

 start (turn 0)

Agent: Hello from your agent

 turn_end (turn 0)

debugger> Hello!
Sent: Hello!

You: Hello!

Agent: Agent heard hello!

 turn_end (turn 1)

debugger> config
Agent: my-agent
Agent ID: agent-123
Environment: my-environment
Environment ID: environment-456
Function: my-function
Function ID: function-789

debugger> quit
Goodbye!
```

## Features

### Rich Terminal Output
- Color-coded tables and information displays
- Formatted dates and timestamps
- Clear status indicators (Yes/No, On/Off)

### Secure Authentication
- Session cookie management
- Secure credential storage
- Direct or web-based authentication using Stytch

### File Management
- Automatic language detection from file extensions
- Temporary file creation for code editing
- Support for multiple programming languages

### Interactive Prompts
- Confirmation dialogs for destructive operations
- Default value suggestions
- Clear error messages and help text
- **All prompts require non-empty input by default unless otherwise specified.**
- To allow empty input, the `validation` parameter can be set to `None` in the prompt utility.
- All prompts and confirmations use single quotes around referenced names/IDs and enforce clear, imperative language.

### Advanced Audio System
- Real-time microphone capture and playback with PyAudio and pygame
- **Echo cancellation**: Removes agent output from mic input to prevent feedback
- **Interruption detection**: Detects when a human interrupts agent speech and stops playback for immediate response
- **Dynamic echo alignment**: Automatically calibrates echo delay for robust interruption detection
- **Hysteresis**: Prevents false stops during brief pauses in conversation
- All audio features are available in the debugger and during phone-based sessions

### Phone Number Management

#### User Phone Number

Manage your user phone number for call-based agent interaction:

```bash
prim phone
```
- View your current phone number
- Add a new phone number if none is set

#### Environment Phone Number

When creating or updating an environment, you can associate a phone number for inbound/outbound calls. This enables phone-based debugging and agent interaction.

- Add a phone number during `prim env create` or `prim env update`
- Use the `phone` command in the debugger to connect/disconnect calls

## Configuration

The CLI automatically manages configuration in your home directory:
- Authentication cookies: `~/.primvoices_cookie`
- Session management and API endpoints

## API Endpoints

- **API Base URL**: `https://api.primvoices.com`
- **Frontend URL**: `https://app.primvoices.com`

## Requirements

- Python 3.7 or higher
- Internet connection for API access

## Dependencies

- `typer`: Command-line interface framework
- `requests`: HTTP client for API communication
- `rich`: Rich terminal output formatting

## CLI Output Conventions

The Prim Voices CLI uses consistent output conventions for all commands to ensure clarity and a professional user experience. These conventions are enforced throughout the codebase:

- **Success messages:**
  - Printed in **bold green** using Rich.
  - Use `print_success()` utility.
  - Example: `[bold green]Agent created successfully![/bold green]`

- **Warning messages:**
  - Printed in **bold yellow** with a `Warning:` prefix using Rich.
  - Use `print_warning()` utility.
  - Example: `[bold yellow]Warning: No Set-Cookie header received[/bold yellow]`

- **Error messages:**
  - Printed in **bold red** with an `Error:` prefix using Rich.
  - Use `print_error()` utility.
  - Example: `[bold red]Error: Unauthorized. Please sign in with prim signin.[/bold red]`

- **IDs:**
  - Always styled as **blue** in output: `[blue]{id}[/blue]`
  - Applies to all user-facing output, including tables and error messages.

- **File paths and URLs:**
  - Always styled as **cyan** in output: `[cyan]{path_or_url}[/cyan]`
  - Applies to all user-facing output, including error/warning messages and informational output.

- **Tables and formatted output:**
  - The CLI uses the [Rich](https://rich.readthedocs.io/) library for all tables and styled output.
  - Table headers use the color defined in `TITLE_COLOR` in `utils/config.py`.

- **Prompts and Confirmations:**
  - All interactive prompts use the `prompt` and `confirm` utilities from `prim_cli/utils/utils.py`.
  - Prompts require non-empty input by default. To allow empty input, pass `validation=None`.
  - Prompts and confirmations use single quotes for referenced names/IDs and clear, imperative language.

**Note:**
- All output and prompt utilities are defined in `prim_cli/utils/utils.py`.
- Please follow these conventions for any new commands or output added to the CLI.

## Developer Notes

### Adding New Commands
- Use Typer's `@app.command` decorator for new commands.
- Use the `prompt` and `confirm` utilities for all user input. By default, prompts require non-empty input. For optional input, set `validation=None`.
- Always use single quotes around referenced names/IDs in prompts and confirmations.
- Use the output utilities (`print_success`, `print_error`, `print_warning`, `print_info`) for all user-facing output.
- Style IDs as blue and file paths as cyan using Rich markup.
- Table headers should use the color defined in `TITLE_COLOR` in `utils/config.py`.

### Testing Agents

**NEW**: Test your agents interactively using text input:

```bash
prim env run <agent_name_or_id> <environment_name_or_id>
```

This command starts an interactive session where you can:
- Send text messages to your agent
- See real-time responses from your agent function
- View conversation history
- Use built-in commands like `help`, `status`, `clear`, `history`

#### Requirements for Real Agent Testing

To test with real agent responses (not simulated), you need:

1. **API Key**: Set the `PRIMVOICES_API_KEY` environment variable
2. **PrimVoices Agents**: The `primvoices-agents` project must be available in the same directory
3. **Deployed Function**: A function must be deployed to the environment you're testing

#### Example Session

```
$ prim env run my-agent development

Starting interactive session for agent 'my-agent' in environment 'development'
Type your messages and press Enter. Type 'quit' or 'exit' to end the session.
Type 'help' for available commands.

Agent function loaded successfully!
You can now interact with your agent using text messages.

You: Hello, how are you?
Agent: Hello! I'm doing well, thank you for asking. How can I help you today?

You: What's the weather like?
Agent: I don't have access to real-time weather information, but I can help you with other questions or tasks. What would you like to know?

You: help
┌─ Help ──────────────────────────────────────────────────────────────────────┐
│ Available commands:                                                         │
│ - help: Show this help message                                             │
│ - quit/exit: End the session                                               │
│ - clear: Clear the conversation history                                    │
│ - history: Show conversation history                                       │
│ - status: Show current session status                                      │
└─────────────────────────────────────────────────────────────────────────────┘

You: quit
Ending session...
Session ended. Total messages: 4
```
