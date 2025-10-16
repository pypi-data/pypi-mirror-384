import dotenv
import os
import typer
import validators

import py4heappe.heappe_v5.core as hp
import py4heappe.heappe_v5.core.base.utils as utils
from py4heappe.heappe_v5.core.base import exceptions
from urllib.parse import urlparse

app = typer.Typer(name="HEAppEConfigurationCLI", no_args_is_help=True, pretty_exceptions_show_locals=False)

def get_api_instance():
    dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
    url : str = os.environ.get("url")

    if url is None:
        raise exceptions.Py4HEAppEInternalException("Py4HEappE is not configured. Please check Conf option.") from None
    
    configuration = hp.Configuration()
    configuration.host = url
    api_instance = hp.ApiClient(configuration)
    return api_instance

def get_project_from_configuration():
    dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

    computationalProject : str = os.environ.get("project")
    if computationalProject is None:
        raise exceptions.Py4HEAppEInternalException("Py4HEappE is not configured. Please check Conf option.") from None

    return computationalProject

@app.command(name="Init")
def environment_preparation():
    """Initialization"""
    utils.print_and_log("Preparation of Py4HEAppE Environment ...")
    dotenv.load_dotenv()

    url: str = os.environ.get("url")
    computationalProject: str = os.environ.get("project")

    if url is not None or computationalProject is not None:
        reconfigure = typer.confirm(f"Py4HEAppE is already configured (URL: \"{url}\", HEAppE accounting string (HPC Computational project): \"{computationalProject}\").\nDo you want to reconfigure it?")
        if not reconfigure:
            return

    url = typer.prompt("Enter the HEAppE instance address (for example: https://heappe.domain.cz/production)")

    normalized = url
    parsed = urlparse(normalized)
    if not parsed.scheme:
        normalized = "http://" + normalized
        parsed = urlparse(normalized)

    host = parsed.hostname

    if not validators.url(normalized) and host not in ("localhost", "127.0.0.1"):
        raise exceptions.Py4HEAppEInternalException("The provided HEAppE URL is not valid.") from None

    if "/swagger/index.html" in normalized:
        normalized = normalized.replace("/swagger/index.html", "")

    computationalProject = typer.prompt("Enter HEAppE accounting string", confirmation_prompt=True)

    dotenv.set_key(os.path.join(os.path.dirname(__file__), '.env'), "url", normalized)
    dotenv.set_key(os.path.join(os.path.dirname(__file__), '.env'), "project", computationalProject)

    utils.print_and_log("Py4HEAppE is configured.")
    return


if __name__ == '__main__':
    app()