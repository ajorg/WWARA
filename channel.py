from copy import copy
from math import sin, cos, sqrt, atan2, radians
from decimal import Decimal

FORMAT = "{call:6} {output:9.4f} {offset:+.2f} {modes} {comment}"
R = 6373.0


class Channel:
    number_k = "Number"
    call_k = "Call"
    name_k = "Name"
    output_k = "Output"
    input_k = "Input"
    bandwidth_k = "Bandwidth"
    fm_k = "FM"
    output_tone_k = "Output Tone"
    input_tone_k = "Input Tone"
    output_code_k = "Output Code"
    input_code_k = "Input Code"
    dmr_k = "DMR"
    dmr_cc_k = "DMR CC"
    c4fm_k = "C4FM"
    c4fm_dsq_k = "C4FM DSQ"
    dstar_k = "D-STAR"
    dstar_mode_k = "D-STAR Mode"
    p25_k = "P25"
    p25_phase_k = "P25 Phase"
    p25_nac_k = "P25 NAC"
    location_k = "Location"
    latitude_k = "Latitude"
    longitude_k = "Longitude"
    rx_only_k = "RX Only"

    fieldnames = (
        number_k,
        call_k,
        name_k,
        output_k,
        input_k,
        bandwidth_k,
        fm_k,
        output_tone_k,
        input_tone_k,
        output_code_k,
        input_code_k,
        dmr_k,
        dmr_cc_k,
        c4fm_k,
        c4fm_dsq_k,
        dstar_k,
        dstar_mode_k,
        p25_k,
        p25_phase_k,
        p25_nac_k,
        location_k,
        latitude_k,
        longitude_k,
        rx_only_k,
    )

    name_length = 256

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
        rx_only=False,
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
        self.rx_only = rx_only
        self.rules = {}
        self._name = None
        self._number = 0

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
        if self._name is None:
            location = self.location or ""
            self._name = f"{self.call} {location}".rstrip(" ")
        return self._name[: self.name_length].rstrip(" ")

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def fm(self):
        return "FM" in self.modes

    @property
    def dmr(self):
        return "DMR" in self.modes

    @property
    def c4fm(self):
        return "C4FM" in self.modes

    @property
    def dstar(self):
        return "D-STAR" in self.modes

    @property
    def p25(self):
        return "P25" in self.modes

    @property
    def atv(self):
        return "ATV" in self.modes

    @property
    def number(self):
        return self._number

    @number.setter
    def number(self, value):
        self._number = value

    @property
    def access(self):
        modes = []
        if "FM" in self.modes:
            mode = "FM"
            if self.bandwidth < 25:
                mode = "NFM"
            if self.input_code:
                modes.append(f"{mode} D{self.input_code}N")
            elif self.input_tone:
                modes.append(f"{mode} {self.input_tone:.1f}")
            else:
                modes.append(mode)
        if "DMR" in self.modes:
            modes.append(f"DMR CC{self.dmr_cc}")
        if "D-STAR" in self.modes:
            modes.append(f"D-STAR {self.dstar_mode}")
        if "C4FM" in self.modes:
            modes.append(f"C4FM {self.c4fm_dsq}")
        if "P25" in self.modes:
            modes.append(f"P25 {self.p25_nac}")
        if "NDXN" in self.modes:
            modes.append(f"NXDN {self.nxdn_ran}")
        if "ATV" in self.modes:
            modes.append("ATV")
        return " & ".join(modes) or "NONE"

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
        output = f"{self.output:.6f}".rstrip("0").rstrip(".")
        offset = f"{self.offset:+.2f}".rstrip("0").rstrip(".")
        if Decimal(offset) == 0:
            offset = "SX"
        _str = f"{self.name} {output} {offset} {self.access}"
        if self.latitude and self.longitude:
            _str += f" ({self.latitude:.2f} {self.longitude:.2f})"
        return _str

    def __getitem__(self, key):
        if key not in self.fieldnames:
            raise KeyError(key)
        return self.get(key)

    def get(self, key, default=None):
        for k, v in self.items():
            if k == key:
                return v
        return default

    def __setitem__(self, key, value):
        if key == self.name_k:
            self.name = value
        elif key == self.number_k:
            self.number = value
        else:
            raise KeyError(key)

    def keys(self):
        return {k: None for k in self.fieldnames}.keys()

    def items(self):
        yield self.number_k, self.number
        yield self.call_k, self.call
        yield self.name_k, self.name
        yield self.output_k, self.output
        yield self.input_k, self.input
        yield self.bandwidth_k, self.bandwidth
        yield self.fm_k, self.fm
        yield self.output_tone_k, self.output_tone
        yield self.input_tone_k, self.input_tone
        yield self.output_code_k, self.output_code
        yield self.input_code_k, self.input_code
        yield self.dmr_k, self.dmr
        yield self.dmr_cc_k, self.dmr_cc
        yield self.c4fm_k, self.c4fm
        yield self.c4fm_dsq_k, self.c4fm_dsq
        yield self.dstar_k, self.dstar
        yield self.dstar_mode_k, self.dstar_mode
        yield self.p25_k, self.p25
        yield self.p25_phase_k, self.p25_phase
        yield self.p25_nac_k, self.p25_nac
        yield self.atv_k, self.atv
        yield self.location_k, self.location
        yield self.latitude_k, self.latitude
        yield self.longitude_k, self.longitude
        yield self.rx_only_k, self.rx_only

    def distance(self, lat, lon):
        R = 6371  # Radius of the earth in km
        dLat = radians(lat - self.latitude)
        dLon = radians(lon - self.longitude)
        a = sin(dLat / 2) * sin(dLat / 2) + cos(radians(self.latitude)) * cos(
            radians(lat)
        ) * sin(dLon / 2) * sin(dLon / 2)
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c  # Distance in km
