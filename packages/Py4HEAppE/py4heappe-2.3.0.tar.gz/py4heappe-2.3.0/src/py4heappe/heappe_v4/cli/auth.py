import json
import typer
import os

import py4heappe.heappe_v4.cli.configuration as configuration
import py4heappe.heappe_v4.core.base.utils as utils
import py4heappe.heappe_v4.core as heappeCore

from py4heappe.heappe_v4.core.base import exceptions
from py4heappe.heappe_v4.core  import rest 
# from py4lexis.session import LexisSession


app = typer.Typer(name="HEAppEAuthCLI", no_args_is_help=True, pretty_exceptions_short=True)

@app.command(name="UserPass")
def authentication_credentials():
    """Username and password authentication"""
    try:
        utils.print_and_log("Username and password authentication")
        client = configuration.get_api_instance()
        if "CREDENTIALS_USERNAME" in os.environ:
            username = os.environ["CREDENTIALS_USERNAME"]
        else:
            username = typer.prompt("Username:")

        if "CREDENTIALS_PASSWORD" in os.environ:
            password = os.environ["CREDENTIALS_PASSWORD"]
        else:
            password = typer.prompt("Password:", hide_input=True)

        cred = {
            "_preload_content": False,
            "body": {
                "Credentials": {
                    "Username": username,
                    "Password": password
                }
            }
        }

        response = heappeCore.UserAndLimitationManagementApi(client).heappe_user_and_limitation_management_authenticate_user_password_post(**cred)
        session_code = json.loads(response.data)

        if "CREDENTIALS_PASSWORD" in os.environ:
            print(session_code)

        utils.print_and_log("User was authenticated.")
        utils.store_session(session_code)

    except rest.ApiException as exception:
        try:
            response_data = json.loads(exception.body)
            raise exceptions.Py4HEAppEAPIException(response_data['title'], response_data['detail'], response_data['status']) from None
        except json.JSONDecodeError:
            raise exceptions.Py4HEAppEException("Link to a HEAppE instance is not set or valid. Please check Conf Init option.") from None

    except exceptions.Py4HEAppEAPIInternalException as exception:
         raise exceptions.Py4HEAppEException(exception.message) from None

    except exceptions.Py4HEAppEInternalException as exception:
         raise exceptions.Py4HEAppEException(exception.message) from None 
    
    except Exception as exception:
        raise exceptions.Py4HEAppEInternalException(f"Other exception: {str(exception)}") from None

@app.command(name="OpenId")
def authentication_openid():
    """OpenID authentication"""
    try:
        utils.print_and_log("OpenID authentication")
        client = configuration.get_api_instance()
        if "CREDENTIALS_TOKEN" in os.environ:
            openIdToken = os.environ["CREDENTIALS_TOKEN"]
        else:
            openIdToken = typer.prompt("OpenID token:")

        cred = {
            "_preload_content": False,
            "body": {
                "Credentials": {
                    "Username": None,
                    "OpenIdAccessToken": openIdToken
                }
            }
        }

        response = heappeCore.UserAndLimitationManagementApi(client).heappe_user_and_limitation_management_authenticate_user_open_id_post(**cred)
        session_code = json.loads(response.data)

        if "CREDENTIALS_TOKEN" in os.environ:
            print(session_code)
        
        utils.print_and_log("User was authenticated.")
        utils.store_session(session_code)

    except rest.ApiException as exception:
        try:
            response_data = json.loads(exception.body)
            raise exceptions.Py4HEAppEAPIException(response_data['title'], response_data['detail'], response_data['status']) from None
        except json.JSONDecodeError:
            raise exceptions.Py4HEAppEException("Link to a HEAppE instance is not set or valid. Please check Conf Init option.") from None

    except exceptions.Py4HEAppEAPIInternalException as exception:
         raise exceptions.Py4HEAppEException(exception.message) from None

    except exceptions.Py4HEAppEInternalException as exception:
         raise exceptions.Py4HEAppEException(exception.message) from None 
    
    except Exception as exception:
        raise exceptions.Py4HEAppEInternalException(f"Other exception: {str(exception)}") from None

# @app.command(name="Lexis")
# def authentication_lexis(useCredentials:bool = typer.Option(default=False, help='Use Credentials for authentication to LEXIS')):
#     """LEXIS token authentication"""
#     try:
#         utils.print_and_log("LEXIS AAI authentication")
#         client = configuration.get_api_instance()
#         session = LexisSession(login_method='credentials' if useCredentials else 'url')
#         cred = {
#             "_preload_content": False,
#             "body": {
#                 "Credentials": {
#                     "Username": None,
#                     "OpenIdAccessToken": session.get_access_token()
#                 }
#             }
#         }

#         response = heappeCore.UserAndLimitationManagementApi(client).heappe_user_and_limitation_management_authenticate_lexis_token_post(**cred)
#         session_code = json.loads(response.data)
#         utils.print_and_log("User was authenticated.")
#         utils.store_session(session_code)  

#     except rest.ApiException as exception:
#         try:
#             response_data = json.loads(exception.body)
#             raise exceptions.Py4HEAppEAPIException(response_data['title'], response_data['detail'], response_data['status']) from None
#         except json.JSONDecodeError:
#             raise exceptions.Py4HEAppEException("Link to a HEAppE instance is not set or valid. Please check Conf Init option.") from None

#     except exceptions.Py4HEAppEAPIInternalException as exception:
#          raise exceptions.Py4HEAppEException(exception.message) from None

#     except exceptions.Py4HEAppEInternalException as exception:
#          raise exceptions.Py4HEAppEException(exception.message) from None 
    
#     except Exception as exception:
#         raise exceptions.Py4HEAppEInternalException(f"Other exception: {str(exception)}") from None


if __name__ == '__main__':
    app()