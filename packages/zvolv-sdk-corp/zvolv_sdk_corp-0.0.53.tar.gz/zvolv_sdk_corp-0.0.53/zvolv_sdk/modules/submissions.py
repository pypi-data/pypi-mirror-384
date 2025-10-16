from elasticsearch_dsl import Search as ESearch
from ..models.submission import LegacySubmission, Submission
import requests
import urllib.parse


class Submissions:
    def __init__(self, session, logger, base_url, workspace_instance):
        self.session = session
        self.logger = logger
        self.base_url = base_url
        self.workspace_instance = workspace_instance

    def get(self, id):
        """
        Get form submission details from id.

        :param id: FormSubmissionID/id of entry
        :return:
        """
        if not id:
            raise ValueError("id field is required to update the submission")

        try:
            url = f"{self.base_url}/api/v1/submissions/{id}"
            response = self.session.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors

            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"Form details retrieved successfully for id {id}")
            else:
                raise ValueError(resp.get('message'))
            return Submission(**resp['data']['elements'][0])
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

    def search(self, form_id: str, search_obj: ESearch):
        """
        Search the Analytics API to fetch data from a specific form.

        This method sends a POST request to the Analytics API, which is based on Elasticsearch.
        It searches the data associated with a specific form ID using the provided query parameters.

        :param form_id: The ID of the form to search.
        :param search_obj: The search query.
        :return:
        """

        # Accept only elasticsearch-dsl Search object as searchObj
        if not isinstance(search_obj, ESearch):
            raise ValueError("searchObj field should be an instance of elasticsearch-dsl Search object")

        if not form_id:
            raise ValueError("formId field is required to search the submissions")

        try:
            query = search_obj.to_dict()
            url = f"{self.base_url}/api/v1/analytics/search"
            response = self.session.post(url, json={'formId': form_id, 'query': query})
            response.raise_for_status()  # Raise an exception for HTTP errors

            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"Successfully completed search operation for form {id}")
            else:
                raise ValueError(resp.get('message'))
            return resp['data']
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

    def put(self, submission: Submission, query_params: dict = None):
        """Update existing submission

        :param submission: An instance of the Submission model representing the submission to update.
        :param query_params: Optional dictionary of query parameters to modify the update behavior.
                        Possible keys include:
                        - "skipValidations": "true"/"false"
                        - "skipAutomation": "true"/"false"
                        - "skipFormulaValidation": "true"/"false"
        :return:
        """
        if not isinstance(submission, Submission):
            raise ValueError("submission field should be an instance of Submission model")

        if not submission.id:
            raise ValueError("id field is required to update the submission")

        if not submission.elements or submission.elements == []:
            raise ValueError("elements field with least 1 element is required to update the submission")

        try:
            if query_params:
                # Encoding the query_params dictionary into query parameters
                query_params = urllib.parse.urlencode(query_params)
                url = f"{self.base_url}/api/v1/submissions/{submission.id}?{query_params}"
            else:
                url = f"{self.base_url}/api/v1/submissions/{submission.id}"

            response = self.session.put(url, json=submission.model_dump(exclude_none=True, exclude_unset=True))
            response.raise_for_status()  # Raise an exception for HTTP errors

            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"Successfully updated entry for id {submission.id}")
            else:
                raise ValueError(resp.get('message'))
            return resp
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

    def post(self, submission: Submission, query_params: dict = None):
        """Create a new submission

        :param submission: An instance of the Submission model representing the submission to create.
        :param query_params: Optional dictionary of query parameters to modify the update behavior.
                        Possible keys include:
                        - "skipValidations": "true"/"false"
                        - "skipAutomation": "true"/"false"
                        - "skipFormulaValidation": "true"/"false"
        :return:
        """
        if not isinstance(submission, Submission):
            raise ValueError("submission field should be an instance of Submission model")

        if not submission.formId:
            raise ValueError("formId field is required to create the submission")

        if not submission.elements:
            raise ValueError("elements field is required to create the submission")

        try:
            if query_params:
                # Encoding the query_params dictionary into query parameters
                query_params = urllib.parse.urlencode(query_params)
                url = f"{self.base_url}/api/v1/submissions?{query_params}"
            else:
                url = f"{self.base_url}/api/v1/submissions"

            response = self.session.post(url, json=submission.model_dump(exclude_none=True, exclude_unset=True))
            response.raise_for_status()  # Raise an exception for HTTP errors

            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"Successfully added a new entry for form {submission.formId}")
            else:
                raise ValueError(resp.get('message'))
            return resp
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

    def get_legacy_submission(self, id):
        """
        Get form submission details from id.

        :param id: FormSubmissionID/id of entry
        :return:
        """
        if not id:
            raise ValueError("id field is required to update the submission")

        try:
            url = f"{self.base_url}/rest/v17/lite/submissions/{id}"
            response = self.session.get(url)
            response.raise_for_status() 

            resp = response.json()
            self.logger.info(f"Submissions: {resp}")
            if resp.get('error') is False:
                self.logger.info(f"Form details retrieved successfully for id {id}")
            else:
                raise ValueError(resp.get('message'))
            return resp['data']['elements'][0]
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

    def post_legacy_submission(self, submission: LegacySubmission, query_params: dict = None):
        """Create a new submission

        :param submission: An instance of the Submission model representing the submission to create.
        :param query_params: Optional dictionary of additional context to modify the workflow or submission behavior.
                    Possible keys include:
                    - "WorkflowID": Integer ID of the workflow to associate with the submission.
                    - "ParentElements": List of top-level parent elements for contextual linkage.
                    - "draft": "1" to save as draft, or None to submit normally.
                    - "AdditionalUserZviceIDs": List of user ZviceIDs to notify.
                    - "AdditionalEmailIDs": List of email addresses for notifications.
                    - "AdditionalMobileNos": List of mobile numbers for notifications.
                    - "wf_stage_info": Dictionary defining specific workflow stage context (e.g. {"wid": ...}).
                    - "dont_create_wf": Boolean; True to prevent workflow creation.
                    - "skip-project-creation": Boolean; True to skip project initiation.

        :return:
        """
        self.logger.info(f"POST")
        if not isinstance(submission, LegacySubmission):
            raise ValueError("submission field should be an instance of Submission model")

        if not submission.FormID:
            raise ValueError("formId field is required to create the submission")

        if not submission.Elements:
            raise ValueError("elements field is required to create the submission")

        self.logger.info(f"POST 1")

        try:
            if query_params:
                # Encoding the query_params dictionary into query parameters
                query_params = urllib.parse.urlencode(query_params)

                url = f"{self.base_url}/rest/v17/{submission.ZviceID}/forms/{submission.FormID}/submissions/?{query_params}"
            else:
                url = f"{self.base_url}/rest/v17/{submission.ZviceID}/forms/{submission.FormID}/submissions"
            body = {str(item.FormMetaID): str(item.Value) for item in submission.Elements}
            body['OverrideMetaData'] = submission.OverrideMetaData
            response = self.session.post(url, json=body)
            response.raise_for_status() 
            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"Successfully added a new entry for form {submission.FormID}")
            else:
                raise ValueError(resp.get('message'))
            return resp
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

    def put_legacy_submission(self, submission: LegacySubmission, query_params: dict = None):
        """Update existing submission

        :param submission: An instance of the Submission model representing the submission to update.
        :param query_params: Optional dictionary of additional context to modify the workflow or submission behavior.
                    Possible keys include:
                    - "WorkflowID": Integer ID of the workflow to associate with the submission.
                    - "ParentElements": List of top-level parent elements for contextual linkage.
                    - "draft": "1" to save as draft, or None to submit normally.
                    - "AdditionalUserZviceIDs": List of user ZviceIDs to notify.
                    - "AdditionalEmailIDs": List of email addresses for notifications.
                    - "AdditionalMobileNos": List of mobile numbers for notifications.
                    - "wf_stage_info": Dictionary defining specific workflow stage context (e.g. {"wid": ...}).
                    - "dont_create_wf": Boolean; True to prevent workflow creation.
                    - "skip-project-creation": Boolean; True to skip project initiation.

        :return:
        """
        if not isinstance(submission, LegacySubmission):
            raise ValueError("submission field should be an instance of LegacySubmission model")

        if not submission.FormSubmissionID:
            raise ValueError("FormSubmissionID field is required to update the submission")

        if not submission.Elements or submission.Elements == []:
            raise ValueError("elements field with least 1 element is required to update the submission")

        try:
            if query_params:
                # Encoding the query_params dictionary into query parameters
                query_params = urllib.parse.urlencode(query_params)
                
                url = f"{self.base_url}/rest/v17/{submission.ZviceID}/forms/{submission.FormID}/submissions/{submission.FormSubmissionID}?{query_params}"
            else:
                url = f"{self.base_url}/rest/v17/{submission.ZviceID}/forms/{submission.FormID}/submissions/{submission.FormSubmissionID}"
            body = {str(item.FormMetaID): str(item.Value) for item in submission.Elements}
            body['OverrideMetaData'] = submission.OverrideMetaData
            response = self.session.put(url, json=body)
            response.raise_for_status() 

            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"Successfully updated entry for id {submission.FormSubmissionID}")
            else:
                raise ValueError(resp.get('message'))
            return resp
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

