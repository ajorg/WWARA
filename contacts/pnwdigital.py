from decimal import Decimal
from urllib.request import urlopen
from html.parser import HTMLParser

from contacts.radioid import contacts

import urllib.request
from html.parser import HTMLParser

RADIOID_CONTACTS = {}
for contact in contacts():
    RADIOID_CONTACTS[contact.id] = contact


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_table = False
        self.in_tr = False
        self.in_th = False
        self.in_td = False
        self.table = []
        self.tr = []
        self.th = []

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.in_table = True
        elif tag == "tr":
            self.in_tr = True
        elif tag == "th":
            self.in_th = True
        elif tag == "td":
            self.in_td = True

    def handle_data(self, data):
        if self.in_td:
            self.tr.append(data.strip())
        if self.in_th:
            self.th.append(data.strip())

    def handle_endtag(self, tag):
        if tag == "table":
            self.in_table = False
        elif tag == "tr":
            self.in_tr = False
            if self.tr:
                self.table.append(dict(zip(self.th, self.tr)))
            self.tr = []
        elif tag == "th":
            self.in_th = False
        elif tag == "td":
            self.in_td = False


FREQUENT_IDS = []


def frequent_ids():
    if FREQUENT_IDS:
        return FREQUENT_IDS
    with urlopen("https://pnwdigital.net/services/frequentids.php") as response:
        content = response.read().decode("utf-8")
    parser = TableParser()
    parser.feed(content)
    for row in parser.table:
        yield RADIOID_CONTACTS[Decimal(row["Call ID"])]


if __name__ == "__main__":
    for contact in frequent_ids():
        print(contact)
