import subprocess
from typing import Optional

__all__ = ['update_package']

def update_package(package_name, logger: Optional[str]=None) -> None:
    # Check if package is up-to-date
    result = subprocess.run(['pip', 'check', package_name], capture_output=True, text=True)
    if 'up-to-date' in result.stdout:
        if logger:
            logger.info(f"{package_name} is already up-to-date.")
        return
    # Install latest version of package
    result = subprocess.run(['pip', 'install', '--upgrade', package_name], capture_output=True, text=True)
    if result.returncode == 0:
        if logger:
            logger.info(f"{package_name} has been updated.")
    else:
        if logger:
            logger.info(f"Error updating {package_name}: {result.stderr}")