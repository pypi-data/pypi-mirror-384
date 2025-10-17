"""
Client for all Endpoints of the "NrvSaldo/" Group
"""

from netztransparenz.base_client import BaseNtClient
import requests
import datetime as dt
import io

import pandas as pd

_nrvsaldo_date_format = "%d.%m.%Y %H:%M %Z"


class NrvSaldoClient(BaseNtClient):
    def __init__(self, client_id, client_pass):
        super().__init__(client_id, client_pass)

    def _basic_read_nrvsaldo(
        self,
        resource_url,
        dt_begin: dt.datetime | None = None,
        dt_end: dt.datetime | None = None,
        transform_dates=False,
    ):
        """
        Internal method to read data in the format of most /nrvsaldo dataseries.
        Target format is: Dates separated in "Datum", "von", "bis", "Zeitzone".
        Return a pandas Dataframe with data of the endpoint specified with resource_url.
        If either dt_begin or dt_end is None, all available data will be queried.

            resource_url -- url of the endpoint without the base url and without leading or trailing "/"
            earliest_data -- first datapoint in the source collection
            dt_begin -- datetime object for start of data in UTC (no values before: 2011-03-31T22:00:00)
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        url = f"{self._API_BASE_URL}/data/{resource_url}"
        if (dt_begin is not None) and (dt_end is not None):
            start_of_data = dt_begin.strftime(self._api_date_format)
            end_of_data = dt_end.strftime(self._api_date_format)
            url = url + f"/{start_of_data}/{end_of_data}"

        response = requests.get(
            url, headers={"Authorization": "Bearer {}".format(self.token)}
        )
        response.raise_for_status()
        df = pd.read_csv(
            io.StringIO(response.text),
            sep=";",
            header=0,
            decimal=",",
            na_values=["N.A.", "N.E.", ""],
        )

        if transform_dates:
            df["von"] = pd.to_datetime(
                df["Datum"] + " " + df["von"] + " " + df["Zeitzone"],
                format=_nrvsaldo_date_format,
            ).dt.tz_convert(None)
            df["bis"] = pd.to_datetime(
                df["Datum"] + " " + df["bis"] + " " + df["Zeitzone"],
                format=_nrvsaldo_date_format,
            ).dt.tz_convert(None)
            # The end of timeframes may be 00:00 of the next day witch is not correctly represented in timestamps
            df["bis"] = df["bis"].where(
                df["bis"].dt.time != dt.time(0, 0), df["bis"] + dt.timedelta(days=1)
            )
            df = df.drop(["Datum", "Zeitzone"], axis=1).set_index("von")
        return df

    def traffic_light(self, dt_begin: dt.datetime, dt_end: dt.datetime):
        """
        Return a pandas Dataframe with data of the endpoint /TrafficLight.

            dt_begin -- datetime object for start of data in UTC (no values before: 2021-10-01T00:00:00)
            dt_end -- datetime object for end of data in UTC
        """
        url = f"{self._API_BASE_URL}/data/TrafficLight/{dt_begin.strftime(self._api_date_format)}/{dt_end.strftime(self._api_date_format)}"

        response = requests.get(
            url, headers={"Authorization": "Bearer {}".format(self.token)}
        )
        response.raise_for_status()
        df = pd.read_json(io.StringIO(response.text))

        return df

    def nrvsaldo_nrvsaldo_betrieblich(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NrvSaldo/NRVSaldo/Betrieblich/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_nrvsaldo(
            "NrvSaldo/NRVSaldo/Betrieblich", dt_begin, dt_end, transform_dates
        )

    def nrvsaldo_nrvsaldo_qualitaetsgesichert(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NrvSaldo/NRVSaldo/Qualitaetsgesichert/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_nrvsaldo(
            "NrvSaldo/NRVSaldo/Qualitaetsgesichert", dt_begin, dt_end, transform_dates
        )

    def nrvsaldo_rzsaldo_betrieblich(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NrvSaldo/RZSaldo/Betrieblich/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_nrvsaldo(
            "NrvSaldo/RZSaldo/Betrieblich", dt_begin, dt_end, transform_dates
        )

    def nrvsaldo_rzsaldo_qualitaetsgesichert(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NrvSaldo/RZSaldo/Qualitaetsgesichert/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_nrvsaldo(
            "NrvSaldo/RZSaldo/Qualitaetsgesichert", dt_begin, dt_end, transform_dates
        )

    def nrvsaldo_prl_betrieblich(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NrvSaldo/PRL/Betrieblich/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_nrvsaldo(
            "NrvSaldo/PRL/Betrieblich", dt_begin, dt_end, transform_dates
        )

    def nrvsaldo_prl_qualitaetsgesichert(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NrvSaldo/PRL/Qualitaetsgesichert/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_nrvsaldo(
            "NrvSaldo/PRL/Qualitaetsgesichert", dt_begin, dt_end, transform_dates
        )

    def nrvsaldo_aktivierte_srl_betrieblich(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /Nrvsaldo/AktivierteSRL/Betrieblich/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_nrvsaldo(
            "Nrvsaldo/AktivierteSRL/Betrieblich", dt_begin, dt_end, transform_dates
        )

    def nrvsaldo_aktivierte_srl_qualitaetsgesichert(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /Nrvsaldo/AktivierteSRL/Qualitaetsgesichert/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_nrvsaldo(
            "Nrvsaldo/AktivierteSRL/Qualitaetsgesichert",
            dt_begin,
            dt_end,
            transform_dates,
        )

    def nrvsaldo_aktivierte_mrl_betrieblich(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NrvSaldo/AktivierteMRL/Betrieblich/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_nrvsaldo(
            "NrvSaldo/AktivierteMRL/Betrieblich", dt_begin, dt_end, transform_dates
        )

    def nrvsaldo_aktivierte_mrl_qualitaetsgesichert(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NrvSaldo/AktivierteMRL/Qualitaetsgesichert/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_nrvsaldo(
            "NrvSaldo/AktivierteMRL/Qualitaetsgesichert",
            dt_begin,
            dt_end,
            transform_dates,
        )

    def nrvsaldo_srl_optimierung_betrieblich(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NrvSaldo/SRLOptimierung/Betrieblich/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_nrvsaldo(
            "NrvSaldo/SRLOptimierung/Betrieblich", dt_begin, dt_end, transform_dates
        )

    def nrvsaldo_srl_optimierung_qualitaetsgesichert(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NrvSaldo/SRLOptimierung/Qualitaetsgesichert/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_nrvsaldo(
            "NrvSaldo/SRLOptimierung/Qualitaetsgesichert",
            dt_begin,
            dt_end,
            transform_dates,
        )

    def nrvsaldo_mrl_optimierung_betrieblich(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NrvSaldo/MRLOptimierung/Betrieblich/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_nrvsaldo(
            "NrvSaldo/MRLOptimierung/Betrieblich", dt_begin, dt_end, transform_dates
        )

    def nrvsaldo_mrl_optimierung_qualitaetsgesichert(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NrvSaldo/MRLOptimierung/Qualitaetsgesichert/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_nrvsaldo(
            "NrvSaldo/MRLOptimierung/Qualitaetsgesichert",
            dt_begin,
            dt_end,
            transform_dates,
        )

    def nrvsaldo_mrl_mol_abweichungen_betrieblich(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NrvSaldo/MrlMolAbweichungen/Betrieblich/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_nrvsaldo(
            "NrvSaldo/MrlMolAbweichungen/Betrieblich", dt_begin, dt_end, transform_dates
        )

    def nrvsaldo_srl_mol_abweichungen_betrieblich(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NrvSaldo/SrlMolAbweichungen/betrieblich/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        url = f"{self._API_BASE_URL}/data/NrvSaldo/SrlMolAbweichungen/betrieblich"
        if (dt_begin is not None) and (dt_end is not None):
            start_of_data = dt_begin.strftime(self._api_date_format)
            end_of_data = dt_end.strftime(self._api_date_format)
            url = url + f"/{start_of_data}/{end_of_data}"

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

        if transform_dates:
            df["von"] = pd.to_datetime(
                df["Datum von"] + " " + df["Uhrzeit von"] + " " + df["Zeitzone von"],
                format=_nrvsaldo_date_format,
            ).dt.tz_convert(None)
            df["bis"] = pd.to_datetime(
                df["Datum bis"] + " " + df["Uhrzeit bis"] + " " + df["Zeitzone bis"],
                format=_nrvsaldo_date_format,
            ).dt.tz_convert(None)
            # The end of timeframes may be 00:00 of the next day witch is not correctly represented in timestamps
            df["bis"] = df["bis"].where(
                df["bis"].dt.time != dt.time(0, 0), df["bis"] + dt.timedelta(days=1)
            )
            df = df.drop(
                [
                    "Datum von",
                    "Uhrzeit von",
                    "Zeitzone von",
                    "Datum bis",
                    "Uhrzeit bis",
                    "Zeitzone bis",
                ],
                axis=1,
            ).set_index("von")
        return df

    def nrvsaldo_difference_betrieblich(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NrvSaldo/Difference/Betrieblich/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_nrvsaldo(
            "NrvSaldo/Difference/Betrieblich", dt_begin, dt_end, transform_dates
        )

    def nrvsaldo_difference_qualitaetsgesichert(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NrvSaldo/Difference/Qualitaetsgesichert/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_nrvsaldo(
            "NrvSaldo/Difference/Qualitaetsgesichert", dt_begin, dt_end, transform_dates
        )

    def nrvsaldo_abschaltbare_lasten_betrieblich(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NrvSaldo/AbschaltbareLasten/Betrieblich/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_nrvsaldo(
            "NrvSaldo/AbschaltbareLasten/Betrieblich", dt_begin, dt_end, transform_dates
        )

    def nrvsaldo_abschaltbare_lasten_qualitaetsgesichert(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NrvSaldo/AbschaltbareLasten/Qualitaetsgesichert/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_nrvsaldo(
            "NrvSaldo/AbschaltbareLasten/Qualitaetsgesichert",
            dt_begin,
            dt_end,
            transform_dates,
        )

    def nrvsaldo_zusatzmassnahmen_betrieblich(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NrvSaldo/Zusatzmassnahmen/Betrieblich/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_nrvsaldo(
            "NrvSaldo/Zusatzmassnahmen/Betrieblich", dt_begin, dt_end, transform_dates
        )

    def nrvsaldo_zusatzmassnahmen_qualitaetsgesichert(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NrvSaldo/Zusatzmassnahmen/Qualitaetsgesichert/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_nrvsaldo(
            "NrvSaldo/Zusatzmassnahmen/Qualitaetsgesichert",
            dt_begin,
            dt_end,
            transform_dates,
        )

    def nrvsaldo_nothilfe_betrieblich(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NrvSaldo/Nothilfe/Betrieblich/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_nrvsaldo(
            "NrvSaldo/Nothilfe/Betrieblich", dt_begin, dt_end, transform_dates
        )

    def nrvsaldo_nothilfe_qualitaetsgesichert(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NrvSaldo/Nothilfe/Qualitaetsgesichert/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_nrvsaldo(
            "NrvSaldo/Nothilfe/Qualitaetsgesichert", dt_begin, dt_end, transform_dates
        )

    def nrvsaldo_rebap_qualitaetsgesichert(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NrvSaldo/reBAP/Qualitaetsgesichert/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_nrvsaldo(
            "NrvSaldo/reBAP/Qualitaetsgesichert", dt_begin, dt_end, transform_dates
        )

    def nrvsaldo_aep_module_qualitaetsgesichert(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NrvSaldo/AEPModule/Qualitaetsgesichert/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_nrvsaldo(
            "NrvSaldo/AEPModule/Qualitaetsgesichert", dt_begin, dt_end, transform_dates
        )

    def nrvsaldo_aep_schaetzer_betrieblich(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NrvSaldo/AepSchaetzer/Betrieblich/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_nrvsaldo(
            "NrvSaldo/AepSchaetzer/Betrieblich", dt_begin, dt_end, transform_dates
        )

    def nrvsaldo_finanzielle_wirkung_aep_module_qualitaetsgesichert(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NrvSaldo/FinanzielleWirkungAEPModule/Qualitaetsgesichert/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_nrvsaldo(
            "NrvSaldo/FinanzielleWirkungAEPModule/Qualitaetsgesichert",
            dt_begin,
            dt_end,
            transform_dates,
        )

    def nrvsaldo_voaa_qualitaetsgesichert(
        self, dt_begin: dt.datetime, dt_end: dt.datetime, transform_dates=False
    ):
        """
        Return a pandas Dataframe with data of the endpoint /NrvSaldo/VoAA/Qualitaetsgesichert/.

            dt_begin -- datetime object for start of data in UTC
            dt_end -- datetime object for end of data in UTC
            transform_dates -- The data contains times with date, time and timezone in separate columns
                               if this option resolves to "True" the times will be transformed into two
                               columns "von" and "bis" that contain fully qualified timestamps. (default: False)
        """
        return self._basic_read_nrvsaldo(
            "NrvSaldo/VoAA/Qualitaetsgesichert", dt_begin, dt_end, transform_dates
        )
