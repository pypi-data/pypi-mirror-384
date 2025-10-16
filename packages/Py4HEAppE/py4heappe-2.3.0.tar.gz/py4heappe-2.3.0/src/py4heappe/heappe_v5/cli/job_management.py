import json
import typer

import py4heappe.heappe_v5.cli.configuration as configuration
import py4heappe.heappe_v5.core.base.utils as utils
import py4heappe.heappe_v5.cli.information as infoCLI
import py4heappe.heappe_v5.core as heappeCore

from py4heappe.heappe_v5.core.base import exceptions
from py4heappe.heappe_v5.core  import rest 

from typing import List, Optional
from typing_extensions import Annotated

app = typer.Typer(name="HEAppEJobManagementCLI", no_args_is_help=True, pretty_exceptions_short=True)

@app.command(name="Create")
def create_job(name: str = typer.Option(..., help='Name of the HPC job'),
               clusterId: int = typer.Option(..., help='Cluster Id'),
               maxCores: int = typer.Option(..., help='Number of cores for the HPC job allocation'),
               wallTimeLimit: int = typer.Option(..., help='Maximum wall time limit for the HPC job [s]'),
               clusterNodeTypeId: int = typer.Option(..., help='Cluster node type identifier'),
               cmdTemplateParameters: Annotated[Optional[List[str]], typer.Option( help='Command template parameters (key:value)')]= None,
               cmdTemplateId: int = typer.Option(..., help='Command template identifier')):
    """Create HPC job"""
    try:
        utils.print_and_log("Creating new HPC job ...") 
        body = {
            "_preload_content": False,
            "body": {
                "SessionCode": utils.load_stored_session(),
                "JobSpecification": {
                    "Name":  name,
                    "ProjectId": infoCLI.get_hpc_project()["Id"],
                    "ClusterId": clusterId,
                    "FileTransferMethodId": clusterId,
                    "WaitingLimit": 0,
                    "Tasks": [
                        {                        
                            "Name":  name,
                            "MinCores": 1,
                            "MaxCores": maxCores,
                            "WalltimeLimit": wallTimeLimit,
                            "StandardOutputFile": "stdout",
                            "StandardErrorFile": "stderr",
                            "ProgressFile": "stdprog",
                            "LogFile": "stdlog",
                            "ClusterNodeTypeId": clusterNodeTypeId,
                            "CommandTemplateId": cmdTemplateId    
                        }
                    ]
                }
            }
        }

        if cmdTemplateParameters:
            if not all(":" in param and param.split(":", 1)[0] and param.split(":", 1)[1] for param in cmdTemplateParameters):
                raise exceptions.Py4HEAppEInternalException("Each parameter must be in key:value format with non-empty key and value.") from None
            
            param_dict = dict(param.split(":", 1) for param in cmdTemplateParameters)
            param_array = [
                {
                    "CommandParameterIdentifier": key,
                    "ParameterValue": value
                }
                for key, value in param_dict.items()
            ]
            body["body"]["JobSpecification"]["Tasks"][0]["TemplateParameterValues"] = param_array

        response = heappeCore.JobManagementApi(configuration.get_api_instance()).heappe_job_management_create_job_post(**body)
        jobId =  json.loads(response.data)["Id"]
        utils.print_and_log(f"\nHPC job was created (Id: {jobId})")
    
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

@app.command(name="Submit")
def submit_job(id:int = typer.Option(..., help='Id (HPC job)')):
    """Submit HPC job"""
    try:
        utils.print_and_log("Submitting HPC job ...") 
        body = {
            "_preload_content": False,
            "body": {
                "CreatedJobInfoId": id,
                "SessionCode": utils.load_stored_session()
            }
        }

        _ = heappeCore.JobManagementApi(configuration.get_api_instance()).heappe_job_management_submit_job_put(**body)
        utils.print_and_log(f"\nHPC job was submitted successfully.")
       
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

@app.command(name="Cancel")
def cancel_job(id:int = typer.Option(..., help='Id (HPC job)')):
    """Cancel HPC job"""
    try:
        utils.print_and_log("Cancelling HPC job ...") 
        body = {
            "_preload_content": False,
            "body": {
                "SubmittedJobInfoId": id,
                "SessionCode": utils.load_stored_session()
            }
        }

        _ = heappeCore.JobManagementApi(configuration.get_api_instance()).heappe_job_management_cancel_job_put(**body)
        utils.print_and_log(f"\nHPC job was cancelled.")
       
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
    
