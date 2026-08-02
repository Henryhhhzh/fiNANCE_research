from datetime import UTC, datetime, timedelta

import polars as pl
import pytest

from tr.data.hygiene import (
    HygieneError,
    assert_ohlc_consistent,
    assert_timestamps,
    find_gaps,
    flag_outliers,
    sha256_file,
    tag_sessions,
    write_manifest,
)

START = datetime(2024, 3, 15, 14, 0, tzinfo=UTC)


def _frame(n: int = 10, step_minutes: int = 1, price: float = 5000.0) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "ts": [START + timedelta(minutes=i * step_minutes) for i in range(n)],
            "open": [price] * n,
            "high": [price] * n,
            "low": [price] * n,
            "close": [price] * n,
            "volume": [100.0] * n,
        }
    ).with_columns(pl.col("ts").dt.convert_time_zone("UTC"))


def test_clean_frame_passes() -> None:
    assert_timestamps(_frame())
    assert_ohlc_consistent(_frame())


def test_naive_timestamps_are_rejected() -> None:
    df = _frame().with_columns(pl.col("ts").dt.replace_time_zone(None))
    with pytest.raises(HygieneError, match="timezone-aware"):
        assert_timestamps(df)


def test_duplicate_timestamps_are_rejected() -> None:
    df = pl.concat([_frame(3), _frame(3)]).sort("ts")
    with pytest.raises(HygieneError, match="duplicate"):
        assert_timestamps(df)


def test_unsorted_timestamps_are_rejected() -> None:
    with pytest.raises(HygieneError, match="monotonic"):
        assert_timestamps(_frame(5).reverse())


def test_impossible_ohlc_is_rejected() -> None:
    df = _frame(3).with_columns(high=pl.lit(4000.0))
    with pytest.raises(HygieneError, match="OHLC"):
        assert_ohlc_consistent(df)


def test_gaps_are_reported_not_filled() -> None:
    df = pl.concat([_frame(3), _frame(3).with_columns(pl.col("ts") + timedelta(minutes=30))])
    gaps = find_gaps(df)
    assert gaps.height == 1
    assert gaps["missing_bars"][0] == 27
    assert df.height == 6


def test_no_gaps_in_continuous_data() -> None:
    assert find_gaps(_frame(20)).height == 0


def test_outliers_are_flagged_not_removed() -> None:
    """Deleting a 30% move deletes the crash you most need to survive."""
    df = _frame(5).with_columns(close=pl.Series([5000.0, 5000.0, 6500.0, 6500.0, 6500.0]))
    flagged = flag_outliers(df)
    assert flagged.height == 5
    assert flagged["is_outlier"].sum() == 1


def test_normal_moves_are_not_flagged() -> None:
    df = _frame(5).with_columns(close=pl.Series([5000.0, 5010.0, 5020.0, 5015.0, 5030.0]))
    assert flag_outliers(df)["is_outlier"].sum() == 0


def test_session_tagging_handles_daylight_saving() -> None:
    """14:00 UTC is 10:00 in New York during EDT (RTH) but 09:00 during EST (pre-open).
    A hardcoded UTC offset gets one of these wrong for half the year."""
    summer = _frame(1)
    winter = _frame(1).with_columns(pl.col("ts") + timedelta(days=250))
    assert tag_sessions(summer)["session"][0] == "RTH"
    assert tag_sessions(winter)["session"][0] == "ETH"


def test_overnight_bars_are_tagged_eth() -> None:
    overnight = _frame(1).with_columns(pl.col("ts") + timedelta(hours=12))
    assert tag_sessions(overnight)["session"][0] == "ETH"


def test_manifest_checksums_every_file(tmp_path) -> None:
    (tmp_path / "a.parquet").write_bytes(b"alpha")
    (tmp_path / "b.parquet").write_bytes(b"beta")
    manifest = tmp_path / "MANIFEST.txt"
    assert write_manifest(tmp_path, manifest) == 2
    assert sha256_file(tmp_path / "a.parquet") in manifest.read_text()


def test_manifest_changes_when_bytes_change(tmp_path) -> None:
    target = tmp_path / "a.parquet"
    target.write_bytes(b"alpha")
    manifest = tmp_path / "MANIFEST.txt"
    write_manifest(tmp_path, manifest)
    before = manifest.read_text()
    target.write_bytes(b"alpha-modified")
    write_manifest(tmp_path, manifest)
    assert manifest.read_text() != before
