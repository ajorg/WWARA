#!/usr/bin/env python
"""Converts a WWARA database dump to GB3GF CSV format for GD-77."""
import codecs
import logging
from csv import DictReader, DictWriter
from decimal import Decimal
from io import BytesIO, StringIO
from sys import stdout, stderr
from zipfile import ZipFile

LOG = logging.getLogger(__name__)

FIELDNAMES = (
    "Channel Number",
    "Channel Name",
    "Channel Type",
    "Rx Frequency",
    "Tx Frequency",
    "Color Code",
    "Timeslot",
    "Contact",
    "Rx Group",
    "Scanlist",
    "RX CTCSS",
    "TX CTCSS",
    "Power",
    "Bandwidth",
    "Rx Only",
    "Squelch",
    "Skip",
    "Tx Admit",
    "TOT",
    "TOT Rekey",
    "Tx Signaling",
    "Rx Signaling",
    "Privacy Group",
    "Emergency System",
    "Flags1",
    "Flags2",
    "Flags3",
    "Flags4",
    "Unknown25",
    "Unknown26",
    "Unknown30",
    "Unknown36",
    "Unknown38",
    "Unknown40",
    "Unknown52",
    "Unknown53",
    "Unknown54",
    "Unknown55",
)


def _drop_decimals(decimal):
    """Decimal.normalize gives 2E+1 for 20..."""
    decimal = str(decimal)
    if "." in decimal:
        decimal = decimal.rstrip("0").rstrip(".")
    return decimal


def _supported(row):
    """Checks if the mode is supported."""
    if "Y" not in (row["DMR"], row["FM_WIDE"], row["FM_NARROW"]):
        return False
    ifreq = Decimal(row["INPUT_FREQ"])
    if ifreq > 144 and ifreq < 148:
        # 2M
        return True
    if ifreq > 420 and ifreq < 450:
        # 70CM
        return True
    return False


def _channel_name(row, prefix="", suffix=""):
    """Formats a usable name for the repeater."""
    length = 16 - len(prefix)
    name = prefix + " ".join((row["CALL"], row["CITY"]))[:length]
    if suffix:
        length = 16 - len(suffix)
        name = ("{:%d.%d}" % (length, length)).format(name) + suffix
    return name


def _channel_type(row):
    """Converts the mode per WWARA to the Channel Type per GD-77"""
    mode = "Analogue"
    if row["DMR"] == "Y":
        mode = "Digital"
    elif row["FM_WIDE"] == "Y":
        mode = "Analogue"
    elif row["FM_NARROW"] == "Y":
        mode = "Analogue"
    return mode


def _color_code(row):
    """Returns the DMR Color Code from the WWARA record"""
    color_code = row.get("DMR_COLOR_CODE").lstrip("CC")
    return color_code or "0"


def _rx_ctcss(row):
    rx_ctcss = row.get("CTCSS_OUT")
    if not rx_ctcss:
        rx_ctcss = "None"
    return rx_ctcss


def _tx_ctcss(row):
    tx_ctcss = row.get("CTCSS_IN")
    if not tx_ctcss:
        tx_ctcss = "None"
    return tx_ctcss


def _bandwidth(row):
    if row.get("FM_WIDE", "N") == "Y":
        return "25KHz"
    elif row.get("FM_NARROW", "N") == "Y":
        return "12.5KHz"


def _entry(row, channel_number, prefix="", suffix="", timeslot=None):
    channel_name = _channel_name(row, prefix, suffix)
    channel_type = _channel_type(row)
    rx_frequency = _drop_decimals(row["OUTPUT_FREQ"])
    tx_frequency = _drop_decimals(row["INPUT_FREQ"])
    color_code = _color_code(row)
    rx_ctcss = _rx_ctcss(row)
    tx_ctcss = _tx_ctcss(row)
    bandwidth = _bandwidth(row)
    return {
        "Channel Number": channel_number,
        "Channel Name": channel_name,
        "Channel Type": channel_type,
        "Rx Frequency": rx_frequency,
        "Tx Frequency": tx_frequency,
        "Color Code": color_code,
        "Timeslot": timeslot,
        "Contact": "None",
        "Rx Group": "None",
        "Scanlist": "None",
        "RX CTCSS": rx_ctcss,
        "TX CTCSS": tx_ctcss,
        "Power": "High",
        "Bandwidth": bandwidth,
        "Rx Only": "No",
        "Squelch": "Normal",
        "Skip": "No",
    }


def _order(name):
    if "-pending-" in name:
        return -3
    elif "-rptrlist-" in name:
        return -4
    elif "-About2Expire-" in name:
        return -2
    elif "-Expired-" in name:
        return -1
    return 0


def convert(zipfile):
    """Converts a WWARA zipfile."""
    wlist = []
    channel_number = 0
    for name in sorted(zipfile.namelist(), key=_order):
        if name.endswith(".csv"):
            print(name, file=stderr)
            prefix = ""
            if "-pending-" in name:
                prefix = "+"
            elif "-About2Expire-" in name:
                prefix = "-"
            elif "-Expired-" in name:
                prefix = "!"
            with zipfile.open(name, "r") as csv:
                # Remove the DATA_SPEC_VERSION header line from the .csv
                csv.readline()
                for row in DictReader(codecs.getreader("us-ascii")(csv)):
                    if not _supported(row):
                        continue
                    channel_number += 1
                    if row.get("DMR") == "Y":
                        timeslot = 1
                        wlist.append(
                            _entry(
                                row,
                                channel_number,
                                prefix,
                                " " + str(timeslot),
                                timeslot,
                            )
                        )
                        channel_number += 1
                        timeslot = 2
                        wlist.append(
                            _entry(
                                row,
                                channel_number,
                                prefix,
                                " " + str(timeslot),
                                timeslot,
                            )
                        )
                    elif "Y" in (row.get("FM_WIDE"), row.get("FM_NARROW")):
                        wlist.append(_entry(row, channel_number, prefix))
    return wlist
    return sorted(wlist, key=lambda x: (x["Channel Type"], Decimal(x["Rx Frequency"])))


if __name__ == "__main__":
    from urllib.request import urlopen

    with urlopen("https://www.wwara.org/DataBaseExtract.zip") as RESPONSE:
        # ZipFile requires a file-like object that supports seek
        FILE_OBJ = BytesIO(RESPONSE.read())
    ZIPFILE = ZipFile(FILE_OBJ)

    WRITER = DictWriter(stdout, FIELDNAMES)
    WRITER.writeheader()

    WRITER.writerows(convert(ZIPFILE))

    FILE_OBJ.close()
