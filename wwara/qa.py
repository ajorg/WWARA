from wwara.database import coordinations
from wwara.plan import in_region, match

SEEN = set()


def test(channel):
    comments = []

    # Match various rules

    # Start with if it matches the band plan
    error = not match(channel)

    # Input and output reversed is not uncommon
    if match(~channel):
        error = False
        comments.append("REVERSED")

    # At least one mode should be defined
    if not channel.modes:
        error = True
        comments.append("NO MODES")

    # Should be within the geographical boundaries
    if not in_region(channel):
        error = True
        comments.append("OUT OF BOUNDS")

    if "FM" in channel.modes:
        # Should have either a CTCSS tone or DCS code
        if not (channel.input_tone or channel.input_code):
            error = True
            comments.append("NO TONE/CODE")
        # But shouldn't have both
        if channel.input_tone and channel.input_code:
            error = True
            comments.append("AMBIGUOUS TONE/CODE")
    else:
        if channel.input_tone or channel.input_code:
            error = True
            comments.append("EXTRA TONE/CODE")

    if "DMR" in channel.modes:
        # Should have a Color Code
        if channel.dmr_cc is None:
            error = True
            comments.append("NO CC")
    else:
        if channel.dmr_cc is not None:
            error = True
            comments.append("EXTRA DMR CC")

    if "C4FM" in channel.modes:
        # Should have a DSQ / DG-ID
        if channel.c4fm_dsq is None:
            # DSQ is obsoleted by DG-ID
            comments.append("NO DSQ")
        # DSQ is limited to 1-126
        # DG-ID is 0-99
        # Neither is octal (AFAICT)
        if not (0 <= channel.c4fm_dsq <= 99):
            comments.append("DG-ID OUT OF RANGE")
        if not (0 <= channel.c4fm_dsq <= 126):
            comments.append("DSQ OUT OF RANGE")
    else:
        if channel.c4fm_dsq is not None:
            error = True
            comments.append("EXTRA C4FM DSQ/DG-ID")

    if "P25" in channel.modes:
        # Should have a NAC
        if channel.p25_nac is None:
            error = True
            comments.append("NO NAC")
    else:
        if channel.p25_nac is not None:
            error = True
            comments.append("EXTRA P25 NAC")

    if "NXDN" in channel.modes:
        # Should have a RAN
        if channel.nxdn_ran is None:
            error = True
            comments.append("NO RAN")
    else:
        if channel.nxdn_ran is not None:
            error = True
            comments.append("EXTRA NXDN RAN")

    # Multimode is unusual, but not bad
    if len(channel.modes) > 1:
        comments.append("MULTIMODE")

    # Should only show up once in the database
    if channel in SEEN:
        # Not counting this as an error because the equality operator is course
        # error = True
        comments.append("DUPLICATE")
    SEEN.add(channel)

    # Basic errors like being too wide for the channel or having the wrong offset
    if channel.errors:
        error = True
        comments.extend(channel.errors)

    # And now we're done evaluating
    return error, comments
