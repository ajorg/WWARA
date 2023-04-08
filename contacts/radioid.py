from json import load
from urllib.request import urlopen
from contact import Contact


def contacts():
    with urlopen("https://radioid.net/static/users.json") as response:
        users = load(response)["users"]
    for user in users:
        if user["id"] != user["radio_id"]:
            print(user)
        yield Contact(
            id=user["id"],
            call=user["callsign"],
            first_name=user["fname"],
            last_name=user["surname"],
            city=user["city"],
            state=user["state"],
            country=user["country"],
        )


if __name__ == "__main__":
    for contact in contacts():
        print(contact)
