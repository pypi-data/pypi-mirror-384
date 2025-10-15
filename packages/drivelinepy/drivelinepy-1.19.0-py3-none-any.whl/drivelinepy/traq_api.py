# ================================================================================
# Author: Garrett York
# Date: 2024/01/31
# Description: Class for TRAQ API
# ================================================================================

from .base_api_wrapper import BaseAPIWrapper
from urllib.parse import urlencode
import json
import os


class TRAQAPI(BaseAPIWrapper):

    DRIVELINE_FACILITY_ID = 1

    # 0 = Inactive, 1 = On-Site, 2 = Remote, 3 = Active, 4 = Archived
    VALID_STATUS_CODES = [0, 1, 2, 3, 4]

    # 0 = Inactive, 1 = On-Site, 2 = Remote, 3 = Active, 4 = Archived
    VALID_PROGRAM_CODES = [-1, 0, 1, 2, 3, 4, 7, 99, 230, 238]

    # 0 = No Sub-Status, 217 = No Facility, 31 = AZ, 215 = WA
    VALID_SUBSTATUS_CODES = [0, 217, 31, 215, 282]

    # 0-Pitching, 1-Hitting
    VALID_TRAINING_TRACKS = [0, 1]

    # Recommended maximum file size for uploads (in MB)
    # Files larger than this may take a long time or timeout
    RECOMMENDED_MAX_FILE_SIZE_MB = 200


    # ---------------------------------------------------------------------------
    # Constructor
    # ---------------------------------------------------------------------------

    def __init__(self, client_id, client_secret, auth_url="https://traq.drivelinebaseball.com",
                 base_url="https://traq.drivelinebaseball.com/"):

        super().__init__(base_url)
        self.auth_url = auth_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.authenticate()

    # ---------------------------------------------------------------------------
    # Method - Authenticate
    # ---------------------------------------------------------------------------

    def authenticate(self):
        """
        Authenticates with the TRAQ API and sets the access token.
        """
        self.logger.info("Entering TRAQ API authenticate()")
        path = "oauth/token"
        payload = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': '*'
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = self.post(path=path, data=payload, headers=headers, is_auth=True)
        response = response.json() if response is not None else None

        if response:
            self.access_token = response.get('access_token')
            self.logger.info("Authentication successful")
        else:
            self.logger.error("Authentication failed")

        self.logger.info("Exiting authenticate()")

    #---------------------------------------------------------------------------
    # Method - Get Users
    # ---------------------------------------------------------------------------

    def get_users(self, traq_id=None, email=None, status_code=None, substatus_code=None, facility_id=None, include_crm_url=False):
        """
        Retrieves user information from the TRAQ API. Prioritizes TRAQ ID over email and status code.

        :param traq_id: TRAQ ID to filter users (optional).
        :param email: Email address to filter users (optional).
        :param status_code: Status code (int) to filter users (optional).
        :param facility_id: Facility ID to filter users (optional).
        :param substatus_code: Substatus code (int) to filter users (optional).
        :param include_crm_url: Boolean to include CRM profile URL (optional).

        :return: User information or list of users.
        """
        self.logger.debug("Entering get_users()")

        endpoint = "api/v1.1/users"
        headers = {'Authorization': f'Bearer {self.access_token}'}
        params = {}

        # Check for facility filter
        if facility_id:
            if self.validate_facility_id(facility_id):
                params['facility_id'] = facility_id
            else:
                return None
        else:
            # if email and traq_id are not provided, warn the user that a facility ID filter is recommended
            if not traq_id and not email:
                self.logger.warning("Facility ID filter was not provided. It is highly recommended to provide a facility ID to avoid large data sets if not pinged by email or TRAQ ID.")

        # Check for unique identifyier filter
        if traq_id:
            if self.validate_traq_id(traq_id):
                params = {'id': traq_id}
            else:
                return None
        elif email:
            if self.validate_email(email):
                params = {'email': email}
            else:
                return None
        else:
            self.logger.error("Neither TRAQ ID or Email provided")

        # Add status_code to params if provided
        if status_code:
            if self.validate_traq_user_status_code(status_code):
                params = {"active": status_code}
            else:
                return None
        else:
            self.logger.debug("Status code filter was not provided")
        
        # Add substatus_code to params if provided -- traq naming convention is a bit wonky here because "status" is actually the substatus_code
        if substatus_code:
            if self.validate_traq_user_substatus_code(substatus_code):
                params['status'] = substatus_code
            else:
                return None
        else:
            self.logger.debug("Substatus code filter was not provided")

        if not params:
            self.logger.debug("No valid filters provided.")
            return None

        response = self.get(endpoint, params=params, headers=headers)
        response = response.json() if response is not None else None

        if response and include_crm_url:
            users_data = response.get('data', [])
            for user in users_data:
                user_id = user.get('id')
                user_facility_id = user.get('facility_id')
                if user_id and self.validate_traq_id(user_id) and user_facility_id == self.DRIVELINE_FACILITY_ID:
                    crm_url = self.get_crm_profile_url(user_id, self.DRIVELINE_FACILITY_ID)
                    if crm_url:
                        user['crm_profile_url'] = crm_url
                else:
                    self.logger.info(f"User {user_id} does not have a valid TRAQ ID or facility ID. Skipping CRM profile URL retrieval.")

        self.logger.debug("Exiting get_users()")
        return response.get('data') if response else None
    
    #---------------------------------------------------------------------------
    # Method - Get CRM Profile URL
    #---------------------------------------------------------------------------

    def get_crm_profile_url(self, user_id, organization_id):
        """
        Retrieves the CRM profile URL for a specific user from the athlete-association-info API.

        :param user_id: TRAQ ID of the user.
        :param organization_id: Organization ID (facility ID).
        :return: CRM profile URL if available, None otherwise.
        """
        endpoint = "api/v1.1/athlete-association-info"
        headers = {'Authorization': f'Bearer {self.access_token}'}
        params = {
            'user_id': user_id,
            'organization_id': organization_id
        }

        response = self.get(endpoint, params=params, headers=headers)
        if response and response.status_code == 200:
            data = response.json()
            athlete_data = data.get('athlete_data', [])
            if athlete_data:
                return athlete_data[0].get('crm_profile_url')
        return None

    #---------------------------------------------------------------------------
    # Method - Get Workouts
    #---------------------------------------------------------------------------

    def get_workouts(self, program):
        """
        Retrieves workouts information from the TRAQ API.

        :param program: Program ID to filter workouts (optional).
        :return: Workouts information or list of workouts.
        """
        self.logger.debug("Entering get_workouts()")

        endpoint = "api/v1.1/list-workouts"
        headers = {'Authorization': f'Bearer {self.access_token}'}
        if self.validate_traq_program(program):
            params = {"program": program}
        else:
            return None  # Invalid program - logging done in validate_traq_program

        response = self.get(endpoint, params=params, headers=headers)
        response = response.json() if response is not None else None

        self.logger.debug("Exiting get_workouts()")
        return response.get('data') if response else None

    #---------------------------------------------------------------------------
    # Method - Get Workouts by Athlete
    #---------------------------------------------------------------------------

    def get_athlete_workouts(self, traq_id, start_date, end_date):
        """
        Retrieves workouts information from the TRAQ API.

        :param traq_id: TRAQ ID to filter users.
        :param start_date: Starting date range to filter workouts.
        :param end_date: Ending date range to filter workouts.
        :return: Workouts filtered by athlete and date information or list of workouts.
        """
        self.logger.debug("Entering get_athlete_workouts()")

        endpoint = "api/v1.1/athlete-workout"
        headers = {'Authorization': f'Bearer {self.access_token}'}
        params = {}
        if self.validate_traq_id(traq_id) and self.validate_date_yyyy_mm_dd(
                start_date) and self.validate_date_yyyy_mm_dd(end_date):
            params = {"start_date": start_date, "end_date": end_date, "user_id": traq_id}
        else:
            return None  # Invalid params - logging done in validation methods
        response = self.get(endpoint, params=params, headers=headers)
        response = response.json() if response is not None else None
        self.logger.debug("Exiting get_athlete_workouts()")

        return response.get('data') if response else None
    
    #---------------------------------------------------------------------------
    # Method - Update Athlete Organization
    #---------------------------------------------------------------------------

    def update_athlete_organization(self, traq_id, facility_id, crm_profile_url=None, program_id=None,
                status_id=None, sub_status_id=None, level_id=None, trainer_id=None):
        """
        Update user information in the TRAQ system.
        The crm_profile_url can only be updated if the user's facility_id is 1.

        :param traq_id: TRAQ ID of the user to update.
        :param facility_id: Facility ID of the user.
        :param crm_profile_url: CRM profile URL to update (optional).
        :return: Updated user data if successful.
        :raises ValueError: If input validation fails.
        :raises Exception: If API request fails or returns unexpected response.
        """
        self.logger.info(f"Attempting to update user. TRAQ ID: {traq_id}, Facility ID: {facility_id}")
        endpoint = "api/v1.1/update-athlete-organization"
        

        # Validate TRAQ ID
        if not self.validate_traq_id(traq_id):
            raise ValueError("Invalid traq_id. Must be a positive integer between 1 and 999999.")

        # Validate Facility ID
        if not self.validate_facility_id(facility_id):
            raise ValueError("Invalid facility_id. Must be a positive integer.")

        # Prepare the update payload
        payload = {
            'user_id': traq_id,
            'organization_id': facility_id
        }

        # Handle crm_profile_url update
        if crm_profile_url is not None:
            if facility_id != self.DRIVELINE_FACILITY_ID:
                raise ValueError("crm_profile_url can only be updated for users with facility_id 1.")
            if not self.validate_url(crm_profile_url):
                raise ValueError("Invalid crm_profile_url. Not a valid URL")
            payload['crm_profile_url'] = crm_profile_url

        # Add program_id, status_id, sub_status_id, level_id, trainer_id to payload if provided
        if program_id is not None:
            if not self.validate_traq_program(program_id):
                raise ValueError("Invalid program_id. Possible options: " + ", ".join(map(str, self.VALID_PROGRAM_CODES)) + ".")
            payload['program_id'] = str(program_id)

        if status_id is not None:
            if not self.validate_traq_user_status_code(status_id):
                raise ValueError("Invalid status_id. Must be an integer between 0 and 4.")
            payload['status_id'] = str(status_id)

        if sub_status_id is not None:
            if not self.validate_traq_user_substatus_code(sub_status_id):
                raise ValueError("Invalid sub_status_id. Possible options: " + ", ".join(map(str, self.VALID_STATUS_CODES)) + ".")
            payload['sub_status_id'] = str(sub_status_id)

        if level_id is not None:
            payload['level_id'] = str(level_id)

        if trainer_id is not None:
                payload['trainer_id'] = [str(trainer_id)]

        # Prepare the API request
        headers = {'Authorization': f'Bearer {self.access_token}'}

        # Send the update request
        try:
            self.logger.info(f"Sending update request to TRAQ API. Endpoint: {endpoint}")
            update_response = self.post(endpoint, data=payload, headers=headers)
            
            if update_response is None:
                raise Exception("Failed to connect to the TRAQ API. Please check your network connection.")

            if update_response.status_code != 200:
                error_message = f"Failed to update user. Status code: {update_response.status_code}"
                try:
                    error_details = update_response.json()
                    error_message += f". Details: {error_details}"
                except ValueError:
                    error_message += f". Response: {update_response.text}"
                self.logger.error(error_message)
                raise Exception(error_message)

            updated_data = update_response.json().get('data')
            if not updated_data:
                raise Exception("Update successful, but no data returned.")
            
            self.logger.info(f"User updated successfully. TRAQ ID: {traq_id}")
            return updated_data

        except Exception as e:
            self.logger.error(f"Error updating user: {str(e)}")
            raise


    #---------------------------------------------------------------------------
    # Method - Get Smart Report Data
    #---------------------------------------------------------------------------    

    def get_smart_report_data(self, traq_id, start_date, end_date, training_track):
        """
        Retrieves smart report data from the TRAQ API.

        :param traq_id: TRAQ ID to filter users.
        :param start_date: Starting date range to filter report data.
        :param end_date: Ending date range to filter report data.
        :param report_type: Type of report to retrieve (default=1).
        :return: Smart report data if successful, None otherwise.
        """
        self.logger.debug("Entering get_smart_report_data()")

        endpoint = "api/v1.1/report/smartreport-data"
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        # Validate input parameters
        valid_traq_id = self.validate_traq_id(traq_id)
        valid_start_date = self.validate_date_yyyy_mm_dd(start_date) 
        valid_end_date = self.validate_date_yyyy_mm_dd(end_date)
        valid_training_track = self.validate_training_track(training_track)

        if not all([valid_traq_id, valid_start_date, valid_end_date, valid_training_track]):
            return None

        params = {
            "user_id": traq_id,
            "begin_date": start_date,
            "end_date": end_date,
            "type": training_track
        }

        response = self.get(endpoint, params=params, headers=headers)
        response = response.json() if response is not None else None

        self.logger.debug("Exiting get_smart_report_data()")
        return response.get('data') if response else None
    
    #---------------------------------------------------------------------------
    # Method - Post Smart Report Data
    #---------------------------------------------------------------------------
    
    def post_smart_report_data(self, traq_id, report_date, training_track, report_data):
        """
        Posts smart report data to the TRAQ API.

        :param traq_id: TRAQ ID of the user.
        :param report_date: Date of the report (YYYY-MM-DD).
        :param training_track: Type of training (0=Pitching, 1=Hitting).
        :param report_data: Dictionary containing the report data metrics.
        :return: API response data if successful, None otherwise.
        """
        self.logger.debug("Entering post_smart_report_data()")

        endpoint = "api/v1.1/report/smartreport-data"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        # Validate input parameters
        if not all([
            self.validate_traq_id(traq_id),
            self.validate_date_yyyy_mm_dd(report_date),
            self.validate_training_track(training_track)
        ]):
            return None
        
        # check if report_data is a dictionary
        if not isinstance(report_data, dict):
            raise ValueError("report_data must be a dictionary.")

        # Prepare payload
        payload = {
            'user_id': traq_id,
            'date': report_date,
            'type': training_track,
            'data': json.dumps(report_data)
        }

        # URL-encode the payload    
        encoded_payload = urlencode(payload)

        response = self.post(endpoint, data=encoded_payload, headers=headers)
        response = response.json() if response is not None else None

        # Check for success in the response
        if response and response.get('success'):
            self.logger.info("Post successful: " + response.get('message', ''))
            self.logger.debug("Exiting post_smart_report_data()")
            return response
        else:
            self.logger.error("Post failed or no data returned.")
            self.logger.debug("Exiting post_smart_report_data()")
            return None

    #---------------------------------------------------------------------------
    # Method - Query
    #---------------------------------------------------------------------------

    def query(self, sql_query):
        """
        Executes a SQL query against the TRAQ API.

        :param sql_query: The SQL query string to be executed.
        :return: The result of the SQL query if successful, None otherwise.
        """
        self.logger.debug("Entering query()")

        endpoint = "api/v1.1/service/sql-query"
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        data = {'query': sql_query}

        response = self.post(endpoint, data=data, headers=headers)
        response = response.json() if response is not None else None

        # Check for success in the response
        if response and response.get('success'):
            self.logger.info("Query executed successfully: " + response.get('message', ''))
            self.logger.debug("Exiting query()")
            return response.get('data')
        else:
            self.logger.error("Query execution failed or no data returned.")
            self.logger.debug("Exiting query()")
            return None

    #---------------------------------------------------------------------------
    # Method - Post Media
    #---------------------------------------------------------------------------

    def post_media(self, user_id, tab_id, name, file_path, max_file_size_mb=None):
        """
        Uploads media file to TRAQ for a specific athlete using streaming.

        This method streams the file directly from disk without loading it entirely
        into memory, making it safe for large file uploads.

        :param user_id: Athlete ID (integer) - Can be seen in URL on athlete profile.
        :param tab_id: Tab ID (integer) - Default tab id is 6050; Miscellaneous tab id is "miscellaneous".
        :param name: Name of file without extension (string).
        :param file_path: Path to the file to be uploaded (string).
        :param max_file_size_mb: Optional maximum file size in MB. If specified, files larger than
                                 this limit will raise a ValueError. Default is None (no limit).
        :return: API response data if successful, None otherwise.
        :raises ValueError: If input validation fails or file exceeds size limit.
        :raises FileNotFoundError: If the specified file does not exist.
        """
        self.logger.info(f"Attempting to add media. User ID: {user_id}, Tab ID: {tab_id}, Name: {name}")

        # Validate user_id (using existing TRAQ ID validation)
        if not self.validate_traq_id(user_id):
            raise ValueError("Invalid user_id. Must be a positive integer between 1 and 999999.")

        # Validate tab_id - can be integer or "miscellaneous"
        if not (isinstance(tab_id, int) or (isinstance(tab_id, str) and tab_id.lower() == "miscellaneous")):
            raise ValueError("Invalid tab_id. Must be an integer or 'miscellaneous'.")

        # Validate name
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Invalid name. Must be a non-empty string.")

        # Validate file exists (os is already imported at module level)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if not os.path.isfile(file_path):
            raise ValueError(f"Path is not a file: {file_path}")

        # Check file size if limit is specified
        if max_file_size_mb is not None:
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > max_file_size_mb:
                raise ValueError(f"File size ({file_size_mb:.2f} MB) exceeds maximum allowed size ({max_file_size_mb} MB)")
            self.logger.info(f"File size: {file_size_mb:.2f} MB (within {max_file_size_mb} MB limit)")

        # Prepare the endpoint and headers
        endpoint = "api/v1.1/add-media"
        headers = {'Authorization': f'Bearer {self.access_token}'}

        # Prepare the payload
        payload = {
            'user_id': str(user_id),
            'tab_id': str(tab_id),
            'name': name
        }

        # Prepare the file for upload
        try:
            # Get file size for logging
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            self.logger.info(f"Preparing to upload file: {os.path.basename(file_path)} ({file_size_mb:.2f} MB)")

            # Determine mime type based on file extension
            file_extension = os.path.splitext(file_path)[1].lower()
            mime_types = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.mp4': 'video/mp4',
                '.mov': 'video/quicktime',
                '.avi': 'video/x-msvideo',
                '.pdf': 'application/pdf',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.xls': 'application/vnd.ms-excel',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.ppt': 'application/vnd.ms-powerpoint',
                '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                '.zip': 'application/zip',
                '.txt': 'text/plain',
                '.csv': 'text/csv'
            }
            mime_type = mime_types.get(file_extension, 'application/octet-stream')
            self.logger.debug(f"File MIME type: {mime_type}")

            # Open the file and stream it for upload
            # The file handle is passed directly to requests, which will stream it
            with open(file_path, 'rb') as file:
                # Create files tuple with the open file handle
                # This ensures streaming instead of loading into memory
                files = [('file', (os.path.basename(file_path), file, mime_type))]

                # Send the request with streaming upload
                self.logger.info(f"Sending add-media request to TRAQ API. Endpoint: {endpoint}")
                self.logger.debug(f"Upload started for {file_size_mb:.2f} MB file")

                # The file will be streamed by requests library since we're passing the file handle
                response = self.post(endpoint, data=payload, headers=headers, files=files)

                if response is None:
                    error_msg = "Failed to connect to the TRAQ API. Please check your network connection."
                    self.logger.error(error_msg)
                    raise Exception(error_msg)

                # Log response time for large files
                self.logger.debug(f"Upload completed. Status code: {response.status_code}")

                if response.status_code != 200:
                    error_message = f"Failed to upload media. Status code: {response.status_code}"
                    try:
                        error_details = response.json()
                        error_message += f". Details: {error_details}"
                    except (ValueError, AttributeError):
                        # Use text if JSON parsing fails
                        error_text = getattr(response, 'text', 'No response text available')
                        error_message += f". Response: {error_text[:500]}"  # Limit error text length
                    self.logger.error(error_message)
                    raise Exception(error_message)

                # Parse response
                try:
                    response_data = response.json()
                except (ValueError, AttributeError) as e:
                    error_msg = f"Failed to parse API response as JSON: {str(e)}"
                    self.logger.error(error_msg)
                    raise Exception(error_msg)

                # Check for success in the response
                if response_data and response_data.get('success'):
                    self.logger.info(f"Media uploaded successfully for user {user_id}. File: {os.path.basename(file_path)} ({file_size_mb:.2f} MB)")
                    return response_data
                else:
                    error_message = f"Media upload failed: {response_data.get('message', 'Unknown error')}"
                    self.logger.error(error_message)
                    raise Exception(error_message)

        except FileNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error uploading media: {str(e)}")
            raise

    #---------------------------------------------------------------------------
    # Validation Methods
    #---------------------------------------------------------------------------

    def validate_facility_id(self, facility_id):
        """
        Validates that the facility id is an integer within the range of 1 to 999999.
        """
        if isinstance(facility_id, int):
            if 1 <= facility_id <= 999999:
                self.logger.info(f"Facility ID is valid: {facility_id}.")
                return True
            else:
                self.logger.error(f"Invalid Facility ID: {facility_id}. It must be a 1-6 digit integer within the range 1 to 999999.")
                return False
        else:
            self.logger.error(f"Invalid Facility ID: {facility_id}. It must be an integer.")
            return False
        

    def validate_training_track(self, training_track):
        """
        Validates that the training track is an int representing one of these possible options: 0, 1.
        If passed as string, attempts to convert to int first.
        """
        # First handle the case where input is a string
        if isinstance(training_track, str):
            error_message = f"Training track must be an integer (0 or 1), got '{training_track}'"
            self.logger.error(error_message)
            raise ValueError(error_message)

        # Now we know it's not a string, check if it's an int in valid range
        if isinstance(training_track, int) and training_track in self.VALID_TRAINING_TRACKS:
            self.logger.info(f"Training track is valid: {training_track}")
            return True
            
        error_message = f"Invalid training track: {training_track}. Possible options: {', '.join(map(str, self.VALID_TRAINING_TRACKS))}."
        self.logger.error(error_message)
        raise ValueError(error_message)

    def validate_traq_id(self, traq_id):
        """
        Validates that the TRAQ ID is an integer within the range of 1 to 999999.
        :param traq_id: The TRAQ ID to be validated.
        :return: Boolean indicating whether the ID is valid.
        """
        if isinstance(traq_id, int):
            if 1 <= traq_id <= 999999:
                self.logger.info(f"TRAQ ID is valid: {traq_id}.")
                return True
            else:
                self.logger.error(f"Invalid TRAQ ID: {traq_id}. It must be a 1-6 digit integer within the range 1 to 999999.")
                raise ValueError(f"Invalid TRAQ ID: {traq_id}. It must be a 1-6 digit integer within the range 1 to 999999.")
        else:
            self.logger.error(f"Invalid TRAQ ID: {traq_id}. It must be an integer.")
            raise ValueError(f"Invalid TRAQ ID: {traq_id}. It must be an integer.")

    def validate_traq_program(self, program):
        """
        Validates that the TRAQ program is an int representing one of these possible options: -1, 0, 1, 2, 3, 4.

        :param program: The TRAQ program number to be validated.
        :return: Boolean indicating whether the program is valid.
        """
        if isinstance(program, int) and program in self.VALID_PROGRAM_CODES:
            self.logger.info(f"TRAQ program is valid: {program}. Exiting validate_traq_program()")
            return True
        else:
            self.logger.error(f"Invalid TRAQ program name int: {program}. Possible options: " + ", ".join(map(str, self.VALID_PROGRAM_CODES)) + ".")
            raise ValueError(f"Invalid TRAQ program name int: {program}. Possible options: " + ", ".join(map(str, self.VALID_PROGRAM_CODES)) + ".")

    def validate_traq_user_status_code(self, status_code):
        """
        :param status_code: The TRAQ status_code number to be validated.
        :return: Boolean indicating whether the program is valid.
        """
        if isinstance(status_code, int) and status_code in self.VALID_STATUS_CODES:
            self.logger.info(f"TRAQ status_code int is valid: {status_code}. Exiting validate_traq_user_status_code()")
            return True
        else:
            self.logger.error(f"Invalid TRAQ status_code int: {status_code}. Possible options: " + ", ".join(map(str, self.VALID_STATUS_CODES)) + ".")
            raise ValueError(f"Invalid TRAQ status_code int: {status_code}. Possible options: " + ", ".join(map(str, self.VALID_STATUS_CODES)) + ".")
        

    def validate_traq_user_substatus_code(self, substatus_code):
        """
        :param substatus_code: The TRAQ substatus_code number to be validated.
        :return: Boolean indicating whether the program is valid.
        """
        if isinstance(substatus_code, int) and substatus_code in self.VALID_SUBSTATUS_CODES:
            self.logger.info(f"TRAQ substatus_code int is valid: {substatus_code}. Exiting validate_traq_user_substatus_code()")
            return True
        else:
            self.logger.error(f"Invalid TRAQ substatus_code int: {substatus_code}. Possible options: " + ", ".join(map(str, self.VALID_SUBSTATUS_CODES)) + ".")
            raise ValueError(f"Invalid TRAQ substatus_code int: {substatus_code}. Possible options: " + ", ".join(map(str, self.VALID_SUBSTATUS_CODES)) + ".")

    


