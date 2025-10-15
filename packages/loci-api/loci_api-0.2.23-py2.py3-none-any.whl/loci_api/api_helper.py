# pylint:disable=line-too-long,broad-exception-caught
"""
API Helper for LOCI
"""
import os
import sys
import json
import time

import requests

from enum import Enum
from typing import Optional
from dataclasses import dataclass, asdict

if 'LOCI_BACKEND_URL' not in os.environ:
    print("ERROR: LOCI_BACKEND_URL not set.")
    sys.exit(-1)

if 'LOCI_API_KEY' not in os.environ:
    print("ERROR: LOCI_API_KEY not set.")
    sys.exit(-1)

DEBUG = os.environ.get('LOCI_API_DEBUG', 'false').lower() == 'true'
BACKEND_HOST_URL = os.environ['LOCI_BACKEND_URL'].rstrip('/')
X_API_KEY = os.environ['LOCI_API_KEY']
REQUEST_TIMEOUT = 10

class FilterType(str, Enum):
    NEW = "New"
    MODIFIED = "Modified"
    NEW_N_MODIFIED = "New||Modified"


@dataclass
class SCMMetadata:
    owner: str
    repo: str
    head_sha: str
    pr_number: str


def _extract_server_message(resp: requests.Response) -> Optional[str]:
    if resp is None:
        return None
    try:
        ct = resp.headers.get("content-type", "")
        if "application/json" in ct:
            data = resp.json()
        else:
            # try anyway if content-type is not set
            data = json.loads(resp.text)
        for key in ("message", "error", "detail", "errors"):
            if key in data:
                val = data[key]
                result = val if isinstance(val, str) else json.dumps(val)
                return f"{result.rstrip('.')}."
    except Exception:
        pass
    try:
        text = (resp.text or "").strip()
        return f"{text.rstrip('.')}." if text else None
    except Exception:
        return None


def handle_request_exception(ex: requests.exceptions.RequestException, *, action: str = "request"):
    """
    Handle and log a Requests-related exception in a human-friendly way.
    Behavior:
      - Detects the type of request error (Timeout, ConnectionError, HTTPError, etc.)
      - Attempts to extract a meaningful message from the backend response, if available.
      - Prints a single-line formatted error message to stderr.

    Args:
        ex (requests.exceptions.RequestException): The exception instance to handle.
        action (str): A short description of the action being performed when the error occurred (e.g., "uploading binary").
    """

    kind = None
    server_msg = None
    if isinstance(ex, requests.exceptions.Timeout):
        kind = "Timeout"
        server_msg = "The server took too long to respond."
    elif isinstance(ex, requests.exceptions.ConnectionError):
        kind = "ConnectionError"
        server_msg = "Failed to establish a server connection."
    elif isinstance(ex, requests.exceptions.TooManyRedirects):
        kind = "Too many redirects"
        server_msg = "The request exceeded the configured number of maximum redirects."
    elif isinstance(ex, requests.exceptions.HTTPError):
        kind = None
    else:
        kind = ex.__class__.__name__

    resp = getattr(ex, "response", None)
    server_msg = _extract_server_message(resp) if not server_msg else server_msg

    msg = f"Error {action}: {server_msg if server_msg else ''} {'(' + kind + ')' if kind else ''}"
    print(msg, file=sys.stderr)

    if DEBUG:
        print(f"↳ details: {ex}", file=sys.stderr)


