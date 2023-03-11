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
                yield Channel(row["CALL"], row["OUTPUT_FREQ"], row["INPUT_FREQ"])
