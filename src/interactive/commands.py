from typing import Dict, Callable, List, Optional, Any
from dataclasses import dataclass
import shlex
import logging
from enum import Enum
import inspect


class CommandType(Enum):
    SCAN = "scan"
    SYSTEM = "system"
    REPORT = "report"
    CONFIG = "config"


@dataclass
class Command:
    name: str
    callback: Callable
    description: str
    usage: str
    type: CommandType
    aliases: List[str] = None
    requires_auth: bool = False


class CommandHandler:
    def __init__(self):
        self.logger = logging.getLogger("nexus.commands")
        self.commands: Dict[str, Command] = {}
        self.aliases: Dict[str, str] = {}
        self._setup_default_commands()

    def _setup_default_commands(self):
        """Register default system commands"""
        self.register_command(
            name="help",
            callback=self.show_help,
            description="Show available commands",
            usage="help [command]",
            type=CommandType.SYSTEM
        )

        self.register_command(
            name="scan",
            callback=self.start_scan,
            description="Start a new security scan",
            usage="scan <target> [options]",
            type=CommandType.SCAN
        )

        self.register_command(
            name="report",
            callback=self.generate_report,
            description="Generate scan report",
            usage="report <format> <output>",
            type=CommandType.REPORT
        )

    def register_command(self,
                         name: str,
                         callback: Callable,
                         description: str,
                         usage: str,
                         type: CommandType,
                         aliases: List[str] = None,
                         requires_auth: bool = False):
        """Register a new command"""
        command = Command(
            name=name,
            callback=callback,
            description=description,
            usage=usage,
            type=type,
            aliases=aliases or [],
            requires_auth=requires_auth
        )

        self.commands[name] = command

        # Register aliases
        if aliases:
            for alias in aliases:
                self.aliases[alias] = name

    def execute(self, command_line: str) -> Any:
        """Execute a command from command line input"""
        try:
            args = shlex.split(command_line)
            if not args:
                return None

            command_name = args[0].lower()
            command_args = args[1:]

            # Check aliases
            if command_name in self.aliases:
                command_name = self.aliases[command_name]

            if command_name in self.commands:
                command = self.commands[command_name]
                return self._execute_command(command, command_args)
            else:
                self.logger.warning(f"Unknown command: {command_name}")
                return None

        except Exception as e:
            self.logger.error(f"Command execution error: {str(e)}")
            return None

    def _execute_command(self, command: Command, args: List[str]) -> Any:
        """Execute a command with given arguments"""
        try:
            # Check authentication requirement
            if command.requires_auth and not self._check_auth():
                self.logger.warning("Authentication required for this command")
                return None

            # Get command parameters
            sig = inspect.signature(command.callback)
            params = sig.parameters

            # Validate argument count
            if len(args) < len([p for p in params.values() if p.default == inspect.Parameter.empty]):
                self.logger.warning(f"Insufficient arguments. Usage: {command.usage}")
                return None

            return command.callback(*args)

        except Exception as e:
            self.logger.error(f"Error executing command {command.name}: {str(e)}")
            return None

    def show_help(self, command_name: str = None) -> str:
        """Show help information"""
        if command_name:
            if command_name in self.commands:
                cmd = self.commands[command_name]
                return f"""
Command: {cmd.name}
Type: {cmd.type.value}
Description: {cmd.description}
Usage: {cmd.usage}
Aliases: {', '.join(cmd.aliases) if cmd.aliases else 'None'}
Requires Auth: {'Yes' if cmd.requires_auth else 'No'}
"""
            return f"Unknown command: {command_name}"

        # Show all commands grouped by type
        help_text = "Available Commands:\n\n"
        for cmd_type in CommandType:
            type_commands = [cmd for cmd in self.commands.values() if cmd.type == cmd_type]
            if type_commands:
                help_text += f"{cmd_type.value.upper()} COMMANDS:\n"
                for cmd in type_commands:
                    help_text += f"  {cmd.name}: {cmd.description}\n"
                help_text += "\n"
        return help_text

    def start_scan(self, target: str, *options) -> None:
        """Start a security scan"""
        self.logger.info(f"Starting scan on target: {target}")
        # Implementation specific to scan control

    def generate_report(self, format: str, output: str) -> None:
        """Generate scan report"""
        self.logger.info(f"Generating {format} report to {output}")
        # Implementation specific to report generation

    def _check_auth(self) -> bool:
        """Check if user is authenticated"""
        # Implementation specific to authentication system
        return True

    def get_commands_by_type(self, cmd_type: CommandType) -> List[Command]:
        """Get all commands of a specific type"""
        return [cmd for cmd in self.commands.values() if cmd.type == cmd_type]

    def get_command(self, name: str) -> Optional[Command]:
        """Get command by name or alias"""
        if name in self.aliases:
            name = self.aliases[name]
        return self.commands.get(name)
