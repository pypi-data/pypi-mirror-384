import os
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


class ContextProvider:
    """Provides system and file system context for AI prompts."""
    
    def __init__(self):
        pass
    
    def get_current_directory(self) -> str:
        """Get the current working directory."""
        return os.getcwd()
    
    def get_directory_contents(self, path: Optional[str] = None, max_items: int = 20) -> List[str]:
        """Get directory contents, limited to avoid overwhelming the AI."""
        target_path = Path(path) if path else Path.cwd()
        
        try:
            contents = []
            for item in target_path.iterdir():
                if len(contents) >= max_items:
                    contents.append(f"... and {len(list(target_path.iterdir())) - max_items} more items")
                    break
                
                if item.is_dir():
                    contents.append(f"{item.name}/")
                else:
                    contents.append(item.name)
            
            return sorted(contents)
        except (PermissionError, FileNotFoundError):
            return ["<unable to read directory>"]
    
    def get_system_info(self) -> Dict[str, str]:
        """Get basic system information."""
        system_info = {
            "os": platform.system(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
        }
        
        # Add shell information
        shell_env = os.environ.get("SHELL", "")
        if shell_env:
            system_info["shell_path"] = shell_env
            system_info["shell_name"] = Path(shell_env).name
        
        return system_info
    
    def get_environment_variables(self, relevant_vars: Optional[List[str]] = None) -> Dict[str, str]:
        """Get relevant environment variables."""
        if relevant_vars is None:
            relevant_vars = ["PATH", "HOME", "USER", "PWD", "SHELL"]
        
        env_vars = {}
        for var in relevant_vars:
            value = os.environ.get(var)
            if value:
                env_vars[var] = value
        
        return env_vars
    
    def build_context(self, include_directory_contents: bool = True) -> Dict:
        """Build comprehensive context dictionary."""
        context = {
            "current_directory": self.get_current_directory(),
            "system_info": self.get_system_info(),
            "environment": self.get_environment_variables(),
        }
        
        if include_directory_contents:
            context["directory_contents"] = self.get_directory_contents()
        
        return context
    
    def format_context_for_prompt(self, context: Optional[Dict] = None) -> str:
        """Format context information for inclusion in AI prompts."""
        if context is None:
            context = self.build_context()
        
        context_lines = [
            "Current Context:",
            f"- Working Directory: {context['current_directory']}",
            f"- OS: {context['system_info'].get('os', 'Unknown')}",
            f"- Shell: {context['system_info'].get('shell_name', 'Unknown')}",
        ]
        
        if "directory_contents" in context and context["directory_contents"]:
            contents_preview = ", ".join(context["directory_contents"][:10])
            if len(context["directory_contents"]) > 10:
                contents_preview += "..."
            context_lines.append(f"- Directory Contents: {contents_preview}")
        
        return "\n".join(context_lines)