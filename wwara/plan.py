from channel import Channel
from rule import Rule

# Comments are taken from the WWARA Band Plan dated 12/18/21
# And WWARA 70cm Band Plan date November 2020
# Also https://www.wwara.org/WWARA_BAND_PLAN_2016_07_06.pdf
REPEATERS = [
    # 10-Meter Band
    # * 20kHz channel spacing
    # 29.6200 - 29.6800 Repeater Outputs 20 kHz Spacing
    # * Paired with repeater inputs - 0.1MHz
    # 29.5200 - 29.5800 Repeater Inputs 20 kHz Spacing
    # * Paired with repeater outputs + 0.1MHz
    Rule("29.62", "29.68", "-0.1", "20"),
    # 6-Meter Band
    # 52.8100 - 53.9900 FM Repeater Outputs
    # * Paired with repeater inputs -1.7MHz
    # 51.1000 - 52.2900 FM Repeater inputs
    # * Paired with repeater inputs +1.7MHz
    # (ajorg) s/inputs/outputs/
    # * 20kHz channel spacing
    # (ajorg) TODO
    # * 52.19/52.99 Shared Non-Protected (SNP) repeater pair
    Rule("52.81", "53.99", "-1.7", "20"),
    # 2-Meter Band
    # 145.1000 - 145.2000 FM Repeater/Linear Translator outputs
    # 144.5000 - 144.6000 FM Repeater/Linear Translator inputs
    # * Washington, the adjoining States and BC use 20 kHz spacing
    #   between repeater channels
    # * Repeater channels are on odd frequencies below 146 MHz
    #   and even frequencies above 146 MHz
    # (ajorg) TODO
    # * 144.53/145.13 and 144.69/145.29 Shared Non-Protected
    #   (SNP) repeater pair
    # (ajorg) Based on coordinated pairs, center frequencies are
    #         145.1100 - 145.1900 FM Repeater/Linear Translator outputs
    #         144.5100 - 144.5900 FM Repeater/Linear Translator inputs
    Rule("145.11", "145.19", "-0.6", "20"),
    # 2-Meter Band
    # 145.2000 - 145.4900 FM Repeater outputs
    # (ajorg) 145.2100 - ?
    # 144.6000 - 144.9000 FM Repeater inputs
    # (ajorg)  - 144.8900 ?
    Rule("145.21", "145.49", "-0.6", "20"),
    # 2-Meter Band
    # (proposed) 145.1000 - 145.4875 NFM Repeater outputs
    Rule("145.1", "145.4875", "-0.6", "12.5", "12.5"),
    # 2-Meter Band
    # 146.0050 Special UNBD Repeater Output #1
    # 146.6050 Special UNBD Repeater Input #1
    # "We flipped the input & output due to interference issues at the site."
    # * Two Special UNBD channels, 6.25 kHz bandwidth only
    Rule("146.605", "146.605", "-0.6", "0", "6.25"),
    # 2-Meter Band
    # 147.9950 Special UNBD Repeater Output #2
    # 147.3950 Special UNBD Repeater Input #2
    # * Two Special UNBD channels, 6.25 kHz bandwidth only
    Rule("147.995", "147.995", "-0.6", "0", "6.25"),
    # 2-Meter Band
    # 146.40625 - 146.50625 VNBD Repeater Outputs
    # 147.40625 - 147.50625 VNBD Repeater Inputs
    # * 146.4125, bottom center frequency; 12.5 kHz steps, 8
    #   channels to 146.5000, + 1 MHz offset; VNBD, UNBD only
    Rule("146.4125", "146.5", "1", "12.5", "12.5"),
    # 2-Meter Band
    # 146.6200 - 147.3800 Repeater outputs
    # * Repeater channels are on odd frequencies below 146 MHz
    #   and even frequencies above 146 MHz
    #
    # 2-Meter Band
    # 146.0100 - 146.4000 Repeater inputs
    # (ajorg) 146.0200 - 146.4000 Repeater inputs (center frequencies)
    Rule("146.62", "147", "-0.6", "20"),
    # 2-Meter Band
    # (proposed) 146.6250 - 146.9875 NFM Repeater outputs
    Rule("146.625", "146.9875", "-0.6", "12.5", "12.5"),
    # 2-Meter Band
    # 147.6100 - 147.9900 Repeater inputs
    # (ajorg) 147.6000 - 147.98 Repeater inputs (center frequencies)
    Rule("147", "147.38", "0.6", "20"),
    # 2-Meter Band
    # (proposed) 147.0000 - 147.3875 NFM Repeater outputs
    Rule("146.625", "146.9875", "0.6", "12.5", "12.5"),
    # 1.25m MHz Band Plan
    # 223.7800 - 223.9800 Repeater Outputs
    # 222.1800 - 222.3800 Repeater Inputs
    # * All FM Repeaters and simplex operations are on 20 kHz
    #   spacing
    Rule("223.78", "223.98", "-1.6", "20"),
    # 1.25m MHz Band Plan
    # 224.0200 - 224.6200 Repeater Outputs
    # 222.4200 - 223.0200 Repeater Inputs
    Rule("224.02", "224.62", "-1.6", "20"),
    # 1.25m MHz Band Plan
    # 224.6800 - 224.8200 Repeater Outputs
    # 223.0800 - 223.2200 Repeater Inputs
    Rule("224.68", "224.82", "-1.6", "20"),
    # 1.25m MHz Band Plan
    # 224.8600 - 224.9800 Repeater Outputs
    # 223.2600 - 223.3800 Repeater Inputs
    Rule("224.86", "224.98", "-1.6", "20"),
    # [Revised] 70cm Band Plan
    # https://www.wwara.org/documents/70cmbandplan/
    # TODO SNPs and other exceptions
    Rule("440.0125", "440.0125", "5", "0", "12.5"),
    Rule("440.0375", "440.7875", "5", "12.5", "12.5"),
    Rule("440.0500", "440.6750", "5", "25", "25"),
    Rule("440.9250", "440.9750", "5", "25", "25"),
    Rule("440.9125", "440.9875", "5", "12.5", "12.5"),
    Rule("441.0125", "442.9875", "5", "12.5", "12.5"),
    Rule("441.0250", "442.9750", "5", "25", "25"),
    Rule("443.0125", "444.9875", "5", "12.5", "12.5"),
    Rule("442.0250", "444.9750", "5", "25", "25"),
    # 33cm MHz Band Plan
    # 927.3000 - 928.0000 Repeater Outputs
    # 902.3000 - 903.0000 Repeater inputs
    # * All FM and data channels at 25 kHz spacing
    # Rule("927.3", "928", "-25", "25"),
    # DRAFT https://groups.io/g/wwara/message/107
    # 927.2125 - 927.9875 Repeater output  25 Mhz Offset
    # 902.2125 - 902.9875 Repeater Input 12.5 khz spacing
    Rule("927.2125", "927.9875", "-25", "12.5"),
    # 23cm MHz Band Plan
    # 1247.000 - 1252.000 D-STAR DD mode repeaters
    # * All FM simplex and repeater channels are on 25kHz spacing
    # (ajorg) DD repeaters are simplex?
    Rule("1247", "1252", "0", "25"),
    # 23cm MHz Band Plan
    # 1240.000 - 1246.000 ATV #1
    # 1252.000 - 1258.000 ATV #2
    # 421.2500 Video carrier for ATV
    # 427.2500 Video carrier for ATV
    # 434.0000 Video carrier for ATV
    # (ajorg) TODO ATV is complicated
    # 23cm MHz Band Plan
    # 1290.000 - 1291.000 D-STAR DV mode repeater outputs
    # 1270.000 - 1271.000 D-STAR DV mode repeater inputs
    # * Includes other narrowband modes with 25kHz spacing
    Rule("1290", "1291", "-20", "25"),
    # 23cm MHz Band Plan
    # 1290.000 - 1295.000 Repeater Outputs
    # 1270.000 - 1275.000 Repeater Inputs
    # * All FM simplex and repeater channels are on 25kHz spacing
    Rule("1290", "1295", "-20", "25"),
]

EXCEPTIONS = {
    # FIXME hack for ATV (cross-band)
    Channel("WW7ATS", "1253.25", "434"): {"comment": "ATV"},
    # AA7MI   440.7250 +5.00 FM TOO WIDE ERROR!
    Channel("AA7MI", "440.725", "445.725"): {"comment": "KNOWN"},
    # WA7LZO Seattle 442.9 +5 P25  (47.61 -122.33) ERROR! NO NAC
    Channel("WA7LZO", "442.9", "447.9"): {"comment": 'KNOWN "Dynamic NAC"'},
}
ERRORS = {}

if __name__ == "__main__":
    from rule import HEADER

    print(HEADER)
    for rule in REPEATERS:
        print(rule)
