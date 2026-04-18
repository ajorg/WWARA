#!/usr/bin/env python3
"""Calculate distances from a location to WWARA repeaters."""
import sys
from decimal import Decimal

from wwara.database import coordinations

DEFAULT_LAT = Decimal("47.80")
DEFAULT_LON = Decimal("-122.25")


def main():
    """Main entry point."""
    lat = DEFAULT_LAT
    lon = DEFAULT_LON
    if len(sys.argv) > 2:
        lat = Decimal(sys.argv[1])
        lon = Decimal(sys.argv[2])

    for channel in sorted(coordinations(), key=lambda c: c.distance(lat, lon)):
        print(f"{channel} {channel.distance(lat, lon):5.1f}km")


if __name__ == "__main__":
    main()
