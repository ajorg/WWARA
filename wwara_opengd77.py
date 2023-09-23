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
DELIMITER = ","


class GB3GFChannel(Channel):
    number_k = "Channel Number"
    name_k = "Channel Name"
    channel_type_k = "Channel Type"
    rx_frequency_k = "Rx Frequency"
    tx_frequency_k = "Tx Frequency"
    bandwidth_k = "Bandwidth (kHz)"
    colour_code_k = "Colour Code"
    timeslot_k = "Timeslot"
    contact_k = "Contact"
    tg_list_k = "TG List"
    dmr_id_k = "DMR ID"
    ts1_ta_tx_k = "TS1_TA_Tx"
    ts2_ta_tx_k = "TS2_TA_Tx ID"
    rx_tone_k = "RX Tone"
    tx_tone_k = "TX Tone"
    squelch_k = "Squelch"
    power_k = "Power"
    rx_only_k = "Rx Only"
    zone_skip_k = "Zone Skip"
    all_skip_k = "All Skip"
    tot_k = "TOT"
    vox_k = "VOX"
    no_beep_k = "No Beep"
    no_eco_k = "No Eco"
    aprs_k = "APRS"
    latitude_k = "Latitude"
    longitude_k = "Longitude"
    fieldnames = (
        number_k,
        name_k,
        channel_type_k,
        rx_frequency_k,
        tx_frequency_k,
        bandwidth_k,
        colour_code_k,
        timeslot_k,
        contact_k,
        tg_list_k,
        dmr_id_k,
        ts1_ta_tx_k,
        ts2_ta_tx_k,
        rx_tone_k,
        tx_tone_k,
        squelch_k,
        power_k,
        rx_only_k,
        zone_skip_k,
        all_skip_k,
        tot_k,
        vox_k,
        no_beep_k,
        no_eco_k,
        aprs_k,
        latitude_k,
        longitude_k,
    )
    name_length = NAME_LENGTH

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
        if "DMR" in self.modes:
            return None
        return self.bandwidth

    @property
    def _rx_only(self):
        if self.rx_only:
            return "Yes"
        return "No"

    def items(self):
        yield self.number_k, self.number
        yield self.name_k, self.name
        yield self.channel_type_k, self._channel_type
        yield self.rx_frequency_k, self._rx_frequency
        yield self.tx_frequency_k, self._tx_frequency
        yield self.bandwidth_k, self._bandwidth
        yield self.colour_code_k, self.dmr_cc or 0
        yield self.timeslot_k, 1
        yield self.contact_k, None
        yield self.tg_list_k, None
        yield self.dmr_id_k, None
        yield self.ts1_ta_tx_k, "Off"  # or "Text" or "APRS" or "APRS & Text"
        yield self.ts2_ta_tx_k, "Off"
        yield self.rx_tone_k, self._rx_tone
        yield self.tx_tone_k, self._tx_tone
        yield self.squelch_k, "Disabled"
        yield self.power_k, "Master"
        yield self.rx_only_k, self._rx_only
        yield self.zone_skip_k, "No"
        yield self.all_skip_k, "No"
        yield self.tot_k, 0
        yield self.vox_k, "Off"
        yield self.no_beep_k, "No"
        yield self.no_eco_k, "No"
        yield self.aprs_k, "None"
        yield self.latitude_k, self.latitude
        yield self.longitude_k, self.longitude


def _supported(channel):
    """Checks if the channel is supported by the radio."""
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
    with open("Channels.csv", "w", newline="") as _channels_csv:
        writer = DictWriter(
            _channels_csv, fieldnames=GB3GFChannel.fieldnames, delimiter=DELIMITER
        )
        writer.writeheader()
        writer.writerows(channels)


ZONES_FIELDNAMES = tuple(["Zone Name"] + ["Channel " + str(i) for i in range(1, 81)])


def zones_csv(channels):
    zones = {
        "WWARA": {"mode": None, "low": 144, "high": 450},
        "WWARA FM": {"mode": "FM", "low": 144, "high": 450},
        "WWARA DMR": {"mode": "DMR", "low": 144, "high": 450},
        "WWARA VHF": {"mode": "FM", "low": 144, "high": 148},
        "WWARA 220": {"mode": "FM", "low": 222, "high": 225},
        "WWARA UHF": {"mode": "FM", "low": 420, "high": 450},
    }
    with open("Zones.csv", "w", newline="") as _zones_csv:
        writer = DictWriter(
            _zones_csv, fieldnames=ZONES_FIELDNAMES, delimiter=DELIMITER
        )
        writer.writeheader()
        for name, spec in zones.items():
            zone = {"Zone Name": name}
            i = 1
            for channel in channels:
                if i > 80:
                    break
                if (spec["mode"] is not None) and (spec["mode"] not in channel.modes):
                    continue
                if not (spec["low"] <= channel.input <= spec["high"]):
                    continue
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
