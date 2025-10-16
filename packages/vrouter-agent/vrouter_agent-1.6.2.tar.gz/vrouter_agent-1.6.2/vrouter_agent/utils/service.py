from .cli import run_command


def check_service_status(name: str):
    """
    Checking vpp service status
    """
    try:
        run_command(["sudo", "systemctl", "is-active", "--quiet", name])
        return True
    except RuntimeError:
        return False


def restart_service(name: str):
    """
    Restarting vpp service
    """
    cmd = run_command(["sudo", "systemctl", "restart", name])
    return cmd
