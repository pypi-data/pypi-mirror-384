# import json
# import typer

# import heappeac_v4.cli.configuration as configuration
# import heappeac_v4.cli.information as infoCLI
# import heappeac_v4.core.base.utils as utils
# import heappeac_v4.core as heappeCore

# from heappeac_v4.core.base import exceptions
# from heappeac_v4.core  import rest 


# app = typer.Typer(name="JobMgmtCLI", no_args_is_help=True, pretty_exceptions_show_locals=False)

# @app.command(name="Create")
# def create_job():
#     """Create HPC job"""
#     try:
#         print("Creating HPC Job ...") 
#         projectId : int = infoCLI.get_hpc_project()["Id"]
#         parameters = {
#             "_preload_content": False,
#             "ProjectId": projectId,
#             "SessionCode": utils.load_stored_session()
#         }


       
#     except rest.ApiException as exception:
#         response_data=json.loads(exception.body)
#         raise exceptions.Py4HEAppEException(response_data['title'], response_data['detail'], response_data['status']) from None
    
#     except Exception as exception:
#         raise exceptions.Py4HEAppEException("Link to a HEAppE instance is not set or valid. Please check Conf Init option.") from None

# @app.command(name="Submit")
# def submit_job(id:int = typer.Option(..., help='Created HPC Job Info Identifier')):
#     """Submit created HPC job"""
#     try:
#         print("Submitting HPC Job ...") 
#         body = {
#             "_preload_content": False,
#             "CreatedJobInfoId": id,
#             "SessionCode": utils.load_stored_session()
#         }

#         _ = heappeCore.JobManagementApi(configuration.get_api_instance()).heappe_job_management_submit_job_put(**body)
#         print("Job submitted successfully")
       
#     except rest.ApiException as exception:
#         response_data=json.loads(exception.body)
#         raise exceptions.Py4HEAppEException(response_data['title'], response_data['detail'], response_data['status']) from None
    
#     except Exception as exception:
#         raise exceptions.Py4HEAppEException("Link to a HEAppE instance is not set or valid. Please check Conf Init option.") from None  

# @app.command(name="Cancel")
# def cancel_job(id:int = typer.Option(..., help='Created HPC Job Info Identifier')):
#     """Cancel Execution of HPC job"""
#     try:
#         print("Cancellation Execution of HPC Job ...") 
#         body = {
#             "_preload_content": False,
#             "CreatedJobInfoId": id,
#             "SessionCode": utils.load_stored_session()
#         }

#         _ = heappeCore.JobManagementApi(configuration.get_api_instance()).heappe_job_management_cancel_job_put(**body)
#         print("Job cancelled successfully")
       
#     except rest.ApiException as exception:
#         response_data=json.loads(exception.body)
#         raise exceptions.Py4HEAppEException(response_data['title'], response_data['detail'], response_data['status']) from None
    
#     except Exception as exception:
#         raise exceptions.Py4HEAppEException("Link to a HEAppE instance is not set or valid. Please check Conf Init option.") from None  


# @app.command(name="Remove")
# def remove_job(id:int = typer.Option(..., help='Created HPC Job Info Identifier')):
#     """Remove HPC job"""
#     try:
#         print("Removing of HPC Job ...") 
#         body = {
#             "_preload_content": False,
#             "CreatedJobInfoId": id,
#             "SessionCode": utils.load_stored_session()
#         }

#         _ = heappeCore.JobManagementApi(configuration.get_api_instance()).heappe_job_management_delete_job_delete(**body)
#         print("Job removed successfully")
       
#     except rest.ApiException as exception:
#         response_data=json.loads(exception.body)
#         raise exceptions.Py4HEAppEException(response_data['title'], response_data['detail'], response_data['status']) from None
    
#     except Exception as exception:
#         raise exceptions.Py4HEAppEException("Link to a HEAppE instance is not set or valid. Please check Conf Init option.") from None  

# @app.command(name="ListJobs")
# def remove_job():
#     """Remove HPC job"""
#     try:
#         print("Removing of HPC Job ...") 
#         parameters = {
#             "_preload_content": False,
#             "SessionCode": utils.load_stored_session()
#         }

#         response= heappeCore.JobManagementApi(configuration.get_api_instance()).heappe_job_management_list_jobs_for_current_user_get(**parameters)
#         print(json.dumps(response.data, indent = 3))
       
#     except rest.ApiException as exception:
#         response_data=json.loads(exception.body)
#         raise exceptions.Py4HEAppEException(response_data['title'], response_data['detail'], response_data['status']) from None
    
