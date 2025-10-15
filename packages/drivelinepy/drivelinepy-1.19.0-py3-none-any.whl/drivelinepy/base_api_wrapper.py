#=================================================================
# Author: Garrett York
# Date: 2023/11/29
# Description: Boiler plate code for API wrapper
#=================================================================

import requests
import logging
from datetime import datetime
import time
from urllib.parse import urljoin,urlparse
import re

class BaseAPIWrapper():

    #-----------------------------------------------------------------
    # Constructor
    #-----------------------------------------------------------------
    def __init__(self, base_url, auth_url=None):
        self.base_url = base_url
        self.auth_url = auth_url
        self.logger = logging.getLogger(__name__)

    #-----------------------------------------------------------------
    # Method - Construct URL
    #-----------------------------------------------------------------

    def _url(self, path, is_auth=False):
        """Construct URL from base/auth url and path."""
        if is_auth:
            url = urljoin(self.auth_url, path)
        else:
            url = urljoin(self.base_url, path)
        
        self.logger.info(f"Constructed URL: {url}")
        return url
    
    #-----------------------------------------------------------------
    # Method - Prepare Parameters
    #-----------------------------------------------------------------

    def _prepare_params(self, base_params, additional_params=None):
        """
        Prepares and merges base parameters with additional parameters.

        :param base_params: A dictionary of base parameters common to all API requests.
        :param additional_params: A dictionary of additional parameters specific to a particular API request.
        :return: A merged dictionary of parameters with none values filtered out.
        """
        self.logger.info(f"Entering _prepare_params() with base parameters: {base_params}")

        if base_params is None:
                base_params = {}
        params = base_params.copy()

        if additional_params is not None:
            params.update(additional_params)  # Merges additional parameters

        # Filtering out None values
        filtered_params = {k: v for k, v in params.items() if v is not None}

        self.logger.debug("Exiting _prepare_params()")
        return filtered_params

    
    #-----------------------------------------------------------------
    # Method - Send Request
    #-----------------------------------------------------------------

    def _send_request(self, method, path, params=None, data=None, headers=None, is_auth=False, files=None, json=None):
        """Send a request to the API."""
        url = self._url(path, is_auth=is_auth)

        # Prepare the keyword arguments for the request method.
        request_kwargs = {
            'params': params,
            'headers': headers,
            'data': data,
            'files': files,
            'json': json
        }

        # Make sure not to send 'None' values
        request_kwargs = {k: v for k, v in request_kwargs.items() if v is not None}

        try:
            # Make a single request with the conditional arguments.
            response = requests.request(method, url, **request_kwargs)
            
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as err:
            self.logger.error(f'HTTP error occurred: {err}')
        except requests.exceptions.RequestException as req_err:
            self.logger.error(f'Request error: {req_err}')
        except Exception as err:
            self.logger.error(f'An unexpected error occurred: {err}')
        return None
    
    #-----------------------------------------------------------------
    # Method - HTTP Functions
    #-----------------------------------------------------------------

    def get(self, path, params=None, headers=None):
        """GET request."""
        return self._send_request('GET', path, params=params, headers=headers)

    def post(self, path, data=None, headers=None, is_auth=False, files=None, json=None):
        """POST request."""
        return self._send_request('POST', path, data=data, headers=headers, is_auth=is_auth, files=files, json=json)

    def put(self, path, data=None, headers=None, json=None):
        """PUT request."""
        return self._send_request('PUT', path, data=data, headers=headers, json=json)

    def options(self, path, headers=None):
        """OPTIONS request."""
        return self._send_request('OPTIONS', path, headers=headers)

    def delete(self, path, headers=None):
        """DELETE request."""
        return self._send_request('DELETE', path, headers=headers)
    
    #-----------------------------------------------------------------
    # Method - Convert Date to Timestamp
    #-----------------------------------------------------------------
    
    def convert_yyyy_mm_dd_to_timestamp(self, date_str, is_end_date=False):
        """
        Convert a date string to a Unix timestamp.

        :param date_str: Date string in 'YYYY-MM-DD' format.
        :param is_end_date: Boolean indicating whether the date is an end date.
                            If True, it will set the time to the end of the day.
        :return: Unix timestamp corresponding to the provided date.
        """
        self.logger.info(f'Entering convert_yyyy_mm_dd_to_timestamp() for date {date_str}')

        if is_end_date:
            date_time_str = date_str + " 23:59:59.999999"
        else:
            date_time_str = date_str + " 00:00:00.000000"
        
        # Converting to datetime object
        date_time_obj = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S.%f')
        # Converting to Unix timestamp
        timestamp = time.mktime(date_time_obj.timetuple())
        self.logger.info("Exiting convert_yyyy_mm_dd_to_timestamp()")
        return timestamp
    
    #-----------------------------------------------------------------
    # Method - Validate Date Format
    #-----------------------------------------------------------------
    
    def validate_date_yyyy_mm_dd(self, date_str):
        """
        Validate a date string in 'YYYY-MM-DD' format.

        :param date_str: Date string in 'YYYY-MM-DD' format.
        :return: Boolean indicating whether the date string is valid.
        """
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            self.logger.info(f"Date string is valid: {date_str}. Exiting validate_date_yyyy_mm_dd()")
            return True
        except ValueError:
            self.logger.error(f"Incorrect data format for date string '{date_str}', should be YYYY-MM-DD. Exiting validate_date_yyyy_mm_dd()")
            return False
        
    def validate_email(self, email):
        """
        Validates that the provided string is a valid email format.

        :param email: The email address to be validated.
        :return: Boolean indicating whether the email is valid.
        """
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(email_regex, email):
            self.logger.info(f"Email address {email} is valid.")
            return True
        else:
            self.logger.error(f"Invalid email address: {email}.")
            return False
        
    def validate_url(self, url, required_scheme='https'):
        """
        Validates that the given string is a valid URL.
        
        :param url: The URL string to validate.
        :param required_scheme: The required URL scheme (default is 'https').
        :return: Boolean indicating whether the URL is valid.
        """
        if not isinstance(url, str):
            self.logger.error(f"Invalid URL: {url}. It must be a string.")
            return False

        try:
            result = urlparse(url)
            is_valid = all([result.scheme, result.netloc])
            is_https = result.scheme == required_scheme
            
            if is_valid and is_https:
                self.logger.info(f"URL is valid: {url}")
                return True
            elif is_valid and not is_https:
                self.logger.error(f"Invalid URL scheme: {url}. It must use {required_scheme}://")
                return False
            else:
                self.logger.error(f"Invalid URL format: {url}")
                return False
        except Exception as e:
            self.logger.error(f"Error validating URL {url}: {str(e)}")
            return False