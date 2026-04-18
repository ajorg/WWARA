"""Tests for the Channel class."""
from decimal import Decimal

import pytest

from channel import Channel


class TestChannelInit:
    """Tests for Channel initialization."""

    def test_basic_channel(self):
        """Test creating a basic channel."""
        ch = Channel(
            call="K7XXX",
            output=Decimal("145.200"),
            input=Decimal("145.800"),
        )
        assert ch.call == "K7XXX"
        assert ch.output == Decimal("145.200")
        assert ch.input == Decimal("145.800")

    def test_channel_with_offset(self):
        """Test creating a channel with offset instead of input."""
        ch = Channel(
            call="K7XXX",
            output=Decimal("442.000"),
            offset=Decimal("5"),
        )
        assert ch.input == Decimal("447.000")

    def test_channel_call_stripped(self):
        """Test that call sign is stripped of whitespace."""
        ch = Channel(call="  K7XXX  ", output=Decimal("145.200"))
        assert ch.call == "K7XXX"

    def test_channel_default_bandwidth(self):
        """Test default bandwidth is 25."""
        ch = Channel(call="K7XXX", output=Decimal("145.200"))
        assert ch.bandwidth == Decimal("25")

    def test_channel_default_modes(self):
        """Test default modes is FM."""
        ch = Channel(call="K7XXX", output=Decimal("145.200"))
        assert ch.modes == ("FM",)


class TestChannelOffset:
    """Tests for Channel offset calculation."""

    def test_positive_offset(self):
        """Test positive offset (input > output)."""
        ch = Channel(
            call="K7XXX",
            output=Decimal("145.200"),
            input=Decimal("145.800"),
        )
        assert ch.offset == Decimal("0.6")

    def test_negative_offset(self):
        """Test negative offset (input < output)."""
        ch = Channel(
            call="K7XXX",
            output=Decimal("442.000"),
            input=Decimal("437.000"),
        )
        assert ch.offset == Decimal("-5")

    def test_zero_offset(self):
        """Test zero offset (simplex)."""
        ch = Channel(
            call="K7XXX",
            output=Decimal("146.520"),
            input=Decimal("146.520"),
        )
        assert ch.offset == Decimal("0")


class TestChannelDistance:
    """Tests for Channel distance calculation."""

    def test_distance_seattle_tacoma(self):
        """Test distance calculation between Seattle and Tacoma."""
        seattle = Channel(
            call="K7SEA",
            output=Decimal("145.200"),
            latitude=Decimal("47.6062"),
            longitude=Decimal("-122.3321"),
        )
        distance = seattle.distance(Decimal("47.45"), Decimal("-122.30"))
        assert 15 < distance < 20  # ~17.5 km

    def test_distance_same_location(self):
        """Test distance to same location is zero."""
        ch = Channel(
            call="K7XXX",
            output=Decimal("145.200"),
            latitude=Decimal("47.6062"),
            longitude=Decimal("-122.3321"),
        )
        distance = ch.distance(Decimal("47.6062"), Decimal("-122.3321"))
        assert distance < 0.1  # Very close to zero


class TestChannelEquality:
    """Tests for Channel equality and hashing."""

    def test_equal_channels(self):
        """Test that channels with same key fields are equal."""
        ch1 = Channel(
            call="K7XXX", output=Decimal("145.200"), input=Decimal("145.800")
        )
        ch2 = Channel(
            call="K7XXX", output=Decimal("145.200"), input=Decimal("145.800")
        )
        assert ch1 == ch2

    def test_equal_ignores_location(self):
        """Test that equality ignores non-key fields like location."""
        ch1 = Channel(
            call="K7XXX",
            output=Decimal("145.200"),
            input=Decimal("145.800"),
            location="Seattle",
        )
        ch2 = Channel(
            call="K7XXX",
            output=Decimal("145.200"),
            input=Decimal("145.800"),
            location="Tacoma",
        )
        assert ch1 == ch2

    def test_not_equal_different_output(self):
        """Test that channels with different output are not equal."""
        ch1 = Channel(
            call="K7XXX", output=Decimal("145.200"), input=Decimal("145.800")
        )
        ch2 = Channel(
            call="K7XXX", output=Decimal("145.210"), input=Decimal("145.810")
        )
        assert ch1 != ch2

    def test_hash_consistency(self):
        """Test that hash is consistent for equal channels."""
        ch1 = Channel(
            call="K7XXX", output=Decimal("145.200"), input=Decimal("145.800")
        )
        ch2 = Channel(
            call="K7XXX", output=Decimal("145.200"), input=Decimal("145.800")
        )
        assert hash(ch1) == hash(ch2)

    def test_channel_in_set(self):
        """Test that channels can be added to sets."""
        ch1 = Channel(
            call="K7XXX", output=Decimal("145.200"), input=Decimal("145.800")
        )
        ch2 = Channel(
            call="K7XXX", output=Decimal("145.200"), input=Decimal("145.800")
        )
        channel_set = {ch1, ch2}
        assert len(channel_set) == 1  # Should be deduplicated


