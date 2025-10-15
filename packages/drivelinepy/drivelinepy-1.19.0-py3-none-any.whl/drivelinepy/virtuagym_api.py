#=================================================================
# Author: Garrett York
# Date: 2023/11/29
# Description: Class for Virtuagym API
#=================================================================

from .base_api_wrapper import BaseAPIWrapper

class VirtuagymAPI(BaseAPIWrapper):

    #---------------------------------------------------------------------------
    # Constructor
    #---------------------------------------------------------------------------

    def __init__(self, api_key, club_secret, base_url="https://api.virtuagym.com/api/v1/"):
        super().__init__(base_url)  # Call to parent class constructor
        self.api_key = api_key
        self.club_secret = club_secret
    
    #---------------------------------------------------------------------------
    # Method - Fetch Data
    #---------------------------------------------------------------------------
    
    def _fetch_data(self, endpoint, initial_params):
        self.logger.debug(f'Entering _fetch_paginated_data() for endpoint {endpoint}')
        all_data_list = []
        params = initial_params

        while True:
            response = self.get(endpoint, params=params)
            response = response.json() if response is not None else None
            if response is None:
                self.logger.error(f"Error fetching data from {endpoint}. The response is None.")
                break

            all_data_list.extend(response.get("result", [])) # .extend() adds the elements of the list to the end of the current list

            if response.get("status", {}).get("results_remaining", 0) > 0:
                next_page_str = response["status"]["next_page"]
                if '=' in next_page_str:
                    params['sync_from'] = next_page_str.split('=')[1]
                    self.logger.info(f"Fetching next page: {params['sync_from']} remaining {response['status']['results_remaining']}")
                else:
                    break
            else:
                break
        self.logger.debug("Exiting _fetch_paginated_data()")
        return all_data_list

    #---------------------------------------------------------------------------
    # Method - Get Club Members
    #---------------------------------------------------------------------------

    def get_club_events(self, club_id, timestamp_start=None, timestamp_end=None, member_id=None, schedule_id=None):

        """
        Retrieve all events of a club based on the supplied queries.

        https://github.com/virtuagym/Virtuagym-Public-API/wiki/Club-Events

        :param club_id: ID of the club.
        :param timestamp_start: Start of the time range (milliseconds, optional).
        :param timestamp_end: End of the time range (milliseconds, optional).
        :param member_id: ID of the member (optional).
        :param schedule_id: ID of the schedule (optional).
        :return: List containing the events.
        """

        self.logger.debug(f'Entering get_club_events() for club id {club_id}')

        all_data_list = []
        endpoint = f"club/{club_id}/events/"

        params = {
            "timestamp_start": timestamp_start,
            "timestamp_end": timestamp_end,
            "member_id": member_id,
            "schedule_id": schedule_id
        }
        
        params = self._prepare_params(params, {"api_key": self.api_key, "club_secret": self.club_secret})

        all_data_list = self._fetch_data(endpoint, params)

        self.logger.debug("Exiting get_club_events()")

        return all_data_list
    
    #---------------------------------------------------------------------------
    # Method - Get Club Members
    #---------------------------------------------------------------------------

    def get_event_participants(self, club_id, event_id=None, timestamp_start=None, timestamp_end=None, fill_guestname=False, schedule_id=None):

        """
        Retrieve event participants of a club based on the supplied queries.

        https://github.com/virtuagym/Virtuagym-Public-API/wiki/Club-Event-Participants

        :param club_id: ID of the club.
        :param event_id: ID of the event.
        :param timestamp_start: Start of the time range (milliseconds, optional).
        :param timestamp_end: End of the time range (milliseconds, optional).
        :param fill_guestname: Boolean indicating whether to fill guest names.
        :param schedule_id: ID of the schedule (optional).
        :return: List containing the event participants.
        """

        self.logger.debug("Entering get_event_participants()")

        all_data_list = []
        endpoint = f"club/{club_id}/eventparticipants/"

        params = {
            "timestamp_start": timestamp_start,
            "timestamp_end": timestamp_end,
            "event_id": event_id,
            "schedule_id": schedule_id,
            "fill_guestname": fill_guestname
        }

        params = self._prepare_params(params, {"api_key": self.api_key, "club_secret": self.club_secret})

        all_data_list = self._fetch_data(endpoint, params)

        self.logger.debug("Exiting get_event_participants()")

        return all_data_list
    
    #---------------------------------------------------------------------------
    # Method - Get Club Members
    #---------------------------------------------------------------------------
    
    def get_club_members(self, club_id, club_member_id=None, sync_from=None, from_id=None, with_options=None, any_sub_club=None, rfid_tag=None, external_id=None, email=None, max_results=None):
        
        """
        Retrieve all members of a club or a specific member based on supplied queries.
        
        https://github.com/virtuagym/Virtuagym-Public-API/wiki/Club-Members

        :param club_id: ID of the club.
        :param club_member_id: ID of the specific club member (optional).
        :param sync_from: Timestamp in milliseconds from which to synchronize (optional).
        :param from_id: Starting point for member IDs (optional).
        :param with_options: Additional data to retrieve (optional).
        :param any_sub_club: Whether to include members from any sub-club (optional).
        :param rfid_tag: RFID tag of the member (optional).
        :param external_id: External ID of the member (optional).
        :param email: Email of the member (optional).
        :param max_results: Maximum number of results to retrieve (optional).
        :return: List containing the member(s) information.
        """
        self.logger.debug("Entering get_club_members()")
        
        all_data_list = []

        if club_member_id:
            endpoint = f"club/{club_id}/member/{club_member_id}"
        else:
            endpoint = f"club/{club_id}/member"

        params = {
            "sync_from": sync_from,
            "from_id": from_id,
            "with": with_options,
            "any_sub_club": any_sub_club,
            "rfid_tag": rfid_tag,
            "external_id": external_id,
            "email": email,
            "max_results": max_results
        }

        params = self._prepare_params(params, {"api_key": self.api_key, "club_secret": self.club_secret})

        all_data_list = self._fetch_data(endpoint, params)

        self.logger.debug("Exiting get_club_members()")

        return all_data_list