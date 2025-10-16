import subprocess
from typing import List, Optional, Tuple
from loguru import logger as log

class SecureSubprocessError(Exception):
    """Custom exception for secure subprocess errors."""
    pass

def run_secure_command(
    command: List[str],
    shell: bool = False,
    capture_output: bool = True,
    text: bool = True,
    check: bool = True,
    env: Optional[dict] = None
) -> Tuple[str, str]:
    """
    Run a command securely using subprocess.
    
    Args:
        command: List of command arguments or string if shell=True
        shell: Whether to run command in shell
        capture_output: Whether to capture stdout/stderr
        text: Whether to return text instead of bytes
        check: Whether to raise exception on non-zero return code
        env: Environment variables to use
        
    Returns:
        Tuple of (stdout, stderr)
        
    Raises:
        SecureSubprocessError: If command execution fails
    """
    try:
        result = subprocess.run(
            command,
            shell=shell,
            capture_output=capture_output,
            text=text,
            check=check,
            env=env
        )
        return result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        log.error(f"Command failed with return code {e.returncode}")
        log.error(f"stdout: {e.stdout}")
        log.error(f"stderr: {e.stderr}")
        raise SecureSubprocessError(f"Command failed: {' '.join(command)}") from e
    except Exception as e:
        log.error(f"Unexpected error running command: {e}")
        raise SecureSubprocessError(f"Command failed: {' '.join(command)}") from e

def run_secure_command_output(
    command: List[str],
    shell: bool = False,
    env: Optional[dict] = None
) -> str:
    """
    Run a command and return its output.
    
    Args:
        command: List of command arguments or string if shell=True
        shell: Whether to run command in shell
        env: Environment variables to use
        
    Returns:
        Command output as string
    """
    stdout, _ = run_secure_command(command, shell=shell, env=env)
    return stdout.strip() 