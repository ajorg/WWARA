#!/usr/bin/env python3
"""Generate CSV files for WWARA repeater maps."""
from csv import DictWriter

from wwara.database import coordinations

FIELDNAMES = (
    "Name",
    "Call",
    "Location",
    "Output",
    "Offset",
    "Mode",
    "Latitude",
    "Longitude",
)
LAYERS = {
    "VHF_FM": {"low": 144, "high": 148, "mode": "FM"},
    "UHF_FM": {"low": 420, "high": 450, "mode": "FM"},
    "VHF_DMR": {"low": 144, "high": 148, "mode": "DMR"},
    "UHF_DMR": {"low": 420, "high": 450, "mode": "DMR"},
}


def rows(low, high, mode):
    """Generate rows for a specific band/mode layer."""
    for channel in channels:
        if (not (low <= channel.input <= high)) or (mode not in channel.modes):
            continue
        yield {
            "Name": str(channel),
            "Call": channel.call,
            "Location": channel.location,
            "Output": channel.output,
            "Offset": channel.offset,
            "Mode": channel.access,
            "Latitude": channel.latitude,
            "Longitude": channel.longitude,
        }


def main():
    """Main entry point."""
    global channels
    channels = list(coordinations())

    for name, layer_params in LAYERS.items():
        with open(f"{name}.csv", "w", newline="") as csvfile:
            writer = DictWriter(csvfile, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows(**layer_params))


if __name__ == "__main__":
    main()
