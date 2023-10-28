import codecs
from csv import DictReader
from datetime import date
from io import StringIO
from os import path
from os.path import abspath, dirname, join
from urllib.request import urlopen

from contact import Contact

CSVFILE_PATH = join(dirname(abspath(__file__)), "pnwdigital.csv")


def all():
    with open(CSVFILE_PATH, mode="r", newline="") as csvfile:
        groups = DictReader(csvfile)
        for row in groups:
            yield Contact(
                name=row["Name"],
                id=row["ID"],
                timeslot=(row["Timeslot"] or None),
                type="Group",
            )


if __name__ == "__main__":
    for contact in all():
        print(f"{contact}: {contact.timeslot}")
