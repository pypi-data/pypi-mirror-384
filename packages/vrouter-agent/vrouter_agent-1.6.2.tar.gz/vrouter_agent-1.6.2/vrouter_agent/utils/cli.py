import subprocess
from loguru import logger as log
import os


def run_command_with_sudo(cmd_args, env=None, name=None):
    """
    Execute a command that may need sudo privileges.
    If running as root (uid 0), skip sudo prefix.
    If not running as root, add sudo prefix.
    
    :param cmd_args: List of command arguments
    :param env: Environment variables dict
    :param name: User-friendly command name
    :return: Tuple of (output, return_code)
    """
    # If running as root, don't use sudo
    if os.getuid() == 0:
        return run_command(cmd_args, env=env, name=name)
    else:
        # Prepend sudo to the command
        sudo_cmd = ["sudo"] + cmd_args
        return run_command(sudo_cmd, env=env, name=name)


def run_command(args, env=None, name=None):
    """Run the command defined by args and return its output and return code.

    :param args: List of arguments for the command to be run.
    :param env: Dict defining the environment variables. Pass None to use
        the current environment.
    :param name: User-friendly name for the command being run. A value of
        None will cause args[0] to be used.
    :param logger: Logger object for logging errors. If None, the default logger is used.
    :return: Tuple containing the command's output and return code.
    """

    if name is None:
        name = args[0]

    # Handle sudo commands intelligently
    # If we're running as root and the command starts with sudo, remove sudo
    if len(args) > 0 and args[0] == "sudo" and os.getuid() == 0:
        args = args[1:]  # Remove sudo from the command
        if name == "sudo":
            name = args[0] if args else "command"

    try:
        output = subprocess.check_output(args, stderr=subprocess.STDOUT, env=env)
        return_code = 0
        if isinstance(output, bytes):
            output = output.decode("utf-8")
    except subprocess.CalledProcessError as e:
        output = e.output.decode("utf-8") if isinstance(e.output, bytes) else e.output
        return_code = e.returncode
        message = "%s failed with return code %d: %s" % (name, return_code, output)
        log.error(message)
        raise RuntimeError(message)

    return output, return_code


def create_dir(path: str):
    """
    Create directory if not exists
    """
    if not os.path.exists(path):
        run_command_with_sudo(["mkdir", "-p", path])


def print_run_command(args):
    """debug testing of run_command"""

    print(args)
    print(run_command(args))
