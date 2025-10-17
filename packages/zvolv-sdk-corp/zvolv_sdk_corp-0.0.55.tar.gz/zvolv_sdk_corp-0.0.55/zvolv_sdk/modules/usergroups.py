import urllib.parse
import requests


class UserGroups:
    def __init__(self, session, logger, base_url, workspace_instance):
        self.session = session
        self.logger = logger
        self.base_url = base_url
        self.workspace_instance = workspace_instance

    def fetch_usergroup_by_id(self, group_id: int, lite: bool = True):
        """
        Retrieve details of a specific user group.

        :param group_id: ID of the user group to retrieve.
        :param lite: Boolean flag to indicate whether to retrieve a lite response with fewer details. Default is True.
        :return: The user group data as a dictionary.
        """
        filters = {
            "light": lite
        }
        try:
            # Encoding the filter dictionary into query parameters
            filter_params = urllib.parse.urlencode(filters)
            url = f"{self.base_url}/rest/v17/usergroups/{group_id}/{self.workspace_instance['BUSINESS_TAG_ID']}?{filter_params}"
            response = self.session.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors

            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"Successfully fetched user group details for group_id: {group_id}")
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