#     except Exception as exception:
#         raise exceptions.Py4HEAppEException("Link to a HEAppE instance is not set or valid. Please check Conf Init option.") from None  

# @app.command(name="ListJobs")
# def remove_job(id:int = typer.Option(..., help='Created HPC Job Info Identifier')):
#     """Remove HPC job"""
#     try:
#         print("Removing of HPC Job ...") 
#         parameters = {
#             "_preload_content": False,
#             "CreatedJobInfoId": id,
#             "SessionCode": utils.load_stored_session()
#         }

#         response = heappeCore.JobManagementApi(configuration.get_api_instance()).heappe_job_management_current_info_for_job_get(**parameters)
#         print(json.dumps(response.data, indent = 3))
       
#     except rest.ApiException as exception:
#         response_data=json.loads(exception.body)
#         raise exceptions.Py4HEAppEException(response_data['title'], response_data['detail'], response_data['status']) from None
    
#     except Exception as exception:
#         raise exceptions.Py4HEAppEException("Link to a HEAppE instance is not set or valid. Please check Conf Init option.") from None  


# @app.command(name="CopyDataToTemp")
# def copy_data_to_temp(id:int = typer.Option(..., help='Created HPC Job Info Identifier'),
#                       path:str = typer.Option(..., help='Path containing data to be copied')):
#     """Copy Data to Temporary location"""
#     try:
#         print("Copying HPC Job Data to Temporary location ...") 
#         body = {
#             "_preload_content": False,
#             "CreatedJobInfoId": id,
#             "Path": path,
#             "SessionCode": utils.load_stored_session()
#         }

#         response = heappeCore.JobManagementApi(configuration.get_api_instance()).heappe_job_management_copy_job_data_to_temp_post(**body)
#         print(f"Specific data was successfully copied to temporary location. Hash for usage the data is: {response.data}")
       
#     except rest.ApiException as exception:
#         response_data=json.loads(exception.body)
#         raise exceptions.Py4HEAppEException(response_data['title'], response_data['detail'], response_data['status']) from None
    
#     except Exception as exception:
#         raise exceptions.Py4HEAppEException("Link to a HEAppE instance is not set or valid. Please check Conf Init option.") from None  

# @app.command(name="CopyDataFromTemp")
# def copy_data_from_temp(id:int = typer.Option(..., help='Created HPC Job Info Identifier'),
#                         temporaryHash:str = typer.Option(..., help='Path containing data to be copied')):
#     """Copy Data From Temporary location"""
#     try:
#         print("Copying HPC Job Data from Temporary location to Job Directory...") 
#         body = {
#             "_preload_content": False,
#             "CreatedJobInfoId": id,
#             "TempSessionCode": temporaryHash,
#             "SessionCode": utils.load_stored_session()
#         }

#         response = heappeCore.JobManagementApi(configuration.get_api_instance()).heappe_job_management_copy_job_data_from_temp_post(**body)
#         print(f"{response.data}")
       
#     except rest.ApiException as exception:
#         response_data=json.loads(exception.body)
#         raise exceptions.Py4HEAppEException(response_data['title'], response_data['detail'], response_data['status']) from None
    
#     except Exception as exception:
#         raise exceptions.Py4HEAppEException("Link to a HEAppE instance is not set or valid. Please check Conf Init option.") from None  

# @app.command(name="GetAllocatedNodes")
# def get_allocated_nodes_ip(id:int = typer.Option(..., help='Created HPC Job Info Identifier')):
#     """Get Allocated Nodes IP Addresses for the HPC Job"""
#     try:
#         print("Getting Allocated Nodes IP Addresses for the HPC Job ...") 
#         parameters = {
#             "_preload_content": False,
#             "CreatedJobInfoId": id,
#             "SessionCode": utils.load_stored_session()
#         }

#         response = heappeCore.JobManagementApi(configuration.get_api_instance()).heappe_job_management_allocated_nodes_ips_get(**parameters)
#         print(f"HPC Job {id} uses the following nodes: {response.data}")
       
#     except rest.ApiException as exception:
#         response_data=json.loads(exception.body)
#         raise exceptions.Py4HEAppEException(response_data['title'], response_data['detail'], response_data['status']) from None
    
#     except Exception as exception:
#         raise exceptions.Py4HEAppEException("Link to a HEAppE instance is not set or valid. Please check Conf Init option.") from None  
    

# if __name__ == '__main__':
#     app()