#!/usr/bin/env python
"""Converts a WWARA database dump to MM7DBT Codeplug Editor CSV format for GD-88."""
import codecs
import logging
from csv import DictReader, DictWriter
from decimal import Decimal
from io import BytesIO
from sys import stdout, stderr
from zipfile import ZipFile

LOG = logging.getLogger(__name__)

FIELDNAMES = (
    "Zone",
    "CH Num",
    "CH Name",
    "RX Freq",
    "TX Freq",
    "RX TS",
    "TX TS",
    "RX CC",
    "TX CC",
    "Type",
    "Power",
    "Bandwidth",
    "RX Only",
    "Contact Name",
    "RX Group Name",
    "Scan List Name",
    "Alarm",
    "Prompt",
    "PCT",
    "MSG Type",
    "TX Policy",
    "EAS",
    "TX Tone Type",
    "TX Tone",
    "RX Tone Type",
    "RX Tone",
    "APRS CH",
    "Relay Monitor",
    "Relay Mode",
)
NAME_LENGTH = 10


def _supported(row):
    """Checks if the mode is supported."""
    if "Y" not in (row["DMR"], row["FM_WIDE"], row["FM_NARROW"]):
        return False
    freq = Decimal(row["OUTPUT_FREQ"])
    if 136 <= freq <= 174:
        # 2m
        return True
    if 400 <= freq <= 480:
        # 70cm
        return True
    return False


def _zone(row):
    if row["DMR"] == "Y":
        return "WWARA DMR"
    freq = Decimal(row["OUTPUT_FREQ"])
    if 136 <= freq <= 174:
        return "WWARA VHF"
    if 400 <= freq <= 480:
        return "WWARA UHF"
    return None


def _channel_name(row):
    """Formats a usable name for the repeater."""
    name = " ".join((row["CALL"], row["CITY"]))[:NAME_LENGTH]
    return name


def _channel_type(row):
    """Converts the mode per WWARA to the Channel Type per GD-77"""
    mode = "ANALOG"
    if row["DMR"] == "Y":
        mode = "DIGITAL"
    elif row["FM_WIDE"] == "Y":
        mode = "ANALOG"
    elif row["FM_NARROW"] == "Y":
        mode = "ANALOG"
    return mode


def _color_code(row):
    """Returns the DMR Color Code from the WWARA record"""
    color_code = row.get("DMR_COLOR_CODE").lstrip("CC")
    return color_code or "0"


def _tone(tone, code):
    tone_type = "OFF"
    tone_value = "0"
    if tone:
        tone_type = "CTCSS"
        tone_value = f"{Decimal(tone):.1f}"
    elif code:
        tone_type = "DCS"
        tone_value = code
    return tone_type, tone_value


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


def _entry(row, ch_num=0):
    zone = _zone(row)
    ch_name = _channel_name(row)
    ch_type = _channel_type(row)
    rx_freq = str(int(Decimal(row["OUTPUT_FREQ"]) * 1000000))
    tx_freq = str(int(Decimal(row["INPUT_FREQ"]) * 1000000))
    color_code = _color_code(row)
    rx_tone_type, rx_tone = _rx_tone(row)
    tx_tone_type, tx_tone = _tx_tone(row)
    bandwidth = _bandwidth(row)
    return {
        "Zone": zone,
        "CH Num": ch_num,
        "CH Name": ch_name,
        "RX Freq": rx_freq,
        "TX Freq": tx_freq,
        "RX TS": 1,
        "TX TS": 1,
        "RX CC": color_code,
        "TX CC": color_code,
        "Type": ch_type,
        "Power": "HIGH",
        "Bandwidth": bandwidth,
        "RX Only": "OFF",
        "Contact Name": "OFF",
        "RX Group Name": "OFF",
        "Scan List Name": "OFF",
        "Alarm": "OFF",
        "Prompt": "OFF",
        "PCT": "PATCS",
        "MSG Type": "UNCONFIRMED",
        "TX Policy": "IMPOLITE",
        "EAS": "OFF",
        "TX Tone Type": tx_tone_type,
        "TX Tone": tx_tone,
        "RX Tone Type": rx_tone_type,
        "RX Tone": rx_tone,
        "APRS CH": 0,
        "Relay Monitor": "OFF",
        "Relay Mode": "OFF",
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
        if entry["CH Name"] in names:
            names[entry["CH Name"]]["entries"].append(entry)
        else:
            names[entry["CH Name"]] = {"entries": [entry]}
            names[entry["CH Name"]]["dups"] = {
                "70cm": 0,
                "1.25m": 0,
                "2m": 0,
                "DMR": 0,
            }
        if entry["Type"] == "DIGITAL":
            names[entry["CH Name"]]["dups"]["DMR"] += 1
        if entry["RX Freq"].startswith("1"):
            names[entry["CH Name"]]["dups"]["2m"] += 1
        if entry["RX Freq"].startswith("2"):
            names[entry["CH Name"]]["dups"]["1.25m"] += 1
        if entry["RX Freq"].startswith("4"):
            names[entry["CH Name"]]["dups"]["70cm"] += 1
    for entry in sorted(wlist, key=lambda x: (x["CH Name"], Decimal(x["RX Freq"]))):
        if len(names[entry["CH Name"]]["entries"]) > 1:
            freq = entry["RX Freq"].rstrip("0").rstrip(".")
            dups = names[entry["CH Name"]]["dups"]
            if dups["DMR"] == 1 and entry["Type"] == "DIGITAL":
                tag = "D"
            elif dups["DMR"] == 1 and dups["2m"] <= 1 and dups["70cm"] <= 1:
                tag = ""
            elif dups["70cm"] == 1 and entry["RX Freq"].startswith("4"):
                tag = "U"
            elif dups["1.25m"] == 1 and entry["RX Freq"].startswith("2"):
                tag = "1.25m"
            elif dups["2m"] == 1 and entry["RX Freq"].startswith("1"):
                tag = "V"
            elif (
                (dups["70cm"] > 1 and entry["RX Freq"].startswith("4"))
                or (dups["1.25m"] > 1 and entry["RX Freq"].startswith("2"))
                or (dups["2m"] > 1 and entry["RX Freq"].startswith("1"))
            ):
                tag = freq[2:]
            length = NAME_LENGTH - len(tag)
            entry["CH Name"] = entry["CH Name"][:length] + tag
    seen = set()
    for entry in wlist:
        if entry["CH Name"] in seen:
            print(
                f"BUG! Duplicate names still exist! {entry['CH Name']}",
                file=stderr,
            )
        else:
            seen.add(entry["CH Name"])


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
    return sorted(wlist, key=lambda x: (x["Type"], Decimal(x["RX Freq"])))


if __name__ == "__main__":
    from urllib.request import urlopen

    WRITER = DictWriter(stdout, FIELDNAMES)
    WRITER.writeheader()
    with urlopen("https://www.wwara.org/DataBaseExtract.zip") as RESPONSE:
        # ZipFile requires a file-like object that supports seek
        with BytesIO(RESPONSE.read()) as FILE_OBJ:
            with ZipFile(FILE_OBJ) as ZIPFILE:
                WRITER.writerows(convert(ZIPFILE))
