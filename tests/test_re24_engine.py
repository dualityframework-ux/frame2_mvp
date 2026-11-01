"""Regression coverage for the corrupted, previously unimported RE24 module."""
import pandas as pd
import pytest
from intelligence.re24_engine import estimate_re24_delta, summarize_re24_proxy


def test_proxy_aggregates_events_and_rounds():
    assert summarize_re24_proxy(pd.DataFrame({'events':['single','walk','strikeout',None]})) == pytest.approx(0.45)
    assert summarize_re24_proxy(pd.DataFrame()) == 0.0
    assert summarize_re24_proxy(pd.DataFrame({'other':[1]})) == 0.0


def test_delta_accounts_for_end_of_inning():
    assert estimate_re24_delta(0, 0, 1, 0) == pytest.approx(0.41)
    assert estimate_re24_delta(1, 2, 0, 3) == pytest.approx(-0.24)
