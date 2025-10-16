import urllib.parse
import requests


class Users:
    def __init__(self, session, logger, base_url, workspace_instance):
        self.session = session
        self.logger = logger
        self.base_url = base_url
        self.workspace_instance = workspace_instance

    def create_users(self, user_payload: list):
        """
        Create user.

        :param user_payload:
        :return:
        """
        try:
            user_payload = [i.model_dump(exclude_none=True) for i in user_payload]

            url = f"{self.base_url}/rest/v13/bulk/add/users"
            response = self.session.post(url, json=user_payload)
            response.raise_for_status()  # Raise an exception for HTTP errors

            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"User profile successfully created.")
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

    def edit_users(self, user_payload: list):
        """
        Create user.

        :param user_payload:
        :return:
        """
        try:
            new_payload = []
            for user in user_payload:
                if not user.EncryptedZviceID:
                    raise Exception("User data validation failed: Missing EncryptedZviceID.")
                elif not user.Profile.UserID:
                    raise Exception("User data validation failed: Missing UserID in Profile.")
                new_payload.append(user.model_dump(exclude_none=True))

            url = f"{self.base_url}/rest/v13/bulk/edit/users"
            response = self.session.put(url, json=new_payload)
            response.raise_for_status()  # Raise an exception for HTTP errors

            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"User profile successfully created.")
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

    def get_users(self, user_payload: list = None, hide_special_usergroups: bool = True):
        """
        Fetch user details.

        :param user_payload: [
                {
                    "operator":"=",
                    "value": "USER_EMAIL",
                    "column": "UserEmail"   # Other inputs you can pass are 'UserID', 'UserPhone',
                }
            ]
        :return:
        """
        if user_payload is None:
            user_payload = []
        filters = {
            "HideSpecialUserGroups": hide_special_usergroups
        }
        try:
            # Encoding the filter dictionary into query parameters
            filter_params = urllib.parse.urlencode(filters)
            url = f"{self.base_url}/rest/v17/search/users?{filter_params}"
            response = self.session.post(url, json=user_payload)
            response.raise_for_status()  # Raise an exception for HTTP errors

            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"PDF generated successfully for custom document {id}")
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
