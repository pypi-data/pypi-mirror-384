import signal
import sys
from typing import List, Dict, Optional, Tuple
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text

from backend import BaseGenie
from context import ContextProvider
from command_executor import CommandExecutor


class SessionManager:
    """Manages interactive chat sessions with conversation history."""
    
    def __init__(self, genie: BaseGenie, context_provider: ContextProvider):
        self.genie = genie
        self.context_provider = context_provider
        self.console = Console()
        self.executor = CommandExecutor()
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history_length = 10  # Keep last 10 exchanges
        self.running = True
        
        # Set up signal handler for graceful exit
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        self.console.print("\n[yellow]Chat session interrupted. Goodbye![/yellow]")
        self.running = False
        sys.exit(0)
    
    def add_to_history(self, role: str, content: str):
        """Add a message to conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content
        })
        
        # Trim history if it gets too long
        if len(self.conversation_history) > self.max_history_length * 2:  # *2 for user+assistant pairs
            self.conversation_history = self.conversation_history[-self.max_history_length * 2:]
    
    def get_context(self) -> Dict:
        """Get current system context."""
        return self.context_provider.build_context()
    
    def format_history_for_prompt(self) -> str:
        """Format conversation history for inclusion in AI prompts."""
        if not self.conversation_history:
            return ""
        
        history_lines = ["Recent conversation:"]
        for msg in self.conversation_history[-6:]:  # Last 3 exchanges
            role_label = "You" if msg["role"] == "user" else "Assistant"
            history_lines.append(f"{role_label}: {msg['content']}")
        
        return "\n".join(history_lines) + "\n\n"
    
    def should_execute_command(self, command: str) -> bool:
        """Check if a response looks like a command that should be executed."""
        # Simple heuristic: if it starts with common command patterns
        command_starters = ['cd ', 'ls', 'mkdir', 'rm', 'cp', 'mv', 'grep', 'find', 'cat', 'echo', 'git ', 'npm ', 'pip ', 'python', 'node']
        return any(command.strip().startswith(starter) for starter in command_starters)
    
    def process_input(self, user_input: str) -> bool:
        """
        Process user input and generate AI response.
        
        Returns:
            True to continue session, False to exit
        """
        # Check for exit commands
        if user_input.lower().strip() in ['exit', 'quit', 'bye', 'goodbye']:
            return False
        
        # Add user input to history
        self.add_to_history("user", user_input)
        
        try:
            # Get current context
            context = self.get_context()
            
            # For chat mode, we'll modify the prompt to include conversation history
            # We'll pass the history through the context for now
            context["conversation_history"] = self.conversation_history
            
            # Get AI response
            command, description = self.genie.ask(user_input, explain=True, context=context)
            
            # Add AI response to history
            self.add_to_history("assistant", f"Command: {command}" + (f"\nDescription: {description}" if description else ""))
            
            # Display the response
            if self.should_execute_command(command):
                # This looks like a command - use the command executor
                self.executor.display_command(command, description)
                
                # Ask if user wants to execute
                if self.executor.prompt_for_execution():
                    if self.executor.check_command_safety(command):
                        self.console.print("[blue]Executing command...[/blue]")
                        return_code, stdout, stderr = self.executor.execute_command(command)
                        self.executor.display_execution_result(return_code, stdout, stderr)
                    else:
                        self.console.print("[yellow]Command execution cancelled due to safety concerns.[/yellow]")
                else:
                    self.console.print("[yellow]Command execution cancelled by user.[/yellow]")
            else:
                # This looks like a general response - display as text
                response_text = command
                if description:
                    response_text += f"\n\n{description}"
                
                self.console.print(Panel(
                    response_text,
                    title="[bold green]Assistant[/bold green]",
                    border_style="green",
                    padding=(0, 1)
                ))
            
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
        
        return True
    
    def display_welcome(self):
        """Display welcome message for chat mode."""
        welcome_text = Text()
        welcome_text.append("Welcome to Star Shell Chat Mode!\n\n", style="bold blue")
        welcome_text.append("You can ask questions, request commands, or have a conversation.\n")
        welcome_text.append("Type 'exit', 'quit', or press Ctrl+C to end the session.\n")
        welcome_text.append("Commands will be offered for execution when appropriate.")
        
        self.console.print(Panel(
            welcome_text,
            title="[bold blue]Star Shell Chat[/bold blue]",
            border_style="blue",
            padding=(1, 2)
        ))
    
    def start_conversation(self):
        """Start the interactive chat session."""
        self.display_welcome()
        
        while self.running:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold blue]You[/bold blue]", console=self.console)
                
                if not user_input.strip():
                    continue
                
                # Process the input
                should_continue = self.process_input(user_input)
                
                if not should_continue:
                    break
                    
            except KeyboardInterrupt:
                # Handle Ctrl+C
                self.console.print("\n[yellow]Chat session ended. Goodbye![/yellow]")
                break
            except EOFError:
                # Handle Ctrl+D
                self.console.print("\n[yellow]Chat session ended. Goodbye![/yellow]")
                break
        
        self.console.print("[green]Thanks for using Star Shell![/green]")