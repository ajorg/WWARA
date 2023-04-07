#!/usr/bin/env python3
import codecs
from csv import DictReader
from decimal import Decimal
from io import BytesIO
from sys import stderr
from urllib.request import urlopen
from zipfile import ZipFile

from channel import Channel

STOCK_CONFIG_URLS = {
    "FRS / GMRS": "https://raw.githubusercontent.com/kk7ds/chirp/master/chirp/stock_configs/US%20FRS%20and%20GMRS%20Channels.csv",
    "MURS": "https://raw.githubusercontent.com/kk7ds/chirp/master/chirp/stock_configs/US%20MURS%20Channels.csv",
    "Calling": "https://raw.githubusercontent.com/kk7ds/chirp/master/chirp/stock_configs/US%20Calling%20Frequencies.csv",
    "NOAA WX": "https://raw.githubusercontent.com/kk7ds/chirp/master/chirp/stock_configs/NOAA%20Weather%20Alert.csv",
    "Marine": "https://raw.githubusercontent.com/kk7ds/chirp/master/chirp/stock_configs/US%20Marine%20VHF%20Channels.csv",
    "Railroad": "https://raw.githubusercontent.com/kk7ds/chirp/master/chirp/stock_configs/US%20CA%20Railroad%20Channels.csv",
}


def _bandwidth(row):
    bandwidth = "25"
    if row["Mode"] in ("NFM",):
        bandwidth = "12.5"
    return Decimal(bandwidth)


def _modes(row):
    modes = []
    if row["Mode"] in ("FM", "NFM"):
        modes.append("FM")
    return modes


def stock_config(name):
    with urlopen(STOCK_CONFIG_URLS[name]) as response:
        for row in DictReader(codecs.getreader("us-ascii")(response)):
            output = Decimal(row["Frequency"])
            offset = Decimal((row["Duplex"] or "") + row["Offset"])
            channel = Channel(
                call=None,
                output=output,
                input=output + offset,
                bandwidth=_bandwidth(row),
                modes=_modes(row),
            )
            channel.name = row["Name"]
            yield channel


def stock_configs():
    for name in STOCK_CONFIG_URLS.keys():
        for channel in stock_config(name):
            yield channel


if __name__ == "__main__":
    for channel in stock_configs():
        print(channel)
