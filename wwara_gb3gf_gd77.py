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

LAT = Decimal(47.80)
LON = Decimal(-122.25)
RANGE = 80

NAME_LENGTH = 16


class GB3GFChannel(Channel):
    fieldnames = (
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
            longitude=channel.longitude,
            rx_only=channel.rx_only,
        )
        self._name = None
        self._number = 0

    @property
    def name(self):
        if self._name is None:
            self._name = " ".join((self.call, self.location))[:NAME_LENGTH]
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def number(self):
        return self._number

    @number.setter
    def number(self, value):
        self._number = value

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

    @property
    def _rx_only(self):
        if self.rx_only:
            return "Yes"
        return "No"

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
        elif key == "Channel Number":
            self.number = value
        else:
            raise KeyError(key)

    def keys(self):
        return {k: None for k in self.fieldnames}.keys()

    def items(self):
        yield "Channel Number", self.number
        yield "Channel Name", self.name
        yield "Channel Type", self._channel_type
        yield "Rx Frequency", self._rx_frequency
        yield "Tx Frequency", self._tx_frequency
        yield "Colour Code", self.dmr_cc or 0
        yield "Timeslot", 1
        yield "Contact", "N/A"
        yield "TG List", "None"
        yield "DMR ID", "None"
        yield "RX Tone", self._rx_tone
        yield "TX Tone", self._tx_tone
        yield "Power", "Master"
        yield "Bandwidth", self._bandwidth
        yield "Squelch", "Disabled"
        yield "Rx Only", self._rx_only
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
        return True
    if 222 <= channel.input <= 225:
        channel.rx_only = True
        return True
    if 420 <= channel.input <= 450:
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


def channels_csv(channels):
    with open("Channels.csv", "w") as _channels_csv:
        writer = DictWriter(
            _channels_csv, fieldnames=GB3GFChannel.fieldnames, delimiter=";"
        )
        writer.writeheader()
        writer.writerows(channels)


ZONES_FIELDNAMES = tuple(["Zone Name"] + ["Channel " + str(i) for i in range(1, 81)])


def zones_csv(channels):
    zones = {
        "WWARA VHF": {"mode": "FM", "low": 144, "high": 148},
        "WWARA 220": {"mode": "FM", "low": 222, "high": 225},
        "WWARA UHF": {"mode": "FM", "low": 420, "high": 450},
        "WWARA FM": {"mode": "FM", "low": 144, "high": 450},
        "WWARA DMR": {"mode": "DMR", "low": 144, "high": 450},
    }
    with open("Zones.csv", "w") as _zones_csv:
        writer = DictWriter(_zones_csv, fieldnames=ZONES_FIELDNAMES, delimiter=";")
        writer.writeheader()
        for name, spec in zones.items():
            zone = {"Zone Name": name}
            print(name, file=stderr)
            i = 1
            for channel in channels:
                if i > 80:
                    break
                if spec["mode"] not in channel.modes:
                    continue
                if not (spec["low"] <= channel.input <= spec["high"]):
                    continue
                print(f"{channel} {channel.distance(LAT, LON):.1f}", file=stderr)
                zone[f"Channel {i}"] = channel.name
                i += 1
            writer.writerow(zone)


if __name__ == "__main__":
    channels = []
    for channel in coordinations():
        if not _supported(channel):
            continue
        channels.append(GB3GFChannel(channel))
    _dedup_names(channels)
    # Sort channels in order of output frequency
    channels_csv(sorted(channels, key=lambda channel: channel.output))
    # Sort channels in zones in order of distance (closest first)
    zones_csv(sorted(channels, key=lambda channel: channel.distance(LAT, LON)))
