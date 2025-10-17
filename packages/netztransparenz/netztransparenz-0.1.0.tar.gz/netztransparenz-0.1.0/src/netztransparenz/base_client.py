"""
Base class for all other clients. Handles login and health check.
"""

import requests
import logging

log = logging.getLogger("BaseNtClient")
_ACCESS_TOKEN_URL = "https://identity.netztransparenz.de/users/connect/token"


class BaseNtClient:
    def __init__(self, client_id, client_pass):
        self._API_BASE_URL = "https://ds.netztransparenz.de/api/v1"
        self._api_date_format = "%Y-%m-%dT%H:%M:%S"
        self._csv_date_format = "%Y-%m-%d %H:%M %Z"

        response = requests.post(
            _ACCESS_TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_pass,
            },
        )

        if response.ok:
            self.token = response.json()["access_token"]
        else:
            message = (
                f"Error retrieving token\n{response.status_code}:{response.reason}"
            )
            log.error(message)
            raise Exception(f"Login failed. {message}")

    def check_health(self):
        """
        Return the text response of the API health endpoint.
        Any Response but "OK" indicates a problem.
        """

        url = f"{self._API_BASE_URL}/health"
        response = requests.get(
            url, headers={"Authorization": "Bearer {}".format(self.token)}
        )
        return response.text