@app.command(name="Remove")
def remove_job(id:int = typer.Option(..., help='Id (HPC job)')):
    """Remove HPC job"""
    try:
        utils.print_and_log("Removing HPC job ...") 
        body = {
            "_preload_content": False,
            "body": {
                "SubmittedJobInfoId": id,
                "SessionCode": utils.load_stored_session()
            }
        }

        _ = heappeCore.JobManagementApi(configuration.get_api_instance()).heappe_job_management_delete_job_delete(**body)
        utils.print_and_log("\nHPC job was removed successfully")
       
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

@app.command(name="List")
def remove_job(jobStates: Annotated[Optional[List[str]], typer.Option( help='HPC job states')]= None):
    """List HPC jobs"""
    try:
        utils.print_and_log("Listing HPC Job ...") 
        parameters = {
            "_preload_content": False,
            "SessionCode": utils.load_stored_session()
        }

        if jobStates:
            parameters["JobStates"] = ",".join(jobStates)

        response = heappeCore.JobManagementApi(configuration.get_api_instance()).heappe_job_management_list_jobs_for_current_user_get(**parameters)
        print(f"\nHPC jobs:\n{json.dumps(json.loads(response.data), indent = 3)}")
       
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

@app.command(name="Info")
def remove_job(id:int = typer.Option(..., help='Id (HPC job)')):
    """Get Current HPC job"""
    try:
        utils.print_and_log("Getting current HPC job ...") 
        parameters = {
            "_preload_content": False,
            "SubmittedJobInfoId": id,
            "SessionCode": utils.load_stored_session()
        }

        response = heappeCore.JobManagementApi(configuration.get_api_instance()).heappe_job_management_current_info_for_job_get(**parameters)
        print(f"\nHPC job:\n{json.dumps(json.loads(response.data), indent = 3)}")
       
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

@app.command(name="CopyDataToTemp")
def copy_data_to_temp(id:int = typer.Option(..., help='Id (HPC job)'),
                      path:str = typer.Option(..., help='Path containing data to be copied')):
    """Copy data to temp location"""
    try:
        utils.print_and_log("Copying HPC job data to temporary location ...") 
        session_code = utils.load_stored_session()
        body = {
            "_preload_content": False,
            "body": {
                "SubmittedJobInfoId": id,
                "Path": path,
                "SessionCode": session_code
            }
        }

        heappeCore.JobManagementApi(configuration.get_api_instance()).heappe_job_management_copy_job_data_to_temp_post(**body)
        utils.print_and_log(f"\nSpecific data was successfully copied to temporary location.")
        print(f"Temp SessionCode for copying the data is: {session_code}.")
       
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

@app.command(name="CopyDataFromTemp")
def copy_data_from_temp(id:int = typer.Option(..., help='Id (HPC job)'),
                        temporaryHash:str = typer.Option(..., help='Path containing data to be copied')):
    """Copy data from temp location"""
    try:
        utils.print_and_log("Copying HPC job data from temporary location to job directory...")
        body = {
            "_preload_content": False,
            "body": {
                "CreatedJobInfoId": id,
                "TempSessionCode": temporaryHash,
                "SessionCode": utils.load_stored_session()
            }
        }

        response = heappeCore.JobManagementApi(configuration.get_api_instance()).heappe_job_management_copy_job_data_from_temp_post(**body)
        utils.print_and_log(f"\n{response.data}")

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

@app.command(name="GetAllocatedNodes")
def get_allocated_nodes_ip(id:int = typer.Option(..., help='Id (HPC job)')):
    """Get HPC job allocated nodes addresses (IP)"""
    try:
        utils.print_and_log("Getting HPC job allocated nodes addresses (IP) ...") 
        parameters = {
            "_preload_content": False,
            "SubmittedTaskInfoId": id,
            "SessionCode": utils.load_stored_session()
        }

        response = heappeCore.JobManagementApi(configuration.get_api_instance()).heappe_job_management_allocated_nodes_i_ps_get(**parameters)
        utils.print_and_log(f"\nHPC job {id} uses the following nodes: {response.data}")
       
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