def upload_binary(file_path, version_name, compare_version_id, project_id, platform, scm_metadata):
    """
    Uploads a file via POST request

    Args:
        file_path (str): Path to the file to upload
        version_name (str): the version name of the new version to be created
        compare_version_id (str): the version id against which we compare the new binary, if empty no comparison will be made
        project_id (str): the project id of the project for which we are creating the version
        platform (str): the platform of the new version (ARM|TRICORE)
        scm_metadata (SCMMetadata): An object containing source control metadata used to provide context about the project and versions being compared.

    Returns:
        report_id: report id of the new report comparing the new version vs the compare_version
    """

    if DEBUG:
        print("call::upload_binary")
        print(f"  file_path          : {file_path}")
        print(f"  version_name       : {version_name}")
        print(f"  compare_version_id : {compare_version_id}")
        print(f"  project_id         : {project_id}")
        print(f"  platform           : {platform}")
        print(f"  scm_metadata       : {json.dumps(asdict(scm_metadata)) if scm_metadata else ''}")

    # Check if file exists
    if not os.path.isfile(file_path):
        print(f"Error: File '{file_path}' does not exist")
        return None

    response = None
    try:
        url = BACKEND_HOST_URL + '/api/v1/reports/xapi-upload'
        if DEBUG:
            print(f"uploading file: {file_path}")
            print(f"url: {url}")

        # Open the file in binary mode and send the request

        files = {
            "binaryFile": (file_path, open(file_path, "rb"), "application/octet-stream")
        }

        values = {
            "versionName": version_name,
            "compareVersionId": compare_version_id,
            "projectId": project_id,
            "platform": platform,
            "scmMetadata": json.dumps(asdict(scm_metadata)) if scm_metadata else "",
        }

        headers = {"X-Api-Key": X_API_KEY}

        response = requests.post(url, files=files, headers=headers, data=values, timeout=REQUEST_TIMEOUT)

        # Check if request was successful
        response.raise_for_status()

        if DEBUG:
            print("\nresponse:")

        # Try to parse JSON response
        try:
            json_response = response.json()
            if DEBUG:
                print(json.dumps(json_response, indent=2))
            return json_response['eventDetails']['reportId']
        except ValueError:
            print(response.text)
            return response.text

    except requests.exceptions.RequestException as e:
        handle_request_exception(e, action="uploading binary")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def get_last_version_id(project_id):
    """
    Gets the version id of the latest valid version uploaded for the project

    Args:
        project_id (str): the project id for which we are getting the latest version

    Returns:
        version_id (str): the version id of the latest valid version uploaded for the project or '' if not found
        version_name (str): the version name of the latest valid version uploaded for the project

    """

    if DEBUG:
        print("call::get_last_version_id")
        print(f"  project_id : {project_id}")

    try:
        url = BACKEND_HOST_URL + '/api/v1/graph/xapi-project-versions'
        if DEBUG:
            print(f"url: {url}")

        headers = { "X-Api-Key": X_API_KEY }
        values = { "projectId": project_id,
                   "app": "diag_poc" }

        response = requests.post(url, headers=headers, data=values, timeout=REQUEST_TIMEOUT)


        # Check if request was successful
        response.raise_for_status()

        if DEBUG:
            print("\nresponse:")

        # Try to parse JSON response
        version_id = ''
        version_name = ''
        version_date = '0000-00-00'
        try:
            json_response = response.json()
            if DEBUG:
                print(json.dumps(json_response, indent=2))
            for version in json_response['message']:
                if version[0]['properties']['status'] == 0:
                    if version[0]['properties']['end_dt'] > version_date:
                        version_id = version[0]['properties']['version_id']
                        version_name = version[0]['properties']['version_name']
                        version_date = version[0]['properties']['end_dt']
            return version_id, version_name
        except ValueError:
            print(response.text)
            return None, None

    except requests.exceptions.RequestException as e:
        handle_request_exception(ex=e, action="getting last version")
        return None, None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None, None

def get_versions(project_id):
    """
    Returns list of all version objects for the project

    Args:
        project_id (str): the projects id for which we are getting the version objects

    Returns:
        versions ([Object]): list of version objects for the project, sorted in descending order with the most recent version first or [] if none found

    """

    if DEBUG:
        print("call::get_versions")
        print(f"  project_id : {project_id}")

    try:
        url = BACKEND_HOST_URL + '/api/v1/graph/xapi-project-versions'
        if DEBUG:
            print(f"url: {url}")

        headers = {"X-Api-Key": X_API_KEY}
        values = {'projectId': project_id,
                  'app': 'diag_poc'}

        response = requests.post(url, headers=headers, data=values, timeout=REQUEST_TIMEOUT)


        # Check if request was successful
        response.raise_for_status()

        if DEBUG:
            print("\nresponse:")

        # Try to parse JSON response
        try:
            json_response = response.json()
            if DEBUG:
                print(json.dumps(json_response, indent=2))
            versions = []
            for version in json_response['message']:
                versions.append(version[0])
            versions.sort(key=lambda x: x['properties']['start_dt'], reverse=True)
            return versions
        except ValueError:
            print(response.text)
            return None

    except requests.exceptions.RequestException as e:
        handle_request_exception(ex=e, action="getting versions")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

