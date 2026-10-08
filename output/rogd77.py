#!/usr/bin/env python
"""Converts channels to ReallyOpenGD77-WebCPSd JSON codeplug format

https://w0chp.radio/ogd77-webcpsd/ https://rogd77.webcps.app/
https://github.com/w0chp/ReallyOpenGD77-WebCPSd
"""

import re
from datetime import datetime, timezone
from decimal import Decimal
from json import dump, load
from sys import argv, stderr

from channel import Channel
from channels import chirp
from output.opengd77 import _supported, _zones
from wwara.database import coordinations

LAT = Decimal("47.80")
LON = Decimal("-122.25")
RANGE = 80

NAME_LENGTH = 16


class RogGD77Channel(Channel):
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
        self._name = channel.name
        self._number = 0

    @property
    def _mode(self):
        if "DMR" in self.modes:
            return "DMR"
        return "FM"

    @property
    def _bandwidth(self):
        bandwidth = self.bandwidth
        if "DMR" in self.modes:
            bandwidth = Decimal("12.5")
        return f"{bandwidth:g}kHz"

    @classmethod
    def _tone(cls, tone, code):
        if not tone:
            if not code:
                return ""
            return f"D{code}N"
        return f"{Decimal(tone):.1f}"

    @property
    def _rx_tone(self):
        return self._tone(self.output_tone, self.output_code)

    @property
    def _tx_tone(self):
        return self._tone(self.input_tone, self.input_code)

    def asdict(self):
        return {
            "id": self.number,
            "name": self.name,
            "rx_freq": float(self.output),
            "tx_freq": float(self.input),
            "mode": self._mode,
            "power": 0,
            "bandwidth": self._bandwidth,
            "rx_tone": self._rx_tone,
            "tx_tone": self._tx_tone,
            "squelch": 0,
            "color_code": int(self.dmr_cc) if self.dmr_cc else 0,
            "timeslot": 1,
            "contact_name": "",
            "tg_list_name": "",
            "rx_only": bool(self.rx_only),
            "no_beep": False,
            "no_eco": False,
            "vox": False,
            "tot": 0,
            "zone_skip": False,
            "all_skip": False,
        }


def _band(freq):
    if 144 <= freq < 148:
        return "VHF"
    if 222 <= freq <= 225:
        return "220"
    if 420 <= freq <= 450:
        return "UHF"
    return None


def _dedup_names(channels):
    names = {}
    for channel in channels:
        info = names.setdefault(
            channel.name,
            {"entries": [], "dups": {"UHF": 0, "220": 0, "VHF": 0, "DMR": 0}},
        )
        info["entries"].append(channel)
        if "DMR" in channel.modes:
            info["dups"]["DMR"] += 1
        band = _band(channel.output)
        if band:
            info["dups"][band] += 1
    for channel in sorted(channels, key=lambda c: (c.name, c.output)):
        entry = names[channel.name]
        if len(entry["entries"]) <= 1:
            continue
        dups = entry["dups"]
        band = _band(channel.output)
        freq = f"{channel.output:.4f}".rstrip("0").rstrip(".").replace(".", "")[2:]
        if dups["DMR"] == 1 and "DMR" in channel.modes:
            tag = "D"
        elif dups["UHF"] == 1 and band == "UHF":
            tag = "U"
        elif dups["220"] == 1 and band == "220":
            tag = "2"
        elif dups["VHF"] == 1 and band == "VHF":
            tag = "V"
        else:
            tag = freq
        length = NAME_LENGTH - len(tag)
        channel.name = re.sub(" +", " ", channel.name.ljust(NAME_LENGTH)[:length] + tag)
    seen = set()
    for channel in channels:
        if channel.name in seen:
            print(f"BUG! Duplicate names still exist! {channel.name}", file=stderr)
        else:
            seen.add(channel.name)


