from flask import Flask, render_template, redirect, url_for
import flask
import requests
import json
from datetime import datetime
import threading
import time

VTN_URL = "http://localhost:8080/openadr3/3.0.1"

HEADERS = {
    "Content-type": "application/json",
    "Authorization": "Bearer bl_token"
}

app = Flask(__name__)

@app.route("/")
def home():
    _create_program()
    _create_event()
    _setup_subscription()

    return render_template("index.html")


@app.route("/callbacks", methods=['POST'])
def callbacks():
    print("callbacks called")
    if flask.request.is_json:
        data = flask.request.get_json()
        # Process the webhook data here
        print("Received data:", data)
        # Respond with a 200 status code to acknowledge receipt
        return flask.jsonify({"status": "success"}), 200
    else:
        # Respond with a 400 status code for invalid requests
        return flask.jsonify({"status": "failure", "reason": "Invalid JSON"}), 400


def _create_program():
    with open("program.json", "r") as json_file:
        data = json.load(json_file)
    response = requests.post(
        f"{VTN_URL}/programs",
        headers=HEADERS,
        json=data
    )
    print("Create program, status code:", response.status_code)
    print("Create program, response Body:", response.json())


def _create_event():
    with open("event_minimal.json", "r") as json_file:
        data = json.load(json_file)
    response = requests.post(
        f"{VTN_URL}/events",
        headers=HEADERS,
        json=data
    )
    print("Create event, status code:", response.status_code)
    print("Create event, response Body:", response.json())


def _setup_subscription():
    with open("subscription.json", "r") as json_file:
        data = json.load(json_file)
    response = requests.post(
        f"{VTN_URL}/subscriptions",
        headers=HEADERS,
        json=data
    )
    print("Status Code:", response.status_code)
    print("Response Body:", response.json())


def poll_service():
    while True:
        try:
            response = requests.get(
                f"{VTN_URL}/reports",
                headers=HEADERS,
            )
            if response.status_code == 200:
                print("Polled service successfully:", response.json())
            else:
                print("Failed to poll service:", response.status_code)
        except Exception as e:
            print("Error polling service:", e)
        
        # Wait 5 seconds before polling again
        time.sleep(5)

if __name__ == "__main__":
    polling_thread = threading.Thread(target=poll_service, daemon=True)
    polling_thread.start()
    app.run(port=8081, debug=True)
