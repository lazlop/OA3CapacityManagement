from flask import Flask, render_template, redirect, url_for
import flask
import requests
import json
from datetime import datetime, timedelta
import threading
import time
import pprint

VTN_URL = "http://localhost:8080/openadr3/3.0.1"

HEADERS = {
    "Content-type": "application/json",
    "Authorization": "Bearer bl_token"
}

all_reports = {}
# For each hour in the day, we have 13 kW available
MAX_HOURLY_CAPACITY = 13
# Tracks all the reservations for all resources.
reservations_by_hour_by_resource = {}

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")


def _create_program() -> bool:
    data = load_json("program.json")
    response = requests.post(
        f"{VTN_URL}/programs",
        headers=HEADERS,
        json=data
    )
    if response.status_code == 201:
        print("Created program")
        return True
    # The program was already on the VTN
    if response.status_code == 409:
        print("Program already exists")
        return True

    print("Failed to create program")
    print("Create program, status code:", response.status_code)
    print("Create program, response body:", response.json())
    return False


# This event describes the capacity that VENs can request.
def _create_capacity_subscription_event():
    data = load_json("event_capacity_subscription.json")
    response = requests.post(
        f"{VTN_URL}/events",
        headers=HEADERS,
        json=data
    )
    if response.status_code == 201:
        print("Created capacity subscription event")
        return True
    print("Failed to create event")
    print("Create event, status code:", response.status_code)
    print("Create event, response body:", response.json())


def _parse_requested_capacity_hours(resource):
    hours = [0] * 24
    start_time_string = resource["intervalPeriod"]["start"]
    current_hour = datetime.strptime(start_time_string, "%Y-%m-%dT%H:%M:%S.%fZ").hour

    for interval in resource["intervals"]:
        for payload in interval["payloads"]:
            values = payload["values"]
            if len(values) == 1:
                value = values[0]
                hours[current_hour] += value
                current_hour += 1
            else:
                print("Report doesn't have single value in payload, ignoring")
    return hours


def _get_available_capacity_for_hour(hour) -> int:
    reserved_capacity = 0
    for reservations in reservations_by_hour_by_resource.values():
        reserved_capacity += reservations[hour]
    return MAX_HOURLY_CAPACITY - reserved_capacity


def _apply_capacity_request(resource_name, hours) -> bool:
    if resource_name not in reservations_by_hour_by_resource:
        reservations_by_hour_by_resource[resource_name] = [0] * 24

    for i in range(24):
        available_capacity = _get_available_capacity_for_hour(i)
        if _get_available_capacity_for_hour(i) < hours[i]:
            print(f"Not enough capacity for hour {i}, available: {available_capacity}, requested: {hours[i]}")
            return False

    for i in range(24):
        reservations_by_hour_by_resource[resource_name][i] += hours[i]
    return True


# Example report
# {'clientName': 'myClient',
#  'createdDateTime': '00:24:23',
#  'eventID': '0',
#  'id': '0',
#  'objectType': 'REPORT',
#  'payloadDescriptors': [{'objectType': 'REPORT_PAYLOAD_DESCRIPTOR',
#                          'payloadType': 'IMPORT_CAPACITY_RESERVATION',
#                          'units': 'KW'}],
#  'programID': '0',
#  'reportName': 'capacityReservationReport',
#  'resources': [{'intervalPeriod': {'duration': 'PT1H',
#                                    'start': '2024-11-13T8:00:00.000Z'},
#                 'intervals': [{'id': 0,
#                                'payloads': [{'type': 'IMPORT_CAPACITY_RESERVATION',
#                                              'values': [5]}]},
#                               {'id': 1,
#                                'payloads': [{'type': 'IMPORT_CAPACITY_RESERVATION',
#                                              'values': [4]}]}],
#                 'resourceName': 'Resource_1'}
#           ]
# }
def _handle_capacity_report(report):
    report_id = report["id"]
    if report_id in all_reports:
        return
    all_reports[report_id] = report

    pprint.pprint(report)
    resources = report["resources"]
    for resource in resources:
        # print("Resource:", resource)
        requested_capacity_hours = _parse_requested_capacity_hours(resource)
        resource_name = resource["resourceName"]
        _apply_capacity_request(resource_name, requested_capacity_hours)
        _post_capacity_reservation_event(ven_id=0, resource_name=resource_name)

        # start_time_string = resource["intervalPeriod"]["start"]
        # start_hour = datetime.strptime(start_time_string, "%Y-%m-%dT%H:%M:%S%z").hour
        # for interval in resource["intervals"]:
        #     print("Interval:", interval)
        #     for payload in interval["payloads"]:
        #         print("Payload:", payload)
        #         values = payload["values"]
        #         if len(values) == 1:
        #             value = values[0]
        #             _accept_reservation(ven_id=0, value=value, hour=start_hour)
        #             start_hour += 1
        #         else:
        #             print("Report doesn't have single value in payload, ignoring")


