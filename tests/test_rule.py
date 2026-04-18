"""Tests for the Rule class."""
from decimal import Decimal

from channel import Channel
from rule import Rule


class TestRuleInit:
    """Tests for Rule initialization."""

    def test_basic_rule(self):
        """Test creating a basic rule."""
        rule = Rule("145.10", "145.20", "-0.6", "20")
        assert rule.low == Decimal("145.10")
        assert rule.high == Decimal("145.20")
        assert rule.offset == Decimal("-0.6")
        assert rule.spacing == Decimal("20")

    def test_rule_with_bandwidth(self):
        """Test creating a rule with bandwidth."""
        rule = Rule("145.10", "145.20", "-0.6", "12.5", "12.5")
        assert rule.bandwidth == Decimal("12.5")

    def test_rule_default_bandwidth(self):
        """Test default bandwidth is 25."""
        rule = Rule("145.10", "145.20", "-0.6", "20")
        assert rule.bandwidth == Decimal("25")


class TestRuleContains:
    """Tests for Rule contains method."""

    def test_valid_channel_in_rule(self):
        """Test that a valid channel is in the rule."""
        rule = Rule("145.10", "145.20", "-0.6", "20")
        # 145.12 is on 20 kHz spacing from 145.10 (145.10 + 0.02 = 145.12)
        ch = Channel(
            call="K7XXX",
            output=Decimal("145.12"),
            input=Decimal("144.52"),
        )
        assert ch in rule

    def test_channel_out_of_range(self):
        """Test that channel outside frequency range is not in rule."""
        rule = Rule("145.10", "145.20", "-0.6", "20")
        ch = Channel(
            call="K7XXX",
            output=Decimal("145.25"),
            input=Decimal("144.65"),
        )
        assert ch not in rule

    def test_wrong_offset(self):
        """Test that channel with wrong offset is not in rule."""
        rule = Rule("145.10", "145.20", "-0.6", "20")
        ch = Channel(
            call="K7XXX",
            output=Decimal("145.15"),
            input=Decimal("145.75"),
        )
        assert ch not in rule

    def test_wrong_spacing(self):
        """Test that channel with wrong spacing is not in rule."""
        rule = Rule("145.10", "145.20", "-0.6", "20")  # 20 kHz spacing
        ch = Channel(
            call="K7XXX",
            output=Decimal("145.115"),
            input=Decimal("144.515"),
        )
        assert ch not in rule  # 145.115 not on 20 kHz boundary

    def test_too_wide_bandwidth(self):
        """Test that channel with too wide bandwidth is not in rule."""
        rule = Rule("145.10", "145.20", "-0.6", "20", "12.5")
        ch = Channel(
            call="K7XXX",
            output=Decimal("145.15"),
            input=Decimal("144.55"),
            bandwidth=Decimal("25"),
        )
        assert ch not in rule

    def test_ultra_narrowband_rule(self):
        """Test ultra-narrowband rule (6.25 kHz)."""
        rule = Rule("147.995", "147.995", "-0.6", "0", "6.25")
        ch = Channel(
            call="K7XXX", output=Decimal("147.995"), input=Decimal("147.395")
        )
        assert ch in rule


class TestRuleContainsIgnoreOffset:
    """Tests for Rule contains method with ignore_offset."""

    def test_ignore_offset_matches_output(self):
        """Test that ignore_offset matches based on output only."""
        rule = Rule("145.10", "145.20", "-0.6", "20")
        # 145.12 is on 20 kHz spacing, but wrong offset
        ch = Channel(
            call="K7XXX",
            output=Decimal("145.12"),
            input=Decimal("145.72"),
        )
        # Wrong offset, but should match with ignore_offset=True
        result = rule.contains(ch, ignore_offset=True)
        assert result is True


class TestRuleEquality:
    """Tests for Rule equality and hashing."""

    def test_equal_rules(self):
        """Test that rules with same parameters are equal."""
        rule1 = Rule("145.10", "145.20", "-0.6", "20")
        rule2 = Rule("145.10", "145.20", "-0.6", "20")
        assert rule1 == rule2

    def test_not_equal_different_low(self):
        """Test that rules with different low are not equal."""
        rule1 = Rule("145.10", "145.20", "-0.6", "20")
        rule2 = Rule("145.11", "145.20", "-0.6", "20")
        assert rule1 != rule2

    def test_hash_consistency(self):
        """Test that hash is consistent for equal rules."""
        rule1 = Rule("145.10", "145.20", "-0.6", "20")
        rule2 = Rule("145.10", "145.20", "-0.6", "20")
        assert hash(rule1) == hash(rule2)

    def test_rule_in_set(self):
        """Test that rules can be added to sets."""
        rule1 = Rule("145.10", "145.20", "-0.6", "20")
        rule2 = Rule("145.10", "145.20", "-0.6", "20")
        rule_set = {rule1, rule2}
        assert len(rule_set) == 1  # Should be deduplicated


class TestRuleString:
    """Tests for Rule string representation."""

    def test_rule_str(self):
        """Test rule string representation."""
        rule = Rule("145.10", "145.20", "-0.6", "20")
        rule_str = str(rule)
        assert "145.1" in rule_str
        assert "145.2" in rule_str
        assert "-0.6" in rule_str


class TestRuleChannelTracking:
    """Tests for Rule channel tracking."""

    def test_channel_rules_populated(self):
        """Test that channel.rules is populated when checking containment."""
        rule = Rule("145.10", "145.20", "-0.6", "20")
        # 145.12 is on 20 kHz spacing from 145.10
        ch = Channel(
            call="K7XXX",
            output=Decimal("145.12"),
            input=Decimal("144.52"),
        )
        _ = ch in rule  # Trigger containment check
        assert rule in ch.rules
        assert "offset" in ch.rules[rule]
        assert "spacing" in ch.rules[rule]
        assert "bandwidth" in ch.rules[rule]
