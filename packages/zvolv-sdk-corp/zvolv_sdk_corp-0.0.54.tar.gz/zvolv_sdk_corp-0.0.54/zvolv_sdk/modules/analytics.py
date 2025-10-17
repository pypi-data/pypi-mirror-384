import requests
from elasticsearch_dsl import Search as ESearch


class Analytics:
    def __init__(self, session, logger, base_url, workspace_instance):
        self.session = session
        self.logger = logger
        self.base_url = base_url
        self.workspace_instance = workspace_instance

    def search(self, form_id: str, search_obj: ESearch):
        """
        Search the Analytics API to fetch data from a specific form.

        This method sends a POST request to the Analytics API, which is based on Elasticsearch.
        It searches the data associated with a specific form ID using the provided query parameters.

        :param form_id: The ID of the form to search.
        :param search_obj: The search query.
        :return:
        """
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
