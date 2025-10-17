#!/usr/bin/env python3
"""
PrimVoices Debugger - Python CLI Version

A command-line debugger for PrimVoices agents that provides real-time monitoring
and interaction capabilities similar to the React-based debugger.

Features:
- WebSocket communication with PrimVoices agents
- Real-time audio capture and playback
- Text message sending
- Debug message monitoring and display
- Audio level monitoring
- Session management
- Configuration presets
"""

import asyncio
import base64
import json
import sys
import uuid
import aiohttp
import traceback
import websockets
import numpy as np

from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable

from ..entities.phone_number import PhoneNumberRepository
from ..utils.config import (
    API_BASE_URL,
    TITLE_STYLE,
    USER_COLOR,
    AGENT_COLOR,
    ID_STYLE,
    USER_STYLE,
    INPUT_SAMPLE_RATE,
    OUTPUT_SAMPLE_RATE,
)
from ..utils.utils import (
    format_phone_number,
    print_standard,
    print_success,
    print_warning,
    print_error,
    print_info,
    console,
)

# Import our modular audio components
from ..utils.audio_input import AudioInput
from ..utils.audio_output import AudioOutput

# Commands that are supported by the debugger
SUPPORTED_COMMANDS = [
    "help",
    "status",
    "messages",
    "clear",
    "config",
    "quit",
    "exit",
    "q",
    "x",
    "debug",
    "send",
    "listen",
    "stop",
    "phone",
]


@dataclass
class DebugMessage:
    """Represents a debug message from the agent"""

    type: str
    turn: int
    name: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class WebSocketConfig:
    """Configuration for WebSocket connection"""

    agent: dict
    environment: dict
    function: dict
    server_url: Optional[str] = None
    api_url: str = API_BASE_URL
    custom_parameters: Dict[str, str] = field(default_factory=dict)


