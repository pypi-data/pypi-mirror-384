"""
Client for all Endpoints of the "Systemdienstleistungen" Group
"""

from netztransparenz.base_client import BaseNtClient
import requests
import datetime as dt
import io

import pandas as pd


class DienstleistungenClient(BaseNtClient):
    def __init__(self, client_id, client_pass):
        super().__init__(client_id, client_pass)

    def _basic_read_systemdienstleistungen(
        self,
        resource_url,
        dt_begin: dt.datetime | None = None,
        dt_end: dt.datetime | None = None,
        transform_dates=False,
    ):
        """
        Internal method to read data in the format of most 'systemdienstleistungen' dataseries.
        Target format is: Dates separated in "BEGINN_DATUM", "BEGINN_UHRZEIT", "ENDE_DATUM",
        "ENDE_UHRZEIT", "ZEITZONE_VON", "ZEITZONE_BIS".
        Return a pandas Dataframe with data of the endpoint specified with resource_url.
        If either dt_begin or dt_end is None, all available data will be queried.

            resource_url -- url of the endpoint without the base url and without leading or trailing "/"
            earliest_data -- first datapoint in the source collection
            dt_begin -- datetime object for start of data in UTC (no values before: 2011-03-31T22:00:00)
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "BEGINN" and "ENDE" that contain fully qualified timestamps. (default: False)
        """
        url = f"{self._API_BASE_URL}/data/{resource_url}"
        if (dt_begin is not None) and (dt_end is not None):
            start_of_data = dt_begin.strftime(self._api_date_format)
            end_of_data = dt_end.strftime(self._api_date_format)
            url = f"{self._API_BASE_URL}/data/{resource_url}/{start_of_data}/{end_of_data}"

        response = requests.get(
            url, headers={"Authorization": "Bearer {}".format(self.token)}
        )
        response.raise_for_status()
        df = pd.read_csv(
            io.StringIO(response.text),
            sep=";",
            header=0,
            decimal=",",
            na_values=["N.A."],
        )

        if transform_dates:
            df["BEGINN"] = pd.to_datetime(
                df["BEGINN_DATUM"]
                + " "
                + df["BEGINN_UHRZEIT"]
                + " "
                + df["ZEITZONE_VON"],
                format="%d.%m.%Y %H:%M %Z",
                utc=True,
            ).dt.tz_localize(None)
            df["ENDE"] = pd.to_datetime(
                df["ENDE_DATUM"] + " " + df["ENDE_UHRZEIT"] + " " + df["ZEITZONE_BIS"],
                format="%d.%m.%Y %H:%M %Z",
                utc=True,
            ).dt.tz_localize(None)
            df = df.drop(
                [
                    "BEGINN_DATUM",
                    "BEGINN_UHRZEIT",
                    "ENDE_DATUM",
                    "ENDE_UHRZEIT",
                    "ZEITZONE_VON",
                    "ZEITZONE_BIS",
                ],
                axis=1,
            )

        return df

    def _basic_read_abregelung(
        self,
        resource_url,
        dt_begin: dt.datetime | None = None,
        dt_end: dt.datetime | None = None,
        transform_dates=False,
    ):
        """
        Internal method to read data in the format of most dataseries concerning power reduction.
        Target format is: Dates separated in "Datum", "Zeitzone", "von", "bis".
        Return a pandas Dataframe with data of the endpoint specified with resource_url.
        If either dt_begin or dt_end is None, all available data will be queried.

            resource_url -- url of the endpoint without the base url and without leading or trailing "/"
            earliest_data -- first datapoint in the source collection
            dt_begin -- datetime object for start of data in UTC (no values before: 2011-03-31T22:00:00)
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "BEGINN" and "ENDE" that contain fully qualified timestamps. (default: False)
        """
        url = f"{self._API_BASE_URL}/data/{resource_url}"
        if (dt_begin is not None) and (dt_end is not None):
            start_of_data = dt_begin.strftime(self._api_date_format)
            end_of_data = dt_end.strftime(self._api_date_format)
            url = f"{self._API_BASE_URL}/data/{resource_url}/{start_of_data}/{end_of_data}"

        response = requests.get(
            url, headers={"Authorization": "Bearer {}".format(self.token)}
        )
        response.raise_for_status()
        df = pd.read_csv(
            io.StringIO(response.text),
            sep=";",
            header=0,
            decimal=",",
            na_values=["N.A."],
        )

        if transform_dates:
            df["von"] = pd.to_datetime(
                df["Datum"] + " " + df["von"] + " " + df["Zeitzone"],
                format="%d.%m.%Y %H:%M %Z",
                utc=True,
            ).dt.tz_localize(None)
            df["bis"] = pd.to_datetime(
                df["Datum"] + " " + df["bis"] + " " + df["Zeitzone"],
                format="%d.%m.%Y %H:%M %Z",
                utc=True,
            ).dt.tz_localize(None)
            df = df.drop(["Datum", "Zeitzone"], axis=1)

        return df

    def redispatch(
        self,
        dt_begin: dt.datetime | None = None,
        dt_end: dt.datetime | None = None,
        transform_dates=False,
    ):
        """
        Return a pandas Dataframe with data of the endpoint /redispatch.
        If either dt_begin or dt_end is None, all available data will be queried.

            dt_begin -- datetime object for start of data in UTC (no values before: 2021-10-01T00:00:00)
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "BEGINN" and "ENDE" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_systemdienstleistungen(
            "redispatch", dt_begin, dt_end, transform_dates
        )

    def kapazitaetsreserve(
        self,
        dt_begin: dt.datetime | None = None,
        dt_end: dt.datetime | None = None,
        transform_dates=False,
    ):
        """
        Return a pandas Dataframe with data of the endpoint /Kapazitaetsreserve.
        If either dt_begin or dt_end is None, all available data will be queried.

            dt_begin -- datetime object for start of data in UTC (no values before: 2021-10-01T00:00:00)
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "BEGINN" and "ENDE" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_systemdienstleistungen(
            "Kapazitaetsreserve", dt_begin, dt_end, transform_dates
        )

    def vorhaltung_krd(
        self,
        dt_begin: dt.datetime | None = None,
        dt_end: dt.datetime | None = None,
        transform_dates=False,
    ):
        """
        Return a pandas Dataframe with data of the endpoint /VorhaltungkRD.
        If either dt_begin or dt_end is None, all available data will be queried.

            dt_begin -- datetime object for start of data in UTC (no values before: 2021-10-01T00:00:00)
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "BEGINN" and "ENDE" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_systemdienstleistungen(
            "VorhaltungkRD", dt_begin, dt_end, transform_dates
        )

    def ausgewiesene_absm(
        self,
        dt_begin: dt.datetime | None = None,
        dt_end: dt.datetime | None = None,
        transform_dates=False,
    ):
        """
        Return a pandas Dataframe with data of the endpoint /AusgewieseneABSM.
        If either dt_begin or dt_end is None, all available data will be queried.

            dt_begin -- datetime object for start of data in UTC (no values before: 2021-10-01T00:00:00)
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "BEGINN" and "ENDE" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_abregelung(
            "AusgewieseneABSM", dt_begin, dt_end, transform_dates
        )

    def zugeteilte_absm(
        self,
        dt_begin: dt.datetime | None = None,
        dt_end: dt.datetime | None = None,
        transform_dates=False,
    ):
        """
        Return a pandas Dataframe with data of the endpoint /ZugeteilteABSM.
        If either dt_begin or dt_end is None, all available data will be queried.

            dt_begin -- datetime object for start of data in UTC (no values before: 2021-10-01T00:00:00)
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "BEGINN" and "ENDE" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_abregelung(
            "ZugeteilteABSM", dt_begin, dt_end, transform_dates
        )

    def erzeugungsverbot(
        self,
        dt_begin: dt.datetime | None = None,
        dt_end: dt.datetime | None = None,
        transform_dates=False,
    ):
        """
        Return a pandas Dataframe with data of the endpoint /Erzeugungsverbot.
        If either dt_begin or dt_end is None, all available data will be queried.

            dt_begin -- datetime object for start of data in UTC (no values before: 2021-10-01T00:00:00)
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "BEGINN" and "ENDE" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_abregelung(
            "Erzeugungsverbot", dt_begin, dt_end, transform_dates
        )
