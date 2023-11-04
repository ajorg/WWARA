#!/usr/bin/env python3
import codecs
from csv import DictReader
from decimal import Decimal
from io import BytesIO
from sys import stderr
from urllib.request import urlopen
from zipfile import ZipFile

from channel import Channel

EXTRACT_URL = "https://www.wwara.org/DataBaseExtract.zip"


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
        modes.append("D-STAR")
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


def coordinations(extract_url=EXTRACT_URL, filenames=False, file_obj=None):
    if file_obj is None:
        file_obj = urlopen(extract_url)
    # ZipFile requires a file-like object that supports seek
    zipfile = ZipFile(BytesIO(file_obj.read()))
    file_obj.close()

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
                dmr_cc = row["DMR_COLOR_CODE"]
                if dmr_cc:
                    dmr_cc = Decimal(dmr_cc.lstrip("C"))
                dstar_mode = None
                if row["DSTAR_DV"] == "Y":
                    dstar_mode = "DV"
                elif row["DSTAR_DD"] == "Y":
                    dstar_mode = "DD"
                p25_phase = None
                if row["P25_PHASE_2"] == "Y":
                    p25_phase = 2
                if row["P25_PHASE_1"] == "Y":
                    p25_phase = 1
                yield Channel(
                    call=row["CALL"],
                    output=Decimal(row["OUTPUT_FREQ"]),
                    input=Decimal(row["INPUT_FREQ"]),
                    bandwidth=_bandwidth(row),
                    modes=_modes(row),
                    output_tone=row["CTCSS_OUT"],
                    input_tone=row["CTCSS_IN"],
                    output_code=row["DCS_CDCSS"],
                    input_code=row["DCS_CDCSS"],
                    dmr_cc=dmr_cc,
                    dstar_mode=dstar_mode,
                    c4fm_dsq=row.get("FUSION_DSQ", "00"),
                    p25_phase=p25_phase,
                    p25_nac=row["P25_NAC"],
                    location=row["CITY"],
                    latitude=row["LATITUDE"],
                    longitude=row["LONGITUDE"],
                )


if __name__ == "__main__":
    for channel in coordinations(filenames=True):
        print(channel)
