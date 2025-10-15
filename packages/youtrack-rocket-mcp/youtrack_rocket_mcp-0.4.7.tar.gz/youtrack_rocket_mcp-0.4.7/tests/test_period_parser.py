"""Tests for period parser utility."""

import pytest

from youtrack_rocket_mcp.utils.period_parser import format_minutes_to_period, parse_period_to_minutes


class TestParsePeriodToMinutes:
    """Tests for parse_period_to_minutes function."""

    def test_parse_simple_hours(self):
        """Test parsing simple hours."""
        assert parse_period_to_minutes('1h') == 60
        assert parse_period_to_minutes('2h') == 120
        assert parse_period_to_minutes('24h') == 1440

    def test_parse_simple_minutes(self):
        """Test parsing simple minutes."""
        assert parse_period_to_minutes('30m') == 30
        assert parse_period_to_minutes('15m') == 15
        assert parse_period_to_minutes('90m') == 90

    def test_parse_simple_days(self):
        """Test parsing simple days."""
        assert parse_period_to_minutes('1d') == 1440
        assert parse_period_to_minutes('2d') == 2880

    def test_parse_simple_weeks(self):
        """Test parsing simple weeks."""
        assert parse_period_to_minutes('1w') == 10080
        assert parse_period_to_minutes('2w') == 20160

    def test_parse_combined_format(self):
        """Test parsing combined time formats."""
        assert parse_period_to_minutes('1h 30m') == 90
        assert parse_period_to_minutes('2d 4h') == 3120
        # 1w = 10080, 2d = 2880, 3h = 180, 30m = 30 => 13170
        assert parse_period_to_minutes('1w 2d 3h 30m') == 13170

    def test_parse_decimal_hours(self):
        """Test parsing decimal hours."""
        assert parse_period_to_minutes('1.5h') == 90
        assert parse_period_to_minutes('2.25h') == 135

    def test_parse_with_spaces(self):
        """Test parsing with various spacing."""
        assert parse_period_to_minutes('1h30m') == 90
        assert parse_period_to_minutes('1h  30m') == 90
        assert parse_period_to_minutes(' 1h 30m ') == 90

    def test_parse_integer_input(self):
        """Test that integer input is returned as-is."""
        assert parse_period_to_minutes(60) == 60
        assert parse_period_to_minutes(120) == 120

    def test_parse_string_integer(self):
        """Test parsing string representation of integer."""
        assert parse_period_to_minutes('60') == 60
        assert parse_period_to_minutes('120') == 120

    def test_parse_invalid_format(self):
        """Test that invalid formats raise ValueError."""
        with pytest.raises(ValueError, match='Invalid period format'):
            parse_period_to_minutes('invalid')

        with pytest.raises(ValueError, match='Invalid period format'):
            parse_period_to_minutes('1x 2y')

    def test_parse_invalid_unit(self):
        """Test that invalid units raise ValueError."""
        with pytest.raises(ValueError, match='Invalid period format'):
            parse_period_to_minutes('1x')

    def test_parse_empty_string(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match='Invalid period string'):
            parse_period_to_minutes('')

    def test_parse_none(self):
        """Test that None raises ValueError."""
        with pytest.raises(ValueError, match='Invalid period string'):
            parse_period_to_minutes(None)  # type: ignore[arg-type]


class TestFormatMinutesToPeriod:
    """Tests for format_minutes_to_period function."""

    def test_format_simple_hours(self):
        """Test formatting simple hours."""
        assert format_minutes_to_period(60) == '1h'
        assert format_minutes_to_period(120) == '2h'

    def test_format_simple_minutes(self):
        """Test formatting simple minutes."""
        assert format_minutes_to_period(30) == '30m'
        assert format_minutes_to_period(15) == '15m'

    def test_format_hours_and_minutes(self):
        """Test formatting hours and minutes."""
        assert format_minutes_to_period(90) == '1h 30m'
        assert format_minutes_to_period(135) == '2h 15m'

    def test_format_days(self):
        """Test formatting days."""
        assert format_minutes_to_period(1440) == '1d'
        assert format_minutes_to_period(2880) == '2d'

    def test_format_weeks(self):
        """Test formatting weeks."""
        assert format_minutes_to_period(10080) == '1w'
        assert format_minutes_to_period(20160) == '2w'

    def test_format_complex(self):
        """Test formatting complex periods."""
        # 13170 = 1w (10080) + 2d (2880) + 3h (180) + 30m (30)
        assert format_minutes_to_period(13170) == '1w 2d 3h 30m'
        assert format_minutes_to_period(3120) == '2d 4h'

    def test_format_zero(self):
        """Test formatting zero minutes."""
        assert format_minutes_to_period(0) == '0m'

    def test_format_float(self):
        """Test formatting float minutes (truncates to int)."""
        assert format_minutes_to_period(90.5) == '1h 30m'
        assert format_minutes_to_period(60.9) == '1h'

    def test_format_invalid_input(self):
        """Test that invalid input raises ValueError."""
        with pytest.raises(ValueError, match='Invalid minutes value'):
            format_minutes_to_period(-1)

        with pytest.raises(ValueError, match='Invalid minutes value'):
            format_minutes_to_period('invalid')  # type: ignore[arg-type]


class TestPeriodParserRoundtrip:
    """Test round-trip parsing and formatting."""

    def test_roundtrip_simple(self):
        """Test round-trip for simple periods."""
        original = '1h'
        minutes = parse_period_to_minutes(original)
        formatted = format_minutes_to_period(minutes)
        assert formatted == original

    def test_roundtrip_combined(self):
        """Test round-trip for combined periods."""
        # Note: Input may be normalized
        minutes = parse_period_to_minutes('1h 30m')
        formatted = format_minutes_to_period(minutes)
        assert formatted == '1h 30m'

        # 1w + 2d + 3h + 30m = 13170 minutes
        minutes = parse_period_to_minutes('1w 2d 3h 30m')
        formatted = format_minutes_to_period(minutes)
        assert formatted == '1w 2d 3h 30m'