def get_version(project_id, version_name):
    """
    Returns the version id for the given version name in the specified project

    Args:
        project_id (str): the id of the project
        version_name (str): the name of the version

    Returns:
        (version_id, report_id) (str|None, str|None)    : the id of the version and report or None if not found
    """

    if DEBUG:
        print("call::get_version")
        print(f"  project_id   : {project_id}")
        print(f"  version_name : {version_name}")

    versions = get_versions(project_id)
    if not versions:
        return None, None

    for version in versions:
        if version_name == version['properties']['version_name']:
            return version['properties']['version_id'], version['properties']['report_id']

    return None, None

def get_reports(project_id, version_name, version_name_base):
    """
    Returns list of all report objects for the given target and base version within the specified project
    Args:
        project_id (str): the id of the project
        version_name (str): the name of the target version
        version_name_base (str): the name of the base version
    """

    if DEBUG:
        print("call::get_reports")
        print(f"  project_id        : {project_id}")
        print(f"  version_name      : {version_name}")
        print(f"  version_name_base : {version_name_base}")
    
    try:
        url = BACKEND_HOST_URL + '/api/v1/graph/xapi-get-reports'
        if DEBUG:
            print(f"url: {url}")

        headers = {"X-Api-Key": X_API_KEY}
        
        values = {
            'project_id': project_id,
            'version_name': version_name,
            'version_name_base': version_name_base
        }

        response = requests.post(url, headers=headers, data=values, timeout=REQUEST_TIMEOUT)

        response.raise_for_status()

        if DEBUG:
            print("\nresponse:")

        try:
            json_response = response.json()
            if DEBUG:
                print(json.dumps(json_response, indent=2))
            
            reports = []
            for report in json_response['message']:
                reports.append(report[0])
            reports.sort(key=lambda x: x['properties']['start_dt'], reverse=True)

            return reports
        except ValueError:
            print(response.text)
            return None

    except requests.exceptions.RequestException as e:
        handle_request_exception(ex=e, action="getting reports")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

def get_versions_data(project_id, version_name, version_name_base):
    """
    Returns the version IDs for the given target and base within the specified project.
    If a diff report exists, the IDs are taken from the same report; otherwise, 
    the IDs of the latest respective versions are returned.

    Args:
        project_id (str): the id of the project
        version_name (str): the name of the target version
        version_name_base (str): the name of the base version

    Returns:
        (version_id, base_version_id, report_id) (str|None, str|None, str|None): obtained version ids or None if not found 
        and additionally the respective report_id if report exists or None if not.
    """

    if DEBUG:
        print("call::get_versions_data")
        print(f"  project_id        : {project_id}")
        print(f"  version_name      : {version_name}")
        print(f"  version_name_base : {version_name_base}")

    if not project_id and version_name and version_name_base:
        return (None, None, None)
    
    if not version_name_base:
        version_id, report_id = get_version(project_id, version_name)
        return (version_id, None, report_id)
    
    reports = get_reports(project_id, version_name, version_name_base)
    if reports:
        last_report = reports[0]
        return (last_report['properties']['target_version'], last_report['properties']['base_version'], last_report['properties']['report_id'])

    version_id, _ = get_version(project_id, version_name)
    version_id_base, _ = get_version(project_id, version_name_base)
    return (version_id, version_id_base, None)

def get_project(project_name):
    """
    Returns the project id for the project with the given project name

    Args:
        project_name (str): the name of the project we are searching

    Returns:
        (project_id, arch) (str|None, str|None): project id and project arch for the matched project or None if not found

    """

    if DEBUG:
        print("call::get_project")
        print(f"  project_name : {project_name}")

    try:
        url = BACKEND_HOST_URL + '/api/v1/projects/xapi-get-project'
        if DEBUG:
            print(f"url: {url}")

        headers = { "X-Api-Key": X_API_KEY }

        values = { "projectName": project_name }

        response = requests.get(url, headers=headers, json=values, timeout=REQUEST_TIMEOUT)

        response.raise_for_status()

        if DEBUG:
            print("\nresponse:")

        # Try to parse JSON response
        try:
            json_response = response.json()
            if DEBUG:
                print(json.dumps(json_response, indent=2))
            if json_response:
                return json_response['id'], json_response['architecture']
            return None, None
        except ValueError:
            print(response.text)
            return None, None

    except requests.exceptions.RequestException as e:
        handle_request_exception(ex=e, action="getting project")
        return None, None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None, None

