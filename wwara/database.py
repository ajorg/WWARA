#!/usr/bin/env python3
import codecs
from csv import DictReader
from decimal import Decimal
from io import BytesIO
from sys import stderr
from urllib.request import urlopen
from zipfile import ZipFile

from channel import Channel


def _bandwidth(row):
    bandwidth = "25"
    if "Y" in (
        row["FM_NARROW"],
        row["DSTAR_DV"],
        row["DSTAR_DD"],
        row["DMR"],
        row["FUSION"],
        row["P25_PHASE_1"],
        row["P25_PHASE_2"],
        row["NXDN_DIGITAL"],
        row["NXDN_MIXED"],
    ):
        bandwidth = "12.5"
    if row["FM_WIDE"] == "Y":
        bandwidth = "25"
    return Decimal(bandwidth)


def _modes(row):
    modes = []
    if "Y" in (row["FM_WIDE"], row["FM_NARROW"]):
        modes.append("FM")
    if "Y" in (row["DSTAR_DV"], row["DSTAR_DD"]):
        modes.append("DSTAR")
    if row["DMR"] == "Y":
        modes.append("DMR")
    if row["FUSION"] == "Y":
        modes.append("C4FM")
    if "Y" in (row["P25_PHASE_1"], row["P25_PHASE_2"]):
        modes.append("P25")
    if "Y" in (row["NXDN_DIGITAL"], row["NXDN_MIXED"]):
        modes.append("NXDN")
    if row["ATV"] == "Y":
        modes.append("ATV")
    return modes


def coordinations(filenames=False):
    with urlopen("https://www.wwara.org/DataBaseExtract.zip") as response:
        # ZipFile requires a file-like object that supports seek
        zipfile = ZipFile(BytesIO(response.read()))

    for name in zipfile.namelist():
        if not name.endswith(".csv"):
            continue
        if "Expire" in name:
            continue
        if filenames:
            print(name, file=stderr)
        with zipfile.open(name, "r") as csv:
            # Remove the DATA_SPEC_VERSION header line from the .csv
            csv.readline()
            for row in DictReader(codecs.getreader("us-ascii")(csv)):
                # TODO Handle links?
                if row["LOCALE"] == "LINK":
                    continue
                yield Channel(
                    call=row["CALL"],
                    output=Decimal(row["OUTPUT_FREQ"]),
                    input=Decimal(row["INPUT_FREQ"]),
                    bandwidth=_bandwidth(row),
                    modes=_modes(row),
                    output_tone=row["CTCSS_IN"],
                    input_tone=row["CTCSS_OUT"],
                    output_code=row["DCS_CDCSS"],
                    input_code=row["DCS_CDCSS"],
                )
