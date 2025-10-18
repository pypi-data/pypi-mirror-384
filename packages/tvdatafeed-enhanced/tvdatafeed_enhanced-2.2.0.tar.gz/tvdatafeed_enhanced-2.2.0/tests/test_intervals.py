"""Tests for Interval enum."""

import pytest
from tvDatafeed import Interval


class TestInterval:
    """Test cases for Interval enum."""

    def test_interval_values(self):
        """Test that all intervals have correct values."""
        assert Interval.in_1_minute.value == "1"
        assert Interval.in_3_minute.value == "3"
        assert Interval.in_5_minute.value == "5"
        assert Interval.in_15_minute.value == "15"
        assert Interval.in_30_minute.value == "30"
        assert Interval.in_45_minute.value == "45"
        assert Interval.in_1_hour.value == "1H"
        assert Interval.in_2_hour.value == "2H"
        assert Interval.in_3_hour.value == "3H"
        assert Interval.in_4_hour.value == "4H"
        assert Interval.in_daily.value == "1D"
        assert Interval.in_weekly.value == "1W"
        assert Interval.in_monthly.value == "1M"
        assert Interval.in_3_monthly.value == "3M"
        assert Interval.in_6_monthly.value == "6M"
        assert Interval.in_yearly.value == "12M"

    def test_interval_names(self):
        """Test that all intervals have correct names."""
        assert Interval.in_1_minute.name == "in_1_minute"
        assert Interval.in_daily.name == "in_daily"
        assert Interval.in_yearly.name == "in_yearly"

    def test_interval_count(self):
        """Test that we have all expected intervals."""
        intervals = list(Interval)
        assert len(intervals) == 16

    def test_interval_access_by_value(self):
        """Test accessing intervals by value."""
        assert Interval("1") == Interval.in_1_minute
        assert Interval("1D") == Interval.in_daily
        assert Interval("12M") == Interval.in_yearly

    def test_interval_iteration(self):
        """Test iterating over intervals."""
        all_intervals = [i for i in Interval]
        assert Interval.in_1_minute in all_intervals
        assert Interval.in_yearly in all_intervals
        assert len(all_intervals) == 16
