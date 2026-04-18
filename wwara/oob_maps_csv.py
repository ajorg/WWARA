#!/usr/bin/env python3
"""Generate CSV for WWARA repeaters outside the defined region."""
import sys
from csv import DictWriter

from wwara.database import coordinations

FIELDNAMES = (
    "Name",
    "Latitude",
    "Longitude",
)
LAT_LO = 45.90
LAT_HI = 49.00
LON_LO = -124.22
LON_HI = -121.32


def in_region(channel):
    """Check if channel is within the defined region."""
    if not (LAT_LO < channel.latitude < LAT_HI):
        return False
    if not (LON_LO < channel.longitude < LON_HI):
        return False
    return True


def rows():
    """Generate rows for channels outside the region."""
    for channel in channels:
        if in_region(channel):
            continue
        yield {
            "Name": str(channel),
            "Latitude": channel.latitude,
            "Longitude": channel.longitude,
        }


def main():
    """Main entry point."""
    global channels
    channels = list(coordinations())

    writer = DictWriter(sys.stdout, fieldnames=FIELDNAMES)
    writer.writeheader()
    writer.writerows(rows())


if __name__ == "__main__":
    main()
