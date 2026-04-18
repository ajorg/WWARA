#!/usr/bin/env python3
"""Convert ARRL CSV to CHIRP CSV format."""
import sys
from csv import DictReader, DictWriter
from decimal import Decimal

fieldnames = (
    "Location",
    "Name",
    "Frequency",
    "Duplex",
    "Offset",
    "Tone",
    "rToneFreq",
    "cToneFreq",
    "DtcsCode",
    "DtcsPolarity",
    "Mode",
    "Comment",
)


def drop_decimals(d):
    """Remove trailing zeros from decimal representation."""
    d = str(d)
    if "." in d:
        d = d.rstrip("0").rstrip(".")
    return d


def convert(input_file, output_file=sys.stdout):
    """Convert ARRL CSV to CHIRP CSV format."""
    with open(input_file) as c:
        c.readline()  # Discard ARRL DATA_SPEC_VERSION line
        d = DictReader(c)

        w = DictWriter(output_file, fieldnames)
        w.writerow(dict(zip(fieldnames, fieldnames)))

        i = 0
        for row in d:
            in_freq = Decimal(row["INPUT_FREQ"])
            out_freq = Decimal(row["OUTPUT_FREQ"])
            duplex = "off"
            offset = Decimal(0)
            if out_freq < in_freq:
                duplex = "+"
                offset = in_freq - out_freq
            elif out_freq > in_freq:
                duplex = "-"
                offset = out_freq - in_freq
            tone = None
            if row["CTCSS_IN"]:
                tone = "Tone"
            elif row["DCS_CDCSS"]:
                tone = "DTCS"
            mode = None
            if row["FM_WIDE"] == "Y":
                mode = "FM"
            elif row["FM_NARROW"] == "Y":
                mode = "NFM"
            else:
                continue
            if "Y" in (
                row["DSTAR_DV"],
                row["DSTAR_DD"],
                row["DMR"],
                row["FUSION"],
                row["P25_PHASE_1"],
                row["P25_PHASE_2"],
                row["NXDN_DIGITAL"],
                row["ATV"],
                row["DATV"],
            ):
                continue  # Not analog modes
            w.writerow(
                {
                    "Location": i,
                    "Name": row["CALL"],
                    "Frequency": row["OUTPUT_FREQ"],
                    "Duplex": duplex,
                    "Offset": drop_decimals(offset),
                    "Tone": tone,
                    "rToneFreq": row["CTCSS_IN"] or "88.5",
                    "cToneFreq": row["CTCSS_OUT"] or "88.5",
                    "DtcsCode": row["DCS_CDCSS"] or "23",
                    "DtcsPolarity": "NN",
                    "Mode": mode,
                    "Comment": " ".join((row["CALL"], row["CITY"])),
                }
            )
            i += 1


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: arrl-csv-to-chirp-csv <input.csv>", file=sys.stderr)
        sys.exit(1)
    convert(sys.argv[1])


if __name__ == "__main__":
    main()
