import os
import requests
import redis
import time

from ..utility.passwords import password_encrypt_sha512



class Auth:


    def __init__(self, session, logger, base_url, workspace_instance):
        self.session = session
        self.logger = logger
        self.base_url = base_url
        self.workspace_instance = workspace_instance
        self.user_instance = None
        self.MAX_RETRIES = 4     # 1 instant, 3 retries with 2s delay (adds 6s)
        self.RETRY_DELAY_SECONDS = 2


    def get_token_with_retry(self, key):
        for attempt in range(self.MAX_RETRIES+1):
            try:
                # Connect to Redis (localhost, default port 6379)
                redis_host = os.environ.get('REDIS_HOST', 'localhost')
                redis_port = int(os.environ.get('REDIS_PORT', 6379))

                # Create a Redis client
                redis_instance = redis.Redis(host=redis_host, port=redis_port, db=0)

                # Attempt to get the token from Redis
                token_data = redis_instance.get(key)
                if token_data:
                    return token_data

                self.logger.warning(f"Token not found in Redis for key {key}, attempt {attempt + 1}/{self.MAX_RETRIES}")

                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY_SECONDS)

            except Exception as e:
                self.logger.error(f"Error fetching token for key {key}, attempt {attempt + 1}/{self.MAX_RETRIES}. Error: {str(e)}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY_SECONDS)

        raise Exception(f'Login Token Retrieval Failed after {self.MAX_RETRIES} attempts')

    def login(self, email: str, password: str):
        """Authenticate a user and store their auth token."""
        response = None
        try: 
            # Step 1: Check if the login token is already cached in Redis
            cached_token = self.get_token_with_retry("{}-SuperAdminToken".format(self.workspace_instance['BUSINESS_DOMAIN']))
            if cached_token:
                self.logger.info(f"Using cached token for key {cached_token}")
            else:
                self.logger.info("No cached token found, proceeding with normal user login")
                
                # If no cached token, proceed with normal login
                if not email or not password:
                    raise ValueError("Email and Password are required to login")

                # Prepare the login request
                url = f"{self.base_url}/rest/v17/user/login"
                
                headers = {
                    'Content-Type': 'application/json',
                    'jwt': 'true',
                    'businessDomain': self.workspace_instance['BUSINESS_DOMAIN'],
                    'businessTagId': self.workspace_instance['BUSINESS_TAG_ID'],
                }

                sha512pwd = password_encrypt_sha512(password)
                data = {'email': email, 'password': sha512pwd}
                            
                self.logger.info(f"Logging in user {email} to workspace {self.workspace_instance['BUSINESS_DOMAIN']}")
                
                # Step 2: Send the login request
                response = self.session.post(url, json=data, headers=headers)
                response.raise_for_status()  # Raise an exception for HTTP errors
            
                resp = response.json()
                if resp.get('error') is False:
                    cached_token = resp['loginToken']
                    self.user_instance = resp
                else:
                    raise ValueError(resp.get('message'))
                

            # Step 3: Store the token in Redis
            headers = {
                'Authorization': f"Bearer {cached_token}",
                'businessDomain': self.workspace_instance['BUSINESS_DOMAIN'],
                'jwt': cached_token,
                'Content-type': 'application/json;charset=UTF-8',
                "device": 'script',
                'businessTagID': self.workspace_instance['BUSINESS_TAG_ID']
            }

            self.session.headers.update(headers)            
            self.logger.info(f"User {email} logged in")
            return {"error": False, "message": "User logged in successfully", "data": self.user_instance}
        
        except requests.exceptions.RequestException as http_err:
            if isinstance(http_err, requests.exceptions.HTTPError) and http_err.response is not None:
                try:
                    error_response = http_err.response.json()
                    status_code = http_err.response.status_code
                    error_message = error_response.get('message', http_err.response.text)
                except ValueError:
                    # Response body is not JSON
                    status_code = http_err.response.status_code
                    error_message = http_err.response.text
            else:
                status_code = 500
                error_message = str(http_err)

            error_message = f"{status_code} Error: {error_message}"
            self.logger.error(f"An error occurred in login(): {error_message}")
            raise requests.exceptions.HTTPError(error_message)      

        except Exception as e:
            self.logger.error(f"An unexpected error occurred in login(): {e}")
            raise e
