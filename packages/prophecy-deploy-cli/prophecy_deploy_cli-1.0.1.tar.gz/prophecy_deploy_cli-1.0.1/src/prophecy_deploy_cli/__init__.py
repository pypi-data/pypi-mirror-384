from importlib import resources as _resources
from pathlib import Path as _Path

def get_binary_path() -> str:
    """Return filesystem path to the packaged deploy CLI binary."""
    try:
        import prophecy_deploy_cli_executable
        return prophecy_deploy_cli_executable.get_executable_path()
    except ImportError:
        raise ImportError("prophecy-deploy-cli-executable package is required")

def get_binary_dir() -> str:
    """Return filesystem path to the directory containing the deploy CLI binary and dependencies."""
    try:
        import prophecy_deploy_cli_executable
        import prophecy_deploy_cli_config
        import prophecy_deploy_cli_deps
        # Return the executable directory as the main binary directory
        exec_path = prophecy_deploy_cli_executable.get_executable_path()
        return str(Path(exec_path).parent)
    except ImportError:
        raise ImportError("All prophecy-deploy-cli packages are required")

def get_shell_script_path() -> str:
    """Return filesystem path to the deploy-cli.sh shell script."""
    try:
        import prophecy_deploy_cli_config
        return prophecy_deploy_cli_config.get_shell_script_path()
    except ImportError:
        raise ImportError("prophecy-deploy-cli-config package is required")

def get_deps_dir() -> str:
    """Return filesystem path to the dependencies directory."""
    try:
        import prophecy_deploy_cli_deps
        return prophecy_deploy_cli_deps.get_bin_dir()
    except ImportError:
        raise ImportError("prophecy-deploy-cli-deps package is required")

def get_config_dir() -> str:
    """Return filesystem path to the config directory."""
    try:
        import prophecy_deploy_cli_config
        return prophecy_deploy_cli_config.get_config_dir()
    except ImportError:
        raise ImportError("prophecy-deploy-cli-config package is required")
