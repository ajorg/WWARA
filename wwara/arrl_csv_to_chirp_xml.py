#!/usr/bin/env python3
"""Convert ARRL CSV to CHIRP XML format."""
import sys
from csv import DictReader
from decimal import Decimal


def drop_decimals(d):
    """Remove trailing zeros from decimal representation."""
    d = str(d)
    if "." in d:
        d = d.rstrip("0").rstrip(".")
    return d


def convert(input_file, output_file=sys.stdout):
    """Convert ARRL CSV to CHIRP XML format."""
    with open(input_file) as c:
        c.readline()  # Discard ARRL DATA_SPEC_VERSION line
        d = DictReader(c)

        print('<?xml version="1.0"?>', file=output_file)
        print("<radio>", file=output_file)
        print("<memories>", file=output_file)

        i = 0
        for row in d:
            name = row["CALL"]
            if name.endswith("/R"):
                name = name[:-2]
            longname = " ".join((name, row["CITY"]))[:16]
            in_freq = Decimal(row["INPUT_FREQ"])
            out_freq = Decimal(row["OUTPUT_FREQ"])
            duplex = "off"
            offset = Decimal(0)
            if out_freq < in_freq:
                duplex = "positive"
                offset = in_freq - out_freq
            elif out_freq > in_freq:
                duplex = "negative"
                offset = out_freq - in_freq
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
                row["P25_PHASE_1"],
                row["P25_PHASE_2"],
                row["NXDN_DIGITAL"],
                row["ATV"],
                row["DATV"],
            ):
                continue  # Not analog modes
            print(f'<memory location="{i}">', file=output_file)
            print(f"<shortName>{name}</shortName>", file=output_file)
            print(f"<longName>{longname}</longName>", file=output_file)
            freq = drop_decimals(out_freq)
            freq_xml = f'<frequency units="MHz">{freq}</frequency>'
            print(freq_xml, file=output_file)
            print('<squelch id="rtone" type="repeater">', file=output_file)
            tone_in = row['CTCSS_IN'] or '88.5'
            print(f"<tone>{tone_in}</tone>", file=output_file)
            print("</squelch>", file=output_file)
            print('<squelch id="ctone" type="ctcss">', file=output_file)
            tone_out = row['CTCSS_OUT'] or '88.5'
            print(f"<tone>{tone_out}</tone>", file=output_file)
            print("</squelch>", file=output_file)
            print('<squelch id="dtcs" type="dtcs">', file=output_file)
            code = row['DCS_CDCSS'] or '023'
            print(f"<code>{code}</code>", file=output_file)
            print("<polarity>NN</polarity>", file=output_file)
            print("</squelch>", file=output_file)
            if row["CTCSS_IN"]:
                sq_set = "<squelchSetting>rtone</squelchSetting>"
                print(sq_set, file=output_file)
            elif row["DCS_CDCSS"]:
                sq_set = "<squelchSetting>dtcs</squelchSetting>"
                print(sq_set, file=output_file)
            print(f"<duplex>{duplex}</duplex>", file=output_file)
            offset_val = drop_decimals(offset)
            offset_xml = f'<offset units="MHz">{offset_val}</offset>'
            print(offset_xml, file=output_file)
            print(f"<mode>{mode}</mode>", file=output_file)
            print('<tuningStep units="kHz">5.0</tuningStep>', file=output_file)
            print("</memory>", file=output_file)
            i += 1

        print("</memories>", file=output_file)
        print("<banks/>", file=output_file)
        print("</radio>", file=output_file)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: arrl-csv-to-chirp-xml <input.csv>", file=sys.stderr)
        sys.exit(1)
    convert(sys.argv[1])


if __name__ == "__main__":
    main()
