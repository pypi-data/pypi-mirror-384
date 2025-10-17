import mimetypes
import os
import requests


class Files:
    def __init__(self, session, logger, base_url, workspace_instance):
        self.session = session
        self.logger = logger
        self.base_url = base_url
        self.workspace_instance = workspace_instance

    def get_file_upload_element(self, absolute_file_path: str = None, file_url: str = None):
        """
        Generate file upload metadata for either a local file or a remote file accessed via URL.

        This function creates a dictionary containing metadata about a file, either from a local
        file path or a remote URL. It includes information such as file name, extension, size,
        MIME type, and other attributes useful for file uploads.

        :param absolute_file_path: The absolute path to a local file.
        :param file_url: A URL pointing to a remote file.
        :return: A list containing a single dictionary with file metadata.
        """
        if not absolute_file_path and not file_url:
            raise ValueError("Either absolute_file_path or file_url must be provided.")

        if absolute_file_path:
            if not os.path.exists(absolute_file_path):
                raise FileNotFoundError(f"The file {absolute_file_path} does not exist.")

            file_size = os.path.getsize(absolute_file_path)
            file_name = os.path.basename(absolute_file_path)
            file_ext = os.path.splitext(file_name)[1][1:]  # Remove the leading dot
            mime_type, _ = mimetypes.guess_type(absolute_file_path, strict=True)
            media = absolute_file_path
        elif file_url:
            try:
                response = requests.get(file_url.replace(self.workspace_instance['BUSINESS_URL'], self.base_url))
                response.raise_for_status()
                file_content = response.content
                file_size = len(file_content)
                file_name = os.path.basename(file_url)
                file_ext = os.path.splitext(file_name)[1][1:]  # Remove the leading dot
                mime_type, _ = mimetypes.guess_type(file_url, strict=True)
                media = file_url.replace(self.base_url, self.workspace_instance['BUSINESS_URL'])
            except requests.RequestException as e:
                raise requests.RequestException(f"Error fetching remote file: {e}")

        return [{
            "media_name": file_name,
            "media_ext": file_ext,
            "media_size": file_size,
            "media_type": mime_type or "application/octet-stream",
            "media": media,
            "media_compressed": True,
            "media_caption": ""
        }]

    def upload_file(self, filename: str, filepath: str):
        """
        Upload a file to the server.

        :param filename: The name of the file to be uploaded.
        :param filepath: The local path of the file to be uploaded.
        :return: The server's response as a dictionary.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"The file {filepath} does not exist.")
        try:
            with open(filepath, 'rb') as file:
                files = {'file': (filename, file)}
                url = f"{self.base_url}/rest/v17/{self.workspace_instance['BUSINESS_TAG_ID']}/{self.workspace_instance['BUSINESS_TAG_ID']}/fileupload/"

                if 'content-type' in self.session.headers or "Content-type" in self.session.headers:
                    del self.session.headers["Content-type"]
                response = self.session.post(url, files=files)
                response.raise_for_status()  # Raise an exception for HTTP errors

                resp = response.json()
                if not resp.get('error', True):
                    self.logger.info(f"Successfully uploaded file: {filename}")
                else:
                    raise ValueError(resp.get('message', 'Unknown error occurred during file upload'))
                return resp["data"]["file_url"]

        except requests.exceptions.RequestException as http_err:
            error_response = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            status_code = error_response.get('statusCode', response.status_code)
            error_message = error_response.get('message', str(http_err))

            error_message = f"{status_code} Error: {error_message}"
            self.logger.error(f"An error occurred during file upload: {error_message}")
            raise requests.exceptions.RequestException(error_message)

        except Exception as e:
            self.logger.error(f"Unexpected error during file upload: {str(e)}")
            raise