import subprocess
import sys
from typing import Tuple, Optional
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Confirm
from star_shell.command_safety import CommandSafetyChecker


class CommandExecutor:
    """Handles command execution with enhanced formatting and safety checks."""
    
    def __init__(self):
        self.console = Console()
        self.safety_checker = CommandSafetyChecker()
    
    def display_command(self, command: str, description: Optional[str] = None):
        """Display the command with enhanced formatting."""
        # Create syntax-highlighted command display
        command_syntax = Syntax(command, "bash", theme="monokai", line_numbers=False)
        
        # Display command in a panel
        self.console.print(Panel(
            command_syntax,
            title="[bold blue]Generated Command[/bold blue]",
            border_style="blue",
            padding=(0, 1)
        ))
        
        # Display description if available
        if description:
            self.console.print(Panel(
                description,
                title="[bold green]Description[/bold green]",
                border_style="green",
                padding=(0, 1)
            ))
    
    def check_command_safety(self, command: str) -> bool:
        """
        Check command safety and display warnings.
        
        Returns:
            True if user confirms execution, False otherwise
        """
        safety_message = self.safety_checker.get_safety_message(command)
        
        if safety_message:
            # Display warning in a red panel
            self.console.print(Panel(
                safety_message,
                title="[bold red]Security Warning[/bold red]",
                border_style="red",
                padding=(0, 1)
            ))
            
            # Ask for explicit confirmation
            return Confirm.ask(
                "[bold red]Do you still want to execute this potentially dangerous command?[/bold red]",
                default=False
            )
        
        return True
    
    def execute_command(self, command: str) -> Tuple[int, str, str]:
        """
        Execute a command and capture output.
        
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        try:
            # Execute the command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            return result.returncode, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out after 30 seconds"
        except Exception as e:
            return -1, "", f"Error executing command: {str(e)}"
    
    def display_execution_result(self, return_code: int, stdout: str, stderr: str):
        """Display the execution results with proper formatting."""
        if return_code == 0:
            # Successful execution
            if stdout.strip():
                self.console.print(Panel(
                    stdout.strip(),
                    title="[bold green]Command Output[/bold green]",
                    border_style="green",
                    padding=(0, 1)
                ))
            else:
                self.console.print("[green]✓ Command executed successfully (no output)[/green]")
        else:
            # Failed execution
            error_message = stderr.strip() if stderr.strip() else f"Command failed with exit code {return_code}"
            
            self.console.print(Panel(
                error_message,
                title="[bold red]Command Failed[/bold red]",
                border_style="red",
                padding=(0, 1)
            ))
            
            if stdout.strip():
                self.console.print(Panel(
                    stdout.strip(),
                    title="[bold yellow]Partial Output[/bold yellow]",
                    border_style="yellow",
                    padding=(0, 1)
                ))
    
    def prompt_for_execution(self) -> bool:
        """Prompt user whether to execute the command."""
        return Confirm.ask("[bold blue]Do you want to execute this command?[/bold blue]")
    
    def handle_command_execution(self, command: str, description: Optional[str] = None) -> bool:
        """
        Complete command execution flow with safety checks and formatting.
        
        Returns:
            True if command was executed successfully, False otherwise
        """
        # Display the command
        self.display_command(command, description)
        
        # Check if user wants to execute
        if not self.prompt_for_execution():
            self.console.print("[yellow]Command execution cancelled by user.[/yellow]")
            return False
        
        # Safety check
        if not self.check_command_safety(command):
            self.console.print("[yellow]Command execution cancelled due to safety concerns.[/yellow]")
            return False
        
        # Execute the command
        self.console.print("[blue]Executing command...[/blue]")
        return_code, stdout, stderr = self.execute_command(command)
        
        # Display results
        self.display_execution_result(return_code, stdout, stderr)
        
        return return_code == 0