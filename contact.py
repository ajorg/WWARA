from decimal import Decimal


class Contact:
    id_k = "ID"
    call_k = "Call"
    timeslot_k = "Timeslot"
    first_name_k = "First Name"
    last_name_k = "Last Name"
    city_k = "City"
    state_k = "State"
    country_k = "Country"
    fieldnames = (
        id_k,
        call_k,
        first_name_k,
        last_name_k,
        city_k,
        state_k,
        country_k,
    )

    def __init__(
        self,
        id,
        call,
        timeslot=None,
        first_name=None,
        last_name=None,
        city=None,
        state=None,
        country=None,
    ):
        self.id = Decimal(id)
        self.call = call
        self.timeslot = timeslot
        self.first_name = first_name
        self.last_name = last_name
        self.city = city
        self.state = state
        self.country = country

    def __str__(self):
        return f"{self.id} {self.call} {self.first_name} {self.last_name}"

    def __getitem__(self, key):
        if key not in self.fieldnames:
            raise KeyError(key)
        return self.get(key)

    def get(self, key, default=None):
        for k, v in self.items():
            if k == key:
                return v
        return default

    def __setitem__(self, key, value):
        raise KeyError(key)

    def keys(self):
        return {k: None for k in self.fieldnames}.keys()

    def items(self):
        yield self.id_k, self.id
        yield self.call_k, self.call
        yield self.first_name_k, self.first_name
        yield self.last_name_k, self.last_name
        yield self.city_k, self.city
        yield self.state_k, self.state
        yield self.country_k, self.country