class TestChannelModes:
    """Tests for Channel mode properties."""

    def test_fm_mode(self):
        """Test FM mode property."""
        ch = Channel(call="K7XXX", output=Decimal("145.200"), modes=["FM"])
        assert ch.fm is True
        assert ch.dmr is False

    def test_dmr_mode(self):
        """Test DMR mode property."""
        ch = Channel(call="K7XXX", output=Decimal("442.000"), modes=["DMR"])
        assert ch.dmr is True
        assert ch.fm is False

    def test_multimode(self):
        """Test multiple modes."""
        ch = Channel(
            call="K7XXX", output=Decimal("442.000"), modes=["FM", "DMR", "P25"]
        )
        assert ch.fm is True
        assert ch.dmr is True
        assert ch.p25 is True


class TestChannelAccess:
    """Tests for Channel access property."""

    def test_fm_with_tone(self):
        """Test FM with CTCSS tone."""
        ch = Channel(
            call="K7XXX",
            output=Decimal("145.200"),
            modes=["FM"],
            input_tone=Decimal("100.0"),
        )
        assert "FM 100.0" in ch.access

    def test_dmr_with_cc(self):
        """Test DMR with color code."""
        ch = Channel(
            call="K7XXX",
            output=Decimal("442.000"),
            modes=["DMR"],
            dmr_cc=Decimal("1"),
        )
        assert "DMR CC1" in ch.access

    def test_nfm_mode(self):
        """Test narrow FM mode."""
        ch = Channel(
            call="K7XXX",
            output=Decimal("145.200"),
            modes=["FM"],
            bandwidth=Decimal("12.5"),
            input_tone=Decimal("100.0"),
        )
        assert "NFM 100.0" in ch.access


class TestChannelName:
    """Tests for Channel name property."""

    def test_name_from_call_and_location(self):
        """Test name generated from call and location."""
        ch = Channel(
            call="K7XXX", output=Decimal("145.200"), location="Seattle"
        )
        assert ch.name == "K7XXX Seattle"

    def test_name_truncated(self):
        """Test that name is truncated to max length."""
        long_location = "A" * 300
        ch = Channel(
            call="K7XXX", output=Decimal("145.200"), location=long_location
        )
        assert len(ch.name) <= Channel.name_length

    def test_custom_name(self):
        """Test setting custom name."""
        ch = Channel(call="K7XXX", output=Decimal("145.200"))
        ch.name = "Custom Name"
        assert ch.name == "Custom Name"


class TestChannelInvert:
    """Tests for Channel inversion (swap input/output)."""

    def test_invert_swaps_frequencies(self):
        """Test that inversion swaps input and output."""
        ch = Channel(
            call="K7XXX",
            output=Decimal("145.200"),
            input=Decimal("145.800"),
        )
        inv = ~ch
        assert inv.output == Decimal("145.800")
        assert inv.input == Decimal("145.200")

    def test_invert_preserves_other_fields(self):
        """Test that inversion preserves other fields."""
        ch = Channel(
            call="K7XXX",
            output=Decimal("145.200"),
            input=Decimal("145.800"),
            location="Seattle",
            modes=["FM"],
        )
        inv = ~ch
        assert inv.call == "K7XXX"
        assert inv.location == "Seattle"
        assert inv.modes == ["FM"]


class TestChannelComparison:
    """Tests for Channel comparison operators."""

    def test_less_than(self):
        """Test less than comparison."""
        ch1 = Channel(call="K7AAA", output=Decimal("145.200"))
        ch2 = Channel(call="K7BBB", output=Decimal("145.210"))
        assert ch1 < ch2

    def test_greater_than(self):
        """Test greater than comparison."""
        ch1 = Channel(call="K7AAA", output=Decimal("145.210"))
        ch2 = Channel(call="K7BBB", output=Decimal("145.200"))
        assert ch1 > ch2


class TestChannelDictInterface:
    """Tests for Channel dictionary-like interface."""

    def test_getitem(self):
        """Test getting values by key."""
        ch = Channel(
            call="K7XXX",
            output=Decimal("145.200"),
            location="Seattle",
        )
        assert ch["Call"] == "K7XXX"
        assert ch["Output"] == Decimal("145.200")
        assert ch["Location"] == "Seattle"

    def test_getitem_invalid_key(self):
        """Test getting invalid key raises KeyError."""
        ch = Channel(call="K7XXX", output=Decimal("145.200"))
        with pytest.raises(KeyError):
            _ = ch["InvalidKey"]

    def test_get_with_default(self):
        """Test get with default value."""
        ch = Channel(call="K7XXX", output=Decimal("145.200"))
        assert ch.get("InvalidKey", "default") == "default"

    def test_keys(self):
        """Test keys method."""
        ch = Channel(call="K7XXX", output=Decimal("145.200"))
        keys = list(ch.keys())
        assert "Call" in keys
        assert "Output" in keys

    def test_items(self):
        """Test items method."""
        ch = Channel(call="K7XXX", output=Decimal("145.200"))
        items = list(ch.items())
        assert ("Call", "K7XXX") in items
        assert ("Output", Decimal("145.200")) in items
