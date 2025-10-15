#================================================================================
# Author: Garrett York
# Date: 2024/02/01
# Description: Class for Slack API
#================================================================================

from .base_api_wrapper import BaseAPIWrapper
import os
import mimetypes
import json

class SlackAPI(BaseAPIWrapper):

    #---------------------------------------------------------------------------
    # Constructor
    #---------------------------------------------------------------------------

    def __init__(self, token, base_url="https://slack.com/api/"):
        super().__init__(base_url)
        self.token = token

    #---------------------------------------------------------------------------
    # Method - Post Message
    #---------------------------------------------------------------------------

    def post_message(self, channel, text, thread_timestamp=None):
        """
        Posts a message to a specified channel on Slack.

        :param channel: The channel ID where the message will be posted.
        :param text: The text of the message to post.
        :param thread_timestamp: The timestamp (string or float) of the parent message to post in a thread.
                                This should be a UNIX timestamp to 6 decimal places, typically obtained from
                                the response of a successful post.
        :return: The response from the Slack API as a JSON object.
        """
        self.logger.info("Entering post_message()")

        if not text:
            error_msg = "Text cannot be None or an empty string."
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        endpoint = "chat.postMessage"
        payload = {
            'channel': channel,
            'text': text
        }
        if thread_timestamp:
            payload['thread_ts'] = thread_timestamp

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Bearer {self.token}'
        }

        response = self.post(endpoint, data=payload, headers=headers)

        if response is None:
            error_msg = "Failed to post message: No response received from Slack API. Please check the network connection and API endpoint."
            self.logger.error(error_msg)
            raise Exception(error_msg)
        
        try:
            response_json = response.json()
        except ValueError as e:
            error_msg = f"Failed to parse JSON response: {e}. Response content: {response.text}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

        if response.status_code != 200 or not response_json.get('ok', False):
            error_msg = (f"Failed to post message to channel {channel}. "
                        f"Status Code: {response.status_code}, Response: {response.text}")
            self.logger.error(error_msg)
            raise Exception(error_msg)

        self.logger.info(f"Message posted successfully to channel {channel}.")
        self.logger.info("Exiting post_message()")
        return response_json
    
    #---------------------------------------------------------------------------
    # Method - Post File + Message (optional)
    #---------------------------------------------------------------------------

    def upload_file(self, channel, file_absolute_path, text=None, thread_timestamp=None, alt_txt=None, snippet_type=None):
        """
        Uploads a file to a specified channel on Slack. Optionally posts the
        file in a thread.

        This method uses the new Slack file upload API (files.getUploadURLExternal and 
        files.completeUploadExternal) to upload files. It follows a three-step process:
        1. Gets an upload URL from Slack
        2. POSTs the file content to that URL
        3. Completes the upload and optionally shares it to a channel

        :param channel: str
            The channel ID where the file will be uploaded.
        :param file_absolute_path: str
            The absolute path to the file to upload.
        :param text: str, optional
            An initial comment to add when uploading the file. Defaults to None.
        :param thread_timestamp: str, optional
            The timestamp of the parent message to post in a thread. Defaults to None.
        :param alt_txt: str, optional
            Description of image for screen-reader. Defaults to None.
        :param snippet_type: str, optional
            Syntax type of the snippet being uploaded (e.g., 'python', 'javascript'). Defaults to None.

        :return: dict
            A dictionary response from the Slack API indicating the success or failure of the file upload.
        """
        self.logger.info("Entering upload_file()")

        if not os.path.exists(file_absolute_path):
            error_msg = f"File not found: {file_absolute_path}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        file_size = os.path.getsize(file_absolute_path)
        file_name = os.path.basename(file_absolute_path)
        
        # Step 1: Get upload URL from Slack
        self.logger.info("Step 1: Getting upload URL from Slack")
        get_url_endpoint = "files.getUploadURLExternal"
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        get_url_payload = {
            'filename': file_name,
            'length': file_size
        }
        
        # Add optional parameters if provided
        if alt_txt:
            get_url_payload['alt_txt'] = alt_txt
        if snippet_type:
            get_url_payload['snippet_type'] = snippet_type
        
        response = self.post(get_url_endpoint, headers=headers, data=get_url_payload)
        
        if response is None:
            error_msg = "Failed to get upload URL: No response received from Slack API."
            self.logger.error(error_msg)
            raise Exception(error_msg)
        
        try:
            upload_url_response = response.json()
        except ValueError as e:
            error_msg = f"Failed to parse JSON response: {e}. Response content: {response.text}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
        
        if response.status_code != 200 or not upload_url_response.get('ok', False):
            error_msg = (f"Failed to get upload URL. "
                        f"Status Code: {response.status_code}, Response: {response.text}")
            self.logger.error(error_msg)
            raise Exception(error_msg)

        # Validate required fields are present in the response
        upload_url = upload_url_response.get('upload_url')
        file_id = upload_url_response.get('file_id')

        if not upload_url or not file_id:
            error_msg = (f"Missing required fields in upload URL response. "
                        f"upload_url: {upload_url}, file_id: {file_id}")
            self.logger.error(error_msg)
            raise Exception(error_msg)
        
        # Step 2: Upload file content to the URL
        self.logger.info("Step 2: Uploading file content")

        # Determine content type for the file
        content_type, _ = mimetypes.guess_type(file_absolute_path)
        if not content_type:
            content_type = 'application/octet-stream'

        upload_headers = {
            'Content-Type': content_type,
            'Content-Length': str(file_size)
        }

        try:
            # Stream the file to avoid loading entire content into memory
            with open(file_absolute_path, 'rb') as file_content:
                # Use self.post directly - urljoin handles absolute URLs correctly
                upload_response = self.post(upload_url, data=file_content, headers=upload_headers)

                if upload_response is None or upload_response.status_code != 200:
                    error_msg = (f"Failed to upload file content. "
                                f"Status Code: {upload_response.status_code if upload_response else 'N/A'}, "
                                f"Response: {upload_response.text if upload_response else 'No response'}")
                    self.logger.error(error_msg)
                    raise Exception(error_msg)

        except FileNotFoundError as e:
            error_msg = f"File not found during upload: {e}"
            self.logger.error(error_msg)
            raise
        except Exception as e:
            error_msg = f"Error uploading file content: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
        
        # Step 3: Complete the upload
        self.logger.info("Step 3: Completing file upload")
        complete_endpoint = "files.completeUploadExternal"
        
        # Build the files array for the complete request
        files_data = [{
            'id': file_id,
            'title': file_name
        }]
        
        complete_payload = {
            'files': json.dumps(files_data)  # Convert to JSON string
        }
        
        # Add channel sharing information if provided
        if channel:
            complete_payload['channel_id'] = channel
            if text:
                complete_payload['initial_comment'] = text
            if thread_timestamp:
                complete_payload['thread_ts'] = thread_timestamp
        
        response = self.post(complete_endpoint, headers=headers, data=complete_payload)
        
        if response is None:
            error_msg = "Failed to complete file upload: No response received from Slack API."
            self.logger.error(error_msg)
            raise Exception(error_msg)
        
        try:
            response_json = response.json()
        except ValueError as e:
            error_msg = f"Failed to parse JSON response: {e}. Response content: {response.text}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
        
        if response.status_code != 200 or not response_json.get('ok', False):
            error_msg = (f"Failed to complete file upload to channel {channel}. "
                        f"Status Code: {response.status_code}, Response: {response.text}")
            self.logger.error(error_msg)
            raise Exception(error_msg)

        # Transform response to match old files.upload format for backwards compatibility
        # Old API returned single 'file' object, new API returns 'files' array
        files_data = response_json.get('files')
        if files_data and isinstance(files_data, list) and len(files_data) > 0:
            response_json['file'] = files_data[0]
            # Keep 'files' array as well for developers who want to use new format
        
        self.logger.info(f"File uploaded successfully to channel {channel}.")
        self.logger.info("Exiting upload_file()")
        return response_json