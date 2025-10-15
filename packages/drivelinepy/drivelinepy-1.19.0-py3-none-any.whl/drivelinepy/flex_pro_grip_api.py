#=================================================================
# Description: Updated FlexProGrip API implementation that handles list response
#=================================================================

from .base_api_wrapper import BaseAPIWrapper
from datetime import datetime, timedelta

class FlexProGripAPI(BaseAPIWrapper):
    """
    API wrapper for FlexProGrip
    """

    #-----------------------------------------------------------------
    # Constructor
    #-----------------------------------------------------------------

    def __init__(self, api_key, base_url="https://flexprogrip.gigalixirapp.com/api/"):
        super().__init__(base_url)
        self.api_key = api_key
        # Use 'api-key' header as shown in the Postman screenshot
        self.headers = {
            "api-key": api_key,
            "Content-Type": "application/json"
        }
        self.logger.info(f"FlexProGripAPI initialized with API key: {api_key[:4]}...")

    #-----------------------------------------------------------------
    # Method - Get Histories
    #-----------------------------------------------------------------

    def get_histories(self, start_date=None, end_date=None):
        """
        Fetches histories data from the FlexProGrip API.
        
        :param start_date: Start date in YYYY-MM-DD format
        :param end_date: End date in YYYY-MM-DD format
        :return: The response from the API (can be a list or dict)
        """
        self.logger.info(f"Entering get_histories(start_date={start_date}, end_date={end_date})")

        # Validate dates if provided
        if start_date and not self.validate_date_yyyy_mm_dd(start_date):
            error_msg = f"Invalid start_date format: {start_date}. Expected format: YYYY-MM-DD."
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        if end_date and not self.validate_date_yyyy_mm_dd(end_date):
            error_msg = f"Invalid end_date format: {end_date}. Expected format: YYYY-MM-DD."
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        endpoint = "histories"
        params = {}

        if start_date:
            params['start_date'] = start_date
        
        if end_date:
            params['end_date'] = end_date

        # Log the headers being used (omitting the actual API key for security)
        self.logger.info(f"Using headers: {{{', '.join(f'{k}: [REDACTED]' if k=='api-key' else f'{k}: {v}' for k, v in self.headers.items())}}}")
        
        response = self.get(endpoint, params=params, headers=self.headers)

        # If the request failed, provide more detailed error information
        if response is None:
            error_msg = "Failed to get histories: No response received from API."
            self.logger.error(error_msg)
            raise Exception(error_msg)
        
        # Debug response status and headers
        self.logger.info(f"Response status code: {response.status_code}")
        
        try:
            response_json = response.json()
        except ValueError as e:
            error_msg = f"Failed to parse JSON response: {e}. Response content: {response.text}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

        if response.status_code != 200:
            error_msg = (f"Failed to get histories. "
                       f"Status Code: {response.status_code}, Response: {response.text}")
            self.logger.error(error_msg)
            raise Exception(error_msg)

        # Determine if response is a list or dict with 'data' key
        if isinstance(response_json, list):
            record_count = len(response_json)
            self.logger.info(f"Successfully fetched {record_count} history records (list format).")
        elif isinstance(response_json, dict) and 'data' in response_json:
            record_count = len(response_json.get('data', []))
            self.logger.info(f"Successfully fetched {record_count} history records (dict format).")
        else:
            self.logger.info(f"Received response in unexpected format: {type(response_json)}")
            
        self.logger.info("Exiting get_histories()")
        return response_json