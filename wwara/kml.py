#!/usr/bin/env python3
"""Generate KML file for WWARA repeaters."""
import xml.etree.ElementTree as ET

from wwara.database import coordinations

LAYERS = {
    "VHF FM": {"low": 144, "high": 148, "mode": "FM"},
    "UHF FM": {"low": 420, "high": 450, "mode": "FM"},
    "VHF DMR": {"low": 144, "high": 148, "mode": "DMR"},
    "UHF DMR": {"low": 420, "high": 450, "mode": "DMR"},
}


def layer(low, high, mode, folder):
    """Add channels to a KML folder."""
    for channel in channels:
        if (not (low <= channel.input <= high)) or (mode not in channel.modes):
            continue
        output = str(channel.output).rstrip("0")
        input_freq = str(channel.input).rstrip("0")
        offset = f"{channel.offset:+.2f}".rstrip("0").rstrip(".")
        access = None
        if mode == "DMR":
            access = f"CC{channel.dmr_cc}"
        elif mode == "FM":
            if channel.input_tone:
                access = f"{channel.input_tone:.1f}"
            elif channel.input_code:
                access = f"D{channel.input_code}N"
        parts = [channel.call, channel.location, output, offset, mode, access]
        channel.name = " ".join(parts)
        if channel.latitude < 0:
            channel.latitude = -channel.latitude
        if channel.longitude > 0:
            channel.longitude = -channel.longitude
        placemark = ET.SubElement(folder, "Placemark")
        name = ET.SubElement(placemark, "name")
        name.text = channel.name
        extended_data = ET.SubElement(placemark, "ExtendedData")
        for k, v in {
            "callsign": channel.call,
            "location": channel.location,
            "output": f"{output} MHz",
            "input": f"{input_freq} MHz",
            "offset": f"{offset} MHz",
            "mode": mode,
            "access": access,
        }.items():
            data = ET.SubElement(extended_data, "Data", name=k)
            value = ET.SubElement(data, "value")
            value.text = v
        point = ET.SubElement(placemark, "Point")
        coords = ET.SubElement(point, "coordinates")
        coords.text = f"{channel.longitude},{channel.latitude},0"


def main():
    """Main entry point."""
    global channels
    channels = list(coordinations())

    kml = ET.Element("kml", xmlns="http://www.opengis.net/kml/2.2")
    doc = ET.SubElement(kml, "Document")
    name = ET.SubElement(doc, "name")
    name.text = "WWARA Repeaters"

    for name_str, parameters in LAYERS.items():
        folder = ET.SubElement(doc, "Folder")
        folder_name = ET.SubElement(folder, "name")
        folder_name.text = name_str
        layer(**parameters, folder=folder)

    tree = ET.ElementTree(kml)
    tree.write("WWARA Repeaters.kml")


if __name__ == "__main__":
    main()
