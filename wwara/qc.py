#!/usr/bin/env python3
"""Quality control check for WWARA repeater database."""
from wwara.database import coordinations
from wwara.plan import EXCEPTIONS
from wwara.qa import test


def main():
    """Main entry point."""
    for channel in coordinations(filenames=False):
        error, comments = test(channel)
        # If a problem is known and accepted, we won't complain
        if channel in EXCEPTIONS:
            comments.append("KNOWN")
        elif error:
            comments.insert(0, "ERROR!")
        comments_str = " ".join(comments)
        print(f"{channel} {comments_str}")


if __name__ == "__main__":
    main()
