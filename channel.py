from copy import copy
from decimal import Decimal
from math import atan2, cos, radians, sin, sqrt

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
    p25_k = "P25"
    p25_phase_k = "P25 Phase"
    # TODO: P25 NAC is hexadecimal, default 0x293, from 0x000 to 0xfff
    p25_nac_k = "P25 NAC"
    dstar_k = "D-STAR"
    dstar_mode_k = "D-STAR Mode"
    nxdn_k = "NXDN"
    # TODO: AFAICT NXDN RANs are decimal, from 1-63 (0 probably means open or all)
    nxdn_ran_k = "NXDN RAN"
    dmr_k = "DMR"
    # TODO: Colour Codes are decimal, 0-15
    dmr_cc_k = "DMR CC"
    c4fm_k = "C4FM"
    # TODO: C4FM DSQ, decimal 001-126 (3 digits), is obsoleted by DG-ID 00-99 (2 digits)
    # Note: DG-ID is backward compatible, and 00 means "open"
    c4fm_dsq_k = "C4FM DSQ"
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
        p25_k,
        p25_phase_k,
        p25_nac_k,
        dstar_k,
        dstar_mode_k,
        nxdn_k,
        nxdn_ran_k,
        dmr_k,
        dmr_cc_k,
        c4fm_k,
        c4fm_dsq_k,
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
        input=None,
        offset=None,
        bandwidth="25",
        modes=("FM",),
        output_tone=None,
        input_tone=None,
        output_code=None,
        input_code=None,
        p25_phase=None,
        p25_nac=None,
        dstar_mode=None,
        nxdn_ran=None,
        dmr_cc=None,
        c4fm_dsq=None,
        location=None,
        latitude=None,
        longitude=None,
        rx_only=False,
    ):
        self.call = None
        if call:
            self.call = call.strip()
        self.output = Decimal(output)
        if input:
            self.input = Decimal(input)
        elif offset:
            self.input = self.output + Decimal(offset)
        else:
            self.input = self.output
        self.bandwidth = Decimal(bandwidth)
        self.modes = modes or []
        self.output_tone = None
        if output_tone:
            self.output_tone = Decimal(output_tone)
        self.input_tone = None
        if input_tone:
            self.input_tone = Decimal(input_tone)
        self.output_code = output_code or None
        self.input_code = input_code or None
        self.p25_phase = p25_phase or None
        self.p25_nac = p25_nac or None
        self.dstar_mode = dstar_mode or None
        self.nxdn_ran = nxdn_ran or None
        self.dmr_cc = dmr_cc or None
        if "DMR" in self.modes:
            if self.dmr_cc:
                self.dmr_cc = Decimal(self.dmr_cc)
            else:
                self.dmr_cc = Decimal(0)
        self.c4fm_dsq = c4fm_dsq or None
        if "C4FM" in self.modes:
            if self.c4fm_dsq:
                self.c4fm_dsq = Decimal(self.c4fm_dsq)
            else:
                self.c4fm_dsq = Decimal(00)
        self.location = location or None
        self.latitude = None
        if latitude:
            self.latitude = Decimal(latitude)
        self.longitude = None
        if longitude:
            self.longitude = Decimal(longitude)
        self.rx_only = rx_only or False
        self.rules = {}
        self._name = None
        self._number = 0

    @property
    def offset(self):
        return self.input - self.output

    def __hash__(self):
        return hash(
            (
                self.call,
                self.output,
                self.input,
                self.input_tone,
                self.input_code,
                self.p25_nac,
                self.nxdn_ran,
                self.dmr_cc,
                self.c4fm_dsq,
            )
        )

    def __eq__(self, other):
        return (
            self.call == other.call
            and self.output == other.output
            and self.input == other.input
            and self.input_tone == other.input_tone
            and self.input_code == other.input_code
            and self.p25_nac == other.p25_nac
            and self.nxdn_ran == other.nxdn_ran
            and self.dmr_cc == other.dmr_cc
            and self.c4fm_dsq == other.c4fm_dsq
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
    def atv(self):
        return "ATV" in self.modes

    @property
    def p25(self):
        return "P25" in self.modes

    @property
    def dstar(self):
        return "D-STAR" in self.modes

    @property
    def nxdn(self):
        return "NXDN" in self.modes

    @property
    def dmr(self):
        return "DMR" in self.modes

    @property
    def c4fm(self):
        return "C4FM" in self.modes

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
        if "ATV" in self.modes:
            modes.append("ATV")
        if "P25" in self.modes:
            modes.append(f"P25 {self.p25_nac}")
        if "D-STAR" in self.modes:
            modes.append(f"D-STAR {self.dstar_mode}")
        if "NDXN" in self.modes:
            modes.append(f"NXDN {self.nxdn_ran}")
        if "DMR" in self.modes:
            modes.append(f"DMR CC{self.dmr_cc}")
        if "C4FM" in self.modes:
            modes.append(f"C4FM {self.c4fm_dsq}")
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
        yield self.atv_k, self.atv
        yield self.p25_k, self.p25
        yield self.p25_phase_k, self.p25_phase
        yield self.p25_nac_k, self.p25_nac
        yield self.dstar_k, self.dstar
        yield self.dstar_mode_k, self.dstar_mode
        yield self.nxdn_k, self.nxdn
        yield self.nxdn_ran_k, self.nxdn_ran
        yield self.dmr_k, self.dmr
        yield self.dmr_cc_k, self.dmr_cc
        yield self.c4fm_k, self.c4fm
        yield self.c4fm_dsq_k, self.c4fm_dsq
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
