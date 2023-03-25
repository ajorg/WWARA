from decimal import Decimal

FORMAT = "{:6}{:10.4f}{:10.4f} {:+.2f} {}"


class Channel:
    def __init__(
        self,
        call,
        output,
        input,
        bandwidth="25",
        modes=("FM",),
        output_tone=None,
        input_tone=None,
        output_code=None,
        input_code=None,
        dmr_color_code=None,
    ):
        self.call = call
        self.output = Decimal(output)
        self.input = Decimal(input)
        self.bandwidth = Decimal(bandwidth)
        self.modes = modes
        self.offset = self.input - self.output
        self.output_tone = output_tone
        self.input_tone = input_tone
        self.output_code = output_code
        self.input_code = input_code
        self.dmr_color_code = dmr_color_code
        self.rules = {}

    def __hash__(self):
        return hash((self.call, self.output, self.input))

    def __eq__(self, other):
        return (
            self.call == other.call
            and self.output == other.output
            and self.input == other.input
        )

    def __lt__(self, other):
        return self.output < other.output

    def __invert__(self):
        return Channel(self.call, self.input, self.output, self.bandwidth)

    def __str__(self):
        comment = []
        if self.rules:
            rule, match = sorted(
                self.rules.items(), key=lambda x: len(x[1]), reverse=True
            )[0]
            if "offset" not in match:
                comment.append("WRONG OFFSET")
            if "spacing" not in match:
                comment.append("MISALIGNED")
            if "bandwidth" not in match:
                comment.append("TOO WIDE")
        return FORMAT.format(
            self.call, self.output, self.input, self.offset, " ".join(comment)
        ).rstrip()
