#!/usr/bin/env python3
"""Compare WWARA repeater data against RepeaterBook."""
import json
from decimal import Decimal, InvalidOperation
from json.decoder import JSONDecodeError
from urllib.request import Request, urlopen

from channel import Channel
from wwara.database import coordinations

HEADERS = {
    "User-Agent": (
        "wwara-repeaterbook/1.0 "
        "(https://github.com/ajorg/WWARA/blob/main/wwara-repeaterbook, "
        "andrew@jorgensenfamily.us)"
    ),
}
API_URL = "https://www.repeaterbook.com/api/export.php?country=United%20States&state={}"


def main():
    """Main entry point."""
    results = []
    for state in ("Washington", "Oregon"):
        request = Request(API_URL.format(state), headers=HEADERS)
        with urlopen(request) as response:
            content = response.read()
            try:
                results.extend(json.loads(content)["results"])
            except JSONDecodeError:
                print(content.decode("utf8"))
                raise

    for channel in coordinations(filenames=True):
        found = False
        candidates = set()
        for result in results:
            modes = []

            tone, code = None, None
            if result["FM analog"] == "Yes":
                modes.append("FM")
                if result["PL"].startswith("D"):
                    code = result["PL"].lstrip("D")
                try:
                    tone = Decimal(result["PL"])
                except (ValueError, InvalidOperation):
                    pass

            dmr_cc = None
            if result["DMR"] == "Yes":
                modes.append("DMR")
                dmr_cc = result["DMR Color Code"]

            dstar_mode = None
            if result["D-Star"] == "Yes":
                modes.append("D-STAR")
                dstar_mode = "DV"

            c4fm_dsq = None
            if result["System Fusion"] == "Yes":
                modes.append("C4FM")
                c4fm_dsq = result["YSF DG ID Uplink"]

            p25_nac = None
            if result["APCO P-25"] == "Yes":
                modes.append("P25")
                p25_nac = result["P-25 NAC"]

            candidate = Channel(
                call=result["Callsign"],
                output=result["Frequency"],
                input=result["Input Freq"],
                location=result.get("Landmark") or result.get("Nearest City"),
                latitude=result["Lat"],
                longitude=result["Long"],
                input_tone=tone,
                input_code=code,
                dmr_cc=dmr_cc,
                dstar_mode=dstar_mode,
                c4fm_dsq=c4fm_dsq,
                p25_nac=p25_nac,
                modes=modes,
            )
            distance = channel.distance(
                candidate.latitude, candidate.longitude
            )
            if (distance < 80) and (channel.output == candidate.output):
                candidates.add(candidate)
            if channel == candidate:
                found = result
                break
        if not found:
            if not candidates:
                print(f"{channel} NOT FOUND")
            else:
                print(f"{channel} CANDIDATES")
                for candidate in sorted(candidates):
                    dist = channel.distance(
                        candidate.latitude, candidate.longitude
                    )
                    print(f"  {candidate} {dist:.1f}km")


if __name__ == "__main__":
    main()
