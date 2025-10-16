# import json
# import os
# import typer

# import py4heappe.heappe_v5.cli.configuration as configuration
# import py4heappe.heappe_v5.core.base.utils as utils
# import py4heappe.heappe_v5.core as heappeCore

# from datetime import datetime
# from py4heappe.heappe_v5.core.base import exceptions
# from py4heappe.heappe_v5.core import rest 
# from typing import List, Optional
# from typing_extensions import Annotated


# app = typer.Typer(name="FileTransferCLI", no_args_is_help=True, pretty_exceptions_show_locals=False)

# @app.command(name="Upload")
# def upload(id:int = typer.Option(..., help='Id (HPC job)'),
#                 path:str = typer.Option(..., help='Path to the file or directory')):
#     """List associated user groups"""
#     try:

#         if not os.path.exists(path):
#             raise exceptions.Py4HEAppEException(f"The specified path does not exist: {path}")

#         if os.path.isfile(path):
#             utils.print_and_log(f"The path '{path}' is a file.")
#         elif os.path.isdir(path):
#             utils.print_and_log(f"The path '{path}' is a directory.")
#         else:
#             raise exceptions.Py4HEAppEException(f"The path '{path}' is neither a file nor a directory.")

#         utils.print_and_log("Listing groups where the user is assigned ...") 
#         body = {
#             "_preload_content": False,
#             "body": {
#                 "SubmittedJobInfoId": id,
#                 "SessionCode": utils.load_stored_session()
#             }
#         }

#         response = heappeCore.FileTransferApi(configuration.get_api_instance()).heappe_file_transfer_request_file_transfer_post(**body)  
#         print(f"\nTemporary Key\n{json.dumps(json.loads(response.data), indent = 3)}")



#   "Id": 0,
#   "ServerHostname": "string",
#   "SharedBasepath": "string",
#   "Protocol": 1,
#   "Port": 0,
#   "ProxyConnection": {
#     "Id": 0,
#     "Host": "string",
#     "Port": 0,
#     "Type": 1,
#     "Username": "string",
#     "Password": "string"
#   },
#   "Credentials": {
#     "Username": "string",
#     "Password": "string",
#     "CipherType": 0,
#     "CredentialsAuthType": 0,
#     "PrivateKey": "string",
#     "PrivateKeyCertificate": "string",
#     "PublicKey": "string",
#     "Passphrase": "string"
#   }
# }




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



# if __name__ == '__main__':
#     app()