#!/usr/bin/env python
"""Converts a WWARA database dump to ICOM format."""
import codecs
import logging
from csv import DictReader, DictWriter
from decimal import Decimal
from io import BytesIO, StringIO
from sys import stdout
from zipfile import ZipFile

LOG = logging.getLogger(__name__)

FIELDNAMES = (
    "Group No",
    "Group Name",
    "Name",
    "Sub Name",
    "Repeater Call Sign",
    "Gateway Call Sign",
    "Frequency",
    "Dup",
    "Offset",
    "Mode",
    "TONE",
    "Repeater Tone",
    "RPT1USE",
    "Position",
    "Latitude",
    "Longitude",
    "UTC Offset",
)


def _drop_decimals(decimal):
    """Decimal.normalize gives 2E+1 for 20..."""
    decimal = str(decimal)
    if "." in decimal:
        decimal = decimal.rstrip("0").rstrip(".")
    return decimal


def _supported(row):
    """Checks if the mode is supported."""
    if "Y" in (
        row["DMR"],
        row["P25_PHASE_1"],
        row["P25_PHASE_2"],
        # row['FUSION'],  # Fusion also operates Analog
        row["NXDN_DIGITAL"],
        row["ATV"],
        row["DATV"],
    ):
        # These are not Analog modes
        return False
    ifreq = Decimal(row["INPUT_FREQ"])
    if ifreq > 144 and ifreq < 148:
        # 2M
        return True
    if ifreq > 420 and ifreq < 450:
        # 70CM
        return True
    return False


def _offset(row):
    """Computes the correct frequency offset."""
    ifreq = Decimal(row["INPUT_FREQ"])
    ofreq = Decimal(row["OUTPUT_FREQ"])
    duplex = "OFF"
    offset = Decimal(0)
    if ofreq < ifreq:
        duplex = "DUP+"
        offset = ifreq - ofreq
    elif ofreq > ifreq:
        duplex = "DUP-"
        offset = ofreq - ifreq
    return duplex, _drop_decimals(offset)


def _mode(row):
    """Converts the mode per WWARA to the mode string for ICOM."""
    mode = "FM"
    if row["DSTAR_DV"] == "Y":
        mode = "DV"
    elif row["FM_WIDE"] == "Y":
        mode = "FM"
    elif row["FM_NARROW"] == "Y":
        mode = "FM-N"
    return mode


def _access(row):
    """Determines the access mode (like CTCSS)."""
    access = "OFF"
    tone = "88.5Hz"
    tsql = "88.5Hz"
    if row["CTCSS_IN"]:
        access = "TONE"
        tone = "{:.1f}Hz".format(Decimal(row["CTCSS_IN"]))
        if row["CTCSS_OUT"]:
            # Unsure if the data is reliable, and I understand most hams don't
            # configure this, lest they miss something.
            # access = 'TSQL'
            tsql = "{:.1f}Hz".format(Decimal(row["CTCSS_OUT"]))
    # No DTCS possible!?
    return access, tone, tsql


def _name(row, pending=False):
    """Formats a usable name for the repeater."""
    name = " ".join((row["CALL"], row["CITY"]))[:16]
    if pending:
        name = "[{}]".format(name[:14])
    return name


def _call(row):
    """Builds an appropriate Call string for D-STAR."""
    call = row["CALL"]
    if row["DSTAR_DV"] == "N" and row["DSTAR_DD"] == "N":
        return call, None
    ifreq = Decimal(row["INPUT_FREQ"])
    if ifreq > 144 and ifreq < 148:
        # 2M
        return "{:<7}C".format(call), "{:<7}G".format(call)
    if ifreq > 420 and ifreq < 450:
        # 70CM
        return "{:<7}B".format(call), "{:<7}G".format(call)


def _position(row):
    """Returns the coordinates, or disables the position."""
    latitude = row["LATITUDE"]
    longitude = row["LONGITUDE"]
    position = "None"
    if latitude and longitude:
        position = "Approximate"
    return position, latitude or "0", longitude or "-0"


def convert(zipfile):
    """Converts a WWARA zipfile."""
    wlist = []
    for name in zipfile.namelist():
        if name.endswith(".csv"):
            pending = bool("-pending-" in name)
            with zipfile.open(name, "r") as csv:
                # Remove the DATA_SPEC_VERSION header line from the .csv
                csv.readline()
                i = 0
                for row in DictReader(codecs.getreader("us-ascii")(csv)):
                    if not _supported(row):
                        continue
                    duplex, offset = _offset(row)
                    mode = _mode(row)
                    name = _name(row, pending)
                    call, gateway = _call(row)
                    # Ignore tone squelch because data might be unreliable
                    access, tone, _ = _access(row)
                    position, latitude, longitude = _position(row)
                    wlist.append(
                        {
                            "Group No": 7,
                            "Group Name": "WWARA",
                            "Name": name,
                            "Sub Name": row["LOCALE"][:8],
                            "Repeater Call Sign": call,
                            "Gateway Call Sign": gateway,
                            "Frequency": _drop_decimals(row["OUTPUT_FREQ"]),
                            "Dup": duplex,
                            "Offset": offset,
                            "Mode": mode,
                            "TONE": access,
                            "Repeater Tone": tone,  # No field for DTCS!?
                            "RPT1USE": "YES",  # Something like "Don't Skip"?
                            "Position": position,
                            "Latitude": latitude,
                            "Longitude": longitude,
                            "UTC Offset": "-8:00",  # PST, but how is this useful!?
                        }
                    )
                    i += 1
    return sorted(wlist, key=lambda x: (x["Mode"], Decimal(x["Frequency"])))


def lambda_handler(event=None, context=None):
    """Handler for use in AWS Lambda."""
    import boto3
    from os import environ

    try:
        from urllib.parse import urlparse
    except ImportError:
        from urlparse import urlparse

    LOG.setLevel(logging.DEBUG)

    client = boto3.client("s3")

    source = environ.get("SOURCE")
    src_parsed = urlparse(source)
    src_bucket = src_parsed.netloc
    src_key = src_parsed.path.lstrip("/")

    destination = environ.get("DESTINATION")
    dst_parsed = urlparse(destination)
    dst_bucket = dst_parsed.netloc
    dst_key = dst_parsed.path.lstrip("/")

    LOG.info("Reading from %s", source)
    src = client.get_object(Bucket=src_bucket, Key=src_key)
    data = src.get("Body").read()
    zipfile = ZipFile(BytesIO(data))

    string_obj = StringIO()
    writer = DictWriter(string_obj, FIELDNAMES)
    writer.writeheader()
    LOG.info("Converting...")
    writer.writerows(convert(zipfile))

    LOG.info("Writing to %s", destination)
    client.put_object(
        Bucket=dst_bucket,
        Key=dst_key,
        Body=string_obj.getvalue(),
        ContentType="text/csv",
        StorageClass="REDUCED_REDUNDANCY",
        ACL="public-read",
    )
    string_obj.close()


if __name__ == "__main__":
    import requests

    RESPONSE = requests.get("https://www.wwara.org/DataBaseExtract.zip")
    # ZipFile requires a file-like object that supports seek
    FILE_OBJ = BytesIO(RESPONSE.content)
    RESPONSE.close()
    ZIPFILE = ZipFile(FILE_OBJ)

    WRITER = DictWriter(stdout, FIELDNAMES)
    WRITER.writeheader()

    WRITER.writerows(convert(ZIPFILE))

    FILE_OBJ.close()
