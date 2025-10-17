# Configuration and constants for primvoices-cli

# use for production
from pathlib import Path

API_BASE_URL = "https://api.primvoices.com"
FRONTEND_URL = "https://app.primvoices.com"

# use for development
# API_BASE_URL = "https://api-dev.primvoices.com"
# FRONTEND_URL = "https://app-dev.primvoices.com"

# use for local development
# API_BASE_URL = "http://localhost:8080"
# FRONTEND_URL = "http://localhost:3000"

# Map file extension to language name
EXT_TO_LANG = {
    "c": "c",
    "cpp": "cpp",
    "cs": "csharp",
    "dart": "dart",
    "go": "go",
    "java": "java",
    "jl": "julia",
    "js": "javascript",
    "kt": "kotlin",
    "lua": "lua",
    "m": "matlab",
    "pl": "perl",
    "php": "php",
    "py": "python",
    "r": "r",
    "rb": "ruby",
    "rs": "rust",
    "scala": "scala",
    "sh": "shell",
    "sql": "sql",
    "swift": "swift",
    "ts": "typescript",
}

# Color constants
TITLE_COLOR = "magenta"
SUCCESS_COLOR = "green"
WARNING_COLOR = "yellow"
ERROR_COLOR = "red"
INFO_COLOR = "dim"
TRUE_COLOR = "green"
FALSE_COLOR = "red"
ID_COLOR = "bright_blue"
PATH_COLOR = "cyan"
USER_COLOR = "cyan"
AGENT_COLOR = "green"

# Style constants
TITLE_STYLE = f"bold {TITLE_COLOR}"
SUCCESS_STYLE = f"bold {SUCCESS_COLOR}"
WARNING_STYLE = f"bold {WARNING_COLOR}"
ERROR_STYLE = f"bold {ERROR_COLOR}"
INFO_STYLE = INFO_COLOR
TRUE_STYLE = TRUE_COLOR
FALSE_STYLE = FALSE_COLOR
ID_STYLE = ID_COLOR
PATH_STYLE = PATH_COLOR
USER_STYLE = f"bold {USER_COLOR}"
AGENT_STYLE = f"bold {AGENT_COLOR}"

# Constant strings
UNNAMED = "Unnamed"
NOT_AVAILABLE = "N/A"
COOKIE_FILE = Path.home() / ".primvoices_cookie"
DEBUG_ENV_NAME = "debug"

# Auth constants
MAX_POLL_ATTEMPTS = 60
POLL_INTERVAL = 2

# Audio input constants
INPUT_SAMPLE_RATE = 16000
INPUT_CHUNK_SIZE = 1024
INPUT_SOUND_THRESHOLD = 0.015
INTERRUPTION_DURATION_MS = 50
DEFAULT_ECHO_DELAY_CHUNKS = 3
ECHO_ALIGNMENT_WINDOW = 20
ECHO_ALIGNMENT_THRESHOLD_FACTOR = 1.5
ECHO_ALIGNMENT_BASELINE_FACTOR = 0.1
ECHO_GRACE_PERIOD = 5
RESIDUAL_THRESHOLD_FACTOR = 0.8
ECHO_ALIGNMENT_SPIKE_FACTOR = 3

# Audio output constants
OUTPUT_SAMPLE_RATE = 24000
OUTPUT_CHUNK_SIZE = 1024
ECHO_BUFFER_SIZE = 50
