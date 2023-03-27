#!/usr/bin/env python
"""Converts a WWARA database dump to GB3GF CSV format for GD-77."""
import logging
import re
from csv import DictWriter
from decimal import Decimal
from sys import stdout, stderr

from channel import Channel
from wwara.database import coordinations

LOG = logging.getLogger(__name__)

NAME_LENGTH = 16


class GB3GFChannel(Channel):
    fieldnames = [
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
    ]
    def __init__(self, channel):
        super().__init__(
            channel.call,
            channel.output,
            channel.input,
            bandwidth=channel.bandwidth,
            modes=channel.modes,
            output_tone=channel.output_tone,
            input_tone=channel.input_tone,
            output_code=channel.output_code,
            input_code=channel.input_code,
            dmr_cc=channel.dmr_cc,
            location=channel.location,
            latitude=channel.latitude,
            longitude=channel.latitude,
        )
        self._name = None

    @property
    def name(self):
        if self._name is None:
            self._name = " ".join((self.call, self.location))[:NAME_LENGTH]
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def _channel_type(self):
        mode = "Analogue"
        if "DMR" in self.modes:
            mode = "Digital"
        return mode

    @property
    def _rx_frequency(self):
        return f"{Decimal(self.output):.5f}"

    @property
    def _tx_frequency(self):
        return f"{Decimal(self.input):.5f}"

    @classmethod
    def _tone(cls, tone, code):
        if not tone:
            if not code:
                return "None"
            return f"D{code}N"
        return f"{Decimal(tone):.1f}"

    @property
    def _rx_tone(self):
        return self._tone(self.output_tone, self.output_code)

    @property
    def _tx_tone(self):
        return self._tone(self.input_tone, self.input_code)

    @property
    def _bandwidth(self):
        return f"{self.bandwidth}KHz"

    def __getitem__(self, key):
        if key == "Channel Name":
            return self.name
        if key == "Channel Type":
            return self._channel_type
        if key == "Rx Frequency":
            return self._rx_frequency
        raise KeyError(key)

    def get(self, key, default=None):
        for k, v in self.items():
            if k == key:
                return v
        return default

    def __setitem__(self, key, value):
        if key == "Channel Name":
            self.name = value
        else:
            raise KeyError(key)

    def keys(self):
        return {k: None for k in self.fieldnames}.keys()

    def items(self):
        yield "Channel Number", 0
        yield "Channel Name", self.name
        yield "Channel Type", self._channel_type
        yield "Rx Frequency", self._rx_frequency
        yield "Tx Frequency", self._tx_frequency
        yield "Colour Code", self.dmr_cc
        yield "Timeslot", 1
        yield "Contact", "N/A"
        yield "TG List", "None"
        yield "DMR ID", "None"
        yield "RX Tone", self._rx_tone
        yield "TX Tone", self._tx_tone
        yield "Power", "Master"
        yield "Bandwidth", self._bandwidth
        yield "Squelch", "Disabled"
        yield "Rx Only", "No"
        yield "Zone Skip", "No"
        yield "All Skip", "No"
        yield "TOT", 0
        yield "VOX", "Off"
        yield "No Beep", "No"
        yield "No Eco", "No"


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


def _dedup_names(
    elist,
    namek="Channel Name",
    typek="Channel Type",
    digital="Digital",
    outputk="Rx Frequency",
):
    names = {}
    for entry in elist:
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
    for entry in sorted(elist, key=lambda x: (x[namek], Decimal(x[outputk]))):
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
    for entry in elist:
        if entry[namek] in seen:
            print(
                f"BUG! Duplicate names still exist! {entry['Channel Name']}",
                file=stderr,
            )
        else:
            seen.add(entry[namek])


LAT = Decimal(47.80)
LON = Decimal(-122.25)


def channels():
    elist = []
    for channel in coordinations():
        if not _supported(channel) or channel.distance(LAT, LON) > 80:
            continue
        elist.append(GB3GFChannel(channel))
    _dedup_names(elist)
    with open("Channels.csv", "w") as channels_csv:
        writer = DictWriter(channels_csv, fieldnames=GB3GFChannel.fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(elist)


if __name__ == "__main__":
    channels()