def get_projects():
    """
    Returns list of all project objects for the company

    Args:

    Returns:
        projects ([Object]): list of project objects for the company

    """

    if DEBUG:
        print("call::get_projects")

    try:
        url = BACKEND_HOST_URL + '/api/v1/projects/xapi-list-all'
        if DEBUG:
            print(f"url: {url}")

        headers = {"X-Api-Key": X_API_KEY}

        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)

        # Check if request was successful
        response.raise_for_status()

        if DEBUG:
            print("\nresponse:")
        projects = []
        # Try to parse JSON response
        try:
            json_response = response.json()
            if DEBUG:
                print(json.dumps(json_response, indent=2))
            for project in json_response:
                projects.append(project)
            return projects
        except ValueError:
            print(response.text)
            return None

    except requests.exceptions.RequestException as e:
        handle_request_exception(ex=e, action="getting projects")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

def upload_finished(project_id, report_id):
    """
    Checks the status of the report with given report id

    Args:
        project_id (str): the projects id for which the report was created
        report_id (str): the report id of the report we are uploading

    Returns:
        (finished, status, status_message) (boolean, int, str): returns the status of the upload
    """
    
    if DEBUG:
        print("call::upload_finished")
        print(f"  project_id : {project_id}")
        print(f"  report_id  : {report_id}")
    
    try:
        url = BACKEND_HOST_URL + '/api/v1/reports/xapi-progress'
        if DEBUG:
            print(f"url: {url}")

        values = {'projectId': project_id,
                  'reportId': report_id}

        response = requests.post(url, data=values, timeout=REQUEST_TIMEOUT)

        # Check if request was successful
        response.raise_for_status()

        if DEBUG:
            print("Server Response:")

        # Try to parse JSON respons
        try:
            json_response = response.json()
            if DEBUG:
                print(json.dumps(json_response, indent=2))
            status = json_response['progress']['status']
            status_message = json_response['progress']['status_message']

            if status != -1:
                return (True, status, status_message)
            else:
                return (False, None, None)

        except ValueError:
            print(response.text)
            return (True, 0, None)

    except requests.exceptions.RequestException as e:
        handle_request_exception(ex=e, action="checking upload status")
        return (True, 0, None)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return (True, 0, None)


def full_upload(file_path, version_name, project_name, use_latest=True, compare_version_id='', wait=True, scm_metadata=None) -> int:
    """
    Uploads a file via POST request and optionally waits for processing to finish
    Args:
        file_path (str): Path to the file to upload
        version_name (str): Name of the version to create
        project_name (str): Name of the project
        use_latest (bool): Whether to use the latest version
        compare_version_id (str): ID of the version to compare against
        wait (bool): Whether to wait for processing to finish
        scm_metadata (dict): Source control metadata

    Returns:
        int: The status of the upload
    """

    if DEBUG:
        print("call::full_upload")
        print(f"  file_path          : {file_path}")
        print(f"  version_name       : {version_name}")
        print(f"  project_name       : {project_name}")
        print(f"  use_latest         : {use_latest}")
        print(f"  compare_version_id : {compare_version_id}")
        print(f"  wait               : {wait}")
        print(f"  scm_metadata       : {json.dumps(asdict(scm_metadata)) if scm_metadata else ''}")

    project_id, platform = get_project(project_name)
    if project_id is None:
        return -1

    if use_latest:
        compare_version_id, _ = get_last_version_id(project_id)

    report_id = upload_binary(file_path, version_name, compare_version_id, project_id, platform, scm_metadata)
    if not report_id:
        return -1

    print(f"Uploaded binary Report ID: {report_id}, Compare Version ID: {compare_version_id}, Project ID: {project_id}")


    status = 0
    tries = 0

    if wait:
        print("Waiting for processing to finish")
        while True:
            finished, status, _ = upload_finished(project_id, report_id)
            if finished:
                break
            tries += 1
            if tries > 360:
                print("Processing not finished after 60 minutes. Please manually check status on the Loci Platform.")
                return -1
            time.sleep(10)

    return status


