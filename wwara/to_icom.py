#!/usr/bin/env python3
"""Converts a WWARA database dump to ICOM format."""
import codecs
import logging
from csv import DictReader, DictWriter
from decimal import Decimal
from io import BytesIO
from sys import stdout
from urllib.request import urlopen
from zipfile import ZipFile

LOG = logging.getLogger(__name__)

FIELDNAMES = (
    "Group No",
    "Group Name",
    "Name",
    "Sub Name",
    "Repeater Call Sign",
    "Gateway Call Sign",
    "Frequency",
    "Dup",
    "Offset",
    "Mode",
    "TONE",
    "Repeater Tone",
    "RPT1USE",
    "Position",
    "Latitude",
    "Longitude",
    "UTC Offset",
)

EXTRACT_URL = "https://www.wwara.org/DataBaseExtract.zip"


def _drop_decimals(decimal):
    """Decimal.normalize gives 2E+1 for 20..."""
    decimal = str(decimal)
    if "." in decimal:
        decimal = decimal.rstrip("0").rstrip(".")
    return decimal


def _supported(row):
    """Checks if the mode is supported."""
    if "Y" in (
        row["DMR"],
        row["P25_PHASE_1"],
        row["P25_PHASE_2"],
        row["NXDN_DIGITAL"],
        row["ATV"],
        row["DATV"],
    ):
        return False
    ifreq = Decimal(row["INPUT_FREQ"])
    if 144 < ifreq < 148:  # 2M
        return True
    if 420 < ifreq < 450:  # 70CM
        return True
    return False


def _offset(row):
    """Computes the correct frequency offset."""
    ifreq = Decimal(row["INPUT_FREQ"])
    ofreq = Decimal(row["OUTPUT_FREQ"])
    duplex = "OFF"
    offset = Decimal(0)
    if ofreq < ifreq:
        duplex = "DUP+"
        offset = ifreq - ofreq
    elif ofreq > ifreq:
        duplex = "DUP-"
        offset = ofreq - ifreq
    return duplex, _drop_decimals(offset)


def _mode(row):
    """Converts the mode per WWARA to the mode string for ICOM."""
    mode = "FM"
    if row["DSTAR_DV"] == "Y":
        mode = "DV"
    elif row["FM_WIDE"] == "Y":
        mode = "FM"
    elif row["FM_NARROW"] == "Y":
        mode = "FM-N"
    return mode


def _access(row):
    """Determines the access mode (like CTCSS)."""
    access = "OFF"
    tone = "88.5Hz"
    tsql = "88.5Hz"
    if row["CTCSS_IN"]:
        access = "TONE"
        tone = "{:.1f}Hz".format(Decimal(row["CTCSS_IN"]))
        if row["CTCSS_OUT"]:
            tsql = "{:.1f}Hz".format(Decimal(row["CTCSS_OUT"]))
    return access, tone, tsql


def _name(row, pending=False):
    """Formats a usable name for the repeater."""
    name = " ".join((row["CALL"], row["CITY"]))[:16]
    if pending:
        name = f"[{name[:14]}]"
    return name


def _call(row):
    """Builds an appropriate Call string for D-STAR."""
    call = row["CALL"]
    if row["DSTAR_DV"] == "N" and row["DSTAR_DD"] == "N":
        return call, None
    ifreq = Decimal(row["INPUT_FREQ"])
    if 144 < ifreq < 148:  # 2M
        return f"{call:<7}C", f"{call:<7}G"
    if 420 < ifreq < 450:  # 70CM
        return f"{call:<7}B", f"{call:<7}G"
    return call, None


def _position(row):
    """Returns the coordinates, or disables the position."""
    latitude = row["LATITUDE"]
    longitude = row["LONGITUDE"]
    position = "None"
    if latitude and longitude:
        position = "Approximate"
    return position, latitude or "0", longitude or "-0"


def convert(zipfile):
    """Converts a WWARA zipfile."""
    wlist = []
    for name in zipfile.namelist():
        if name.endswith(".csv"):
            pending = bool("-pending-" in name)
            with zipfile.open(name, "r") as csv:
                csv.readline()  # Remove DATA_SPEC_VERSION header
                for row in DictReader(codecs.getreader("us-ascii")(csv)):
                    if not _supported(row):
                        continue
                    duplex, offset = _offset(row)
                    mode = _mode(row)
                    name = _name(row, pending)
                    call, gateway = _call(row)
                    access, tone, _ = _access(row)
                    position, latitude, longitude = _position(row)
                    wlist.append(
                        {
                            "Group No": 7,
                            "Group Name": "WWARA",
                            "Name": name,
                            "Sub Name": row["LOCALE"][:8],
                            "Repeater Call Sign": call,
                            "Gateway Call Sign": gateway,
                            "Frequency": _drop_decimals(row["OUTPUT_FREQ"]),
                            "Dup": duplex,
                            "Offset": offset,
                            "Mode": mode,
                            "TONE": access,
                            "Repeater Tone": tone,
                            "RPT1USE": "YES",
                            "Position": position,
                            "Latitude": latitude,
                            "Longitude": longitude,
                            "UTC Offset": "-8:00",
                        }
                    )
    return sorted(wlist, key=lambda x: (x["Mode"], Decimal(x["Frequency"])))


def main():
    """Main entry point."""
    with urlopen(EXTRACT_URL) as response:
        zipfile = ZipFile(BytesIO(response.read()))

    writer = DictWriter(stdout, FIELDNAMES)
    writer.writeheader()
    writer.writerows(convert(zipfile))


if __name__ == "__main__":
    main()
