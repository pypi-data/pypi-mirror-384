import re
from typing import List, Tuple, Optional


class CommandSafetyChecker:
    """Checks commands for potentially dangerous operations."""
    
    # Patterns for potentially dangerous commands
    DANGEROUS_PATTERNS = [
        # File system operations
        (r'\brm\s+(-[rf]*\s+)?/', "Recursive file deletion"),
        (r'\brm\s+(-[rf]*\s+)?\*', "Wildcard file deletion"),
        (r'\brmdir\s+', "Directory removal"),
        (r'\bdd\s+', "Low-level disk operations"),
        (r'\bmkfs\s+', "File system formatting"),
        (r'\bformat\s+', "Disk formatting"),
        
        # System operations
        (r'\bsudo\s+rm\s+', "Privileged file deletion"),
        (r'\bsudo\s+dd\s+', "Privileged disk operations"),
        (r'\bsudo\s+mkfs\s+', "Privileged file system formatting"),
        (r'\bsudo\s+fdisk\s+', "Privileged disk partitioning"),
        (r'\bsudo\s+shutdown\s+', "System shutdown"),
        (r'\bsudo\s+reboot\s+', "System reboot"),
        (r'\bsudo\s+halt\s+', "System halt"),
        (r'\bsudo\s+poweroff\s+', "System power off"),
        
        # Network operations
        (r'\bcurl\s+.*\|\s*sh', "Executing downloaded scripts"),
        (r'\bwget\s+.*\|\s*sh', "Executing downloaded scripts"),
        (r'\bchmod\s+\+x\s+.*&&.*', "Making files executable and running"),
        
        # Process operations
        (r'\bkill\s+-9\s+', "Force killing processes"),
        (r'\bkillall\s+', "Killing all processes by name"),
        (r'\bpkill\s+', "Pattern-based process killing"),
        
        # Package management (potentially dangerous)
        (r'\bsudo\s+apt\s+remove\s+', "Package removal"),
        (r'\bsudo\s+yum\s+remove\s+', "Package removal"),
        (r'\bsudo\s+dnf\s+remove\s+', "Package removal"),
        (r'\bbrew\s+uninstall\s+', "Package removal"),
        
        # File permissions
        (r'\bchmod\s+777\s+', "Setting overly permissive file permissions"),
        (r'\bchown\s+.*root\s+', "Changing ownership to root"),
        
        # Redirection that could overwrite important files
        (r'>\s*/etc/', "Writing to system configuration directories"),
        (r'>\s*/boot/', "Writing to boot directory"),
        (r'>\s*/usr/', "Writing to system directories"),
    ]
    
    # Commands that are generally safe
    SAFE_COMMANDS = [
        'ls', 'cd', 'pwd', 'cat', 'less', 'more', 'head', 'tail',
        'grep', 'find', 'which', 'whereis', 'man', 'help',
        'echo', 'printf', 'date', 'whoami', 'id', 'uname',
        'ps', 'top', 'htop', 'df', 'du', 'free', 'uptime',
        'history', 'alias', 'type', 'file', 'stat',
        'git status', 'git log', 'git diff', 'git show',
        'pip list', 'pip show', 'npm list', 'npm info',
    ]
    
    def __init__(self):
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), description)
            for pattern, description in self.DANGEROUS_PATTERNS
        ]
    
    def is_safe_command(self, command: str) -> bool:
        """Check if a command is generally considered safe."""
        command_lower = command.lower().strip()
        
        # Check if it's in the safe commands list
        for safe_cmd in self.SAFE_COMMANDS:
            if command_lower.startswith(safe_cmd.lower()):
                return True
        
        return False
    
    def check_command_safety(self, command: str) -> Tuple[bool, List[str]]:
        """
        Check if a command is potentially dangerous.
        
        Returns:
            Tuple of (is_dangerous, list_of_warnings)
        """
        if self.is_safe_command(command):
            return False, []
        
        warnings = []
        
        for pattern, description in self.compiled_patterns:
            if pattern.search(command):
                warnings.append(description)
        
        return len(warnings) > 0, warnings
    
    def get_safety_message(self, command: str) -> Optional[str]:
        """Get a formatted safety warning message for a command."""
        is_dangerous, warnings = self.check_command_safety(command)
        
        if not is_dangerous:
            return None
        
        warning_text = "⚠️  WARNING: This command may be dangerous!\n"
        warning_text += "Potential risks:\n"
        for warning in warnings:
            warning_text += f"  • {warning}\n"
        warning_text += "\nPlease review the command carefully before executing."
        
        return warning_text