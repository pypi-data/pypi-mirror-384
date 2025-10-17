from ..modules.documents import Documents
import requests
from typing import Union


class Communications:
    def __init__(self, session, logger, base_url, workspace_instance):
        self.session = session
        self.logger = logger
        self.base_url = base_url
        self.workspace_instance = workspace_instance

    def send_mail_to_roles(self, roles: list, subject_template_id: Union[int, str], message_template_id: Union[int, str], variables: dict, communication_type: str = "MAIL"):
        """
        Send mail to roles.

        :param roles: List of roles to receive the email, e.g., ['Role1', 'Role2'].
        :param subject_template_id: Template ID of custom document.
        :param message_template_id: Template ID of custom document.
        :param variables: Dictionary of variables to be used in the email templates.
        :param communication_type: Type of communication, default is "MAIL".
        :return:
        """
        try:
            document = Documents(self.session, self.logger, self.base_url, self.workspace_instance)

            subject = document.get_custom_template_data(subject_template_id, variables)
            message = document.get_custom_template_html(message_template_id, variables)

            body = {
                'groupname': roles,
                'commtype': [communication_type],
                'title': subject,
                'msg': message
            }

            business_tag = dict(self.session.headers)["businessTagID"]
            url = f"{self.base_url}/rest/v13/usergroups/message/{business_tag}"
            response = self.session.post(url, json=body)
            response.raise_for_status()  # Raise an exception for HTTP errors

            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"Email sent successfully.")
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

    def send_mail_to_emails(self, emails: list, subject_template_id: Union[int, str], message_template_id: Union[int, str], variables: dict, cc=None, bcc=None, reply_to=None, attachments=None, user_name=None, default_footer=False, verify=True):
        """
        Send mail to email addresses.

        :param emails: List of email addresses to receive the email, e.g., ['EmailId1', 'EmailId2'].
        :param subject_template_id: Template ID of custom document.
        :param message_template_id: Template ID of custom document.
        :param variables: Dictionary of variables to be used in the email templates.
        :param cc: Optional list of email addresses to be added in the CC field.
        :param bcc: Optional list of email addresses to be added in the BCC field.
        :param reply_to: Optional email address to be used as the reply-to address.
        :param attachments: Optional list of file attachments to include in the email.
        :param user_name: Optional username to be associated with the email.
        :param default_footer: Boolean flag to include or exclude default footer, default is False.
        :param verify: Boolean flag for SSL verification, default is True.
        :return:
        """
        try:
            document = Documents(self.session, self.logger, self.base_url, self.workspace_instance)

            subject = document.get_custom_template_data(subject_template_id, variables)
            message = document.get_custom_template_html(message_template_id, variables)

            emails = ','.join(emails)
            business_tag = dict(self.session.headers)["businessTagID"]

            body = {
                "email": emails,
                "OrgName": business_tag,
                "subject": subject,
                "msg": message,
                "attachments": attachments,
                "defaultFooterHide": default_footer,
                "verify": verify
            }

            if cc:
                body['cc'] = cc
            if bcc:
                body['bcc'] = bcc
            if reply_to:
                body['replyTo'] = reply_to
            if user_name:
                body["username"] = user_name

            url = f"{self.base_url}/rest/v13/{business_tag}/send/email"
            response = self.session.post(url, json=body)
            response.raise_for_status()  # Raise an exception for HTTP errors

            resp = response.json()
            if resp.get('error') is False:
                self.logger.info(f"Email sent successfully.")
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
