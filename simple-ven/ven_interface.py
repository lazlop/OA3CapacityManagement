import requests
import json
from datetime import datetime, timedelta
# assuming 1 hour duration intervals
# not sure based on examples what the format of times should be
# may need to convert the time so that its format is always 2 digits, like 01 rather than 1
# kWh is used in the capacity request example, but doesn't make sense to me so using kW instead
HEADERS = {
            "Content-Type": "application/json",
            "Authorization": "Bearer ven_token"
        }

class CapacityAPIInterface:
    def __init__(self, api_url, client_name):
        """
        Initialize the API interface with the base API URL.
        
        Args:
        - api_url (str): The URL of the REST API endpoint to communicate with.
        """
        self.api_url = api_url
        self.client_name = client_name
    
    def get_capacity_event(self):
        r = requests.get("http://localhost:8080/openadr3/3.0.1/events", headers = HEADERS)
        # Should log the ID 
        return r

    def post_capacity_request(self, program_id, event_id, intervals):
        """
        Post a capacity request event to the REST API.
        
        Args:
        - program_id (str): The ID of the program.
        - event_id (str): The event ID.
        - intervals (list): List of intervals (start, duration). capacity_request_values (list): List of capacity values for each interval.
        
        Returns:
        - Response object from the POST request.
        """
        
        intervals_payload = []
        for i, interval in enumerate(intervals):
            interval_payload = {
                "id": i,
                "payloads": [{
                    "type": "IMPORT_CAPACITY_RESERVATION",
                    "values": [interval[1]]
                }]
            }
            intervals_payload.append(interval_payload)

        payload = {
            "reportName": "capacityReservationReport",
            "programID": program_id,
            "eventID": event_id,
            "clientName": self.client_name,
            "payloadDescriptors": [{
                "payloadType": "IMPORT_CAPACITY_RESERVATION",
                "units": "KW" # KWH originally
                }],
            "resources": [{
            "resourceName": self.client_name,
            "intervalPeriod": {
                "start": f"2024-11-13T{intervals[0][0]}:00:00.000Z",
                "duration": "PT1H"
            },
            "intervals": intervals_payload
            }]
        }
        headers = HEADERS
        # print(json.dumps(payload, indent = 4))
        response = requests.post(f"{self.api_url}/reports", json=payload, headers=headers)
        print(response.status_code)        
        return response