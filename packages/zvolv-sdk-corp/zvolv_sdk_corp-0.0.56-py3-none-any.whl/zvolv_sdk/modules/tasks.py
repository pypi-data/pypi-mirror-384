from elasticsearch_dsl import Search as ESearch
from ..models.task import LegacyTaskRequestBody, Task
import requests


class Tasks:
    def __init__(self, session, logger, base_url, workspace_instance):
        self.session = session
        self.logger = logger
        self.base_url = base_url
        self.workspace_instance = workspace_instance
    
    def get(self, id):
        """
        Get form details from id

        :param id:
        :return:
        """
        try:
            url = f"{self.base_url}/api/v1/tasks/{id}"
            response = self.session.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors

            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"Successfully fetched task for task {id}")
            else:
                raise ValueError(resp.get('message'))
            return Task(**resp['data']['elements'][0])
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
    
    def search(self, search_obj: ESearch):
        """
        Search tasks

        :param search_obj:
        :return:
        """
        # Accept only elasticsearch-dsl Search object as searchObj
        if not isinstance(search_obj, ESearch):
            raise ValueError("searchObj field should be an instance of elasticsearch-dsl Search object")

        try:
            query = search_obj.to_dict()
            url = f"{self.base_url}/api/v1/analytics/search"
            response = self.session.post(url, json={'isTask': True, 'query': query})
            response.raise_for_status()  # Raise an exception for HTTP errors

            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"Successfully completed search operation for task.")
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
    
    def put(self, task: Task):
        """
        Update existing task

        :param task:
        :return:
        """
        # task should be a valid Task model
        if not isinstance(task, Task):
            raise ValueError("task field should be an instance of Task model")
        # id or uuid field is required in the task model to update the task
        if not task.id and not task.uuid:
            raise ValueError("id or uuid field is required to update the task")

        try:
            url = f"{self.base_url}/api/v1/tasks"
            response = self.session.put(url, json=task.model_dump(exclude_none=True, exclude_unset=True))
            response.raise_for_status()  # Raise an exception for HTTP errors

            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"Successfully updated task for id {task.id}")
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
    
    def post(self, task: Task):
        """
        Create a new task

        :param task:
        :return:
        """
        if not isinstance(task, Task):
            raise ValueError("task field should be an instance of Task model")

        try:
            url = f"{self.base_url}/api/v1/tasks"
            response = self.session.post(url, json=task.model_dump(exclude_none=True, exclude_unset=True))
            response.raise_for_status()  # Raise an exception for HTTP errors

            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"Successfully added a new entry for form {task.title}")
            else:
                raise ValueError(resp.get('message'))
            return resp["data"]
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

    def get_legacy_task(self, id):
            """
            Get task details from id

            :param id:
            :return:
            """

            try:
                business_tag_id = self.session.headers.get('businessTagID')

                url = f"{self.base_url}/rest/v17/tasks/getsingle/{business_tag_id}/{id}"
                response = self.session.get(url)
                response.raise_for_status()  

                resp = response.json()
                if resp.get('error') is False:
                    self.logger.info(f"Successfully fetched task for task {id}")
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
        
    def update_legacy_task(self, task: LegacyTaskRequestBody):
        """
        Update existing task

        :param task:
        :return:
        """
        # task should be a valid Task model
        if not isinstance(task, LegacyTaskRequestBody):
            raise ValueError("task field should be an instance of Task model")
        # id or uuid field is required in the task model to update the task
        if not task.TaskID:
            raise ValueError("id or uuid field is required to update the task")

        try:
            business_tag_id = self.session.headers.get('businessTagID')
            url = f"{self.base_url}/rest/v17/tasks/edit/{business_tag_id}"
            response = self.session.post(url, json=task.model_dump(exclude_none=True, exclude_unset=True))
            response.raise_for_status()  
        
            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"Successfully updated task for id {task.TaskID}")
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
    
    def post_legacy_adhoc_task(self, task: LegacyTaskRequestBody):
        """
        Create a new task

        :param task:
        :return:
        """
        if not isinstance(task, LegacyTaskRequestBody):
            raise ValueError("task field should be an instance of Task model")

        try:
            business_tag_id = self.session.headers.get('businessTagID')
            url = f"{self.base_url}/rest/v17/org/{business_tag_id}/workflow/addtask/stage"
            response = self.session.post(url, json=task.model_dump(exclude_none=True, exclude_unset=True))
            response.raise_for_status()  

            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"Successfully added a new entry for form {task.Title}")
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
        
    def get_all_legacy_tasks_by_wid(self, wid):
        """
        Get all tasks from wid

        :param wid:
        :return:
        """
        try:
            business_tag_id = self.session.headers.get('businessTagID')
            url = f"{self.base_url}/rest/v17/tasks/{business_tag_id}/{business_tag_id}/workflow/{wid}"
            response = self.session.get(url)
            response.raise_for_status()  

            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"Successfully fetched task for task {id}")
            else:
                raise ValueError(resp.get('message'))
            return resp['data']['elements']
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
