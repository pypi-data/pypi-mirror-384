import urllib.parse
import requests


class Documents:
    def __init__(self, session, logger, base_url, workspace_instance):
        self.session = session
        self.logger = logger
        self.base_url = base_url
        self.workspace_instance = workspace_instance

    def get_custom_template_data(self, id: int, variables: dict):
        """
        Get custom Template Data.

        :param id: Template ID of custom document
        :param variables: Dictionary of variables to be used in the template.
        :return:
        """
        try:
            url = f"{self.base_url}/rest/v13/custom/documents/generate/{id}"
            response = self.session.post(url, json=variables)
            response.raise_for_status()  # Raise an exception for HTTP errors

            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"Template data retrieved successfully for custom document {id}")
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

    def get_custom_template_html(self, id: int, variables: dict):
        """
        Get custom Template HTML.

        :param id: Template ID of custom document
        :param variables: Dictionary of variables to be used in the template.
        :return:
        """
        try:
            url = f"{self.base_url}/rest/v13/custom/documents/generate/{id}"
            response = self.session.post(url, json=variables)
            response.raise_for_status()  # Raise an exception for HTTP errors

            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"Template HTML retrieved successfully for custom document {id}")
            else:
                raise ValueError(resp.get('message'))
            return resp["html"]
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

    def get_custom_document_link(self, id: int, variables: dict, filters: dict = None):
        """
        Generate PDF link using custom doc template.

        :param id: Template ID of custom document
        :param variables: Dictionary of variables to be used in the template.
        :param filters: Optional dictionary of filters to apply to the document. The dictionary can include:
            - "header_doc_id": Header Custom Document ID
            - "footer": "yes/no"
            - "style": "yes/no"
            - "orientation": "P/L" (P = Portrait, L = Landscape)
            - "margin_left": Left margin in integer units.
            - "margin_right": Right margin in integer units.
            - "margin_top": Top margin in integer units.
            - "margin_bottom": Bottom margin in integer units.
            - "margin_header": Header margin in integer units.
            - "margin_footer": Footer margin in integer units.
            - "UseLogoAsWatermark": Boolean value for watermark usage.
        :return:
        """
        if filters is None:
            filters = {}
        try:
            if filters:
                filter_dict = filters
                # Encoding the filter dictionary into query parameters
                filter_params = urllib.parse.urlencode(filter_dict)
                url = f"{self.base_url}/rest/v13/custom/documents/link/{id}?{filter_params}"
            else:
                url = f"{self.base_url}/rest/v13/custom/documents/link/{id}"
            response = self.session.post(url, json=variables)
            response.raise_for_status()  # Raise an exception for HTTP errors

            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"PDF generated successfully for custom document {id}")
            else:
                raise ValueError(resp.get('message'))
            return resp["data"]["link"]
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
