import requests
import urllib.parse
import json


class Workflows:
    def __init__(self, session, logger, base_url, workspace_instance):
        self.session = session
        self.logger = logger
        self.base_url = base_url
        self.workspace_instance = workspace_instance

    def get_project_tasks_metadata(self, wid: str, filters: dict = None):
        """
        Fetch metadata for tasks within a workflow ID, applying optional filters.

        :param wid: Workflow ID for which task details are being retrieved.
        :param filters: Optional dictionary to filter tasks, including:
            - "stageCodes": List of specific stage codes.
            - "status": List of task statuses (e.g., "Active", "Assigned").
            - "department": List of departments to filter by (e.g., "DepartmentA/TagA", "DepartmentB/TagB").
        :return: List of task metadata.
        """
        if filters is None:
            filters = {}
        try:
            if filters:
                filter_dict = {'filter': json.dumps(filters)}
                # Encoding the filter dictionary into query parameters
                filter_params = urllib.parse.urlencode(filter_dict)
                url = f"{self.base_url}/rest/v13/tasks/wormgraph/workflow/{wid}?{filter_params}"
            else:
                url = f"{self.base_url}/rest/v13/tasks/wormgraph/workflow/{wid}"
            response = self.session.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors

            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"Successfully fetched tasks for WorkflowID {wid}")
            else:
                raise ValueError(resp.get('message'))
            return resp['data']['tasks']

        except requests.exceptions.RequestException as http_err:
            error_response = response.json()
            status_code = error_response.get('statusCode', response.status_code)
            error_message = error_response.get('message', str(http_err))

            error_message = f"{status_code} Error: {error_message}"
            self.logger.error(f"An error occurred: {error_message}")
            raise requests.exceptions.HTTPError(error_message)
        except Exception as e:
            self.logger.error(e)
            raise e

    def apply_task_metadata_changes(self, wid: str, stage_code: str, task_metadata_changes: dict):
        """
        Edit task metadata for a specific workflow ID.

        This method allows you to apply changes to a task's metadata within a specified workflow.
        It constructs a request body to update the task data based on the provided stage code and metadata changes.

        :param wid: Workflow ID to which the changes are being applied.
        :param stage_code: Stage code of the task whose metadata is being updated.
        :param task_metadata_changes: Dictionary containing the metadata changes for the task.
        :return: Response from the server containing the result of the update operation.

        :raises ValueError: If the response contains an error message.
        :raises requests.exceptions.HTTPError: For any HTTP-related errors during the request.
        :raises Exception: For any other errors that may occur.
        """
        if not wid:
            raise ValueError("id field is required to apply metadata changes.")

        if not stage_code:
            raise ValueError("stage_code field is required to apply metadata changes.")

        if not task_metadata_changes:
            raise ValueError("task_metadata_changes field is required to apply metadata changes.")

        try:
            body = {
                'bulk_edit': [
                    {
                        'stage': {'code': stage_code},
                        'data': {'task_data': task_metadata_changes}
                    }
                ]
            }
            url = f"{self.base_url}/rest/v17/workflow/{wid}/bulk/edit/wf"
            response = self.session.put(url, json=body)
            response.raise_for_status()  # Raise an exception for HTTP errors

            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"Successfully applied changes for task {stage_code} in project {wid}.")
            else:
                raise ValueError(resp.get('message'))

        except requests.exceptions.RequestException as http_err:
            error_response = response.json()
            status_code = error_response.get('statusCode', response.status_code)
            error_message = error_response.get('message', str(http_err))

            error_message = f"{status_code} Error: {error_message}"
            self.logger.error(f"An error occurred while applying changes: {error_message}")
            raise requests.exceptions.HTTPError(error_message)
        except Exception as e:
            self.logger.error(e)
            raise e

        return resp  # Return the last response received


    def create_project(self, title: str, formID: str, form_input_data: dict):
        """
        Create a new project.

        :param title: The title of the project (required).
        :param formID: The form ID (required).
        :param form_input_data: Dictionary containing form input data.

        :raises ValueError: If required parameters are missing.
        :raises requests.exceptions.HTTPError: For HTTP request errors.
        :raises Exception: For any other errors during execution.
        """
        if not title:
            raise ValueError("The 'title' field is required to create or update the project.")

        if not formID:
            raise ValueError("The 'formID' field is required to associate with the project.")

        try:
            business_tag = dict(self.session.headers)["businessTagID"]
            body = {
                'title': title,
                'pcf_form_id': formID,
                'pcf_sub': form_input_data
            }

            url = f"{self.base_url}/rest/v17/workflow/{business_tag}"
            response = self.session.post(url, json=body)
            response.raise_for_status()  # Raise an exception for HTTP errors

            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"Successfully created project '{title}' (Form ID: {formID}).")
            else:
                raise ValueError(f"Failed to create project: {resp.get('message')}")

        except requests.exceptions.RequestException as http_err:
            error_response = response.json()
            status_code = error_response.get('statusCode', response.status_code)
            error_message = error_response.get('message', str(http_err))

            error_message = f"{status_code} Error: {error_message}"
            self.logger.error(f"An HTTP error occurred while creating the project:: {error_message}")
            raise requests.exceptions.HTTPError(error_message)
        except Exception as e:
            self.logger.error(e)
            raise e

        return resp  # Return the last response received
