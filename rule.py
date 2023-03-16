from decimal import Decimal

HEADER = "BOTTOM - TOP +/-OFFSET |SPACING| [BANDWIDTH]"
FORMAT = "{:4.4f} MHz - {:4.4f} MHz {:+.1f} KHz |{:.1f} KHz| [{:f} KHz]"


class Rule:
    def __init__(self, low, high, offset, spacing, bandwidth="25"):
        self.low = Decimal(low)
        self.high = Decimal(high)
        self.offset = Decimal(offset)
        self.spacing = Decimal(spacing)
        self.bandwidth = Decimal(bandwidth)

    def __hash__(self):
        return hash((self.low, self.high, self.offset, self.spacing, self.bandwidth))

    def __eq__(self, other):
        return (
            self.low == other.low
            and self.high == other.high
            and self.offset == other.offset
            and self.spacing == other.spacing
            and self.bandwidth == other.bandwidth
        )

    def __str__(self):
        return FORMAT.format(self.low, self.high, self.offset, self.spacing, self.bandwidth)

    def __contains__(self, channel):
        # Is the output in this rule's range?
        if self.low <= channel.output <= self.high:
            channel.rules[self] = set()
            # Does it have the correct offset?
            if channel.offset == self.offset:
                channel.rules[self].add("offset")
            else:
                return False
            # Is it also aligned to this rule's spacing?
            # `or 1` accounts for single-channel rules with 0 spacing
            if (channel.output - self.low) % ((self.spacing / 1000) or 1) == 0:
                channel.rules[self].add("spacing")
            else:
                return False
            # And does it have a small enough bandwidth?
            if channel.bandwidth <= self.bandwidth:
                channel.rules[self].add("bandwidth")
            else:
                return False
            return True
        return False
