"""
Inofficial wrapper for the API of the www.netztransparenz.de platform.

To access the API it is required to set up a free account and client in the
Netztransparenz extranet. (see: https://www.netztransparenz.de/en/Web-API)
"""

from .vermarktung_client import VermarktungClient
from .hochrechnung_client import HochrechnungClient
from .dienstleistungen_client import DienstleistungenClient
from .nrvsaldo_client import NrvSaldoClient


class NetztransparenzClient(
    VermarktungClient, HochrechnungClient, DienstleistungenClient, NrvSaldoClient
):
    def __init__(self, client_id, client_pass):
        super().__init__(client_id, client_pass)
