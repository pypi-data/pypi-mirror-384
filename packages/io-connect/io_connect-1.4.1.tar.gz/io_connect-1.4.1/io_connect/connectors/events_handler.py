import urllib3
import requests
import io_connect.constants as c
import pandas as pd
from datetime import datetime, timezone
import pytz
from typeguard import typechecked
import logging
from io_connect.utilities.store import ERROR_MESSAGE, Logger
from io_connect.utilities.schemas import DateDict
from dateutil import parser
from typing import Optional, Union, Literal, List, Dict
from io_connect import DataAccess
import numpy as np
import concurrent.futures
import json
import math


# Disable pandas' warning about chained assignment
pd.options.mode.chained_assignment = None

# Disable urllib3's warning about insecure requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@typechecked
class EventsHandler:
    __version__ = c.VERSION

    def __init__(
        self,
        user_id: str,
        data_url: str,
        on_prem: Optional[bool] = False,
        tz: Optional[Union[pytz.BaseTzInfo, timezone]] = c.UTC,
        log_time: Optional[bool] = False,
        logger: Optional[logging.Logger] = None,
    ):
        """
        A class to handle event-related operations.

        Parameters:
        ----------
        user_id : str
            The user ID used for authentication and identification in requests.

        data_url : str
            The URL or IP address of the third-party server from which event data is retrieved.

        on_prem : Optional[bool], default=False
            A flag indicating whether to use the on-premises server. If True, the on-premises server is used; otherwise, the cloud server is used.

        tz : Optional[Union[pytz.BaseTzInfo, timezone]], default=c.UTC
            The timezone to use for time-related operations. If not provided, defaults to UTC.

        Example:
        -------
        >>> import pytz
        >>> handler = EventsHandler(user_id="user123", data_url="https://api.example.com", on_prem=True, tz=pytz.timezone('America/New_York'))
        >>> print(handler.user_id)
        user123
        >>> print(handler.data_url)
        https://api.example.com
        >>> print(handler.on_prem)
        True
        >>> print(handler.tz)
        America/New_York
        """
        self.user_id = user_id
        self.data_url = data_url
        self.on_prem = on_prem
        self.tz = tz
        self.log_time = log_time
        self.logger = Logger(logger)

    def __iso_utc_time(self, time: Optional[Union[str, datetime]] = None) -> str:
        """
        Converts a given time to an ISO 8601 formatted string in UTC.

        If no time is provided, the current time in the specified timezone is used.

        Parameters:
        ----------
        time : Optional[Union[str, datetime]]
            The time to convert, which can be a string or a datetime object.
            If a string is provided, it will be parsed into a datetime object.
            If None is provided, the current time in the `self.tz` timezone will be used.

        Returns:
        -------
        str
            The time converted to an ISO 8601 formatted string in UTC.

        Raises:
        ------
        ValueError
            If there is a mismatch between the offset times of the provided time and `self.tz`.

        Notes:
        -----
        - If the provided time is a string, it will be parsed assuming the year comes first, followed by month and then year.
        - If the provided time does not have timezone information, it will be assumed to be in `self.tz` timezone.
        - The method ensures the time is converted to UTC before returning the ISO 8601 string.
        """
        # If time is not provided, use the current time in the specified timezone
        if time is None:
            return datetime.now(c.UTC).isoformat()

        if isinstance(time, str):
            time = parser.parse(time, dayfirst=False, yearfirst=True)

        # If the datetime object doesn't have timezone information, assume it's in self.tz timezone
        if time.tzinfo is None:
            if isinstance(self.tz, pytz.BaseTzInfo):
                # If tz is a pytz timezone, localize the datetime
                time = self.tz.localize(time)

            else:
                # If tz is a datetime.timezone object, replace tzinfo
                time = time.replace(tzinfo=self.tz)

        elif self.tz.utcoffset(time.replace(tzinfo=None)) != time.tzinfo.utcoffset(
            time
        ):
            raise ValueError(
                f"Mismatched offset times between time: ({time.tzinfo.utcoffset(time)}) and self.tz:({self.tz.utcoffset(time.replace(tzinfo=None))})"
            )

        # Return datetime object after converting to Unix timestamp
        return time.astimezone(c.UTC).isoformat()

    def publish_event(
        self,
        message: str,
        meta_data: str,
        hover_data: str,
        created_on: Optional[str],
        event_tags_list: Optional[list] = None,
        event_names_list: Optional[list] = None,
        title: Optional[str] = None,
        on_prem: Optional[bool] = None,
    ):
        """
        Publish an event with the given details to the server.

        Parameters:
        ----------
        message : str
            The main message or description of the event.

        meta_data : str
            Metadata associated with the event in string format.

        hover_data : str
            Data to be displayed when hovering over the event, in string format.

        created_on : Optional[str]
            The creation date of the event in string format. If not provided, the current date and time will be used.

        event_tags_list : Optional[list], default=None
            A list of pre-existing tags associated with the event. Either `event_tags_list` or `event_names_list` must be provided.

        event_names_list : Optional[list], default=None
            A list of human-readable names corresponding to event tags. These names are resolved into tag IDs using the `get_event_categories` method. Either `event_tags_list` or `event_names_list` must be provided.

        title : Optional[str], default=None
            The title of the event. If not provided, it will be set to None.

        on_prem : Optional[bool], default=None
            A flag indicating whether to publish the event to an on-premises server. If not provided, the default value from the class attribute (`self.on_prem`) will be used.

        Returns:
        -------
        dict
            The response data from the server in dictionary format.

        Raises:
        ------
        ValueError
            If any name in `event_names_list` does not have a corresponding tag ID.

        requests.exceptions.RequestException
            If there is an issue with the request to the server.

        Exception
            For other generic exceptions, such as missing tags when neither `event_tags_list` nor `event_names_list` is provided.

        Notes:
        -----
        - The method constructs the appropriate URL based on whether the event is being published to an on-premises server or a cloud server.
        - If `event_names_list` is provided, it resolves the names to tag IDs using the `get_event_categories` method.
        - If both `event_tags_list` and `event_names_list` are provided, only `event_names_list` will be used.
        - It prepares the request header and payload, then sends a POST request to the server.
        - The server's response is checked for success, and the data is returned if the request is successful.

        Example:
        -------
        >>> obj = EventsHandler(USER_ID, THIRD_PARTY_SERVER, ON_PREM, tz)
        >>> response = obj.publish_event(
        ...     message="System update completed",
        ...     meta_data="{'version': '1.2.3', 'status': 'successful'}",
        ...     hover_data="Update was applied successfully without any issues.",
        ...     event_names_list=['System Update'],
        ...     created_on="2023-06-14T12:00:00Z",
        ...     title="System Update"
        ... )
        >>> print(response)
        {'eventId': '12345', 'status': 'published'}
        """
        try:
            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem

            if event_names_list:
                # Initialize event_tags_list as an empty list, as event_names_list will be used to populate it.
                event_tags_list = []

                # Fetch the available event categories from the server or a local method.
                data = self.get_event_categories()

                # Iterate through each name in event_names_list to find its corresponding tag ID.
                for tag in event_names_list:
                    matched = next(
                        (item["_id"] for item in data if item["name"] == tag), None
                    )
                    # If no matching tag ID is found for the given name, raise an error.
                    if not matched:
                        raise ValueError(f"Tag '{tag}' not found in data.")
                    # Add the resolved tag ID to the event_tags_list.
                    event_tags_list.append(matched)

            # Ensure that at least one tag is present in event_tags_list after processing.
            if not event_tags_list:
                raise Exception("No event tags found.")

            # Construct the URL based on the on_prem flag
            protocol = "http" if on_prem else "https"

            url = c.PUBLISH_EVENT_URL.format(protocol=protocol, data_url=self.data_url)

            header = {"userID": self.user_id}
            payload = {
                "title": title,
                "message": message,
                "metaData": meta_data,
                "eventTags": event_tags_list,
                "hoverData": hover_data,
                "createdOn": created_on,
            }
            with Logger(self.logger, f"API {url} response time:", self.log_time):
                # Make the request
                response = requests.post(url, headers=header, json=payload, verify=True)

            # Check the response status code
            response.raise_for_status()

            # Parse the JSON response
            response_content = response.json()

            if "data" not in response_content:
                raise requests.exceptions.RequestException()

            return response_content["data"]

        except requests.exceptions.RequestException as e:
            error_message = (
                ERROR_MESSAGE(response, url)
                if "response" in locals()
                else f"\n[URL] {url}\n[EXCEPTION] {e}"
            )
            self.logger.error(f"[EXCEPTION] {type(e).__name__}: {error_message}")

        except Exception as e:
            self.logger.error(f"[EXCEPTION] {e}")

    def get_events_in_timeslot(
        self,
        start_time: Union[str, datetime],
        end_time: Optional[Union[str, datetime]] = None,
        on_prem: Optional[bool] = None,
    ) -> list:
        """
        Retrieves events within a specified time slot.

        This method fetches events that occurred between the given start and end times.
        The times are converted to ISO 8601 formatted strings in UTC before making the request.
        The method handles both on-premises and third-party servers based on the `on_prem` flag.

        Parameters:
        ----------
        start_time : Union[str, datetime]
            The start time for the event search, in string or datetime format.
        end_time : Optional[Union[str, datetime]]
            The end time for the event search, in string or datetime format.
            If not provided, the current time is used.
        on_prem : Optional[bool]
            Flag indicating if the server is on-premises. If not provided,
            the class attribute `self.on_prem` is used.

        Returns:
        -------
        list
            A list of events found within the specified time slot.

        Raises:
        ------
        ValueError
            If the `end_time` is before the `start_time`.

        Notes:
        -----
        - The method constructs the request URL based on the `on_prem` flag.
        - The request header includes the user ID.
        - The response is checked for successful status, and the event data is extracted from the response.

        Exceptions:
        -----------
        - Handles `requests.exceptions.RequestException` to catch request-related errors.
        - Catches all other exceptions to prevent the program from crashing and prints the exception message.

        Example:
        -------
        >>> obj = EventsHandler(USER_ID,THIRD_PARTY_SERVER,ON_PREM, tz)
        >>> events = obj.get_events_in_timeslot(start_time="2023-06-14T12:00:00Z")
        >>> print(events)
        [{'event_id': 1, 'timestamp': '2023-06-14T11:59:59Z', ...}, ...]
        """
        try:
            # Convert start_time and end_time to iso utc timestamps
            start_time = self.__iso_utc_time(start_time)
            end_time = self.__iso_utc_time(end_time)

            # Raise an error if end_time is before start_time
            if datetime.fromisoformat(end_time) < datetime.fromisoformat(start_time):
                raise ValueError(
                    f"Invalid time range: start_time({start_time}) should be before end_time({end_time})."
                )

            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem

            # Construct the URL based on the on_prem flag
            protocol = "http" if on_prem else "https"

            url = c.GET_EVENTS_IN_TIMESLOT_URL.format(
                protocol=protocol, data_url=self.data_url
            )

            header = {"userID": self.user_id}
            payload = {"startTime": start_time, "endTime": end_time}

            with Logger(self.logger, f"API {url} response time:", self.log_time):
                response = requests.put(url, headers=header, json=payload, verify=False)

            # Check the response status code
            response.raise_for_status()

            # Parse the JSON response
            response_content = response.json()

            if "data" not in response_content:
                raise requests.exceptions.RequestException()

            return response_content["data"]

        except requests.exceptions.RequestException as e:
            error_message = (
                ERROR_MESSAGE(response, url)
                if "response" in locals()
                else f"\n[URL] {url}\n[EXCEPTION] {e}"
            )
            self.logger.error(f"[EXCEPTION] {type(e).__name__}: {error_message}")
            return []

        except Exception as e:
            self.logger.error(f"[EXCEPTION] {e}")
            return []

    def get_event_data_count(
        self,
        end_time: Optional[Union[str, datetime]] = None,
        count: Optional[int] = 10,
        on_prem: Optional[bool] = None,
    ) -> list:
        """
        Retrieve a specified number of event data records up to a given end time.

        Parameters:
        ----------
        end_time : Optional[Union[str, datetime]]
            The end time up to which event data records are retrieved. It can be a string in ISO 8601 format or a datetime object.
            If None, the current time is used.

        count : Optional[int]
            The number of event data records to retrieve. The default value is 10. Must be less than 10,000.

        on_prem : Optional[bool]
            Flag indicating whether to use the on-premises server. If None, the default value from the class attribute self.on_prem is used.

        Returns:
        -------
        list
            A list of event data records.

        Raises:
        ------
        Exception
            If the count is greater than 10,000.
        requests.exceptions.RequestException
            If there is an error with the HTTP request.

        Notes:
        -----
        - The method converts the provided `end_time` to an ISO 8601 UTC timestamp.
        - If `on_prem` is not provided, the method uses the class attribute `self.on_prem`.
        - The URL for the request is constructed based on the `on_prem` flag.
        - The method sends a PUT request to the constructed URL with appropriate headers and payload.
        - If the request is successful, the response is parsed from JSON to a list and returned.
        - If there is an exception during the request or other processing, an empty list is returned and the exception is logged to the console.

        Example:
        -------
        >>> obj = EventsHandler(USER_ID,THIRD_PARTY_SERVER,ON_PREM, tz)
        >>> events = obj.get_event_data_count('2023-06-14T12:00:00Z', count=5)
        >>> print(events)
        [{'event_id': 1, 'timestamp': '2023-06-14T11:59:59Z', ...}, ...]

        """
        try:
            if count > 10000:
                raise Exception("Count should be less than or equal to 10000.")

            # Convert end_time to iso utc timestamp
            end_time = self.__iso_utc_time(end_time)

            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem

            # Construct the URL based on the on_prem flag
            protocol = "http" if on_prem else "https"

            url = c.GET_EVENT_DATA_COUNT_URL.format(
                protocol=protocol, data_url=self.data_url
            )

            header = {"userID": self.user_id}
            payload = {"endTime": str(end_time), "count": count}

            with Logger(self.logger, f"API {url} response time:", self.log_time):
                response = requests.put(url, headers=header, json=payload, verify=False)

            # Check the response status code
            response.raise_for_status()

            # Parse the JSON response
            response_content = response.json()

            if "data" not in response_content:
                raise requests.exceptions.RequestException()

            return response_content["data"]

        except requests.exceptions.RequestException as e:
            error_message = (
                ERROR_MESSAGE(response, url)
                if "response" in locals()
                else f"\n[URL] {url}\n[EXCEPTION] {e}"
            )
            self.logger.error(f"[EXCEPTION] {type(e).__name__}: {error_message}")
            return []

        except Exception as e:
            self.logger.error(f"[EXCEPTION] {e}")
            return []

    def get_event_categories(
        self,
        on_prem: Optional[bool] = None,
    ) -> list:
        """
        Retrieve a list of event categories from the server.

        Parameters:
        ----------
        on_prem : Optional[bool]
            Flag indicating whether to use the on-premises server. If None, the default value from the class attribute `self.on_prem` is used.

        Returns:
        -------
        list
            A list of event categories.

        Raises:
        ------
        requests.exceptions.RequestException
            If there is an error with the HTTP request.

        Notes:
        -----
        - If `on_prem` is not provided, the method uses the class attribute `self.on_prem`.
        - The URL for the request is constructed based on the `on_prem` flag.
        - The method sends a GET request to the constructed URL with appropriate headers.
        - If the request is successful, the response is parsed from JSON to a list and returned.
        - If there is an exception during the request or other processing, an empty list is returned and the exception is logged to the console.

        Example:
        -------
        >>> obj = EventsHandler(USER_ID,THIRD_PARTY_SERVER,ON_PREM, tz)
        >>> categories = obj.get_event_categories()
        >>> print(categories)
        ['Category1', 'Category2', 'Category3', ...]
        """
        try:
            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem

            # Construct the URL based on the on_prem flag
            protocol = "http" if on_prem else "https"

            url = c.GET_EVENT_CATEGORIES_URL.format(
                protocol=protocol, data_url=self.data_url
            )

            header = {"userID": self.user_id}

            with Logger(self.logger, f"API {url} response time:", self.log_time):
                response = requests.get(url, headers=header, verify=False)

            # Check the response status code
            response.raise_for_status()

            # Parse the JSON response
            response_content = response.json()

            if "data" not in response_content:
                raise requests.exceptions.RequestException()

            return response_content["data"]

        except requests.exceptions.RequestException as e:
            error_message = (
                ERROR_MESSAGE(response, url)
                if "response" in locals()
                else f"\n[URL] {url}\n[EXCEPTION] {e}"
            )
            self.logger.error(f"[EXCEPTION] {type(e).__name__}: {error_message}")
            return []

        except Exception as e:
            self.logger.error(f"[EXCEPTION] {e}")
            return []

    def get_detailed_event(
        self,
        event_tags_list: Optional[list] = None,
        start_time: Union[str, datetime] = None,
        end_time: Optional[Union[str, datetime]] = None,
        on_prem: Optional[bool] = None,
    ) -> list:
        """
        Retrieve detailed event data for a specified time range and event tags.

        Parameters:
        ----------
        event_tags_list : Optional[list]
            A list of event tags to filter the events. If None, all event categories are considered.

        start_time : Union[str, datetime]
            The start time for fetching events. It can be a string in ISO 8601 format or a datetime object.

        end_time : Optional[Union[str, datetime]]
            The end time for fetching events. It can be a string in ISO 8601 format or a datetime object. If None, the current time is used.

        on_prem : Optional[bool]
            Flag indicating whether to use the on-premises server. If None, the default value from the class attribute `self.on_prem` is used.

        Returns:
        -------
        list
            A list of detailed event data records.

        Raises:
        ------
        requests.exceptions.RequestException
            If there is an error with the HTTP request.
        ValueError
            If the API response indicates a failure.

        Notes:
        -----
        - The method converts the provided `start_time` and `end_time` to ISO 8601 UTC timestamps.
        - If `on_prem` is not provided, the method uses the class attribute `self.on_prem`.
        - The URL for the request is constructed based on the `on_prem` flag.
        - The method sends a PUT request to the constructed URL with appropriate headers and payload to fetch event data in pages.
        - If there are more pages of data, the method fetches subsequent pages until all data is retrieved.
        - If there is an exception during the request or other processing, an empty list is returned and the exception is logged to the console.

        Example:
        -------
        >>> obj = EventsHandler(USER_ID,THIRD_PARTY_SERVER,ON_PREM, tz)
        >>> detailed_events = obj.get_detailed_event( event_tags_list=['tag1', 'tag2'], start_time = '2023-06-01T00:00:00Z')
        >>> print(detailed_events)
        [{'event_id': 1, 'timestamp': '2023-06-01T00:00:01Z', ...}, ...]

        """
        try:
            # Convert start_time and end_time to iso utc timestamps
            start_time = self.__iso_utc_time(start_time)
            end_time = self.__iso_utc_time(end_time)

            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem

            # Construct the URL based on the on_prem flag
            protocol = "http" if on_prem else "https"

            # Construct the URL for fetching detailed event data
            url = c.GET_DETAILED_EVENT_URL.format(
                protocol=protocol, data_url=self.data_url
            )

            # Retrieve event categories based on whether it's on-premises or not
            events = self.get_event_categories(on_prem=on_prem)

            # Extract the IDs from the events
            id_list = [item["_id"] for item in events]

            # Check for event_tag
            if event_tags_list is None:
                tags = id_list
            else:
                # If event_tags_list is provided, find the intersection with id_list
                tags = list(set(event_tags_list).intersection(id_list))

            # Prepare the request header with user ID
            header = {"userID": self.user_id}

            # Prepare the payload for the request
            payload = {
                "startTime": start_time,
                "endTime": end_time,
                "eventTags": tags,
                "count": 1000,
            }

            raw_data = []
            page = 1

            # Loop to fetch data until there is no more data to fetch
            while True:
                # Log the current page being fetched
                self.logger.display_log(f"[INFO] Fetching Data from page {page}")

                with Logger(self.logger, f"API {url} response time:", self.log_time):
                    # Send a PUT request to fetch data from the current page
                    response = requests.put(
                        url + f"/{page}/1000",
                        headers=header,
                        json=payload,
                        verify=False,
                    )
                # Check the response status code
                response.raise_for_status()

                # Parse the JSON response
                response_content = response.json()

                # Check for errors in the API response
                if response_content["success"] is False:
                    raise requests.exceptions.RequestException()

                response_data = response_content["data"]["data"]
                raw_data.extend(response_data)

                page += 1  # Move to the next page

                if len(raw_data) >= response_content["data"]["totalCount"]:
                    break  # Break the loop if no more data is available

            return raw_data

        except requests.exceptions.RequestException as e:
            error_message = (
                ERROR_MESSAGE(response, url)
                if "response" in locals()
                else f"\n[URL] {url}\n[EXCEPTION] {e}"
            )
            self.logger.error(f"[EXCEPTION] {type(e).__name__}: {error_message}")
            return []

        except Exception as e:
            self.logger.error(f"[EXCEPTION] {e}")
            return []

    def _get_paginated_data(self, url, payload, parallel):
        """
        Sends a PUT request to the specified API endpoint and processes the response.

        Args:
            url (str): The API endpoint URL.
            payload (dict): The JSON payload to be sent in the request.
            parallel (bool): Determines whether to return only the "rows" field from the response data.

        Returns:
            dict: The processed response data. If `parallel` is True, returns only the "rows" field; otherwise, returns full data.

        Raises:
            requests.exceptions.RequestException: If the request fails or the response does not contain valid data.
            Exception: For any other unexpected errors.
        """
        try:
            # Log API response time using a custom Logger class
            with Logger(self.logger, f"API {url} response time:", self.log_time):
                # Send a PUT request with the provided payload and user authentication header
                response = requests.put(
                    url, json=payload, headers={"userID": self.user_id}, verify=False
                )
            # Raise an exception for HTTP errors (e.g., 4xx or 5xx responses)
            response.raise_for_status()

            # Parse the JSON response
            response_content = response.json()
            data = response_content.get("data")

            if data:
                # If `parallel` is True, return only the "rows" field; otherwise, return the full data
                return data.get("rows", {}) if parallel else data

            # Raise an exception if the response does not contain the expected "data" field
            raise requests.exceptions.RequestException()

        except requests.exceptions.RequestException as e:
            # Log API-related exceptions (e.g., network errors, timeout, invalid response)
            error_message = (
                ERROR_MESSAGE(response, url)
                if "response" in locals()
                else f"\n[URL] {url}\n[EXCEPTION] {e}"
            )
            self.logger.error(f"[EXCEPTION] {type(e).__name__}: {error_message}")
            raise

        except Exception as e:
            # Log any other unexpected exceptions
            self.logger.error(f"[EXCEPTION] {e}")
            raise

    def get_mongo_data(
        self,
        device_id: str,
        end_time: str,
        start_time: Optional[str] = None,
        limit: Optional[int] = None,
        alias: Optional[bool] = False,
        on_prem: Optional[bool] = None,
    ):
        """
        Fetches data from the MongoDB for custom table Dev type for given device within a specified time range

        Parameters:
        - device_id (str): The ID of the device.
        - start_time (Optional[str]): The start time for data retrieval.
        - end_time (str): The end time for data retrieval.
        - limit (int): No of rows
        - on_prem (Optional[bool]): Indicates if the operation is on-premise. Defaults to class attribute if not provided.

        Returns:
        - pd.DataFrame: The DataFrame containing the fetched and processed data.

        Exceptions Handled:
        - requests.exceptions.RequestException: Raised when there is an issue with the HTTP request.
        - Exception: General exception handling for other errors
        """
        try:
            if start_time and limit:
                raise Exception("Cannot process both start_time and limit.")

            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem
            # Determine the protocol based on the on_prem flag
            protocol = "http" if on_prem else "https"

            # Construct API URL for data retrieval
            url = c.GET_MONGO_DATA.format(protocol=protocol, data_url=self.data_url)

            # Prepare the payload
            payload = {
                "devID": device_id,
                "endTime": end_time,
                "rawData": True,
                **({"startTime": start_time} if start_time else {}),
                **({"limit": limit} if limit else {}),
            }

            if start_time:
                # Parse the response JSON
                data = self._get_paginated_data(url + "/1/500", payload, parallel=False)

                total_pages = data.get("totalPages", 0)
                initial_results = data.get("rows", [])

                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    results = list(
                        executor.map(
                            lambda page: self._get_paginated_data(
                                url + f"/{page}/500", payload, parallel=True
                            ),
                            list(range(2, total_pages + 1)),
                        )
                    )

                results.append(initial_results)
                # Flatten results
                rows = [
                    row.get("data", {}) for page_rows in results for row in page_rows
                ]

            else:
                results = self._get_paginated_data(url, payload, parallel=False)
                rows = [row["data"] for row in results]

            # Convert to DataFrame and sort
            df = pd.DataFrame(rows)

            if df.empty:
                return df

            df = df.sort_values(by="D0", ascending=False).reset_index(drop=True)

            if alias:
                metadata = self.get_device_metadata(
                    device_id=device_id, on_prem=on_prem
                )

                sensor_list = df.columns.tolist()

                # Create a dictionary mapping sensor IDs to sensor names
                sensor_map = {
                    item["sensorId"]: "{} ({})".format(
                        item["sensorName"], item["sensorId"]
                    )
                    for item in metadata["sensors"]
                    if item["sensorId"] in sensor_list
                }

                # Rename the DataFrame columns using the constructed mapping
                df.rename(columns=sensor_map, inplace=True)

            return df

        except Exception as e:
            self.logger.error(f"[EXCEPTION] {e}")
            return pd.DataFrame()

    def get_device_rows_advanced(
        self,
        device_id: str,
        filter: Optional[Dict[str, Union[List[str], List[DateDict]]]] = None,
        sort: Optional[List[Dict[str, Literal["asc", "desc"]]]] = None,
        alias: Optional[bool] = False,
        limit: int = 100,
        page: int = 1,
        single_page: bool = False,
        on_prem: Optional[bool] = None,
    ) -> pd.DataFrame:
        """
        Retrieve device data rows with advanced filtering, sorting, pagination, and optional aliasing.

        This method fetches rows of device data from an API endpoint, supports filtering,
        pagination, optional parallel fetching of multiple pages, and allows column aliasing
        based on device metadata.

        Parameters
        ----------
        device_id : str
            The unique identifier of the device for which data is to be retrieved.
        filter : Optional[Dict[str, Union[List[str], List[DateDict]]]], default=None
            Optional filters to apply on the data. Keys are field names, and values are
            lists of strings or date dictionaries specifying filter criteria.
        sort : Optional[List[Dict[str, Literal["asc", "desc"]]]], default=None
            Optional sorting instructions. Each dictionary should specify a field and the
            sort order ("asc" or "desc"). Currently commented out in the payload.
        alias : Optional[bool], default=False
            If True, rename DataFrame columns using sensor metadata for more readable names.
        single_page : bool, default=False
            If True, fetch only the specified page; otherwise, fetch all pages in parallel.
        limit : int, default=100
            Number of rows per page to fetch.
        page : int, default=1
            Page number to start fetching from.
        on_prem : Optional[bool], default=None
            Determines whether to use HTTP (on-premises) or HTTPS (cloud) protocol. If None,
            the class-level default `self.on_prem` is used.

        Returns
        -------
        pd.DataFrame
            A pandas DataFrame containing the requested device data rows, sorted by the
            "D0" column in descending order. Columns may be aliased if `alias=True`.
            Returns an empty DataFrame if an exception occurs or no data is found.

        Notes
        -----
        - Uses `self._get_paginated_data` to retrieve paginated data from the API.
        - Supports parallel fetching of multiple pages with a maximum of 5 concurrent threads.
        - Column aliasing uses `self.get_device_metadata` to map sensor IDs to readable names.
        - Logs any exceptions encountered and returns an empty DataFrame in such cases.
        """
        try:
            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem
            # Determine the protocol based on the on_prem flag
            protocol = "http" if on_prem else "https"

            # Construct API URL for data retrieval
            url = c.GET_DEVICE_ROWS.format(protocol=protocol, data_url=self.data_url)

            total_pages = page  # Initialize with page to enter the loop

            payload = {
                "devID": device_id,
                **({"search": {"data": filter}} if filter else {}),
                # **({"sort": sort} if sort else {}),
                "limit": limit,
                "page": page,
                "rawData": True,
            }

            response = self._get_paginated_data(url, payload, parallel=False)

            total_count = response.get("totalCount", 0)  # Total number of documents
            initial_results = response.get("rows", [])

            # Calculate the total number of pages
            total_pages = math.ceil(total_count / limit)

            rows = initial_results.copy()  # Start with the first page

            # Fetch remaining pages in parallel if needed
            if not single_page and total_pages > 1:
                # Generate page numbers starting from 2
                pages_to_fetch = list(range(2, total_pages + 1))

                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    results = list(
                        executor.map(
                            lambda page: self._get_paginated_data(
                                url, {**payload, "page": page}, parallel=True
                            ),
                            pages_to_fetch,
                        )
                    )

                results.append(initial_results)
                # Flatten results
                rows = [
                    row.get("data", {}) for page_rows in results for row in page_rows
                ]

            else:
                rows = [row["data"] for row in initial_results]

            # Convert to DataFrame and sort
            df = pd.DataFrame(rows)

            if df.empty:
                return df

            df = df.sort_values(by="D0", ascending=False).reset_index(drop=True)

            if alias:
                metadata = self.get_device_metadata(
                    device_id=device_id, on_prem=on_prem
                )

                sensor_list = df.columns.tolist()

                # Create a dictionary mapping sensor IDs to sensor names
                sensor_map = {
                    item["sensorId"]: "{} ({})".format(
                        item["sensorName"], item["sensorId"]
                    )
                    for item in metadata["sensors"]
                    if item["sensorId"] in sensor_list
                }

                # Rename the DataFrame columns using the constructed mapping
                df.rename(columns=sensor_map, inplace=True)

            return df

        except Exception as e:
            self.logger.error(f"[EXCEPTION] {e}")
            return pd.DataFrame()

    def get_maintenance_module_data(
        self,
        start_time: Union[int, str, datetime, np.int64],
        end_time: Optional[Union[int, str, datetime, np.int64]] = None,
        remark_group: list = None,
        event_id: list = None,
        maintenance_module_id: str = None,
        operator: Literal["count", "activeDuration", "inactiveDuration"] = None,
        data_precision: int = None,
        periodicity: Optional[
            Literal["hour", "day", "week", "month", "quarter", "year"]
        ] = None,
        cycle_time: Optional[str] = None,
        week_start: Optional[int] = None,
        month_start: Optional[int] = None,
        year_start: Optional[int] = None,
        shifts: Optional[list] = None,
        shift_operator: Optional[
            Literal["sum", "mean", "median", "mode", "min", "max"]
        ] = None,
        filter: Optional[dict] = None,
        on_prem: Optional[bool] = None,
    ):
        """
        Fetch maintenance module data based on the provided parameters.

        This function retrieves maintenance-related data from an API, transforming
        input parameters into a payload and handling the request-response cycle.

        Args:
            start_time (Union[int, str, datetime]): The start time of the query, as a Unix timestamp,
                ISO 8601 string, or a `datetime` object.
            end_time (Optional[Union[int, str, datetime]]): The end time of the query, optional.
            remark_group (list): A list of remark groups to filter by.
            event_id (list): A list of event IDs to include in the query.
            maintenance_module_id (str): The ID of the maintenance module to query.
            operator (Literal["count", "activeDuration", "inactiveDuration"]):
                The type of aggregation to apply to the data.
            data_precision (int): The precision for the returned data.
            periodicity (Optional[Literal["hour", "day", "week", "month", "quarter", "year"]]):
                The periodicity of the data (e.g., "day" for daily data).
            cycle_time (Optional[str]): The cycle time for calculating periodic data.
            week_start (Optional[int]): The starting day of the week (0 for Sunday, 1 for Monday).
            month_start (Optional[int]): The starting day of the month.
            year_start (Optional[int]): The starting month of the year.
            shifts (Optional[list]): A list of shifts to include in the query.
            shift_operator (Optional[Literal["sum", "mean", "median", "mode", "min", "max"]]):
                The aggregation operator to use for shifts.
            on_prem (Optional[bool]): Whether the API should use the on-premises protocol ("http")
                instead of cloud-based ("https").

        Returns:
            dict: The parsed response data from the API. If any errors occur, returns an empty dictionary.

        Raises:
            requests.exceptions.RequestException: If there is an error during the API request.
            Exception: If the API response contains errors or any other exception occurs.

        Notes:
            - The function assumes the existence of a `DataAccess` object and a `c.GET_MAINTENANCE_MODULE_DATA`
              constant for URL construction.
            - The `time_to_unix` method is used to convert input times into Unix timestamps.

        Example:
            data = EventsHandler(USER_ID, DATA_URL).get_maintenance_module_data(
                start_time="2023-01-01T00:00:00Z",
                end_time="2023-01-31T23:59:59Z",
                operator="count",
                periodicity="day",
                remark_group=remark_group_list,
                event_id=event_id_list,
                maintenance_module_id=maintenance_module_id,
                operator="activeDuration",
                data_precision=2,
            )
        """
        try:
            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem

            # Determine the protocol based on the on_prem flag
            protocol = "http" if on_prem else "https"

            # Convert start_time and end_time to Unix timestamps
            start_time_unix = DataAccess(
                self.user_id, self.data_url, "", tz=self.tz
            ).time_to_unix(start_time)
            end_time_unix = DataAccess(
                self.user_id, self.data_url, "", tz=self.tz
            ).time_to_unix(end_time)

            # Validate that the start time is before the end time
            if end_time_unix < start_time_unix:
                raise ValueError(
                    f"Invalid time range: start_time({start_time}) should be before end_time({end_time})."
                )

            # Build the API payload with the required parameters
            payload = {
                "userID": self.user_id,
                "startTime": start_time_unix,
                "endTime": end_time_unix,
                "remarkGroup": remark_group,
                "eventID": event_id,
                "maintenanceModuleID": maintenance_module_id,
                "operator": operator,
                "timezone": str(self.tz),
                "dataPrecision": data_precision,
            }

            # Add periodicity and related parameters if specified
            if periodicity:
                payload.update(
                    {
                        "periodicity": periodicity,
                        "weekStart": week_start,
                        "monthStart": month_start,
                        "yearStart": year_start,
                        "eventID": event_id,
                    }
                )

            # Add cycle time to the payload if provided
            if cycle_time:
                payload.update({"cycleTime": cycle_time})

            # Add shift-related parameters if provided
            if shifts:
                payload.update({"shifts": shifts, "shiftOperator": shift_operator})

            if filter:
                payload.update({"filter": filter})

            # Construct API URL for data retrieval
            url = c.GET_MAINTENANCE_MODULE_DATA.format(
                protocol=protocol, data_url=self.data_url
            )

            with Logger(self.logger, f"API {url} response time:", self.log_time):
                # Parse the response JSON
                response = requests.put(
                    url,
                    json=payload,
                    verify=False,
                )

            # Check the response status code
            response.raise_for_status()

            # Parse the JSON response
            response_content = response.json()

            if "errors" in response_content:
                raise requests.exceptions.RequestException()

            return response_content["data"]

        except requests.exceptions.RequestException as e:
            error_message = (
                ERROR_MESSAGE(response, url)
                if "response" in locals()
                else f"\n[URL] {url}\n[EXCEPTION] {e}"
            )
            self.logger.error(f"[EXCEPTION] {type(e).__name__}: {error_message}")
            return {}

        except Exception as e:
            self.logger.error(f"[EXCEPTION] {e}")
            return {}

    def get_device_data(
        self,
        devices: list = None,
        n: Optional[int] = 5000,
        end_time: Optional[str] = None,
        start_time: Optional[str] = None,
        on_prem: Optional[bool] = None,
    ) -> pd.DataFrame:
        """
        Fetch device data from the API with optional filters for time range and device list.

        Args:
            devices (list, optional): List of device IDs to filter data for. Defaults to None (fetch all devices).
            n (int, optional): Maximum number of records to fetch. Defaults to 5000.
            end_time (str, optional): End time for the data range in ISO 8601 format. Defaults to None.
            start_time (str, optional): Start time for the data range in ISO 8601 format. Defaults to None.
            on_prem (bool, optional): Flag to indicate whether to use on-premise protocol ("http"). Defaults to None (uses "https").

        Returns:
            pd.DataFrame: A Pandas DataFrame containing the flattened device data.
            If an exception occurs, an empty DataFrame is returned.
        """
        try:
            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem

            # Determine the protocol based on the on_prem flag
            protocol = "http" if on_prem else "https"

            # Prepare the payload for the request
            payload = {
                "devices": devices,
                "page": 1,
                "limit": n,
                "rawData": True,
            }
            if start_time:
                payload.update({"startTime": start_time})

            if end_time:
                payload.update({"endTime": end_time})

            # Construct API URL for data retrieval
            url = c.GET_DEVICE_DATA.format(protocol=protocol, data_url=self.data_url)

            with Logger(self.logger, f"API {url} response time:", self.log_time):
                # Send a PUT request to fetch data
                response = requests.put(url, json=payload, verify=False)
            # Check the response status code
            response.raise_for_status()

            # Parse the response JSON
            response_content = response.json()
            if "error" in response_content:
                raise requests.exceptions.RequestException()

            device_data = response_content["rows"]
            flat_data = []

            # Flatten the device data for easier processing
            for record in device_data:
                flat_record = {}
                flat_record = {"_id": record["_id"], "devID": record["devID"]}

                # Include additional data fields from the record
                flat_record.update(record["data"])
                flat_data.append(flat_record)

            # Convert the flattened data into a Pandas DataFrame
            df = pd.DataFrame(flat_data)

            return df

        except requests.exceptions.RequestException as e:
            error_message = (
                ERROR_MESSAGE(response, url)
                if "response" in locals()
                else f"\n[URL] {url}\n[EXCEPTION] {e}"
            )
            self.logger.error(f"[EXCEPTION] {type(e).__name__}: {error_message}")
            return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"[EXCEPTION] {e}")
            return pd.DataFrame()

    def get_sensor_rows(
        self,
        device_id: Optional[str] = None,
        sensor: str = None,
        value: str = None,
        end_time: Optional[str] = None,
        start_time: Optional[str] = None,
        alias: Optional[bool] = False,
        on_prem: Optional[bool] = None,
    ) -> pd.DataFrame:
        """
        Retrieve device data rows from the server based on sensor parameters and optional time range filters.

        This method queries the `TableDeviceRow` collection using the specified sensor key-value pair and time constraints.
        It constructs a GET request to the appropriate API endpoint and flattens the returned sensor data into a DataFrame.

        Parameters:
        ----------
        device_id : Optional[str], default=None
            The unique identifier of the device. If not provided, results may include multiple devices depending on server behavior.

        sensor : str
            The sensor key used to filter the data (e.g., 'temperature', 'humidity').

        value : str
            The expected value of the sensor to filter the records.

        end_time : Optional[str], default=None
            The end timestamp for the data range in ISO 8601 format (e.g., "2023-06-14T12:00:00Z"). If not provided, no upper bound is applied.

        start_time : Optional[str], default=None
            The start timestamp for the data range in ISO 8601 format. If not provided, no lower bound is applied.

        on_prem : Optional[bool], default=None
            Whether to send the request to an on-premises server (`http`) or a cloud server (`https`).
            If not specified, the method uses the value of `self.on_prem`.

        Returns:
        -------
        pd.DataFrame
            A Pandas DataFrame containing the flattened sensor data rows. If no data is returned or an error occurs, an empty DataFrame is returned.

        Raises:
        ------
        requests.exceptions.RequestException
            If the request fails or returns an error status code or malformed content.

        Exception
            For other unexpected exceptions encountered during execution.

        Notes:
        -----
        - Constructs the request payload with the specified filters and uses the appropriate server protocol.
        - Flattens nested sensor data for ease of use in downstream analysis or visualization.
        - Suppresses SSL verification warnings due to `verify=False` usage in requests.

        Example:
        -------
        >>> df = events_handler.get_sensor_rows(
        ...     device_id="device123",
        ...     sensor="temperature",
        ...     value="25.3",
        ...     start_time="2023-06-14T10:00:00Z",
        ...     end_time="2023-06-14T12:00:00Z",
        ...     on_prem=True
        ... )
        >>> print(df.head())
        """
        try:
            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem

            # Determine the protocol based on the on_prem flag
            protocol = "http" if on_prem else "https"

            # Prepare the payload for the request
            payload = {"devID": device_id, "key": sensor, "value": value}
            if start_time:
                payload.update({"sTime": start_time})

            if end_time:
                payload.update({"eTime": end_time})

            # Construct API URL for data retrieval
            url = c.GET_SENSOR_ROWS.format(protocol=protocol, data_url=self.data_url)

            with Logger(self.logger, f"API {url} response time:", self.log_time):
                # Send a GET request to fetch data
                response = requests.get(url, params=payload, verify=False)
            # Check the response status code
            response.raise_for_status()

            # Parse the response JSON
            response_content = response.json()
            if "error" in response_content:
                raise requests.exceptions.RequestException()

            device_data = response_content["data"]
            flat_data = []

            # Flatten the device data for easier processing
            for record in device_data:
                flat_record = {}
                flat_record = {"_id": record["_id"], "devID": record["devID"]}

                # Include additional data fields from the record
                flat_record.update(record["data"])
                flat_data.append(flat_record)

            # Convert the flattened data into a Pandas DataFrame
            df = pd.DataFrame(flat_data)

            if alias:
                metadata = self.get_device_metadata(
                    device_id=device_id, on_prem=on_prem
                )

                sensor_list = df.columns.tolist()

                # Create a dictionary mapping sensor IDs to sensor names
                sensor_map = {
                    item["sensorId"]: "{} ({})".format(
                        item["sensorName"], item["sensorId"]
                    )
                    for item in metadata["sensors"]
                    if item["sensorId"] in sensor_list
                }

                # Rename the DataFrame columns using the constructed mapping
                df.rename(columns=sensor_map, inplace=True)

            return df

        except requests.exceptions.RequestException as e:
            error_message = (
                ERROR_MESSAGE(response, url)
                if "response" in locals()
                else f"\n[URL] {url}\n[EXCEPTION] {e}"
            )
            self.logger.error(f"[EXCEPTION] {type(e).__name__}: {error_message}")
            return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"[EXCEPTION] {e}")
            return pd.DataFrame()

    def get_device_metadata(
        self, device_id: str, on_prem: Optional[bool] = None
    ) -> dict:
        """
        Fetches metadata for a specific device.

        Args:
            device_id (str): The identifier of the device.
            on_prem (bool, optional): Specifies whether to use on-premises data server. If not provided, uses the class default.

        Returns:
            dict: Metadata for the specified device.

        Example:
            >>> events_handler = EventsHandler(user_id="my_user_id", data_url="data.url.com", ds_url="example_ds.com")
            >>> metadata = events_handler.get_device_metadata(device_id="device123", on_prem=True)
            >>> print(metadata)
            {'id': 'device123', 'name': 'Device XYZ', 'location': 'Room A', ...}

        Raises:
            requests.exceptions.RequestException: If an error occurs during the HTTP request, such as a network issue or timeout.
            Exception: If an unexpected error occurs during metadata retrieval, such as parsing JSON data or other unexpected issues.
        """
        try:
            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem

            # Construct the URL based on the on_prem flag
            protocol = "http" if on_prem else "https"
            url = c.GET_DEVICE_METADATA_MONGO_URL.format(
                protocol=protocol, data_url=self.data_url
            )

            with Logger(self.logger, f"API {url} response time:", self.log_time):
                # Make the request
                response = requests.get(
                    url + f"/{self.user_id}",
                    params={"devID": device_id},
                    verify=False,
                )

            # Check the response status code
            response.raise_for_status()

            # Parse the JSON response
            response_content = response.json()

            if "data" not in response_content:
                raise requests.exceptions.RequestException()

            return response_content["data"]

        except requests.exceptions.RequestException as e:
            error_message = (
                ERROR_MESSAGE(response, url)
                if "response" in locals()
                else f"\n[URL] {url}\n[EXCEPTION] {e}"
            )
            self.logger.error(f"[EXCEPTION] {type(e).__name__}: {error_message}")
            return {}

        except (TypeError, ValueError) as e:
            self.logger.error(f"[EXCEPTION] {type(e).__name__}: {e}")
            return {}

        except Exception as e:
            self.logger.error(f"[EXCEPTION] {e}")
            return {}

    def get_maintenance_module_filter(
        self,
        start_time: Union[int, str, datetime, np.int64] = None,
        end_time: Optional[Union[int, str, datetime, np.int64]] = None,
        events: list = None,
        module_id: str = None,
        oldest_first: Optional[Literal[1, -1]] = 1,
        limit: Optional[int] = 50,
        on_prem: Optional[bool] = None,
    ) -> list:
        """
        Fetches maintenance module events within a specified time range.

        Args:
            start_time (int | str | datetime | np.int64, optional): Start time of the query. Can be a UNIX timestamp, datetime object, or ISO 8601 string. Defaults to None.
            end_time (int | str | datetime | np.int64, optional): End time of the query. Can be a UNIX timestamp, datetime object, or ISO 8601 string. Defaults to None.
            events (list, optional): List of event types to filter. Defaults to None (no event filtering).
            module_id (str, optional): Identifier of the maintenance module. Defaults to None.
            oldest_first (Literal[1, -1], optional): Sorting order of results.
                1 → Ascending (oldest → latest).
                -1 → Descending (latest → oldest).
                Defaults to 1.
            limit (int, optional): Maximum number of records per page (max 50). Defaults to 50.
            on_prem (bool, optional): Specifies whether to use on-premises data server. If not provided, uses the class default.

        Returns:
            list: A list of maintenance module events matching the filters.

        Example:
            >>> events_handler = EventsHandler(user_id="my_user_id", data_url="data.url.com", ds_url="example_ds.com")
            >>> events = events_handler.get_maintenance_module_filter(
            ...     start_time="2023-01-01T00:00:00Z",
            ...     end_time="2023-01-31T23:59:59Z",
            ...     events=["failure", "maintenance"],
            ...     module_id="module123",
            ...     oldest_first=-1,
            ...     limit=50,
            ...     on_prem=True
            ... )
            >>> print(events)
            [{'id': 'evt001', 'moduleId': 'module123', 'event': 'failure', 'timestamp': 1672531200, ...}, ...]

        Raises:
            ValueError: If the provided time range is invalid (start_time is after end_time).
            requests.exceptions.RequestException: If an error occurs during the HTTP request, such as a network issue or timeout.
            Exception: If an unexpected error occurs during data retrieval, such as parsing JSON data or other unexpected issues.
        """
        try:
            # Convert start_time and end_time to iso utc timestamps
            start_time_unix = DataAccess(
                self.user_id, self.data_url, "", tz=self.tz
            ).time_to_unix(start_time)
            end_time_unix = DataAccess(
                self.user_id, self.data_url, "", tz=self.tz
            ).time_to_unix(end_time)

            # Validate that the start time is before the end time
            if end_time_unix < start_time_unix:
                raise ValueError(
                    f"Invalid time range: start_time({start_time}) should be before end_time({end_time})."
                )

            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem

            # Construct the URL based on the on_prem flag
            protocol = "http" if on_prem else "https"
            url = c.GET_MAINTENANCE_MODULE_FILTER.format(
                protocol=protocol, data_url=self.data_url
            )
            payload = {
                "userId": self.user_id,
                "moduleId": module_id,
                "startTime": start_time_unix,
                "endTime": end_time_unix,
                "events": events,
                "sortOrder": oldest_first,
            }
            page = 0
            all_data = []
            limit = max(0, min(limit, 50))

            while True:
                with Logger(self.logger, f"API {url} response time:", self.log_time):
                    # Make the request
                    response = requests.put(
                        url + f"/{page}/{limit}",
                        data=json.dumps(payload),
                        headers={
                            "Content-Type": "application/json",
                        },
                    )

                # Check the response status code
                response.raise_for_status()

                # Parse the JSON response
                response_content = response.json()

                if "data" not in response_content:
                    raise requests.exceptions.RequestException()

                # Append results
                data = response_content["data"]["data"]
                total_count = response_content["data"]["totalCount"]
                all_data.extend(data)

                # Stop if we’ve fetched everything OR not in fetch_all mode
                if len(all_data) >= total_count or not data:
                    break

                # Increment skip for next page
                page += 1

            return all_data

        except requests.exceptions.RequestException as e:
            error_message = (
                ERROR_MESSAGE(response, url)
                if "response" in locals()
                else f"\n[URL] {url}\n[EXCEPTION] {e}"
            )
            self.logger.error(f"[EXCEPTION] {type(e).__name__}: {error_message}")
            return []

        except (TypeError, ValueError) as e:
            self.logger.error(f"[EXCEPTION] {type(e).__name__}: {e}")
            return []

        except Exception as e:
            self.logger.error(f"[EXCEPTION] {e}")
            return []