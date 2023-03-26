#!/usr/bin/env python
"""Converts a WWARA database dump to GB3GF CSV format for GD-77."""
import logging
import re
from csv import DictWriter
from decimal import Decimal
from sys import stdout, stderr

from wwara.database import coordinations

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
NAME_LENGTH = 16


def _supported(channel):
    """Checks if the mode is supported."""
    if "DMR" not in channel.modes and "FM" not in channel.modes:
        return False
    if 144 <= channel.input <= 148:
        # 2M
        return True
    if 222 <= channel.input <= 225:
        # 70cm
        return True  # Could return true here
    if 420 <= channel.input <= 450:
        # 70cm
        return True
    return False


def _channel_name(channel):
    """Formats a usable name for the repeater."""
    name = " ".join((channel.call, channel.location))[:NAME_LENGTH].rstrip(" ")
    return name


def _channel_type(channel):
    mode = "Analogue"
    if "DMR" in channel.modes:
        mode = "Digital"
    return mode


def _tone(tone, code):
    if not tone:
        if not code:
            return "None"
        return f"D{code}N"
    return f"{Decimal(tone):.1f}"


def _rx_tone(channel):
    return _tone(channel.output_tone, channel.output_code)


def _tx_tone(channel):
    return _tone(channel.input_tone, channel.input_code)


def _entry(channel, channel_number=0):
    channel_name = _channel_name(channel)
    channel_type = _channel_type(channel)
    rx_frequency = f"{Decimal(channel.output):.5f}"
    tx_frequency = f"{Decimal(channel.input):.5f}"
    color_code = channel.dmr_cc
    rx_tone = _rx_tone(channel)
    tx_tone = _tx_tone(channel)
    bandwidth = f"{channel.bandwidth}KHz"
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


def _dedup_names(
    wlist,
    namek="Channel Name",
    typek="Channel Type",
    digital="Digital",
    outputk="Rx Frequency",
):
    names = {}
    for entry in wlist:
        if entry[namek] in names:
            names[entry[namek]]["entries"].append(entry)
        else:
            names[entry[namek]] = {"entries": [entry]}
            names[entry[namek]]["dups"] = {
                "UHF": 0,
                "220": 0,
                "VHF": 0,
                "DMR": 0,
            }
        if entry[typek] == digital:
            names[entry[namek]]["dups"]["DMR"] += 1
        if entry[outputk].startswith("1"):
            names[entry[namek]]["dups"]["VHF"] += 1
        if entry[outputk].startswith("2"):
            names[entry[namek]]["dups"]["220"] += 1
        if entry[outputk].startswith("4"):
            names[entry[namek]]["dups"]["UHF"] += 1
    for entry in sorted(wlist, key=lambda x: (x[namek], Decimal(x[outputk]))):
        if len(names[entry[namek]]["entries"]) > 1:
            freq = entry[outputk].rstrip("0").replace(".", "")[2:]
            dups = names[entry[namek]]["dups"]
            if dups["DMR"] == 1 and entry[typek] == digital:
                tag = "D"
            elif dups["UHF"] == 1 and entry[outputk].startswith("4"):
                tag = "U"
            elif dups["220"] == 1 and entry[outputk].startswith("2"):
                tag = "2"
            elif dups["VHF"] == 1 and entry[outputk].startswith("1"):
                tag = "V"
            elif (
                (dups["UHF"] > 1 and entry[outputk].startswith("4"))
                or (dups["220"] > 1 and entry[outputk].startswith("2"))
                or (dups["VHF"] > 1 and entry[outputk].startswith("1"))
            ):
                tag = freq
            length = NAME_LENGTH - len(tag)
            entry[namek] = re.sub(
                " +", " ", entry[namek].ljust(NAME_LENGTH)[:length] + tag
            )
    seen = set()
    for entry in wlist:
        if entry[namek] in seen:
            print(
                f"BUG! Duplicate names still exist! {entry['Channel Name']}",
                file=stderr,
            )
        else:
            seen.add(entry[namek])


if __name__ == "__main__":
    WRITER = DictWriter(stdout, FIELDNAMES, delimiter=";")
    WRITER.writeheader()
    LIST = []
    for channel in coordinations():
        if _supported(channel):
            LIST.append(_entry(channel))
    _dedup_names(LIST)
    WRITER.writerows(
        sorted(LIST, key=lambda x: (x["Channel Type"], Decimal(x["Rx Frequency"])))
    )
