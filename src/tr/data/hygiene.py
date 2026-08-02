"""Data hygiene rules. GOAL.md §4.2.

Every rule here is a thing that silently corrupts a backtest if it goes unchecked.
None of them raise on data being *ugly* — gaps and outliers are recorded, never
repaired. Forward-filling a gap manufactures fake tradability during an outage, and
deleting an outlier deletes the crash you most need to survive.
"""

import hashlib
from pathlib import Path

import polars as pl

REQUIRED_COLUMNS = ("ts", "open", "high", "low", "close", "volume")
EXCHANGE_TZ = "America/New_York"
RTH_OPEN_MINUTES = 9 * 60 + 30
RTH_CLOSE_MINUTES = 16 * 60
DEFAULT_OUTLIER_MOVE = 0.20


class HygieneError(Exception):
    pass


def validate_schema(df: pl.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise HygieneError(f"missing required columns: {missing}")
    dtype = df["ts"].dtype
    if not isinstance(dtype, pl.Datetime):
        raise HygieneError(f"ts must be a Datetime column, got {dtype}")
    if dtype.time_zone is None:
        raise HygieneError("ts must be timezone-aware; naive timestamps hide DST bugs")
    if dtype.time_zone != "UTC":
        raise HygieneError(f"ts must be stored in UTC, got {dtype.time_zone}")


def assert_timestamps(df: pl.DataFrame) -> None:
    validate_schema(df)
    if df.height == 0:
        raise HygieneError("empty frame")
    if df["ts"].n_unique() != df.height:
        raise HygieneError(f"{df.height - df['ts'].n_unique()} duplicate timestamps")
    if not df["ts"].is_sorted():
        raise HygieneError("timestamps are not monotonically increasing")


def assert_ohlc_consistent(df: pl.DataFrame) -> None:
    bad = df.filter(
        (pl.col("high") < pl.max_horizontal("open", "close"))
        | (pl.col("low") > pl.min_horizontal("open", "close"))
        | (pl.col("high") < pl.col("low"))
        | (pl.col("volume") < 0)
    )
    if bad.height:
        raise HygieneError(f"{bad.height} bars violate OHLC ordering or have negative volume")


def find_gaps(df: pl.DataFrame, interval_seconds: int = 60) -> pl.DataFrame:
    """Missing bars, recorded rather than filled.

    Expect large legitimate gaps: the daily CME maintenance halt, weekends, holidays.
    The log exists so you can tell those apart from a broken download.
    """
    deltas = df.select(
        gap_start=pl.col("ts"),
        gap_end=pl.col("ts").shift(-1),
        seconds=(pl.col("ts").shift(-1) - pl.col("ts")).dt.total_seconds(),
    ).drop_nulls()
    return deltas.filter(pl.col("seconds") > interval_seconds).with_columns(
        missing_bars=(pl.col("seconds") / interval_seconds - 1).cast(pl.Int64)
    )


def flag_outliers(df: pl.DataFrame, max_move: float = DEFAULT_OUTLIER_MOVE) -> pl.DataFrame:
    """Adds `is_outlier`. Never drops. A 20% one-minute move might be a bad print or
    might be the Flash Crash — you check, you don't assume."""
    return df.with_columns(
        is_outlier=(pl.col("close") / pl.col("close").shift(1) - 1).abs() > max_move
    ).with_columns(pl.col("is_outlier").fill_null(False))


def tag_sessions(df: pl.DataFrame) -> pl.DataFrame:
    """RTH vs ETH by exchange local time, so DST is handled by the calendar rather
    than by a hardcoded UTC offset that silently breaks twice a year."""
    local = pl.col("ts").dt.convert_time_zone(EXCHANGE_TZ)
    # Cast before arithmetic: dt.hour() is i8, so hour * 60 overflows for any hour
    # past 02:00 and silently wraps into a different session.
    minutes = local.dt.hour().cast(pl.Int32) * 60 + local.dt.minute().cast(pl.Int32)
    return df.with_columns(
        session=pl.when(
            (local.dt.weekday() <= 5)
            & (minutes >= RTH_OPEN_MINUTES)
            & (minutes < RTH_CLOSE_MINUTES)
        )
        .then(pl.lit("RTH"))
        .otherwise(pl.lit("ETH"))
    )


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(data_dir: Path, manifest_path: Path, pattern: str = "**/*.parquet") -> int:
    """Checksums every data file so a changed number can be traced to changed bytes."""
    entries = sorted(
        f"{sha256_file(p)}  {p.relative_to(data_dir)}"
        for p in data_dir.glob(pattern)
        if p.is_file()
    )
    manifest_path.write_text("\n".join(entries) + ("\n" if entries else ""))
    return len(entries)
