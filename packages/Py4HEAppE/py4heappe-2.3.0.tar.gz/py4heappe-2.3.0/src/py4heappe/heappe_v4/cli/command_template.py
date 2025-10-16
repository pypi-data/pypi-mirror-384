import json
import typer

import py4heappe.heappe_v4.cli.configuration as configuration
import py4heappe.heappe_v4.cli.information as infoCLI
import py4heappe.heappe_v4.core.base.utils as utils
import py4heappe.heappe_v4.core as heappeCore

from py4heappe.heappe_v4.core.base import exceptions
from py4heappe.heappe_v4.core  import rest 


app = typer.Typer(name="HEAppECommandTemplateCLI", no_args_is_help=True, pretty_exceptions_short=True)

@app.command(name="List")
def get_command_templates_for_project():
    """List all command templates"""
    try:      
        utils.print_and_log("Fetching command templates of a configured HEAppE project …") 
        projectId : int = infoCLI.get_hpc_project()["Id"]
        parameters = {
            "_preload_content": False,
            "ProjectId": projectId,
            "SessionCode": utils.load_stored_session()
        }

        response = heappeCore.ManagementApi(configuration.get_api_instance()).heappe_management_command_templates_get(**parameters)
        commandTemplates =  json.loads(response.data)
        print(f"\nList of command templates for HEAppE project {projectId}:")
        print(json.dumps(commandTemplates, indent = 3))
        
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

@app.command("Create")
def create_command_template(Name:str = typer.Option(..., help='Name'),
                           desc:str = typer.Option(..., help='Description'),
                           extAllocCommand:str = typer.Option(None, help='Extended allocation command'),
                           execScript:str = typer.Option(..., help='Path to executable file/script'),
                           prepScript:str = typer.Option(None, help='Path to preparation script or specific prerequisites/module loads'),
                           clusterNodeTypeId:int = typer.Option(..., help='Cluster node type identifier')):
    """Create new command template"""
    try:
        utils.print_and_log("Creating new command template …")
        body = {
            "_preload_content": False,
            "body": {
                "Name": Name,
                "Description": desc,
                "ExtendedAllocationCommand": extAllocCommand,
                "PreparationScript": prepScript,
                "ExecutableFile": execScript,
                "ClusterNodeTypeId": clusterNodeTypeId,
                "TemplateParameters": [],
                "ProjectId": infoCLI.get_hpc_project()["Id"],
                "SessionCode": utils.load_stored_session()
            }
        }

        response = heappeCore.ManagementApi(configuration.get_api_instance()).heappe_management_command_template_post(**body)
        commandTemplateId =  json.loads(response.data)["Id"]
        utils.print_and_log(f"\nCommand template was created (Id: {commandTemplateId})")

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

@app.command("Modify")
def modify_command_template(id:int = typer.Option(..., help='Id (Command template)'),
                            Name:str = typer.Option(..., help='Name'),
                            desc:str = typer.Option(..., help='Description'),
                            extAllocCommand:str = typer.Option(None, help='Extended allocation command'),
                            execScript:str = typer.Option(..., help='Path to executable file/script'),
                            prepScript:str = typer.Option(None, help='Path to preparation script or specific prerequisites/module loads'),
                            clusterNodeTypeId:int = typer.Option(None, help='Cluster node type identifier')):
    """Modify existing command template"""
    try:
        utils.print_and_log("Modifying the command template …")
        body = {
            "_preload_content": False,
            "body": {
                "Id": id,
                "Name": Name,
                "Description": desc,
                "ExtendedAllocationCommand": extAllocCommand,
                "PreparationScript": prepScript,
                "ExecutableFile": execScript,
                "ClusterNodeTypeId": clusterNodeTypeId,
                "TemplateParameters": [],
                "SessionCode": utils.load_stored_session()
            }
        }

        _ = heappeCore.ManagementApi(configuration.get_api_instance()).heappe_management_command_template_put(**body)
        utils.print_and_log(f"\nCommand template was modified.")

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

@app.command("Remove")
def remove_command_template(id:int = typer.Option(..., help='Id (Command template)')):
    """Remove existing command template"""
    try:
        utils.print_and_log("Removing the command template …")
        body = {
            "_preload_content": False,
            "body": {
                "CommandTemplateId": id,
                "SessionCode": utils.load_stored_session()
            }
        }
        
        _ = heappeCore.ManagementApi(configuration.get_api_instance()).heappe_management_remove_command_template_delete(**body)
        utils.print_and_log("\nCommand template was removed.")

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

