#!/usr/bin/env python3
"""List available frequencies from the WWARA band plan."""
import sys
from decimal import Decimal

sys.path.insert(0, "..")

from channel import Channel
from wwara.database import coordinations
from wwara.plan import REPEATERS


def match(channel):
    """Check if channel matches any rule."""
    for rule in REPEATERS:
        if channel in rule:
            return True
    return False


def main():
    """Main entry point."""
    channels = set()
    for rule in REPEATERS:
        if rule.bandwidth == Decimal("12.5"):
            continue
        output = rule.low
        if rule.spacing == Decimal(0):
            channels.add(Channel("EMPTY", output, output + rule.offset))
            continue
        while output <= rule.high and rule.offset:
            channels.add(Channel("EMPTY", output, output + rule.offset))
            output += rule.spacing / 1000

    for channel in coordinations():
        channels.discard(Channel("EMPTY", channel.output, channel.input))
        channels.discard(Channel("EMPTY", channel.input, channel.output))

    for channel in sorted(channels):
        print(channel)


if __name__ == "__main__":
    main()
