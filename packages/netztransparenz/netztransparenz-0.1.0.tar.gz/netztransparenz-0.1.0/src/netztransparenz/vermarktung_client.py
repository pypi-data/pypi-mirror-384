"""
Client for all /vermarktung/ Endpoints and other Endpoints with market data like /Spotmarkpreise
"""

from netztransparenz.base_client import BaseNtClient
import requests
import datetime as dt
import io

import pandas as pd

_csv_date_format = "%Y-%m-%d %H:%M %Z"


class VermarktungClient(BaseNtClient):
    def __init__(self, client_id, client_pass):
        super().__init__(client_id, client_pass)

    def _basic_read_vermarktung(
        self,
        resource_url,
        dt_begin: dt.datetime | None = None,
        dt_end: dt.datetime | None = None,
        transform_dates=False,
        dateformat=_csv_date_format,
    ):
        """
        Internal method to read data in the format of most /vermarktung dataseries.
        Target format is: Dates separated in "datum", "von", "bis", "zeitzone".
        Return a pandas Dataframe with data of the endpoint specified with resource_url.
        If either dt_begin or dt_end is None, all available data will be queried.

            resource_url -- url of the endpoint without the base url and without leading or trailing "/"
            earliest_data -- first datapoint in the source collection
            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        url = f"{self._API_BASE_URL}/{resource_url}"
        if (dt_begin is not None) and (dt_end is not None):
            start_of_data = dt_begin.strftime(self._api_date_format)
            end_of_data = dt_end.strftime(self._api_date_format)
            url = f"{self._API_BASE_URL}/{resource_url}/{start_of_data}/{end_of_data}"

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
                df["Datum"] + " " + df["von"] + " " + df["Zeitzone von"],
                format=dateformat,
                utc=True,
            )
            df["bis"] = pd.to_datetime(
                df["Datum"] + " " + df["bis"] + " " + df["Zeitzone bis"],
                format=dateformat,
                utc=True,
            )
            # The end of timeframes may be 00:00 of the next day which is not correctly represented in timestamps
            df["bis"] = df["bis"].where(
                df["bis"].dt.time != dt.time(0, 0), df["bis"] + dt.timedelta(days=1)
            )
            df = df.drop(["Datum", "Zeitzone von", "Zeitzone bis"], axis=1).set_index(
                "von"
            )

        return df

    def _basic_read_negative_preise(
        self,
        resource_url,
        dt_begin: dt.datetime,
        dt_end: dt.datetime,
        transform_dates=False,
    ):
        """
        Internal method to read data in the format of the /NegativePreise dataseries.
        Target format is: Only two columns "Datum" and "Negativ", start and end dates not optional.
        Return a pandas Dataframe with data of the endpoint specified with resource_url.

            resource_url -- url of the endpoint without the base url and without leading or trailing "/"
            earliest_data -- first datapoint in the source collection
            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times as a string in the format "%Y-%m-%d %H:%M"
                               if this option resolves to "True" the times will be transformed into a
                               fully qualified timestamp. (default: False)
        """
        url = f"{self._API_BASE_URL}/{resource_url}/{dt_begin.strftime(self._api_date_format)}/{dt_end.strftime(self._api_date_format)}"

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
            df["Datum"] = pd.to_datetime(df["Datum"], format="%Y-%m-%d %H:%M")

        return df

    def vermarktung_differenz_einspeiseprognose(
        self,
        dt_begin: dt.datetime | None = None,
        dt_end: dt.datetime | None = None,
        transform_dates=False,
    ):
        """
        Return a pandas Dataframe with data of the endpoint /vermarktung/DifferenzEinspeiseprognose.
        If either dt_begin or dt_end is None, all available data will be queried.

            dt_begin -- datetime object for start of data in UTC (no values before: 2011-03-31T22:00:00)
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_vermarktung(
            "data/vermarktung/DifferenzEinspeiseprognose",
            dt_begin,
            dt_end,
            transform_dates,
        )

    def vermarktung_inanspruchnahme_ausgleichsenergie(
        self,
        dt_begin: dt.datetime | None = None,
        dt_end: dt.datetime | None = None,
        transform_dates=False,
    ):
        """
        Return a pandas Dataframe with data of the endpoint /vermarktung/InanspruchnahmeAusgleichsenergie.
        If either dt_begin or dt_end is None, all available data will be queried.

            dt_begin -- datetime object for start of data in UTC (no values before: 2011-03-31T22:00:00)
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_vermarktung(
            "data/vermarktung/InanspruchnahmeAusgleichsenergie",
            dt_begin,
            dt_end,
            transform_dates,
        )

    def vermarktung_untertaegige_strommengen(
        self,
        dt_begin: dt.datetime | None = None,
        dt_end: dt.datetime | None = None,
        transform_dates=False,
    ):
        """
        Return a pandas Dataframe with data of the endpoint /vermarktung/UntertaegigeStrommengen.
        If either dt_begin or dt_end is None, all available data will be queried.

            dt_begin -- datetime object for start of data in UTC (no values before: 2011-03-31T22:00:00)
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_vermarktung(
            "data/vermarktung/UntertaegigeStrommengen",
            dt_begin,
            dt_end,
            transform_dates,
        )

    def vermarktung_epex(
        self,
        dt_begin: dt.datetime | None = None,
        dt_end: dt.datetime | None = None,
        transform_dates=False,
    ):
        """
        Return a pandas Dataframe with data of the endpoint /vermarktung/VermarktungEpex.
        If either dt_begin or dt_end is None, all available data will be queried.

            dt_begin -- datetime object for start of data in UTC (no values before: 2011-12-31T22:00:00)
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_vermarktung(
            "data/vermarktung/VermarktungEpex", dt_begin, dt_end, transform_dates
        )

    def vermarktung_exaa(
        self,
        dt_begin: dt.datetime | None = None,
        dt_end: dt.datetime | None = None,
        transform_dates=False,
    ):
        """
        Return a pandas Dataframe with data of the endpoint /vermarktung/VermarktungExaa.
        If either dt_begin or dt_end is None, all available data will be queried.

            dt_begin -- datetime object for start of data in UTC (no values before: 2011-12-31T22:00:00)
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_vermarktung(
            "data/vermarktung/VermarktungExaa", dt_begin, dt_end, transform_dates
        )

    def vermarktung_solar(
        self,
        dt_begin: dt.datetime | None = None,
        dt_end: dt.datetime | None = None,
        transform_dates=False,
    ):
        """
        Return a pandas Dataframe with data of the endpoint /vermarktung/VermarktungsSolar.
        If either dt_begin or dt_end is None, all available data will be queried.

            dt_begin -- datetime object for start of data in UTC (no values before: 2013-12-31T23:00:00)
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_vermarktung(
            "data/vermarktung/VermarktungsSolar", dt_begin, dt_end, transform_dates
        )

    def vermarktung_wind(
        self,
        dt_begin: dt.datetime | None = None,
        dt_end: dt.datetime | None = None,
        transform_dates=False,
    ):
        """
        Return a pandas Dataframe with data of the endpoint /vermarktung/VermarktungsWind.
        If either dt_begin or dt_end is None, all available data will be queried.

            dt_begin -- datetime object for start of data in UTC (no values before: 2013-12-31T23:00:00)
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_vermarktung(
            "data/vermarktung/VermarktungsWind", dt_begin, dt_end, transform_dates
        )

    def vermarktung_sonstige(
        self,
        dt_begin: dt.datetime | None = None,
        dt_end: dt.datetime | None = None,
        transform_dates=False,
    ):
        """
        Return a pandas Dataframe with data of the endpoint /vermarktung/VermarktungsSonstige.
        If either dt_begin or dt_end is None, all available data will be queried.

            dt_begin -- datetime object for start of data in UTC (no values before: 2013-12-31T23:00:00)
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_vermarktung(
            "data/vermarktung/VermarktungsSonstige", dt_begin, dt_end, transform_dates
        )

    def spotmarktpreise(
        self,
        dt_begin: dt.datetime | None = None,
        dt_end: dt.datetime | None = None,
        transform_dates=False,
    ):
        """
        Return a pandas Dataframe with data of the endpoint /Spotmarktpreise.
        If either dt_begin or dt_end is None, all available data will be queried.

            dt_begin -- datetime object for start of data in UTC (no values before: 2013-12-31T23:00:00)
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_vermarktung(
            "data/Spotmarktpreise",
            dt_begin,
            dt_end,
            transform_dates=transform_dates,
            dateformat="%d.%m.%Y %H:%M %Z",
        )

    def negative_preise_1h(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NegativePreise/1.
        dt_begin and dt_end should not be too far apart since the api may throw an error for spans more than a year.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times as a string in the format "%Y-%m-%d %H:%M"
                               if this option resolves to "True" the times will be transformed into a
                               fully qualified timestamp. (default: False)
        """
        return self._basic_read_negative_preise(
            "data/NegativePreise/1", dt_begin, dt_end, transform_dates
        )

    def negative_preise_3h(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NegativePreise/1.
        dt_begin and dt_end should not be too far apart since the api may throw an error for spans more than a year.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times as a string in the format "%Y-%m-%d %H:%M"
                               if this option resolves to "True" the times will be transformed into a
                               fully qualified timestamp. (default: False)
        """
        return self._basic_read_negative_preise(
            "data/NegativePreise/3", dt_begin, dt_end, transform_dates
        )

    def negative_preise_4h(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NegativePreise/1.
        dt_begin and dt_end should not be too far apart since the api may throw an error for spans more than a year.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times as a string in the format "%Y-%m-%d %H:%M"
                               if this option resolves to "True" the times will be transformed into a
                               fully qualified timestamp. (default: False)
        """
        return self._basic_read_negative_preise(
            "data/NegativePreise/4", dt_begin, dt_end, transform_dates
        )

    def negative_preise_6h(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NegativePreise/1.
        dt_begin and dt_end should not be too far apart since the api may throw an error for spans more than a year.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times as a string in the format "%Y-%m-%d %H:%M"
                               if this option resolves to "True" the times will be transformed into a
                               fully qualified timestamp. (default: False)
        """
        return self._basic_read_negative_preise(
            "data/NegativePreise/6", dt_begin, dt_end, transform_dates
        )

    def jahresmarktpraemie(self, year: int | None = None):
        """
        Return a pandas Dataframe with data of the endpoint /Jahresmarktpraemie.
        If no year is given, all available data will be queried.

            year -- int representation of the year to get the data for (earliest data: 2020)
        """
        url = f"{self._API_BASE_URL}/data/Jahresmarktpraemie/"
        if year is not None:
            url = url + str(year)

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
        return df

    def marktpraemie(self, dt_begin: dt.date, dt_end: dt.date, transform_dates=False):
        """
        Return a pandas Dataframe with data of the endpoint /marktpraemie.
        Year & month of both start and end are extracted from dt_begin and dt_end.

            dt_begin -- date object for start of data (day will be ignored)
            dt_end -- date object for end of data (day will be ignored)
            transform_dates -- data contains months in th format "1/2012"
        """
        url = f"{self._API_BASE_URL}/data/marktpraemie/{dt_begin.month}/{dt_begin.year}/{dt_end.month}/{dt_end.year}"
        response = requests.get(
            url, headers={"Authorization": "Bearer {}".format(self.token)}
        )
        response.raise_for_status()
        df = pd.read_csv(
            io.StringIO(response.text),
            sep=";",
            header=0,
            decimal=",",
            na_values=["N.A.", ""],
        )
        return df

    def id_aep(self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False):
        """
        Return a pandas Dataframe with data of the endpoint /IdAep.
        The raw data contains the columns: "Datum von;(Uhrzeit) von;Zeitzone;(Uhrzeit) bis;Zeitzone;ID AEP in €/MWh"
        Since pandas can not handle ambigious columns the 'Zeitzone' columns are renamed to 'Zeitzone von' and 'Zeitzone bis' respectively.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        url = f"{self._API_BASE_URL}/data/IdAep/{dt_begin.strftime(self._api_date_format)}/{dt_end.strftime(self._api_date_format)}"

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
        df.rename(
            columns={"Zeitzone": "Zeitzone von", "Zeitzone.1": "Zeitzone bis"},
            inplace=True,
        )

        if transform_dates:
            df["von"] = pd.to_datetime(
                df["Datum von"] + " " + df["(Uhrzeit) von"] + " " + df["Zeitzone von"],
                format=_csv_date_format,
                utc=True,
            )
            df["bis"] = pd.to_datetime(
                df["Datum von"] + " " + df["(Uhrzeit) bis"] + " " + df["Zeitzone bis"],
                format=_csv_date_format,
                utc=True,
            )
            # The end of timeframes may be 00:00 of the next day which is not correctly represented in timestamps
            df["bis"] = df["bis"].where(
                df["bis"].dt.time != dt.time(0, 0), df["bis"] + dt.timedelta(days=1)
            )
            df = df.drop(
                ["Datum von", "Zeitzone von", "Zeitzone bis"], axis=1
            ).set_index("von")

        return df
