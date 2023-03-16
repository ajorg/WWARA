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
    "Data type",
    "Name",
    "Channel Type",
    "Rx Frequency",
    "Tx Frequency",
    "Color Code",
    "Timeslot",
    "Contact",
    "Contact Type",
    "Contact Id",
    "Rx Group",
    "Scanlist",
    "Zone",
    "RX CTCSS",
    "TX CTCSS",
    "Power",
    "Bandwidth",
    "Rx Only",
    "Squelch",
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
    "RssiThreshold",
    "VoiceEmphasis",
    "TxSignaling",
    "UnmuteRule",
    "RxSignaling",
    "ArtsInterval",
    "Optional DMRID",
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


def _name(row, prefix=""):
    """Formats a usable name for the repeater."""
    length = 16 - len(prefix)
    name = prefix + " ".join((row["CALL"], row["CITY"]))[:length]
    return name


def _channel_type(row):
    """Converts the mode per WWARA to the Channel Type per GD-77"""
    mode = "Analog"
    if row["DMR"] == "Y":
        mode = "Digital"
    elif row["FM_WIDE"] == "Y":
        mode = "Analog"
    elif row["FM_NARROW"] == "Y":
        mode = "Analog"
    return mode


def _color_code(row):
    """Returns the DMR Color Code from the WWARA record"""
    color_code = row.get("DMR_COLOR_CODE").lstrip("CC")
    return color_code or "0"


def _zone(row):
    # TODO Zones have limits and the CPS fails import when it reaches them
    if _channel_type(row) == "Digital":
        return "DMR"
    else:
        return "None"


def _ctcss(tone):
    if not tone:
        return "None"
    return "{:.1f}".format(Decimal(tone))


def _rx_ctcss(row):
    return _ctcss(row.get("CTCSS_OUT"))


def _tx_ctcss(row):
    return _ctcss(row.get("CTCSS_IN"))


def _bandwidth(row):
    if row.get("FM_WIDE") == "Y":
        return "25"
    elif "Y" in (row.get("DMR"), row.get("FM_NARROW")):
        return "12.5"


def _entry(row, prefix=""):
    name = _name(row, prefix)
    channel_type = _channel_type(row)
    rx_frequency = "{:.5f}".format(Decimal(row["OUTPUT_FREQ"]))
    tx_frequency = "{:.5f}".format(Decimal(row["INPUT_FREQ"]))
    color_code = _color_code(row)
    zone = _zone(row)
    rx_ctcss = _rx_ctcss(row)
    tx_ctcss = _tx_ctcss(row)
    bandwidth = _bandwidth(row)
    # Bits (low to high)
    # 0|0x01: Squelch
    # 1|0x02: 25 KHz
    # 2|0x04: RX Only
    # 3|0x08: 
    # 4|0x10: All Skip
    # 5|0x20: Zone Skip
    # 6|0x40: Vox
    # 7|0x80: Power
    # 1   = 00000001: LP 12.5 KHz 
    # 17  = 00010001: LP 12.5 KHz All-skip
    # 129 = 10000001: HP 12.5 KHz
    # 131 = 10000011: HP 25 KHz
    # 135 = 10000111: HP 25 KHz Rx-only
    # 151 = 10010111: HP 25 KHz Rx-only All-skip
    flags = 0x80 | 0x01
    if bandwidth == "25":
        flags |= 0x02
    return {
        "Data type": "CH_DATA",
        "Name": name,
        "Channel Type": channel_type,
        "Rx Frequency": rx_frequency,
        "Tx Frequency": tx_frequency,
        "Color Code": color_code,
        "Timeslot": 1,
        "Contact": "N/A",
        "Contact Type": 0,
        "Contact Id": "N/A",
        "Rx Group": "None",
        "Scanlist": "None",
        "Zone": zone,
        "RX CTCSS": rx_ctcss,
        "TX CTCSS": tx_ctcss,
        "Power": "Master",
        "Bandwidth": bandwidth,
        "Rx Only": "No",
        "Squelch": "Master",
        "Tx Admit": 0,
        "TOT": 0,
        "TOT Rekey": 0,
        "Tx Signaling": 0,
        "Rx Signaling": 0,
        "Privacy Group": 0,
        "Emergency System": 0,
        "Flags1": 0,
        "Flags2": 0,
        "Flags3": 0,
        "Flags4": flags,
        "RssiThreshold": -80,
        "VoiceEmphasis": 0,
        "TxSignaling": 0,
        "UnmuteRule": 0,
        "RxSignaling": 0,
        "ArtsInterval": 0,
        "Optional DMRID": None,
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


def _dedup_names(wlist):
    names = {}
    for entry in wlist:
        if entry["Name"] in names:
            names[entry["Name"]]["entries"].append(entry)
        else:
            names[entry["Name"]] = {"entries": [entry]}
            names[entry["Name"]]["dups"] = {"70cm": 0, "2m": 0, "DMR": 0}
        if entry["Channel Type"] == "Digital":
            names[entry["Name"]]["dups"]["DMR"] += 1
        if entry["Rx Frequency"].startswith("1"):
            names[entry["Name"]]["dups"]["2m"] += 1
        if entry["Rx Frequency"].startswith("4"):
            names[entry["Name"]]["dups"]["70cm"] += 1
    for entry in sorted(wlist, key=lambda x: (x["Name"], Decimal(x["Rx Frequency"]))):
        if len(names[entry["Name"]]["entries"]) > 1:
            freq = entry["Rx Frequency"].rstrip("0").rstrip(".")
            dups = names[entry["Name"]]["dups"]
            if dups["DMR"] == 1 and entry["Channel Type"] == "Digital":
                tag = "|D"
            elif dups["DMR"] == 1 and dups["2m"] <= 1 and dups["70cm"] <= 1:
                tag = ""
            elif dups["70cm"] == 1 and entry["Rx Frequency"].startswith("4"):
                tag = "70cm"
            elif dups["2m"] == 1 and entry["Rx Frequency"].startswith("1"):
                tag = "2m"
            elif (dups["70cm"] > 1 and entry["Rx Frequency"].startswith("4")) or (dups["2m"] > 1 and entry["Rx Frequency"].startswith("1")):
                tag = freq
            length = 16 - len(tag)
            entry["Name"] = entry["Name"][:length].rstrip() + tag

def convert(zipfile):
    """Converts a WWARA zipfile."""
    wlist = []
    for name in sorted(zipfile.namelist(), key=_order):
        if name.endswith(".csv"):
            print(name, file=stderr)
            prefix = ""
            if "-pending-" in name:
                prefix = "+"
            elif "-About2Expire-" in name:
                prefix = "-"
                continue
            elif "-Expired-" in name:
                prefix = "!"
                continue
            with zipfile.open(name, "r") as csv:
                # Remove the DATA_SPEC_VERSION header line from the .csv
                csv.readline()
                for row in DictReader(codecs.getreader("us-ascii")(csv)):
                    if not _supported(row):
                        continue
                    wlist.append(_entry(row, prefix))
    _dedup_names(wlist)
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