class PrimVoicesDebugger:
    """Main debugger class that handles WebSocket communication and UI"""

    def __init__(self, config: WebSocketConfig):
        self.config = config
        self.audio_input = AudioInput()
        self.audio_output = AudioOutput()
        self.websocket = None
        self.is_connected = False
        self.is_listening = False
        self.phone_number = None
        self.phone_connected = False

        # Session IDs
        self.call_sid = str(uuid.uuid4())
        self.stream_sid = str(uuid.uuid4())

        # Message tracking
        self.debug_messages: List[DebugMessage] = []
        self.current_turn = 0

        # Audio processing task
        self.audio_processing_task: Optional[asyncio.Task] = None

        # Callbacks
        self.on_debug_message: Optional[Callable] = None

    @property
    def is_playing(self) -> bool:
        """Check if audio is currently playing"""
        return self.audio_output.is_playing

    async def get_agent_configuration(self) -> Dict[str, Any]:
        """Get agent configuration from API"""
        query_params = {
            "inputType": "mic",
            "environment": f"{self.config.environment.name}|{self.config.function.id}",
        }

        # Add custom parameters
        for key, value in self.config.custom_parameters.items():
            query_params[f"custom_{key}"] = value

        url = f"{self.config.api_url}/v1/agents/{self.config.agent.id}/call"

        try:
            async with aiohttp.ClientSession() as aio_session:
                async with aio_session.post(
                    url, params=query_params, json={}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", {})
                    else:
                        response_text = await response.text()
                        print_error(f"API error response: {response_text}")
                        raise Exception(
                            f"Failed to get agent configuration: {response.status} - {response_text}"
                        )
        except Exception as e:
            # Handle HTTP errors consistently
            print_error(f"Failed to get agent configuration: {e}")
            raise

    async def connect(self):
        """Establish WebSocket connection"""
        try:
            # Production mode - get agent configuration from API first
            agent_config = await self.get_agent_configuration()
            self.config.server_url = agent_config.get("url")
            self.config.custom_parameters.update(agent_config.get("parameters", {}))

            if not self.config.server_url:
                raise Exception("No server URL available from agent configuration")

            # Connect to WebSocket
            self.websocket = await websockets.connect(self.config.server_url)
            self.is_connected = True

            # Send start message in the format expected by the production server
            start_message = {
                "start": {
                    "streamSid": self.stream_sid,
                    "callSid": self.call_sid,
                    "customParameters": self.config.custom_parameters,
                }
            }

            await self.websocket.send(json.dumps(start_message))

            # Start message listener
            asyncio.create_task(self._message_listener())

        except Exception as e:
            print_error(f"Failed to connect: {e}")
            raise

    async def disconnect(self):
        """Close WebSocket connection and clean up resources"""
        self.is_connected = False
        self.is_listening = False

        # Stop audio processing first
        if self.audio_processing_task and not self.audio_processing_task.done():
            self.audio_processing_task.cancel()
            try:
                await self.audio_processing_task
            except asyncio.CancelledError:
                pass
            self.audio_processing_task = None

        # Stop audio recording
        self.audio_input.stop_recording()

        # Stop audio input and output
        self.audio_input.stop_recording()
        self.audio_output.stop_playback()

        # Close WebSocket connection
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                print_error(f"Error closing WebSocket: {e}")
            self.websocket = None

    async def _message_listener(self):
        """Listen for incoming WebSocket messages"""
        try:
            async for message in self.websocket:
                try:
                    parsed_message = json.loads(message)
                    await self._handle_message(parsed_message)
                except json.JSONDecodeError as e:
                    print_error(f"Failed to parse message as JSON: {e}")
                    print_error(f"Raw message: {message}")
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print_error(f"Error in message listener: {e}")

            print_error(f"Traceback: {traceback.format_exc()}")
        finally:
            self.is_connected = False

    async def _handle_message(self, data: Dict[str, Any]):
        """Handle incoming WebSocket messages"""
        try:
            event_type = data.get("event")

            if event_type == "media":
                await self._handle_audio_message(data)
            elif event_type == "clear":
                await self._handle_clear_message(data)
            elif event_type == "mark":
                await self._handle_mark_message(data)
            elif event_type == "debug":
                await self._handle_debug_message(data)
            else:
                print_warning(f"Unknown message type: {event_type}")

        except Exception as e:
            print_error(f"Error handling message: {e}")

    async def _handle_audio_message(self, data: Dict[str, Any]):
        """Handle audio messages from server"""
        if "media" not in data or "payload" not in data["media"]:
            return

        try:
            # Decode base64 audio
            base64_data = data["media"]["payload"]
            audio_bytes = base64.b64decode(base64_data)

            # Production servers send raw 16-bit PCM at 24 kHz for mic input.
            # The is_playing flag will be managed by the audio output module
            self.audio_output.play_pcm_bytes(
                audio_bytes, sample_rate=OUTPUT_SAMPLE_RATE
            )

        except Exception as e:
            print_error(f"Error handling audio message: {e}")

    async def _handle_clear_message(self, data: Dict[str, Any]):
        """Handle clear messages from server"""
        # Stop audio playback (but NOT recording!)
        self.audio_output.stop_playback()

    async def _handle_mark_message(self, data: Dict[str, Any]):
        """Handle mark messages from server"""
        # Add mark event to the audio output queue
        self.audio_output.add_mark_event(data, self.websocket)

    async def _handle_debug_message(self, data: Dict[str, Any]):
        """Handle debug messages from server"""
        debug_msg = DebugMessage(
            type=data.get("type", "unknown"),
            turn=data.get("turn", 0),
            name=data.get("name", "unknown"),
            data=data.get("data", {}),
        )

        self.debug_messages.append(debug_msg)
        self.current_turn = max(self.current_turn, debug_msg.turn)

        if self.on_debug_message:
            self.on_debug_message(debug_msg)

    def start_listening(self) -> bool:
        """Start listening for microphone input"""
        if not self.is_connected:
            raise Exception("Not connected to server")

        if self.phone_connected:
            print_info("Cannot listen while connected to phone number.")
            return False

        self.audio_input.start_recording()
        self.is_listening = True

        # Start the continuous audio processing task
        if self.audio_processing_task is None or self.audio_processing_task.done():
            self.audio_processing_task = asyncio.create_task(
                self._audio_processing_loop()
            )
        return True

    def stop_listening(self) -> bool:
        """Stop listening for microphone input"""
        self.audio_input.stop_recording()
        self.is_listening = False

        # Clear any accumulated audio to prevent sending leftover chunks
        self.audio_input.clear_queue()

        # Stop the audio processing task
        if self.audio_processing_task and not self.audio_processing_task.done():
            self.audio_processing_task.cancel()
            self.audio_processing_task = None
        return True

    def phone(self):
        """Connect to phone number"""
        if not self.is_connected:
            raise Exception("Not connected to server")

        if self.phone_connected:
            print_info("Disconnected from phone number")
            self.phone_connected = False
            return True

        if self.is_listening:
            if not self.stop_listening():
                print_error("Failed to stop listening for microphone input.")
                return False
            self.audio_input.clear_queue()
            print_info("Stopped listening for microphone input.")

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}")
        ) as progress:
            task = progress.add_task("Connecting to phone number...", total=None)
            self.phone_connected = True
            # use environment phone number if available
            if self.config.environment.phone_number:
                phone = self.config.environment.phone_number

            # use user phone number if environment phone number is not available
            else:
                phone_number_repository = PhoneNumberRepository()
                phone_number = phone_number_repository.get()
                if not phone_number:
                    print_error("No phone number found.")
                    return False
                if not phone_number_repository.debug(
                    self.config.agent, self.config.environment, self.config.function
                ):
                    print_error("Failed to start debugging with phone number.")
                    return False
                phone = phone_number.phone_number
            progress.update(task, description=f"Call {format_phone_number(phone)}")

        return True

    async def _audio_processing_loop(self):
        """Continuously process and send audio chunks with interruption detection"""

        # Track playback state to detect when it starts
        was_playing = False

        try:
            while self.is_listening and self.is_connected:

                # Check if playback just started
                if self.is_playing and not was_playing:
                    # Playback just started - notify audio input for echo alignment
                    self.audio_input.notify_playback_started()
                was_playing = self.is_playing

                # Get audio chunk from the queue
                audio_chunk = self.audio_input.get_audio_chunk()

                if audio_chunk is not None:
                    should_send = False
                    if not self.is_playing:
                        # Not playing, send audio normally
                        should_send = True
                    else:
                        # Currently playing - check for interruption with echo cancellation
                        echo_buffer = self.audio_output.get_echo_buffer()
                        is_interruption, buffered_chunks = (
                            self.audio_input.detect_interruption(
                                audio_chunk, echo_buffer
                            )
                        )

                        if is_interruption:
                            # Interruption detected! Stop playback immediately and send buffered chunks
                            self.audio_output.stop_playback()

                            # Send all buffered chunks from the start of the interruption
                            for chunk in buffered_chunks:
                                await self.send_audio_chunk(chunk)

                            # Don't send the current chunk again since it's already in the buffer
                            should_send = False

                    if should_send:
                        await self.send_audio_chunk(audio_chunk)

                # Small delay to prevent overwhelming the CPU
                await asyncio.sleep(0.01)  # 10ms delay

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print_error(f"Error in audio processing loop: {e}")

            print_error(f"Traceback: {traceback.format_exc()}")

    async def send_text_event(self, text: str):
        """Send text message to agent"""
        if not self.is_connected or not self.websocket:
            raise Exception("Not connected to server")

        message = {"event": "text", "text": text}

        await self.websocket.send(json.dumps(message))

    async def send_audio_chunk(self, audio_data: np.ndarray):
        """Send audio chunk to server - matches WebSocketClient.ts exactly"""
        if not self.is_connected or not self.websocket:
            return

        try:
            # Get the current sample rate from the audio processor
            current_sample_rate = self.audio_input.sample_rate  # Currently 16kHz
            target_sample_rate = INPUT_SAMPLE_RATE  # Server expects 16kHz

            # Downsample if needed (though our input should already be 16kHz)
            if current_sample_rate != target_sample_rate:
                audio_data = self.audio_input.downsample_audio(
                    audio_data, current_sample_rate, target_sample_rate
                )

            # Convert to μ-law format
            mu_law_data = self.audio_input.mu_law_encode(audio_data)

            # Encode to base64
            base64_data = base64.b64encode(mu_law_data).decode("utf-8")

            # Send via WebSocket - match the exact format from WebSocketClient.ts
            message = {
                "event": "media",
                "streamSid": self.stream_sid,
                "media": {"payload": base64_data},
            }

            await self.websocket.send(json.dumps(message))
            # print_success(f"Audio chunk sent successfully. Audio level: {audio_level}")

        except Exception as e:
            print_error(f"Error sending audio chunk: {e}")


