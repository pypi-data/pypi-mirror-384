"""Test the core Stable functionality."""
import pytest
import numpy as np
from scipy import stats
from stable import Stable


def test_ttest():
    """Test t-test functionality."""
    result = stats.ttest_ind([1, 2, 3], [4, 5, 6])
    stable = Stable(result)
    assert stable.is_supported()
    assert "t-test" in stable.get_test_name()


def test_from_ttest():
    """Test from_ttest class method."""
    stable = Stable.from_ttest([1, 2, 3], [4, 5, 6])
    assert stable.is_supported()
    assert "t-test" in stable.get_test_name()


def test_summary():
    """Test summary method."""
    result = stats.ttest_ind([1, 2, 3], [4, 5, 6])
    stable = Stable(result)
    summary = stable.summary()
    assert isinstance(summary, str)
    assert len(summary) > 0


def test_to_markdown():
    """Test markdown export."""
    result = stats.ttest_ind([1, 2, 3], [4, 5, 6])
    stable = Stable(result)
    markdown = stable.to_markdown()
    assert isinstance(markdown, str)
    assert "|" in markdown  # Should contain table formatting
