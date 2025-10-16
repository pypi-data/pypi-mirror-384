import json
import typer

import py4heappe.heappe_v5.cli.configuration as configuration
import py4heappe.heappe_v5.core.base.utils as utils
import py4heappe.heappe_v5.core as heappeCore

from datetime import datetime
from py4heappe.heappe_v5.core.base import exceptions
from py4heappe.heappe_v5.core import rest 
from typing import List, Optional
from typing_extensions import Annotated


app = typer.Typer(name="ReportCLI", no_args_is_help=True, pretty_exceptions_show_locals=False)

@app.command(name="GroupList")
def list_groups():
    """List associated user groups"""
    try:
        utils.print_and_log("Listing groups where the user is assigned ...") 
        parameters = {
            "_preload_content": False,
            "SessionCode": utils.load_stored_session()
        }

        response = heappeCore.JobReportingApi(configuration.get_api_instance()).heappe_job_reporting_list_adaptor_user_groups_get(**parameters)
        print(f"\nAssociated user groups:\n{json.dumps(json.loads(response.data), indent = 3)}")

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

@app.command(name="UserUsage")
def get_user_report(userId:int = typer.Option(..., help='Id (User)'),
                    startDate:str = typer.Option(None, help='Start Date with time (Format: YYYY-MM-DDTHH:mm:ss)'),
                    endDate:str = typer.Option(None, help='End Date with time (Format:YYYY-MM-DDTHH:mm:ss)'),
                    subProjects: Annotated[Optional[List[str]], typer.Option(help='Sub projects')]= None):
    """Resource usage report for user"""
    try:
        utils.print_and_log("Fetching usage report for user ...") 
        parameters = {
            "_preload_content": False,
            "UserId": userId,
            "StartTime": startDate if startDate is not None else "2000-01-01T00:00:00Z",
            "EndTime": endDate if endDate is not None else datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "SessionCode": utils.load_stored_session()
        }

        if subProjects:
            parameters["SubProjects"] = subProjects
        
        response = heappeCore.JobReportingApi(configuration.get_api_instance()).heappe_job_reporting_user_resource_usage_report_get(**parameters)
        print(f"\nUser usage report:\n{json.dumps(json.loads(response.data), indent = 3)}")
       
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

@app.command(name="GroupUsage")
def get_group_report(groupId:int = typer.Option(..., help='Id (User group)'),
                     startDate:str = typer.Option(None, help='Start Date with time (Format: YYYY-MM-DDTHH:mm:ss)'),
                     endDate:str = typer.Option(None, help='End Date with time (Format:YYYY-MM-DDTHH:mm:ss)'),
                     subProjects: Annotated[Optional[List[str]], typer.Option(help='Sub projects')]= None):
    """Resource usage report for user group"""
    try:
        utils.print_and_log("Fetching usage report for user group ...") 
        parameters = {
            "_preload_content": False,
            "GroupId": groupId,
            "StartTime": startDate if startDate is not None else "2000-01-01T00:00:00Z",
            "EndTime": endDate if endDate is not None else datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "SessionCode": utils.load_stored_session()
        }
       
        if subProjects:
            parameters["SubProjects"] = subProjects

        response = heappeCore.JobReportingApi(configuration.get_api_instance()).heappe_job_reporting_user_group_resource_usage_report_get(**parameters)
        print(f"\nUser group usage report:\n{json.dumps(json.loads(response.data), indent = 3)}")
       
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

@app.command(name="GroupsUsageDetailed")
def get_detailed_jobs_report(subProjects: Annotated[Optional[List[str]], typer.Option(help='Sub projects')]= None):
    """Detailed resource usage report for user groups"""
    try:
        utils.print_and_log("Fetching detailed usage report for user groups ...") 
        parameters = {
            "_preload_content": False,
            "SessionCode": utils.load_stored_session()
        }
        
        if subProjects:
            parameters["SubProjects"] = subProjects

        response = heappeCore.JobReportingApi(configuration.get_api_instance()).heappe_job_reporting_jobs_detailed_report_get(**parameters)
        print(f"\nDetailed user groups usage report:\n{json.dumps(json.loads(response.data), indent = 3)}")

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

@app.command(name="JobUsage")
def get_detailed_job_report(id:int = typer.Option(..., help='Id (Job)')):
    """Resource usage report for job"""
    try:
        utils.print_and_log("Fetching job usage report ...") 
        parameters = {
            "_preload_content": False,
            "JobId": id,
            "SessionCode": utils.load_stored_session()
        }

        response = heappeCore.JobReportingApi(configuration.get_api_instance()).heappe_job_reporting_resource_usage_report_for_job_get(**parameters)
        print(f"\nJob usage report: \n{json.dumps(json.loads(response.data), indent = 3)}")

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