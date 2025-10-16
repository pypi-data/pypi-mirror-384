import requests


class Workspace:
    def __init__(self, session, logger, base_url):
        self.session = session
        self.logger = logger
        self.base_url = base_url
        self.workspace_instance = None
    
    def init(self, domain):
        """Set the domain for the workspace."""
        try:
            if not domain:
                raise ValueError("Domain is required to initialize the workspace")
            self.session.headers.update({'domain': domain})
            # Fetch workspace details from domain.
            url = f"{self.base_url}/rest/v17/organisation/web/config/{domain}"
            response = self.session.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors

            resp = response.json()
            if resp.get('error') is False:
                self.workspace_instance = resp['data']
                self.logger.info(f"Workspace initialized: {domain}")
            else:
                raise ValueError(resp.get('message'))

            # Additional API call to fetch configuration details
            url = f"{self.base_url}/config.json"
            response = self.session.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors
            config_resp = response.json()

            # Update self.workspace_instance dict with the config response
            if isinstance(self.workspace_instance, dict):
                self.workspace_instance.update(config_resp)
            else:
                self.workspace_instance = config_resp

            # Create BUSINESS_URL from PROTOCOL and HOST, removing any path after the domain.
            protocol = config_resp.get('PROTOCOL', '')
            host = config_resp.get('HOST', '')
            # Split on '/' and take the first part to remove any trailing paths (like '/rest').
            base_host = host.split('/')[0]
            business_url = f"{protocol}{base_host}"

            # Add BUSINESS_URL to workspace_instance dictionary
            self.workspace_instance['BUSINESS_URL'] = business_url

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

