#!/usr/bin/env python
"""Converts a WWARA database dump to GB3GF CSV format for GD-77."""
import codecs
import logging
from csv import DictReader, DictWriter
from decimal import Decimal
from io import BytesIO
from sys import stdout, stderr
from zipfile import ZipFile

LOG = logging.getLogger(__name__)

FIELDNAMES = (
    "Channel Number",
    "Channel Name",
    "Channel Type",
    "Rx Frequency",
    "Tx Frequency",
    "Colour Code",
    "Timeslot",
    "Contact",
    "TG List",
    "DMR ID",
    "RX Tone",
    "TX Tone",
    "Power",
    "Bandwidth",
    "Squelch",
    "Rx Only",
    "Zone Skip",
    "All Skip",
    "TOT",
    "VOX",
    "No Beep",
    "No Eco",
    None,
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
    if 144 <= ifreq <= 148:
        # 2M
        return True
    if 222 <= ifreq <= 225:
        # 70cm
        return False  # Could return true here
    if 420 <= ifreq <= 450:
        # 70cm
        return True
    return False


def _channel_name(row):
    """Formats a usable name for the repeater."""
    length = 16
    name = " ".join((row["CALL"], row["CITY"]))[:length]
    return name


def _channel_type(row):
    """Converts the mode per WWARA to the Channel Type per GD-77"""
    mode = "Analog"
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


def _zone(row):
    # TODO Zones have limits and the CPS fails import when it reaches them
    if _channel_type(row) == "Digital":
        return "DMR"
    return "None"


def _tone(tone, code):
    if not tone:
        if not code:
            return "None"
        return f"D{code}N"
    return f"{Decimal(tone):.1f}"


def _rx_tone(row):
    tone = row.get("CTCSS_OUT")
    code = row.get("DCS_CDCSS")
    return _tone(tone, code)


def _tx_tone(row):
    tone = row.get("CTCSS_IN")
    code = row.get("DCS_CDCSS")
    return _tone(tone, code)


def _bandwidth(row):
    if "Y" in (row.get("DMR"), row.get("FM_NARROW")):
        return "12.5KHz"
    return "25KHz"


def _entry(row, channel_number=0):
    channel_name = _channel_name(row)
    channel_type = _channel_type(row)
    rx_frequency = f"{Decimal(row['OUTPUT_FREQ']):.5f}"
    tx_frequency = f"{Decimal(row['INPUT_FREQ']):.5f}"
    color_code = _color_code(row)
    rx_tone = _rx_tone(row)
    tx_tone = _tx_tone(row)
    bandwidth = _bandwidth(row)
    return {
        "Channel Number": channel_number,
        "Channel Name": channel_name,
        "Channel Type": channel_type,
        "Rx Frequency": rx_frequency,
        "Tx Frequency": tx_frequency,
        "Colour Code": color_code,
        "Timeslot": 1,
        "Contact": "N/A",
        "TG List": "None",
        "DMR ID": "None",
        "RX Tone": rx_tone,
        "TX Tone": tx_tone,
        "Power": "Master",
        "Bandwidth": bandwidth,
        "Squelch": "Disabled",
        "Rx Only": "No",
        "Zone Skip": "No",
        "All Skip": "No",
        "TOT": 0,
        "VOX": "Off",
        "No Beep": "No",
        "No Eco": "No",
    }


def _order(name):
    if "-pending-" in name:
        return -3
    if "-rptrlist-" in name:
        return -4
    if "-About2Expire-" in name:
        return -2
    if "-Expired-" in name:
        return -1
    return 0


def _dedup_names(wlist):
    names = {}
    for entry in wlist:
        if entry["Channel Name"] in names:
            names[entry["Channel Name"]]["entries"].append(entry)
        else:
            names[entry["Channel Name"]] = {"entries": [entry]}
            names[entry["Channel Name"]]["dups"] = {
                "70cm": 0,
                "1.25m": 0,
                "2m": 0,
                "DMR": 0,
            }
        if entry["Channel Type"] == "Digital":
            names[entry["Channel Name"]]["dups"]["DMR"] += 1
        if entry["Rx Frequency"].startswith("1"):
            names[entry["Channel Name"]]["dups"]["2m"] += 1
        if entry["Rx Frequency"].startswith("2"):
            names[entry["Channel Name"]]["dups"]["1.25m"] += 1
        if entry["Rx Frequency"].startswith("4"):
            names[entry["Channel Name"]]["dups"]["70cm"] += 1
    for entry in sorted(
        wlist, key=lambda x: (x["Channel Name"], Decimal(x["Rx Frequency"]))
    ):
        if len(names[entry["Channel Name"]]["entries"]) > 1:
            freq = entry["Rx Frequency"].rstrip("0").rstrip(".")
            dups = names[entry["Channel Name"]]["dups"]
            if dups["DMR"] == 1 and entry["Channel Type"] == "Digital":
                tag = "D"
            elif dups["DMR"] == 1 and dups["2m"] <= 1 and dups["70cm"] <= 1:
                tag = ""
            elif dups["70cm"] == 1 and entry["Rx Frequency"].startswith("4"):
                tag = "70cm"
            elif dups["1.25m"] == 1 and entry["Rx Frequency"].startswith("2"):
                tag = "1.25m"
            elif dups["2m"] == 1 and entry["Rx Frequency"].startswith("1"):
                tag = "2m"
            elif (
                dups["70cm"] > 1
                and entry["Rx Frequency"].startswith("4")
                or dups["1.25m"] > 1
                and entry["Rx Frequency"].startswith("2")
                or dups["2m"] > 1
                and entry["Rx Frequency"].startswith("1")
            ):
                tag = freq
            length = 16 - len(tag)
            entry["Channel Name"] = entry["Channel Name"][:length].rstrip() + tag
    seen = set()
    for entry in wlist:
        if entry["Channel Name"] in seen:
            print(
                f"BUG! Duplicate names still exist! {entry['Channel Name']}",
                file=stderr,
            )
        else:
            seen.add(entry["Channel Name"])


def convert(zipfile):
    """Converts a WWARA zipfile."""
    wlist = []
    for name in sorted(zipfile.namelist(), key=_order):
        if name.endswith(".csv"):
            if "Expire" in name:
                continue
            print(name, file=stderr)
            with zipfile.open(name, "r") as csv:
                # Remove the DATA_SPEC_VERSION header line from the .csv
                csv.readline()
                for row in DictReader(codecs.getreader("us-ascii")(csv)):
                    if not _supported(row):
                        continue
                    wlist.append(_entry(row))
    _dedup_names(wlist)
    return sorted(wlist, key=lambda x: (x["Channel Type"], Decimal(x["Rx Frequency"])))


if __name__ == "__main__":
    from urllib.request import urlopen

    WRITER = DictWriter(stdout, FIELDNAMES, delimiter=";")
    WRITER.writeheader()
    with urlopen("https://www.wwara.org/DataBaseExtract.zip") as RESPONSE:
        # ZipFile requires a file-like object that supports seek
        with BytesIO(RESPONSE.read()) as FILE_OBJ:
            with ZipFile(FILE_OBJ) as ZIPFILE:
                WRITER.writerows(convert(ZIPFILE))
