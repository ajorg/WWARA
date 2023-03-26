from copy import copy
from math import sin, cos, sqrt, atan2, radians
from decimal import Decimal

FORMAT = "{call:6} {output:9.4f} {offset:+.2f} {modes} {comment}"
R = 6373.0


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
        dmr_cc=None,
        c4fm_dsq=None,
        dstar_mode=None,
        p25_phase=None,
        p25_nac=None,
        location=None,
        latitude=None,
        longitude=None,
    ):
        self.call = call
        self.output = Decimal(output)
        self.input = Decimal(input)
        self.bandwidth = Decimal(bandwidth)
        self.modes = modes
        self.output_tone = output_tone
        if input_tone:
            self.input_tone = Decimal(input_tone)
        else:
            self.input_tone = None
        self.output_code = output_code
        self.input_code = input_code
        self.dmr_cc = dmr_cc
        self.c4fm_dsq = c4fm_dsq
        if "C4FM" in self.modes:
            if self.c4fm_dsq:
                self.c4fm_dsq = Decimal(self.c4fm_dsq)
            else:
                self.c4fm_dsq = 00
        self.dstar_mode = dstar_mode
        self.p25_phase = p25_phase
        self.p25_nac = p25_nac
        self.location = location
        self.latitude = None
        if latitude:
            self.latitude = Decimal(latitude)
        self.longitude = None
        if longitude:
            self.longitude = Decimal(longitude)
        self.rules = {}

    @property
    def offset(self):
        return self.input - self.output

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
        inverse = copy(self)
        inverse.output, inverse.input = self.input, self.output
        return inverse

    @property
    def name(self):
        return f"{self.call} {self.location}"

    @property
    def errors(self):
        _errors = []
        if self.rules:
            rule, match = sorted(
                self.rules.items(), key=lambda x: len(x[1]), reverse=True
            )[0]
            if "offset" not in match:
                _errors.append("WRONG OFFSET")
            if "spacing" not in match:
                _errors.append("MISALIGNED")
            if "bandwidth" not in match:
                _errors.append("TOO WIDE")
        return _errors

    def __str__(self):
        output = str(self.output).rstrip("0")
        offset = f"{self.offset:+.2f}".rstrip("0").rstrip(".")
        modes = []
        if "FM" in self.modes:
            if self.input_code:
                modes.append(f"FM D{self.input_code}N")
            elif self.input_tone:
                modes.append(f"FM {self.input_tone:.1f}")
            else:
                modes.append("FM SQ?")
        if "DMR" in self.modes:
            modes.append(f"DMR CC{self.dmr_cc}")
        if "DSTAR" in self.modes:
            modes.append(f"D-STAR {self.dstar_mode}")
        if "C4FM" in self.modes:
            modes.append(f"C4FM {self.c4fm_dsq}")
        if "P25" in self.modes:
            modes.append(f"P25 {self.p25_nac}")
        if "NDXN" in self.modes:
            modes.append(f"NXDN {self.nxdn_ran}")
        if "ATV" in self.modes:
            modes.append("ATV")
        mode = " & ".join(modes) or "NONE"
        _str = f"{self.name} {output} {offset} {mode}"
        if self.latitude and self.longitude:
            _str += f" ({self.latitude:.2f} {self.longitude:.2f})"
        return _str

    def distance(self, lat, lon):
        R = 6371  # Radius of the earth in km
        dLat = radians(lat - self.latitude)
        dLon = radians(lon - self.longitude)
        a = sin(dLat / 2) * sin(dLat / 2) + cos(radians(self.latitude)) * cos(
            radians(lat)
        ) * sin(dLon / 2) * sin(dLon / 2)
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c  # Distance in km