def create_date_string(hour):
    # Use today's date as the base date
    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Adjust the hour and format as ISO 8601 with milliseconds and 'Z'
    date_string = (base_date + timedelta(hours=hour)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    
    return date_string


def _create_interval_for_hour(hour, value):
    return {
        "id": hour,
        "intervalPeriod": {
            "start": create_date_string(hour),
            "duration": "PT1H"
        },
        "payloads": [
            {
                "type": "CAPACITY_AVAILABLE",
                "values": [value]
            },
        ],
    }


# Called once we have accepted or rejected a reservation.
# Lets VENs know how much their total reservation are.
def _post_capacity_reservation_event(ven_id, resource_name):
    with open("event_capacity_available.json", "r") as json_file:
        data = json.load(json_file)
    data["targets"][0]["values"] = [ven_id]

    reservations_by_hour = reservations_by_hour_by_resource[resource_name]
    for i in range(24):
        if reservations_by_hour[i] > 0:
            interval = _create_interval_for_hour(i, reservations_by_hour[i])
            data["intervals"].append(interval)

    response = requests.post(
        f"{VTN_URL}/events",
        headers=HEADERS,
        json=data
    )
    if response.status_code == 201:
        print("Posted capacity reservation event")
        return
    print("Failed to post capacity reservation event")
    print("Code:", response.status_code)
    print("Response Body:", response.json())


def poll_service():
    while True:
        try:
            response = requests.get(
                f"{VTN_URL}/reports",
                headers=HEADERS,
            )
            if response.status_code == 200:
                if len(response.json()) > 0:
                    print("Polled service, got reports", len(response.json()))
                    for report in response.json():
                        if report["reportName"] == "capacityReservationReport":
                            _handle_capacity_report(report)
            else:
                print("Failed to poll service:", response.status_code)
        except Exception as e:
            print("Error polling service:", e)
        
        # Wait 5 seconds before polling again
        time.sleep(5)


# TODO: This is not working so we'll just use polling for now.
# @app.route("/callbacks", methods=['POST'])
# def callbacks():
#     print("callbacks called")
#     if flask.request.is_json:
#         data = flask.request.get_json()
#         # Process the webhook data here
#         print("Received data:", data)
#         # Respond with a 200 status code to acknowledge receipt
#         return flask.jsonify({"status": "success"}), 200
#     else:
#         # Respond with a 400 status code for invalid requests
#         return flask.jsonify({"status": "failure", "reason": "Invalid JSON"}), 400


# def _setup_subscription():
#     with open("subscription.json", "r") as json_file:
#         data = json.load(json_file)
#     response = requests.post(
#         f"{VTN_URL}/subscriptions",
#         headers=HEADERS,
#         json=data
#     )
#     print("Status Code:", response.status_code)
#     print("Response Body:", response.json())


def load_json(file_name):
    with open(file_name, "r") as json_file:
        data = json.load(json_file)
    return data


if __name__ == "__main__":
    _create_program()
    _create_capacity_subscription_event()

    polling_thread = threading.Thread(target=poll_service, daemon=True)
    polling_thread.start()

    app.run(port=8081, debug=True)