class DebuggerUI:
    """User interface for the debugger"""

    def __init__(self, debugger: PrimVoicesDebugger):
        self.debugger = debugger
        self.running = False

        # Track whether we are waiting for the agent to finish its current turn.
        # When True, the interactive prompt will not be displayed so that the
        # assistant's response appears without the prompt directly above it.
        self.awaiting_response = False

        # Setup callbacks
        self.debugger.on_debug_message = self._on_debug_message

    def _print_user(self, message: DebugMessage):
        """Print user text in the user color"""
        user_text = message.data.get("text", "")
        print_standard(f"\n[{USER_COLOR}]You:[/{USER_COLOR}] {user_text}")

    def _print_agent(self, message: DebugMessage):
        """Print agent text in the agent color"""
        bot_text = message.data.get("text", "")
        print_standard(f"\n[{AGENT_COLOR}]Agent:[/{AGENT_COLOR}] {bot_text}")

    def _print_generic(self, message: DebugMessage):
        """Print generic debug message"""
        if message.name == "error":
            print_error(f"{message.data.get('message', 'Unknown error')}")
        else:
            print_info(f"{message.name} (turn {message.turn})")

    def _print_prompt(self):
        """Print the prompt"""
        print_standard(f"\n[{USER_STYLE}]debugger>[/{USER_STYLE}] ", end="")

    def _on_debug_message(self, message: DebugMessage):
        """Pretty-print incoming debug messages in real time."""
        # Ensure we're on a fresh line (avoids printing in the middle of the prompt)

        if message.type == "input" and message.name == "text":
            self._print_user(message)
        elif message.type == "output" and message.name == "text_to_speech":
            self._print_agent(message)
        else:
            # Fallback generic display
            self._print_generic(message)

        # After a turn ends, re-display the prompt headline so the next Prompt.ask
        # appears on a new line without the user pressing Enter again.
        if message.name == "turn_end":
            # The agent finished its turn; allow the next user command.
            self.awaiting_response = False
            # Show the prompt immediately after the turn ends
            self._print_prompt()

    def display_status(self):
        """Display current status"""
        status_table = Table(
            show_header=False, show_lines=False, box=None, pad_edge=False
        )

        status_table.add_row(
            f"[{TITLE_STYLE}]Connected[/{TITLE_STYLE}]",
            "✅" if self.debugger.is_connected else "❌",
        )
        status_table.add_row(
            f"[{TITLE_STYLE}]Listening[/{TITLE_STYLE}]",
            "🎤" if self.debugger.is_listening else "🔇",
        )
        status_table.add_row(
            f"[{TITLE_STYLE}]Playing[/{TITLE_STYLE}]",
            "🔊" if self.debugger.is_playing else "🔇",
        )
        status_table.add_row(
            f"[{TITLE_STYLE}]Current Turn[/{TITLE_STYLE}]",
            str(self.debugger.current_turn),
        )
        status_table.add_row(
            f"[{TITLE_STYLE}]Messages[/{TITLE_STYLE}]",
            str(len(self.debugger.debug_messages)),
        )

        print_standard(status_table)

    def display_messages(self, limit: int = 10):
        """Display recent debug messages"""
        if not self.debugger.debug_messages:
            print_info("No debug messages yet")
            return

        messages_table = Table(
            "ID",
            "Turn",
            "Type",
            "Name",
            "Data",
            show_header=True,
            header_style=TITLE_STYLE,
        )

        recent_messages = self.debugger.debug_messages[-limit:]

        for i, msg in enumerate(recent_messages):
            data_str = (
                json.dumps(msg.data, indent=2)[:100] + "..."
                if len(json.dumps(msg.data)) > 100
                else json.dumps(msg.data)
            )
            messages_table.add_row(
                f"[{ID_STYLE}]{i}[/{ID_STYLE}]",
                str(msg.turn),
                f"[{USER_COLOR if msg.type == 'input' else AGENT_COLOR}]"
                f"{msg.type}[/{USER_COLOR if msg.type == 'input' else AGENT_COLOR}]",
                msg.name,
                data_str,
            )

        print_standard(messages_table)

    def display_debug(self, message_index: str):
        """Display debug information"""
        msg_index = int(message_index)
        if msg_index >= len(self.debugger.debug_messages):
            print_error(f"No message with ID {msg_index}.")
            return

        msg = self.debugger.debug_messages[msg_index]
        data_str = json.dumps(msg.data, indent=2)
        table = Table(show_header=False, show_lines=False, box=None, pad_edge=False)
        table.add_row(f"[{TITLE_STYLE}]Message Turn[/{TITLE_STYLE}]", f"{msg.turn}")
        table.add_row(f"[{TITLE_STYLE}]Message Type[/{TITLE_STYLE}]", f"{msg.type}")
        table.add_row(f"[{TITLE_STYLE}]Message Name[/{TITLE_STYLE}]", f"{msg.name}")
        table.add_row(f"[{TITLE_STYLE}]Message Data[/{TITLE_STYLE}]", f"{data_str}")
        print_standard(table)

    def display_config(self):
        """Display current agent, environment, and function"""
        config_table = Table(
            show_header=False, show_lines=False, box=None, pad_edge=False
        )
        config_table.add_row(
            f"[{TITLE_STYLE}]Agent[/{TITLE_STYLE}]",
            f"{self.debugger.config.agent.name}",
        )
        config_table.add_row(
            f"[{TITLE_STYLE}]Agent ID[/{TITLE_STYLE}]",
            f"[{ID_STYLE}]{self.debugger.config.agent.id}[/{ID_STYLE}]",
        )
        config_table.add_row(
            f"[{TITLE_STYLE}]Environment[/{TITLE_STYLE}]",
            f"{self.debugger.config.environment.name}",
        )
        config_table.add_row(
            f"[{TITLE_STYLE}]Environment ID[/{TITLE_STYLE}]",
            f"[{ID_STYLE}]{self.debugger.config.environment.id}[/{ID_STYLE}]",
        )
        config_table.add_row(
            f"[{TITLE_STYLE}]Function[/{TITLE_STYLE}]",
            f"{self.debugger.config.function.name}",
        )
        config_table.add_row(
            f"[{TITLE_STYLE}]Function ID[/{TITLE_STYLE}]",
            f"[{ID_STYLE}]{self.debugger.config.function.id}[/{ID_STYLE}]",
        )
        print_standard(config_table)

    def display_help(self):
        """Display help information"""
        help_text = f"""
[{TITLE_STYLE}]PrimVoices Debugger Commands:[/{TITLE_STYLE}]

[{TITLE_STYLE}]Audio & Messaging:[/{TITLE_STYLE}]
  send <text> - Send text message to agent
  listen      - Start microphone recording (automatically sends audio to agent)
  stop        - Stop microphone recording
  phone       - Connect to phone number (or disconnect if already connected)

[{TITLE_STYLE}]Monitoring:[/{TITLE_STYLE}]
  status      - Show connection status
  messages    - Show recent debug messages
  debug <id>  - Show detailed info for message ID
  clear       - Clear message history
  config      - Show current agent, environment, and function

[{TITLE_STYLE}]Other:[/{TITLE_STYLE}]
  help        - Show this help
  quit/exit   - Exit debugger

[{TITLE_STYLE}]Notes:[/{TITLE_STYLE}]
• Type any text (not a command) to send it as a message
• Use 'listen' to start voice conversation - audio is automatically transmitted
• The debugger auto-connects on startup
• Use Ctrl+C to interrupt, then 'quit' to exit properly
        """

        print_standard(Panel(help_text, title="Help"))

    async def run_interactive(self):
        """Run interactive command-line interface"""
        self.running = True

        print_success("PrimVoices Debugger")
        print_info("Type 'help' for available commands, or 'quit' to exit")

        # Automatically connect to the agent on startup so the user does not have
        # to type the `connect` command manually.
        try:
            with Progress(
                SpinnerColumn(), TextColumn("[progress.description]{task.description}")
            ) as progress:
                task = progress.add_task("Connecting...", total=None)
                await self.debugger.connect()
                progress.update(task, description="Connected!")

            # Send a quick ping to verify the websocket is healthy
            try:
                await self.debugger.websocket.send(json.dumps({"event": "ping"}))
            except Exception as e:
                print_error(
                    f"Failed to send ping: {e}. Please check your connection "
                    f"and restart the debugger."
                )

            # We expect the agent to respond shortly; hold prompt until then.
            self.awaiting_response = True
        except Exception as e:
            print_error(
                f"Auto-connect failed: {e}. Please check your connection "
                f"and restart the debugger."
            )

        while self.running:
            try:
                # Do not prompt the user while we are waiting for the agent to
                # finish its turn (i.e. until a `turn_end` debug message is
                # received).  This prevents a prompt from appearing right
                # before the assistant's response.
                if self.awaiting_response:
                    await asyncio.sleep(0.1)
                    continue

                # Prompt.ask blocks the event loop. Run it in a thread so that
                # background tasks (WebSocket listener, etc.) keep running and
                # messages appear as soon as they arrive.
                command = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: console.input(),
                )

                if not command.strip():
                    continue

                parts = command.split()
                cmd = parts[0].lower()
                args = parts[1:] if len(parts) > 1 else []

                if cmd not in SUPPORTED_COMMANDS:
                    # Not a command, just a text message
                    if not self.debugger.is_connected:
                        print_error("Not connected. Please restart the debugger.")
                    else:
                        # Pause prompt until agent responds to this text
                        self.awaiting_response = True
                        await self.debugger.send_text_event(command)
                    continue

                if cmd == "quit" or cmd == "exit" or cmd == "q" or cmd == "x":
                    # Disconnect gracefully before exiting
                    if self.debugger.is_connected:
                        await self.debugger.disconnect()
                    self.running = False
                    break

                elif cmd == "send":
                    if not self.debugger.is_connected:
                        print_error("Not connected. Please restart the debugger.")
                    else:
                        # Pause prompt until agent responds to this text
                        text = " ".join(args)
                        self.awaiting_response = True
                        await self.debugger.send_text_event(text)
                    continue

                elif cmd == "help":
                    self.display_help()

                elif cmd == "status":
                    self.display_status()

                elif cmd == "listen":
                    if not self.debugger.is_connected:
                        print_error("Not connected. Please restart the debugger.")
                    else:
                        if self.debugger.start_listening():
                            print_success("Started listening")

                elif cmd == "stop":
                    if self.debugger.stop_listening():
                        print_warning("Stopped listening")

                elif cmd == "messages":
                    self.display_messages()

                elif cmd == "clear":
                    self.debugger.debug_messages.clear()
                    print_warning("Message history cleared")

                elif cmd == "config":
                    self.display_config()

                elif cmd == "debug":
                    self.display_debug(args[0])

                elif cmd == "phone":
                    self.debugger.phone()

                else:
                    print_error(f"Unknown command: {cmd}")
                self._print_prompt()

            except KeyboardInterrupt:
                print_warning("Use 'quit' to exit")
            except Exception as e:
                print_error(e)

        # Cleanup
        await self.debugger.disconnect()
        print_success("Goodbye!")


async def run_debugger(agent: dict, environment: dict, function: dict):
    """Main entry point"""

    try:
        # Load configuration
        config = WebSocketConfig(
            agent=agent,
            api_url=API_BASE_URL,
            environment=environment,
            function=function,
        )

        # Create debugger
        debugger = PrimVoicesDebugger(config)

        # Create UI
        ui = DebuggerUI(debugger)

        # Run interactive interface
        await ui.run_interactive()

    except Exception as e:
        print_error(e)
        sys.exit(1)
