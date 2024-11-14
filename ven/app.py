from flask import Flask, render_template, redirect, url_for
import flask
import requests
import json
from datetime import datetime, timedelta
import threading
import time
import pprint
import random

VTN_URL = "http://localhost:8080/openadr3/3.0.1"

HEADERS = {
    "Content-type": "application/json",
    "Authorization": "Bearer ven_token"
}

# Tracks all the reservations for all resources.
reservations_by_hour_by_resource = {}


def _create_resources():
    reservations_by_hour_by_resource["Fremont Home"] = [0] * 24
    reservations_by_hour_by_resource["Palo Alto Home"] = [0] * 24
    reservations_by_hour_by_resource["Redwood City Home"] = [0] * 24


def _post_reservation_request(
        resource_name,
        start_hour,
        capacities,
        program_id = "0",
        event_id = "0"
):
    intervals_payload = []
    for i, capacity in enumerate(capacities):
        interval_payload = {
            "id": i,
            "payloads": [{
                "type": "IMPORT_CAPACITY_RESERVATION",
                "values": [capacity]
            }]
        }
        intervals_payload.append(interval_payload)

    payload = {
        "reportName": "capacityReservationReport",
        "programID": program_id,
        "eventID": event_id,
        "clientName": "myClient",
        "payloadDescriptors": [{
            "payloadType": "IMPORT_CAPACITY_RESERVATION",
            "units": "KW" # KWH originally
            }],
        "resources": [{
        "resourceName": resource_name,
        "intervalPeriod": {
            "start": f"2024-11-13T{start_hour}:00:00.000Z",
            "duration": "PT1H"
        },
        "intervals": intervals_payload
        }]
    }
    headers = HEADERS
    # print(json.dumps(payload, indent = 4))
    response = requests.post(f"{VTN_URL}/reports", json=payload, headers=headers)
    print(response.status_code)        
    return response


def is_peak_hour(hour):
    return 9 <= hour <= 21

def is_high_usage_hour(hour):
    return (6 <= hour << 10) or (17 <= hour <= 19)

if __name__ == "__main__":
    _create_resources()
    for current_hour in range(24):
        for resource_name in reservations_by_hour_by_resource.keys():
            # resource_index = random.randrange(len(reservations_by_hour_by_resource))
            # resource_name = list(reservations_by_hour_by_resource.keys())[resource_index]
            capacity_needed = 0
            if is_peak_hour(current_hour):
                capacity_needed += 2 + random.randrange(3)
            if is_high_usage_hour(current_hour):
                capacity_needed += 1 + random.randrange(3)
            # capacity_needed = random.randrange(8)
            # hours_needed = random.randrange(3)
            hours_needed = 1
            _post_reservation_request(
                resource_name=resource_name,
                start_hour=current_hour,
                capacities=[capacity_needed] * hours_needed
            )
        time.sleep(3)
