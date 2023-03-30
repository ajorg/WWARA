#!/usr/bin/env python
"""Converts a WWARA database dump to GD88DRS CSV format for GD-77."""
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

DELIMITER = ","
NAME_LENGTH = 10


class GD88DRSChannel(Channel):
    number_k = "Z-0"
    name_k = "CH Name"
    type_k = "CH mode"
    analog_v = "Analog"
    digital_v = "Digital"
    output_k = "RX Freq"
    input_k = "TX Freq"
    fieldnames = (
        number_k,
        type_k,
        name_k,
        output_k,
        input_k,
        "Power",
        "RX Only",
        "Alarm ACK",
        "Prompt",
        "PCT",
        "RX TS",
        "TX TS",
        "RX CC",
        "TX CC",
        "Msg Type",
        "TX Policy",
        "RX Group",
        "Encryption List",
        "Scan List",
        "Contacts",
        "EAS",
        "Relay Monitor",
        "Relay mode",
        "Bandwidth",
        "RX QT/DQT",
        "TX QT/DQT",
        "APRS",
    )
    timeslot = 1  # Class variable so it can be varied... not sure

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
        mode = self.analog_v
        if "DMR" in self.modes:
            mode = self.digital_v
        return mode

    @property
    def _rx_frequency(self):
        return f"{Decimal(self.output):.5f}"

    @property
    def _tx_frequency(self):
        return f"{Decimal(self.input):.5f}"

    @property
    def _timeslot(self):
        return f"Slot {self.timeslot}"

    @classmethod
    def _tone(cls, tone, code):
        if not tone:
            if not code:
                return "Off"
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
        return str(self.bandwidth).rstrip("0").rstrip(".")

    @property
    def _rx_only(self):
        if self.rx_only:
            return "Yes"
        return "No"

    def __getitem__(self, key):
        if key == self.name_k:
            return self.name
        if key == self.type_k:
            return self._channel_type
        if key == self.output_k:
            return self._rx_frequency
        raise KeyError(key)

    def get(self, key, default=None):
        for k, v in self.items():
            if k == key:
                return v
        return default

    def __setitem__(self, key, value):
        if key == self.name_k:
            self.name = value
        elif key == self.number_k:
            self.number = value
        else:
            raise KeyError(key)

    def keys(self):
        # This looks dumb, but the object keys() returns
        # has properties that are easiest to implement
        # this way.
        return dict(self.items()).keys()

    def items(self):
        yield self.number_k, self.number
        yield self.type_k, self._channel_type
        yield self.name_k, self.name
        yield self.output_k, self._rx_frequency
        yield self.input_k, self._tx_frequency
        yield "Power", "High"
        yield "RX Only", "Off"
        yield "Alarm ACK", "Off"
        yield "Prompt", "Off"  # What?
        yield "PCT", "Patcs"  # Something to do with trunking
        yield "RX TS", self._timeslot
        yield "TX TS", self._timeslot
        yield "RX CC", self.dmr_cc or 0
        yield "TX CC", self.dmr_cc or 0
        yield "Msg Type", "Unconfirmed"
        yield "TX Policy", "Impolite"  # BCLO
        yield "RX Group", "Off"  # TBD
        yield "Encryption List", "Off"
        yield "Scan List", "Off"
        yield "Contacts", "Off"  # TBD
        yield "EAS", "Off"
        yield "Relay Monitor", "Off"
        yield "Relay mode", "Off"
        yield "Bandwidth", self._bandwidth
        yield "RX QT/DQT", self._rx_tone
        yield "TX QT/DQT", self._tx_tone
        yield "APRS", "Off"


def _supported(channel):
    """Checks if the mode is supported."""
    if "DMR" not in channel.modes and "FM" not in channel.modes:
        return False
    if 144 <= channel.input <= 148:
        return True
    if 222 <= channel.input <= 225:
        # channel.rx_only = True
        # return True
        pass
    if 420 <= channel.input <= 450:
        return True
    return False


def _dedup_names(
    elist,
):
    name_k = elist[0].name_k
    type_k = elist[0].type_k
    digital_v = elist[0].digital_v
    output_k = elist[0].output_k
    names = {}
    for entry in elist:
        if entry[name_k] in names:
            names[entry[name_k]]["entries"].append(entry)
        else:
            names[entry[name_k]] = {"entries": [entry]}
            names[entry[name_k]]["dups"] = {
                "UHF": 0,
                "220": 0,
                "VHF": 0,
                "DMR": 0,
            }
        if entry[type_k] == digital_v:
            names[entry[name_k]]["dups"]["DMR"] += 1
        if entry[output_k].startswith("1"):
            names[entry[name_k]]["dups"]["VHF"] += 1
        if entry[output_k].startswith("2"):
            names[entry[name_k]]["dups"]["220"] += 1
        if entry[output_k].startswith("4"):
            names[entry[name_k]]["dups"]["UHF"] += 1
    for entry in sorted(elist, key=lambda x: (x[name_k], Decimal(x[output_k]))):
        if len(names[entry[name_k]]["entries"]) > 1:
            freq = entry[output_k].rstrip("0").replace(".", "")[2:]
            dups = names[entry[name_k]]["dups"]
            if dups["DMR"] == 1 and entry[type_k] == digital_v:
                tag = "D"
            elif dups["UHF"] == 1 and entry[output_k].startswith("4"):
                tag = "U"
            elif dups["220"] == 1 and entry[output_k].startswith("2"):
                tag = "2"
            elif dups["VHF"] == 1 and entry[output_k].startswith("1"):
                tag = "V"
            elif (
                (dups["UHF"] > 1 and entry[output_k].startswith("4"))
                or (dups["220"] > 1 and entry[output_k].startswith("2"))
                or (dups["VHF"] > 1 and entry[output_k].startswith("1"))
            ):
                tag = freq
            length = NAME_LENGTH - len(tag)
            entry[name_k] = re.sub(
                " +", " ", entry[name_k].ljust(NAME_LENGTH)[:length] + tag
            )
    seen = set()
    for entry in elist:
        if entry[name_k] in seen:
            print(
                f"BUG! Duplicate names still exist! {entry[name_k]}",
                file=stderr,
            )
        else:
            seen.add(entry[name_k])


def channels_csv(channels):
        writer = DictWriter(
            stdout, fieldnames=GD88DRSChannel.fieldnames, delimiter=DELIMITER
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
        channels.append(GD88DRSChannel(channel))
    _dedup_names(channels)
    # Sort channels in order of output frequency
    channels_csv(sorted(channels, key=lambda channel: channel.output))
