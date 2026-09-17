"""
Unit Tests for Agricultural Time-Series Dataset Construction and Sufficiency Gating.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

from datetime import date, timedelta

from ml.forecasting.dataset import TimeSeriesDataset


def test_dataset_chronological_sorting() -> None:
    """Verifies that unsorted input records are strictly sorted ascending by date."""
    records = [
        {"record_date": "2024-09-12", "normalized_modal_price": 28.5},
        {"record_date": "2024-09-10", "normalized_modal_price": 27.0},
        {"record_date": "2024-09-11", "normalized_modal_price": 27.8},
    ]

    dataset = TimeSeriesDataset.from_records(records, "tomato", "mandi_ch_49")
    assert dataset.dates == ["2024-09-10", "2024-09-11", "2024-09-12"]
    assert dataset.prices == [27.0, 27.8, 28.5]
    assert dataset.origin_date == "2024-09-12"


def test_dataset_deterministic_deduplication() -> None:
    """Verifies that multiple records on the same date are averaged without silent overwrite."""
    records = [
        {"record_date": "2024-09-10", "normalized_modal_price": 26.0, "arrival_tonnes": 10.0},
        {"record_date": "2024-09-10", "normalized_modal_price": 30.0, "arrival_tonnes": 15.0},
        {"record_date": "2024-09-11", "normalized_modal_price": 28.0, "arrival_tonnes": 20.0},
    ]

    dataset = TimeSeriesDataset.from_records(records, "tomato", "mandi_ch_49")
    assert len(dataset.dates) == 2
    assert dataset.dates == ["2024-09-10", "2024-09-11"]
    assert dataset.prices == [28.0, 28.0]
    assert dataset.arrivals == [25.0, 20.0]


def test_data_sufficiency_gating() -> None:
    """Verifies that fewer than 30 observations fails sufficiency check."""
    start = date(2024, 8, 1)
    short_records = [
        {"record_date": (start + timedelta(days=i)).isoformat(), "normalized_modal_price": 25.0 + i * 0.1}
        for i in range(25)
    ]
    sufficient_records = [
        {"record_date": (start + timedelta(days=i)).isoformat(), "normalized_modal_price": 25.0 + i * 0.1}
        for i in range(35)
    ]

    short_ds = TimeSeriesDataset.from_records(short_records, "tomato", "mandi_ch_49")
    is_suff_short, count_short, msg_short = short_ds.check_sufficiency(min_observations=30)
    assert not is_suff_short
    assert count_short == 25
    assert "minimum 30 required" in msg_short

    suff_ds = TimeSeriesDataset.from_records(sufficient_records, "tomato", "mandi_ch_49")
    is_suff_ok, count_ok, _ = suff_ds.check_sufficiency(min_observations=30)
    assert is_suff_ok
    assert count_ok == 35


def test_calendar_gap_detection_zero_silent_interpolation() -> None:
    """Verifies that date gaps are audited as DateGap entries rather than silently interpolated."""
    records = [
        # Friday trading session
        {"record_date": "2024-09-06", "normalized_modal_price": 28.0},
        # Monday trading session (expected weekend gap)
        {"record_date": "2024-09-09", "normalized_modal_price": 28.5},
        # Wednesday trading session (unexpected gap: Tuesday missing)
        {"record_date": "2024-09-11", "normalized_modal_price": 29.0},
    ]

    dataset = TimeSeriesDataset.from_records(records, "tomato", "mandi_ch_49")
    assert len(dataset.gaps) == 2

    # Weekend gap
    assert dataset.gaps[0].start_date == "2024-09-06"
    assert dataset.gaps[0].end_date == "2024-09-09"
    assert dataset.gaps[0].calendar_days_missing == 2
    assert dataset.gaps[0].gap_type == "EXPECTED_CALENDAR_GAP"

    # Midweek unexpected reporting gap
    assert dataset.gaps[1].start_date == "2024-09-09"
    assert dataset.gaps[1].end_date == "2024-09-11"
    assert dataset.gaps[1].calendar_days_missing == 1
    assert dataset.gaps[1].gap_type == "UNEXPECTED_REPORTING_GAP"