@app.command("CreateFromGeneric")
def create_command_template_from_generic(id:str = typer.Option(..., help='Id (Generic command template)'),
                                         name:str = typer.Option(..., help='Name'),
                                         desc:str = typer.Option(..., help='Description'),
                                         extAllocCommand:str = typer.Option(None, help='Extended allocation command'),
                                         execScript:str = typer.Option(..., help='Path to executable file/script'),
                                         prepScript:str = typer.Option(None, help='Path to preparation script or specific prerequisites/module loads')):
    """Create new static command template from a generic one"""
    try:
        utils.print_and_log("Creating new static command template from a generic one …")
        body = {
            "_preload_content": False,
            "body": {
                "GenericCommandTemplateId": id, 
                "Name": name,
                "Description": desc,
                "ExtendedAllocationCommand": extAllocCommand,
                "PreparationScript": prepScript,
                "ExecutableFile": execScript,
                "ProjectId": infoCLI.get_hpc_project()["Id"],
                "SessionCode": utils.load_stored_session()
            }
        }

        response = heappeCore.ManagementApi(configuration.get_api_instance()).heappe_management_command_template_from_generic_post(**body)
        jsonData =  json.loads(response.data)
        commandTemplateId= jsonData["Id"]
        utils.print_and_log(f"\nCommand template was created (Id: {commandTemplateId}):")
        print(json.dumps(jsonData, indent = 3))

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

@app.command("ModifyFromGeneric")
def modify_command_template_from_generic(id:int = typer.Option(..., help='Id (Command template)'),
                                         name:str = typer.Option(..., help='Name'),
                                         desc:str = typer.Option(..., help='Description'),
                                         extAllocCommand:str = typer.Option(None, help='Extended allocation command'),
                                         execScript:str = typer.Option(..., help='Path to executable file/script'),
                                         prepScript:str = typer.Option(None, help='Path to preparation script or specific prerequisites/module loads')):
    """Modify existing command template created from a generic one"""
    try:
        utils.print_and_log("Modifying the command template …")
        body = {
            "_preload_content": False,
            "body": {
                "CommandTemplateId": id,
                "Name": name,
                "Description": desc,
                "ExtendedAllocationCommand": extAllocCommand,
                "PreparationScript": prepScript,
                "ExecutableFile": execScript,
                "ProjectId": infoCLI.get_hpc_project()["Id"],
                "SessionCode": utils.load_stored_session()
            }
        }

        _ = heappeCore.ManagementApi(configuration.get_api_instance()).heappe_management_command_template_from_generic_put(**body)
        utils.print_and_log(f"\nCommand template was modified.")

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

@app.command("CreateParameter")
def create_command_template_parameter(uniqueName:str = typer.Option(..., help='Identifier (Name)'),
                                     query:str = typer.Option(None, help='Query'),
                                     desc:str = typer.Option(..., help='Description'),
                                     cmdTemplateId:int = typer.Option(..., help='Id (Command template)')):
    "Create new command template parameter"
    try:
        utils.print_and_log("Creating command template parameter …")
        body = {
            "_preload_content": False,
            "body": {
                "Identifier": uniqueName,
                "Query": query if query is not None else "",
                "Description": desc,
                "CommandTemplateId": cmdTemplateId,
                "SessionCode": utils.load_stored_session()
            }
        }

        response = heappeCore.ManagementApi(configuration.get_api_instance()).heappe_management_command_template_parameter_post(**body)
        commandTemplateParameterId =  json.loads(response.data)["Id"]
        utils.print_and_log(f"\nCommand template parameter was created  (Id: {commandTemplateParameterId})")

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

@app.command("ModifyParameter")
def modify_command_template_parameter(id:int = typer.Option(..., help='Id (Command template parameter)'),
                                      uniqueName:str = typer.Option(..., help='Identifier (Name)'),
                                      query:str = typer.Option(None, help='Query'),
                                      desc:str = typer.Option(..., help='Description')):
    "Modify existing command template parameter"
    try:
        utils.print_and_log("Modifying the selected command template parameter …")
        body = {
            "_preload_content": False,
            "body": {
                "Id": id,
                "Identifier": uniqueName,
                "Query": query if query is not None else "",
                "Description": desc,
                "SessionCode": utils.load_stored_session()
            }
        }

        _ = heappeCore.ManagementApi(configuration.get_api_instance()).heappe_management_command_template_parameter_put(**body)
        utils.print_and_log(f"\nCommand template parameter was modified.")

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

@app.command("RemoveParameter")
def remove_command_template_parameter(id:int = typer.Option(..., help='Id (Command template parameter)')):
    "Remove existing command template parameter"
    try:
        utils.print_and_log("Removing the command template parameter …")
        body = {
            "_preload_content": False,
            "body": {
                "Id": id,
                "SessionCode": utils.load_stored_session()
            }
        }

        _ = heappeCore.ManagementApi(configuration.get_api_instance()).heappe_management_command_template_parameter_delete(**body)
        utils.print_and_log("\nCommand template parameter was removed.")

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


if __name__ == '__main__':
    app()