def _blank_codeplug():
    return {
        "general": {
            "dmr_id": 0,
            "callsign": "",
            "boot_line1": "",
            "boot_line2": "",
            "boot_text_enabled": True,
            "vhf_min": 136,
            "vhf_max": 174,
            "uhf_min": 400,
            "uhf_max": 480,
        },
        "channels": [],
        "contacts": [],
        "tg_lists": [],
        "zones": [],
        "scan_lists": [],
        "dtmf_contacts": [],
        "aprs_configs": [],
        "satellites": [],
        "vfo_a": {
            "rx_freq": 146.52,
            "tx_freq": 146.52,
            "mode": "FM",
            "power": 9,
            "bandwidth": "25kHz",
            "rx_tone": "",
            "tx_tone": "",
            "squelch": 0,
        },
        "vfo_b": {
            "rx_freq": 446.00,
            "tx_freq": 446.00,
            "mode": "FM",
            "power": 9,
            "bandwidth": "25kHz",
            "rx_tone": "",
            "tx_tone": "",
            "squelch": 0,
        },
    }


if __name__ == "__main__":
    channels = []
    with open(argv[1]) as zones_f:
        zones = load(zones_f)
    codeplug = _blank_codeplug()
    if len(argv) > 2:
        with open(argv[2]) as source_f:
            source_codeplug = load(source_f)
        general = {**codeplug["general"], **source_codeplug.get("general", {})}
        codeplug.update(source_codeplug)
        codeplug["general"] = general
    zone_list = []
    for zone_name, zone in zones.items():
        print(f"{zone_name}:")
        zone_channels = []
        if zone is None:
            continue
        elif isinstance(zone, (str, bytes)):
            if zone.startswith(":"):
                _, source, _zone = zone.split(":", 2)
                if source == "chirp":
                    for channel in chirp.zone(_zone):
                        print(channel)
                        rog_channel = RogGD77Channel(channel)
                        channels.append(rog_channel)
                        zone_channels.append(rog_channel.name)
            zone_list.append({"name": zone_name, "channels": zone_channels})
            continue
        for item_name, item in zone.items():
            zone_channels.append(item_name)
            if item is None:
                print(item_name)
                continue
            try:
                if "input" not in item:
                    item["input"] = item["output"]
                if "offset" in item:
                    item["input"] = Decimal(item["output"]) + Decimal(item["offset"])
                    del item["offset"]
                channel = Channel(call=None, **item)
                channel.name = item_name
                channels.append(RogGD77Channel(channel))
                print(channel)
            except (TypeError, KeyError, ArithmeticError) as e:
                print(e)
                print(item)
        zone_list.append({"name": zone_name, "channels": zone_channels})
    if "<WWARA" in zones:
        seen = set()
        wwara_channels = []
        for channel in coordinations():
            if not _supported(channel):
                continue
            if channel in seen:
                # Avoids a nasty duplicate
                continue
            seen.add(channel)
            wwara_channels.append(RogGD77Channel(channel))
        _dedup_names(wwara_channels)
        # Sort channels in order of output frequency
        channels.extend(sorted(wwara_channels, key=lambda channel: channel.output))
        for _zone_name, zone_channel_names in _zones(
            sorted(wwara_channels, key=lambda channel: channel.distance(LAT, LON))
        ):
            zone_list.append({"name": _zone_name, "channels": list(zone_channel_names)})
    for number, channel in enumerate(channels):
        channel.number = number
    codeplug["channels"] = [channel.asdict() for channel in channels]
    codeplug["zones"] = [
        {"id": i, "name": zone["name"], "channels": zone["channels"]}
        for i, zone in enumerate(zone_list)
    ]
    callsign = codeplug["general"].get("callsign") or "codeplug"
    filename = f"{callsign.upper()}_{datetime.now(tz=timezone.utc).date().isoformat()}.json"
    with open(filename, "w") as codeplug_f:
        dump(codeplug, codeplug_f, indent=2)
    print(f"Wrote {filename}")