def get_function_insights(version_id,
                          version_id_base: str | None = None,
                          report_id: str | None = None,
                          perc_resp_limit: float | None = None,
                          perc_thro_limit: float | None = None,
                          perc_bott_limit: float | None = None,
                          pairs: list = None,
                          filter: FilterType | None = None):
    """
    Returns function insights for the specified comparison between versions.
    Args:
        version_id (str): The ID of the target version.
        version_id_base (str|None): The ID of the base version. If None, no comparison will be made.
        report_id (str|None): The ID of the report. If None, the latest report for the version(s) will be used.
        perc_resp_limit (float|None): The response time percentage limit to filter functions. If None, no filtering will be applied.
        perc_thro_limit (float|None): The throughput percentage limit to filter functions. If None, no filtering will be applied.
        perc_bott_limit (float|None): The bottleneck percentage limit to filter functions. If None, no filtering will be applied.
        pairs (list|None): A list of function pairs to filter the insights. If None, no filtering will be applied.
        filter (FilterType|None): The type of functions to filter (NEW, MODIFIED, NEW_N_MODIFIED). If None, no filtering will be applied.
    Returns:
        dict|None: A dictionary containing the function insights, or None if no insights are found.
    """

    if DEBUG:
        print("call::get_function_insights")
        print(f"  version_id      : {version_id}")
        print(f"  version_id_base : {version_id_base}")
        print(f"  report_id       : {report_id}")
        print(f"  perc_resp_limit : {perc_resp_limit}")
        print(f"  perc_thro_limit : {perc_thro_limit}")
        print(f"  perc_bott_limit : {perc_bott_limit}")
        print(f"  pairs           : {pairs}")
        print(f"  filter          : {filter.value if filter else None}")

    try:
        url = BACKEND_HOST_URL + '/api/v1/data/xapi-function-insights'

        if DEBUG:
            print(f"version_id      : {version_id}")
            print(f"version_id_base : {version_id_base}")
            print(f"report_id       : {report_id}")
            print(f"perc_resp_limit : {perc_resp_limit}")
            print(f"perc_thro_limit : {perc_thro_limit}")
            print(f"perc_bott_limit : {perc_bott_limit}")
            print(f"pairs           : {pairs}")
            print(f"filter          : {filter.value if filter else None}")

        values = {
            'version_id': version_id,
            'version_id_base': version_id_base,
            'report_id': report_id,
            'perc_resp_limit': perc_resp_limit,
            'perc_thro_limit': perc_thro_limit,
            'perc_bott_limit': perc_bott_limit,
            'pairs': pairs,
            'filter': filter.value if filter else None,
        }

        headers = {"X-Api-Key": X_API_KEY}
        response = requests.post(url, headers=headers, json=values, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        if DEBUG:
            print("\nresponse:")

        try:
            json_response = response.json()
            if DEBUG:
                print(json.dumps(json_response, indent=2))
            return json_response
        except ValueError:
            print(response.text)
            return None

    except requests.exceptions.RequestException as e:
        handle_request_exception(ex=e, action="getting function insights")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
    

def get_flame_graph(
    project_id: str,
    version_id: str,
    source_container: str,
    source_long_name: str,
) -> str|None:
    """
    Returns the flame graph for a specified function.

    Args:
        project_id (str): The ID of the project.
        version_id (str): The ID of the project version to retrieve function insights for.
        source_container (str): The binary/container of the function.
        source_long_name (str): The long name of the function.

    Returns:
        str: A string representing the JSON representation of the flame graph for the specified function.    
    """

    if DEBUG:
        print("call::get_flame_graph")
        print(f"  project_id       : {project_id}")
        print(f"  version_id       : {version_id}")
        print(f"  source_container : {source_container}")
        print(f"  source_long_name : {source_long_name}")

    try:
        url = BACKEND_HOST_URL + "/api/v1/data/xapi-flame-graph"

        if DEBUG:
            print(f"project_id        : {project_id}")
            print(f"version_id        : {version_id}")
            print(f"source_container  : {source_container}")
            print(f"source_long_name  : {source_long_name}")

        values = {
            "project_id": project_id,
            "version_id": version_id,
            "source_container": source_container,
            "source_long_name": source_long_name,
        }

        headers = {"X-Api-Key": X_API_KEY}
        response = requests.post(
            url, headers=headers, json=values, timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        if DEBUG:
            print("\nresponse:")

        try:
            json_response = response.json()
            if DEBUG:
                print(json.dumps(json_response, indent=2))
            return json_response["message"]
        except ValueError:
            print(response.text)
            return None
    
    except requests.exceptions.RequestException as e:
        handle_request_exception(ex=e, action="getting flame graph")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def get_version_status(
        project_id: str,
        version_id: str):
    """
    Checks the status of a provided project version.

    Args:
        project_id (str): The ID of the project.
        version_id (str): The ID of the project version to retrieve status information for.

    Returns:
        dict|None: A dictionary containing the status details, or None if the project version is not found. The structure of the dictionary is as follows:

        ```json
        {
              "status": int,            # overall status code (0 = success, -1 = progress, 1 = error)
              "total": int,             # total number of analyzed items
              "counts": {               # per-state counters
                "passed": int,
                "failed": int,
                "pending": int
              },
              "updated_at": str,        # timestamp of last update
              "analysis": [             # per-binary analysis entries
                {
                  "binary": str,        # name of the binary
                  "step": str,          # step name (e.g., "complete", "pending", "failed")
                  "status": int,        # step status code
                  "updated_at": str     # timestamp of the step update
                }, ...
              ]
        }
        ```
    """
    if DEBUG:
        print("call::get_version_status")
        print(f"  project_id : {project_id}")
        print(f"  version_id : {version_id}")

    try:
        url = BACKEND_HOST_URL + "/api/v1/reports/xapi-version-progress"
        
        if DEBUG:
            print(f"project_id        : {project_id}")
            print(f"version_id        : {version_id}")

        values = {
            "projectId": project_id,
            "versionId": version_id,
        }

        headers = {"X-Api-Key": X_API_KEY}
        response = requests.post(
            url, headers=headers, json=values, timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        if DEBUG:
            print("\nresponse:")

        try:
            json_response = response.json()
            if DEBUG:
                print(json.dumps(json_response, indent=2))

            report_id = json_response['progress']['report_id']
            if not report_id:
                return None    
            
            # we are returning report status as overall status for the version
            # ['progress']['status'] will return solely binary upload status without any post-processing done)
            finished, status, status_message = upload_finished(project_id=project_id, report_id=report_id)
            if not finished:
                status = -1
            page = "report-list" if status == 0 else "report"
            url = (
                f"{BACKEND_HOST_URL.replace('api.', '', 1)}/#/main/{project_id}/{page}/{report_id}"
                if report_id
                else ""
            )

            statuses = json_response['progress']['statuses']
            containers = json_response['progress']['containers']
            result = {
                "status": status,
                "status_message": status_message,
                "url": url,
                "total": len(containers) if containers else -1,
                "counts": {
                    "passed": sum(1 for s in statuses if s == 0) if statuses else -1,
                    "failed": sum(1 for s in statuses if s > 0) if statuses else -1,
                    "pending": sum(1 for s in statuses if s == -1) if statuses else -1,
                },
                "updated_at": json_response['progress']['end_dt'],
                "analysis": []
            }

            if containers:
                for idx, container in enumerate(containers):
                    result["analysis"].append({
                        "binary": container,
                        "step": json_response['progress']['actions'][idx],
                        "status": json_response['progress']['statuses'][idx],
                        "updated_at": json_response['progress']['action_timestamps'][idx]
                    })

            return result
        except ValueError:
            print(response.text)
            return None

    except requests.exceptions.RequestException as e:
        handle_request_exception(ex=e, action="getting version status")
        return None
    except Exception as e:
        print(f'Unexpected error: {e}')
        return None

def get_function_insights_summary(
    project_id: str,
    version_id: str,
    version_id_base: str,
    scm_metadata: SCMMetadata
) -> dict | None:
    """
    Returns an AI agent summary for the specified comparison between versions.

    Args:
        project_id (str): The ID of the project.
        version_id (str): The ID of the target version.
        version_id_base (str): The ID of the base version.
        scm_metadata (SCMMetadata): An object containing source control metadata used to provide context about the project and versions being compared.

    Returns:
        str|None: A string containing the AI agent summary for the specified comparison, or None if no summary has been generated.
    """

    if DEBUG:
        print("call::get_function_insights_summary")
        print(f"  project_id        : {project_id}")
        print(f"  version_id        : {version_id}")
        print(f"  version_id_base   : {version_id_base}")
        print(f"  scm_metadata      : {json.dumps(asdict(scm_metadata)) if scm_metadata else ''}")

    try:
        url = BACKEND_HOST_URL + "/api/v1/data/xapi-insights-summary"
        j_scm_metadata = json.dumps(asdict(scm_metadata)) if scm_metadata else ""

        if DEBUG:
            print(f"project_id        : {project_id}")
            print(f"version_id        : {version_id}")
            print(f"version_id_base   : {version_id_base}")
            print(f"scm_metadata      : {j_scm_metadata}")
        
        values = {
            "project_id": project_id,
            "version_id": version_id,
            "version_id_base": version_id_base,
            "scm_metadata": j_scm_metadata
        }

        ght_key = 'LOCI_GITHUB_TOKEN'
        if ght_key not in os.environ:
            print(f'ERROR: Environment variable "{ght_key}" is not set')
            return None
        
        gh_token = os.environ[ght_key]

        headers = {
            "X-Api-Key": X_API_KEY,
            "X-Github-AT": gh_token
        }

        response = requests.post(
            url, headers=headers, json=values
        )
        response.raise_for_status()

        if DEBUG:
            print("\nresponse:")

        try:
            json_response = response.json()
            if DEBUG:
                print(json.dumps(json_response, indent=2))
            return json_response["message"]
        except ValueError:
            print(response.text)
            return None

    except requests.exceptions.RequestException as e:
        handle_request_exception(ex=e, action="getting AI summary")
        return None
    except Exception as e:
        print(f'Unexpected error: {e}')



def get_report_data(report_id: str):
    """
    Returns report symbols data for the specified report.

    Args:
        report_id (str): The ID of the report to retrieve symbol data for.

    Returns:
        dict|None: A dictionary containing the report symbols data, or None if the report is not found. The structure of the dictionary is as follows:

        ```json
        {
              "target_total": int,  # Total number of symbols in the target version
              "base_total": int,    # Total number of symbols in the base version
              "modified": int,      # Number of modified symbols
              "new": int,           # Number of new symbols
              "deleted": int        # Number of deleted symbols
        }
        ```
    """

    if DEBUG:
        print("call::get_report_data")
        print(f"  report_id : {report_id}")

    try:
        url = BACKEND_HOST_URL + '/api/v1/graph/xapi-get-report-symbols'

        values = {
            'report_id': report_id
        }

        headers = {"X-Api-Key": X_API_KEY}
        response = requests.post(url, headers=headers, json=values, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        if DEBUG:
            print("\nresponse:")

        try:
            json_response = response.json()
            if DEBUG:
                print(json.dumps(json_response, indent=2))

            if not json_response['message'] or not json_response['message'][0]:
                return None

            target_total = json_response['message'][0][0]
            modified = json_response['message'][0][1] or 0
            added = json_response['message'][0][2] or 0
            removed = json_response['message'][0][3] or 0
            base_total = target_total + removed - added
            return {
                'target_total': target_total,
                'base_total': base_total,
                'modified': modified,
                'new': added,
                'deleted': removed
            }
        except ValueError:
            print(response.text)
            return None

    except requests.exceptions.RequestException as e:
        handle_request_exception(ex=e, action="getting report data")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def get_auth_status():
    """
    Checks if the provided API key is valid by making a test request to the backend.

    Returns:
        dict|None: A dictionary containing the authentication status details, or None if the API key is invalid. The structure of the dictionary is as follows:

        ```json
        {
              "company": str,        # Name of the company associated with the API key
              "agentic": bool,       # Whether the company has agentic features enabled
              "max_users": int,      # Maximum number of users allowed for the company
              "created_at": str,     # Timestamp of when the company was created
              "active_until": str    # Timestamp of when the company's subscription is active until
        }
        ```
    """

    if DEBUG:
        print("call::get_auth_status")

    try:
        url = BACKEND_HOST_URL + '/api/v1/companies/xapi-get-company-by-api-key'
        if DEBUG:
            print(f"url: {url}")

        headers = { "X-Api-Key": X_API_KEY }

        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        if DEBUG:
            print("\nresponse:")

        try:
            json_response = response.json()
            if DEBUG:
                print(json.dumps(json_response, indent=2))
            
            if not json_response['message']:
                return None
            
            return {
                'company': json_response['message']['name'],
                'agentic': json_response['message']['agentic'],
                'max_users': json_response['message']['max_users'],
                'created_at': json_response['message']['timestamp'],
                'active_until': json_response['message']['active_until']
            }
        except ValueError:
            print(response.text)
            return None

    except requests.exceptions.RequestException as e:
        handle_request_exception(ex=e, action="checking authentication status")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None