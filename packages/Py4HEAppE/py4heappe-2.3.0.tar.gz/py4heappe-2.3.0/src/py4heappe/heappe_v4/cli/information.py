import json
import typer

import py4heappe.heappe_v4.cli.configuration as configuration
import py4heappe.heappe_v4.core.base.utils as utils
import py4heappe.heappe_v4.core as heappeCore

from py4heappe.heappe_v4.core.base import exceptions
from py4heappe.heappe_v4.core  import rest 


app = typer.Typer(name="HEAppEInfoCLI", no_args_is_help=True, pretty_exceptions_short=True)

def get_hpc_project():
    try:
        utils.print_and_log("Fetching computational project …")
        parameters = {
            "_preload_content": False,
            "SessionCode": utils.load_stored_session()
        }    

        response = heappeCore.UserAndLimitationManagementApi(configuration.get_api_instance()).heappe_user_and_limitation_management_projects_for_current_user_get(**parameters)
        project = next((f["Project"] for f in json.loads(response.data)if f["Project"]["AccountingString"] == configuration.get_project_from_configuration()), None)

        if project is None:
            raise exceptions.Py4HEAppEInternalException("The computational project does not exist.") from None

        return project

    except rest.ApiException as exception:
        try:
            response_data = json.loads(exception.body)
            raise exceptions.Py4HEAppEAPIInternalException(response_data['title'], response_data['detail'], response_data['status']) from None
        except json.JSONDecodeError:
            raise exceptions.Py4HEAppEInternalException("Link to a HEAppE instance is not set or valid. Please check Conf Init option.") from None
    
    except exceptions.Py4HEAppEInternalException as exception:
         raise exceptions.Py4HEAppEInternalException(exception.message) from None 
           
    except Exception as exception:
        raise exceptions.Py4HEAppEInternalException(f"Other exception: {str(exception)}") from None
    
@app.command(name="Version")
def get_api_version():
    """Version information"""
    try:
        utils.print_and_log("Fetching HEAppE API version information …")
        parameters = {
            "_preload_content": False,
            "SessionCode": utils.load_stored_session()
        }    

        response= heappeCore.ManagementApi(configuration.get_api_instance()).heappe_management_version_information_get(**parameters)
        version: str = json.loads(response.data)["Version"]
        utils.print_and_log(f"\nVersion of API: {version}")

    except rest.ApiException as exception:
        try:
            response_data = json.loads(exception.body)
            raise exceptions.Py4HEAppEAPIException(response_data['title'], response_data['detail'], response_data['status']) from None
        except json.JSONDecodeError:
            raise exceptions.Py4HEAppEException("Link to a HEAppE instance is not set or valid. Please check Conf Init option.") from None

    except exceptions.Py4HEAppEInternalException as exception:
         raise exceptions.Py4HEAppEException(exception.message) from None 
    
    except Exception as exception:
        raise exceptions.Py4HEAppEInternalException(f"Other exception: {str(exception)}") from None

@app.command(name="ClusterInfo")
def get_cluster_information():
    """Cluster information"""
    try:
        utils.print_and_log("Fetching cluster information …")
        parameters = {
            "_preload_content": False
        }    

        response= heappeCore.ClusterInformationApi(configuration.get_api_instance()).heappe_cluster_information_list_available_clusters_get(**parameters)
        print(f"\nCluster information:\n{json.dumps(json.loads(response.data), indent = 3)}")

    except rest.ApiException as exception:
        try:
            response_data = json.loads(exception.body)
            raise exceptions.Py4HEAppEAPIException(response_data['title'], response_data['detail'], response_data['status']) from None
        except json.JSONDecodeError:
            raise exceptions.Py4HEAppEException("Link to a HEAppE instance is not set or valid. Please check Conf Init option.") from None

    except exceptions.Py4HEAppEInternalException as exception:
         raise exceptions.Py4HEAppEException(exception.message) from None 
    
    except Exception as exception:
        raise exceptions.Py4HEAppEInternalException(f"Other exception: {str(exception)}") from None

@app.command("ListParamsFromGeneric")
def get_parameters_from_generic_cmd_template_script(id:int = typer.Option(..., help='Id (Command template)'),
                                                    userScriptPath:str = typer.Option(None, help='Path to executable file/script')):
    """List command template parameters from generic command template"""
    try:
        utils.print_and_log("Fetching command template parameters from generic command template …")
        body = {
            "_preload_content": False,
            "body": {
                "UserScriptPath": userScriptPath,
                "CommandTemplateId": id,
                "ProjectId": get_hpc_project()["Id"],
                "SessionCode": utils.load_stored_session()
            }
        }

        response = heappeCore.ClusterInformationApi(configuration.get_api_instance()).heappe_cluster_information_request_command_template_parameters_name_post(**body)
        print(f"\nCommand template parameters:\n{json.dumps(json.loads(response.data), indent = 3)}")

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
    
@app.command(name="ClusterNodeUsage")
def get_cluster_node_usage(clusterNodeId :int = typer.Option(default=...,  help='Id (Cluster node type)')):
    """Cluster node usage information"""
    try:
        utils.print_and_log("Fetching cluster information …")
        parameters = {
            "_preload_content": False,
            "ClusterNodeId": clusterNodeId,
            "ProjectId": get_hpc_project()["Id"],
            "SessionCode": utils.load_stored_session(),
        }    
    
        response= heappeCore.ClusterInformationApi(configuration.get_api_instance()).heappe_cluster_information_current_cluster_node_usage_get(**parameters)
        print(f"\nCluster node type usage:\n{json.dumps(json.loads(response.data), indent = 3)}")

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