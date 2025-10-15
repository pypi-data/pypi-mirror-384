import os
import requests
import socket
import datetime


class SplunkLogger:
    def __init__(self):
        self.hec_url = os.getenv("SPLUNK_HEC_URL")
        self.hec_token = os.getenv("SPLUNK_HEC_TOKEN")

        if not self.hec_url:
            raise ValueError("SPLUNK_HEC_URL environment variable is not set.")
        if not self.hec_token:
            raise ValueError("SPLUNK_HEC_TOKEN environment variable is not set.")

        self.host = os.getenv("SPLUNK_HOST", socket.gethostname())
        self.source = os.getenv("SPLUNK_SOURCE", "RPA")
        self.sourcetype = os.getenv("SPLUNK_SOURCETYPE", "_json")
        self.index = os.getenv("SPLUNK_INDEX", "rdb")

    def log_event(self, event_data):
        if "Time" not in event_data:
            event_data["Time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if "Level" not in event_data:
            event_data["Level"] = "INFO"

        payload = {
            "host": self.host,
            "source": self.source,
            "sourcetype": self.sourcetype,
            "index": self.index,
            "event": event_data
        }

        resp = requests.post(
            f"{self.hec_url}/event",
            headers={"Authorization": f"Splunk {self.hec_token}"},
            json=payload,
            verify=False
        )
        resp.raise_for_status()

    def info(self, message, **kwargs):
        event_data = {"Message": message, "Level": "INFO"}
        event_data.update(kwargs)
        self.log_event(event_data)

    def error(self, message, **kwargs):
        event_data = {"Message": message, "Level": "ERROR"}
        event_data.update(kwargs)
        self.log_event(event_data)

    def warning(self, message, **kwargs):
        event_data = {"Message": message, "Level": "WARNING"}
        event_data.update(kwargs)
        self.log_event(event_data)
