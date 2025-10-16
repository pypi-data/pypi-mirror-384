"""
Safe command execution with shell support
"""

import subprocess
import shlex
from typing import Optional, Tuple


class CommandRunner:
    """Execute shell commands safely"""
    
    @staticmethod
    def run(
        command: str,
        shell: Optional[str] = None,
        cwd: Optional[str] = None,
        timeout: int = 30
    ) -> Tuple[bool, str, str]:
        """
        Execute a command and return results
        
        Args:
            command: Command to execute
            shell: Shell to use (powershell, bash, cmd) or None for direct
            cwd: Working directory
            timeout: Timeout in seconds
        
        Returns:
            Tuple of (success, stdout, stderr)
        """
        try:
            if shell == "powershell":
                cmd = ["powershell", "-Command", command]
            elif shell == "cmd":
                cmd = ["cmd", "/c", command]
            elif shell == "bash":
                cmd = ["bash", "-c", command]
            else:
                # Direct execution (split command)
                cmd = shlex.split(command)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=timeout
            )
            
            success = result.returncode == 0
            # Ensure stdout and stderr are never None
            stdout = result.stdout if result.stdout is not None else ""
            stderr = result.stderr if result.stderr is not None else ""
            return success, stdout, stderr
            
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return False, "", str(e)
    
    @staticmethod
    def run_async(command: str, **kwargs):
        """Run command in background (non-blocking)"""
        # TODO: Implement async execution with asyncio
        pass

