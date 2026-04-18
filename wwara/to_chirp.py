#!/usr/bin/env python3
"""Convert WWARA database to CHIRP XML format."""
import codecs
import xml.etree.ElementTree as ET
from csv import DictReader
from decimal import Decimal
from io import BytesIO
from urllib.request import urlopen
from zipfile import ZipFile

EXTRACT_URL = "https://www.wwara.org/DataBaseExtract.zip"


def drop_decimals(d):
    """Remove trailing zeros from decimal representation."""
    d = str(d)
    if "." in d:
        d = d.rstrip("0").rstrip(".")
    return d


def convert(zipfile, output_file="wwara.chirp"):
    """Convert WWARA database to CHIRP XML format."""
    for n in zipfile.namelist():
        if n.endswith(".csv") and "pending" not in n:
            radio = ET.Element("radio")
            tree = ET.ElementTree(radio)
            memories = ET.SubElement(radio, "memories")
            with zipfile.open(n) as c:
                c.readline()  # Remove DATA_SPEC_VERSION header
                d = DictReader(codecs.getreader("us-ascii")(c))
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
                    memory = ET.SubElement(memories, "memory", location=str(i))
                    ET.SubElement(memory, "shortName").text = name
                    ET.SubElement(memory, "longName").text = longname
                    freq_elem = ET.SubElement(memory, "frequency", units="MHz")
                    freq_elem.text = drop_decimals(out_freq)
                    rtone = ET.SubElement(
                        memory, "squelch", id="rtone", type="repeater"
                    )
                    rtone.text = row["CTCSS_IN"] or "88.5"
                    ctone = ET.SubElement(
                        memory, "squelch", id="ctone", type="ctcss"
                    )
                    ctone.text = row["CTCSS_OUT"] or "88.5"
                    dtcs = ET.SubElement(
                        memory, "squelch", id="dtcs", type="dtcs"
                    )
                    dtcs_code = ET.SubElement(dtcs, "code")
                    dtcs_code.text = row["DCS_CDCSS"] or "023"
                    dtcs_pol = ET.SubElement(dtcs, "polarity")
                    dtcs_pol.text = "NN"
                    if row["CTCSS_IN"]:
                        sq_set = ET.SubElement(memory, "squelchSetting")
                        sq_set.text = "rtone"
                    elif row["DCS_CDCSS"]:
                        sq_set = ET.SubElement(memory, "squelchSetting")
                        sq_set.text = "dtcs"
                    duplex_elem = ET.SubElement(memory, "duplex")
                    duplex_elem.text = duplex
                    offset_elem = ET.SubElement(memory, "offset", units="MHz")
                    offset_elem.text = drop_decimals(offset)
                    mode_elem = ET.SubElement(memory, "mode")
                    mode_elem.text = mode
                    step_elem = ET.SubElement(
                        memory, "tuningStep", units="kHz"
                    )
                    step_elem.text = "5.0"
                    i += 1
            ET.SubElement(radio, "banks")
            tree.write(output_file, xml_declaration=True)


def main():
    """Main entry point."""
    with urlopen(EXTRACT_URL) as response:
        f = BytesIO(response.read())
    z = ZipFile(f)
    convert(z)
    f.close()


if __name__ == "__main__":
    main()
