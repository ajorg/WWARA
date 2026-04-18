"""Tests for the Contact class."""
from decimal import Decimal

import pytest

from contact import Contact


class TestContactInit:
    """Tests for Contact initialization."""

    def test_basic_contact(self):
        """Test creating a basic contact."""
        contact = Contact(id=Decimal("12345"), call="K7XXX")
        assert contact.id == Decimal("12345")
        assert contact.call == "K7XXX"

    def test_contact_with_name(self):
        """Test creating a contact with explicit name."""
        contact = Contact(id=Decimal("12345"), name="John Doe")
        assert contact.name == "John Doe"

    def test_contact_full_details(self):
        """Test creating a contact with all details."""
        contact = Contact(
            id=Decimal("12345"),
            call="K7XXX",
            first_name="John",
            last_name="Doe",
            city="Seattle",
            state="WA",
            country="USA",
        )
        assert contact.first_name == "John"
        assert contact.last_name == "Doe"
        assert contact.city == "Seattle"
        assert contact.state == "WA"
        assert contact.country == "USA"


class TestContactName:
    """Tests for Contact name property."""

    def test_name_from_call_and_first_name(self):
        """Test name generated from call and first name."""
        contact = Contact(
            id=Decimal("12345"), call="K7XXX", first_name="John"
        )
        assert contact.name == "K7XXX John"

    def test_explicit_name_takes_precedence(self):
        """Test that explicit name takes precedence."""
        contact = Contact(
            id=Decimal("12345"),
            name="Custom Name",
            call="K7XXX",
            first_name="John",
        )
        assert contact.name == "Custom Name"


class TestContactString:
    """Tests for Contact string representation."""

    def test_contact_str(self):
        """Test contact string representation."""
        contact = Contact(id=Decimal("12345"), call="K7XXX")
        contact_str = str(contact)
        assert "12345" in contact_str


class TestContactDictInterface:
    """Tests for Contact dictionary-like interface."""

    def test_getitem(self):
        """Test getting values by key."""
        contact = Contact(
            id=Decimal("12345"),
            call="K7XXX",
            first_name="John",
            last_name="Doe",
        )
        assert contact["ID"] == Decimal("12345")
        assert contact["Call"] == "K7XXX"
        assert contact["First Name"] == "John"

    def test_getitem_invalid_key(self):
        """Test getting invalid key raises KeyError."""
        contact = Contact(id=Decimal("12345"), call="K7XXX")
        with pytest.raises(KeyError):
            _ = contact["InvalidKey"]

    def test_get_with_default(self):
        """Test get with default value."""
        contact = Contact(id=Decimal("12345"), call="K7XXX")
        assert contact.get("InvalidKey", "default") == "default"

    def test_keys(self):
        """Test keys method."""
        contact = Contact(id=Decimal("12345"), call="K7XXX")
        keys = list(contact.keys())
        assert "ID" in keys
        assert "Call" in keys

    def test_items(self):
        """Test items method."""
        contact = Contact(id=Decimal("12345"), call="K7XXX")
        items = list(contact.items())
        assert ("ID", Decimal("12345")) in items
        assert ("Call", "K7XXX") in items


class TestContactSetitem:
    """Tests for Contact setitem (should raise)."""

    def test_setitem_raises(self):
        """Test that setting values raises KeyError."""
        contact = Contact(id=Decimal("12345"), call="K7XXX")
        with pytest.raises(KeyError):
            contact["ID"] = Decimal("54321")
