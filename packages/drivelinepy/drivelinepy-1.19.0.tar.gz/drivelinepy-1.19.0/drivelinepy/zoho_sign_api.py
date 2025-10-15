#=================================================================
# Author: Garrett York
# Date: 2024-11-26
# Description: Class for Zoho Sign API
#=================================================================

from .base_api_wrapper import BaseAPIWrapper
from datetime import datetime
import json
import urllib.parse

class ZohoSignAPI(BaseAPIWrapper):

    # request_name | folder_name | owner_full_name | recipient_email | form_name | created_time
    VALID_SORT_COLUMNS = ["request_name", "folder_name", "owner_full_name", "recipient_email", "form_name", "created_time"]

    VALID_SORT_ORDERS = ["ASC", "DESC"]
    
    #-----------------------------------------------------------------
    # Method - Constructor
    #-----------------------------------------------------------------

    def __init__(self, client_id, client_secret, refresh_token,
                 auth_url="https://accounts.zoho.com", 
                 base_url="https://sign.zoho.com/api/v1/",
                 redirect_uri="https://sign.zoho.com"):
        super().__init__(base_url)
        self.auth_url = auth_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.redirect_uri = redirect_uri
        self.time_of_last_refresh = None
        self.access_token = None
        self._refresh_access_token()

    #-----------------------------------------------------------------
    # Method - Get Headers
    #-----------------------------------------------------------------

    def _get_headers(self):
        self.logger.debug("Entering _get_headers()")
        if self.check_if_access_token_needs_refreshed():
            if not self._refresh_access_token():
                return None

        headers = {
            'Authorization': f'Zoho-oauthtoken {self.access_token}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        self.logger.info('Headers have been set!')
        self.logger.debug("Exiting _get_headers()")
        return headers
    
    #-----------------------------------------------------------------
    # Method - Refresh Access Token
    #-----------------------------------------------------------------

    def _refresh_access_token(self):
        """
        Refreshes the OAuth access token using the refresh token.
        
        :return: True if the access token was successfully refreshed, False otherwise.
        """
        self.logger.debug("Entering _refresh_access_token()")
        self.time_of_last_refresh = datetime.now()

        path = "/oauth/v2/token"  # a / at the end of the path will break things

        data = {
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'refresh_token'
        }
        # Remove Content-Type header and let requests handle it
        headers = {}

        response = self.post(path=path, headers=headers, data=data, is_auth=True)
        response = response.json() if response is not None else None

        if response is None:
            self.logger.error("Failed to refresh access token - response is None")
            return False
        else:
            if "access_token" in response:
                self.access_token = response["access_token"]
                self.logger.info("Access token refreshed")
                self.logger.debug("Exiting _refresh_access_token()")
                return True
            else:
                self.logger.error("Failed to refresh access token - access token does not exist in response")
                return False
            
    #-----------------------------------------------------------------
    # Method - Check if Access Token Needs Refreshed
    #-----------------------------------------------------------------
            
    def check_if_access_token_needs_refreshed(self):
        """
        Checks if the access token needs to be refreshed.
        return: True if the access token needs to be refreshed, False otherwise.
        """
        self.logger.debug("Entering check_last_refresh()")

        if not self.access_token or not self.time_of_last_refresh:
            return True

        time_since_last_refresh = datetime.now() - self.time_of_last_refresh

        exit_message = "Exiting check_last_refresh()"
        if time_since_last_refresh.seconds > 3600:  # Changed to 1 hour to match CRM
            self.logger.debug(exit_message)
            self.logger.info("Token needs to be refreshed")
            return True
        else:
            self.logger.debug(exit_message)
            self.logger.info("Token does not need to be refreshed")
            return False

    #-----------------------------------------------------------------
    # Method - Fetch Data
    #-----------------------------------------------------------------
    
    def _fetch_data(self, endpoint, initial_params, data_key):
        self.logger.info(f'Entering _fetch_data() for endpoint {endpoint}')
        all_data_list = []
        
        params = initial_params.copy() if initial_params else {}
        
        while True:
            self.logger.info(f"Fetching data from {endpoint} - Start Index {params['start_index']}")
            
            headers = self._get_headers()
            if not headers:
                break

            # Construct the data dictionary and encode it properly
            data_dict = {
                "page_context": params
            }
            
            # Convert to JSON and URL encode it
            encoded_data = urllib.parse.quote(json.dumps(data_dict))
            
            # Use params instead of data
            query_params = "data=" + encoded_data
            
            # Use params parameter instead of data
            response = self.get(endpoint, headers=headers, params=query_params)
            response = response.json() if response is not None else None

            if response is None:
                self.logger.error(f"Error fetching data from {endpoint}")
                break

            # Process the response
            if data_key in response:
                data_items = response[data_key]
                if isinstance(data_items, list):
                    all_data_list.extend(data_items)
                    self.logger.info(f"Retrieved {len(data_items)} {data_key} from start_index {params['start_index']}")
                    
                    # Check if there are more pages using page_context
                    page_context_response = response.get('page_context', {})
                    if page_context_response.get('has_more_rows', False):
                        params['start_index'] = params['start_index'] + 1
                    else:
                        break
                else:
                    all_data_list.append(data_items)
                    break
            else:
                self.logger.error(f"No '{data_key}' key found in the response")
                break

        self.logger.info(f"Exiting _fetch_data() with total {len(all_data_list)} {data_key} fetched")
        return all_data_list

    #-----------------------------------------------------------------
    # Method - Get Documents
    #-----------------------------------------------------------------

    def get_documents(self, email=None,start_index=1):
    # def get_requests(self, start_index=1, sort_order=None, row_count=None, search_columns=None, sort_column=None):
        """
        Fetches signing documents from Zoho Sign API.
        
        Args:
            start_index (int, optional): Starting index for pagination (1 to n)
            sort_order (str, optional): Sort direction ('ASC' or 'DESC')
            row_count (int, optional): Number of rows to return (default is 20)
            search_columns (dict, optional): Search criteria for filtering results
            sort_column (str, optional): Column to sort results by
        """
        self.logger.debug("Entering get_documents()")
        
        data = {}
        endpoint = "requests"
        data_key = "requests"
        
        # Add parameters
        if start_index is not None:
            if not isinstance(start_index, int):
                raise ValueError("start_index must be an integer")
            data["start_index"] = start_index

        # Uncomment this section when pagination is better understood
        # if row_count is not None:
        #     if not isinstance(row_count, int):
        #         raise ValueError("row_count must be an integer")
        #     data["row_count"] = row_count

        # if search_columns is not None:
        #     if not isinstance(search_columns, dict):
        #         raise ValueError("search_columns must be a dictionary")
        #     data["search_columns"] = search_columns

        # if sort_column is not None:
        #     if sort_column not in self.VALID_SORT_COLUMNS:
        #         raise ValueError(f"Invalid sort column: {sort_column}. Valid columns are: {', '.join(self.VALID_SORT_COLUMNS)}")
        #     data["sort_column"] = sort_column

        # if sort_order is not None:
        #     if sort_order not in self.VALID_SORT_ORDERS:
        #         raise ValueError(f"Invalid sort order: {sort_order}. Valid orders are: {', '.join(self.VALID_SORT_ORDERS)}")
        #     data["sort_order"] = sort_order

        if email is not None:
            valid_email = self.validate_email(email)
            if not valid_email:
                raise ValueError(f"Invalid email: {email}")
            data["search_columns"] = {"recipient_email": email}
        else:
            raise ValueError("No email provided")

        documents = self._fetch_data(endpoint, data, data_key)

        self.logger.info(f"Exiting get_documents() with {len(documents)} documents fetched")
            
        return documents
    
    
