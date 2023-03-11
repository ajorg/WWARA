from decimal import Decimal

FORMAT = "{:6}{:10.4f}{:10.4f} {:+.2f} {}"


class Channel:
    def __init__(self, call, output, input):
        self.call = call
        self.output = Decimal(output)
        self.input = Decimal(input)
        self.offset = self.input - self.output
        self.rules = {}

    def __hash__(self):
        return hash((self.call, self.output, self.input))

    def __eq__(self, other):
        return (
            self.call == other.call
            and self.output == other.output
            and self.input == other.input
        )

    def __invert__(self):
        return Channel(self.call, self.input, self.output)

    def __str__(self):
        comment = ""
        if self.rules:
            rule, match = sorted(
                self.rules.items(), key=lambda x: len(x[1]), reverse=True
            )[0]
            if "offset" not in match:
                comment += " WRONG OFFSET"
            if "spacing" not in match:
                comment += " MISALIGNED"
        return FORMAT.format(self.call, self.output, self.input, self.offset, comment).rstrip()