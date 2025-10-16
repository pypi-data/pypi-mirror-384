import os
import platform
import subprocess

from py4heappe.heappe_v4.core.base import exceptions
from py4heappe.heappe_v4.core.base.logger import logger

def print_and_log(message: str):
    print(message)
    logger.info(message)

def get_user_shell_for_platform():
    current_platform=platform.system()
    if current_platform == "Linux" or current_platform == "Darwin":
        # Use bash for Linux and macOS (Darwin is the name for macOS)
        return "bash"
    elif current_platform == "Windows":
        return "powershell"
    else:
        raise exceptions.Py4HEAppEInternalException(f"Unsupported platform: {current_platform}") from None

def store_session(sessionCode: str):
    try:
        if sessionCode is None:
            raise exceptions.Py4HEAppEInternalException("Problem occurs with authentication to HEAppE instance.") from None
    
        environment_snapshot: dict = os.environ
        environment_snapshot.update({"sessionCode": sessionCode}) 
        subprocess.call(get_user_shell_for_platform(), env=environment_snapshot)

    except exceptions.Py4HEAppEInternalException as exception:
         raise exceptions.Py4HEAppEInternalException(exception.message) from None

    except Exception:
        raise exceptions.Py4HEAppEInternalException("Problem occurs during storing HEAppE sessionCode into variable.") from None
    
def load_stored_session():
    sessionCode: str = os.environ.get("sessionCode")

    if sessionCode is None:
        raise exceptions.Py4HEAppEInternalException("Session for HEAppE instance does not exist! You have to authenticate to HEAppE instance.") from None
    
    return sessionCode