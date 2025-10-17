from ..models.form import Form
import requests


class Forms:
    def __init__(self, session, logger, base_url, workspace_instance):
        self.session = session
        self.logger = logger
        self.base_url = base_url
        self.workspace_instance = workspace_instance
    
    def get(self, id):
        """
        Get form details using id

        :param id: The ID/formSubmissionID of the form to retrieve.
        :return:
        """
        try:
            url = f"{self.base_url}/api/v1/forms/{id}"
            response = self.session.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors

            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"Successfully fetched form for {id}")
            else:
                raise ValueError(resp.get('message'))
            return Form(**resp['data']['elements'][0])
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

    def put(self, form: Form, enable_retrofit: bool = False, enable_resync: bool = False):
        """
        Update existing form

        :param form: An instance of the Form model to be updated.
        :param enable_retrofit: Boolean flag to enable retrofit functionality.
        :param enable_resync: Boolean flag to enable re-sync functionality.
        :return:
        """
        # form should be a valid Form model
        if not isinstance(form, Form):
            raise ValueError("form field should be an instance of Form model")
        # id or uuid field is required in the form model to update the form
        if not form.id and not form.uuid:
            raise ValueError("id or uuid field is required to update the form")

        try:
            url = f"{self.base_url}/api/v1/forms?enableRetrofit={enable_retrofit}&enableReSync={enable_resync}"
            response = self.session.put(url, json=form.model_dump(exclude_none=True, exclude_unset=True))
            response.raise_for_status()  # Raise an exception for HTTP errors

            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"Successfully updated task for id {form.id}")
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
    
    def post(self, form: Form):
        """
        Create a new form

        :param form: An instance of the Form model to be created.
        :return:
        """
        if not isinstance(form, Form):
            raise ValueError("form field should be an instance of Form model")

        try:
            url = f"{self.base_url}/api/v1/forms"
            response = self.session.post(url, json=form.model_dump(exclude_none=True, exclude_unset=True))
            response.raise_for_status()  # Raise an exception for HTTP errors

            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"Successfully completed search operation for form {form.title}")
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

    def get_legacy_form(self, id):
        """
        Get form details using id

        :param id: The ID/formSubmissionID of the form to retrieve.
        :return:
        """
        try:
            url = f"{self.base_url}/rest/v17/lite/forms/{id}"
            response = self.session.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors

            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"Successfully fetched form for {id}")
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

