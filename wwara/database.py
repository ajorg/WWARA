#!/usr/bin/env python3
import codecs
from csv import DictReader
from io import BytesIO
from urllib.request import urlopen
from zipfile import ZipFile

from channel import Channel


def coordinations(filenames=False):
    with urlopen("https://www.wwara.org/DataBaseExtract.zip") as response:
        # ZipFile requires a file-like object that supports seek
        zipfile = ZipFile(BytesIO(response.read()))

    for name in zipfile.namelist():
        if not name.endswith(".csv"):
            continue
        if filenames:
            print(name)
        with zipfile.open(name, "r") as csv:
            # Remove the DATA_SPEC_VERSION header line from the .csv
            csv.readline()
            for row in DictReader(codecs.getreader("us-ascii")(csv)):
                # TODO Handle links?
                if row["LOCALE"] == "LINK":
                    continue
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
                yield Channel(
                    row["CALL"], row["OUTPUT_FREQ"], row["INPUT_FREQ"], bandwidth
                )
