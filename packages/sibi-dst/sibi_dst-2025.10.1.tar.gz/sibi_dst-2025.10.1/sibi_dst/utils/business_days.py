from __future__ import annotations

import datetime as dt
from typing import Any, Dict, Iterable, Optional

import dask.dataframe as dd
import numpy as np
import pandas as pd

from sibi_dst.utils import Logger


# ---------------- Vectorized helpers (used by Dask map_partitions) ----------------

def _to_np_days(series: pd.Series) -> np.ndarray:
    """Coerce to numpy datetime64[D] with NaT-safe conversion."""
    s = pd.to_datetime(series, errors="coerce")
    # Return day precision array directly
    return s.dt.floor("D").to_numpy(dtype="datetime64[D]")


def _vectorized_busday_count(
        part: pd.DataFrame,
        begin_col: str,
        end_col: str,
        holidays: Iterable[str],
        weekmask: Optional[str],
        inclusive: bool,
) -> pd.Series:
    start = _to_np_days(part[begin_col])
    end = _to_np_days(part[end_col])

    kwargs: Dict[str, Any] = {}
    if holidays:
        kwargs["holidays"] = np.array(list(holidays), dtype="datetime64[D]")
    if weekmask:
        kwargs["weekmask"] = weekmask

    end_adj = end
    if inclusive:
        with np.errstate(invalid="ignore"):
            end_adj = end + np.timedelta64(1, "D")

    valid = (~pd.isna(start)) & (~pd.isna(end))
    result = np.full(part.shape[0], np.nan, dtype="float64")
    if valid.any():
        counts = np.busday_count(
            start[valid].astype("datetime64[D]"),
            end_adj[valid].astype("datetime64[D]"),
            **kwargs,
        ).astype("float64")
        result[valid] = counts

    return pd.Series(result, index=part.index)


def _vectorized_busday_offset(
        part: pd.DataFrame,
        start_col: str,
        n_days_col: str,
        holidays: Iterable[str],
        weekmask: Optional[str],
        roll: str,
) -> pd.Series:
    start = _to_np_days(part[start_col])
    n_days = pd.to_numeric(part[n_days_col], errors="coerce").to_numpy()

    kwargs: Dict[str, Any] = {"roll": roll}
    if holidays:
        kwargs["holidays"] = np.array(list(holidays), dtype="datetime64[D]")
    if weekmask:
        kwargs["weekmask"] = weekmask

    valid = (~pd.isna(start)) & (~pd.isna(n_days))
    out = np.full(part.shape[0], np.datetime64("NaT", "ns"), dtype="datetime64[ns]")
    if valid.any():
        offs = np.busday_offset(
            start[valid].astype("datetime64[D]"),
            n_days[valid].astype("int64"),
            **kwargs,
        ).astype("datetime64[ns]")
        out[valid] = offs

    return pd.Series(out, index=part.index)


# ---------------- BusinessDays ----------------

class BusinessDays:
    """
    Business day calculations with custom holidays and optional weekmask.
    """

    def __init__(
            self,
            holiday_list: Dict[str, list[str]] | Iterable[str],
            debug: bool = False,
            logger: Optional[Logger] = None,
            weekmask: Optional[str] = None,
    ) -> None:
        self.debug = debug
        self.logger = logger or Logger.default_logger(logger_name=self.__class__.__name__)
        self.weekmask = weekmask

        if isinstance(holiday_list, dict):
            flat = [d for _, days in sorted(holiday_list.items()) for d in days]
        else:
            flat = list(holiday_list)

        seen = set()
        flat_unique = []
        for d in flat:
            if d not in seen:
                seen.add(d)
                flat_unique.append(d)
        self.holidays: tuple[str, ...] = tuple(flat_unique)

    # -------- Scalar API --------

    def get_business_days_count(
            self,
            begin_date: str | dt.date | pd.Timestamp,
            end_date: str | dt.date | pd.Timestamp,
            *,
            inclusive: bool = False,
    ) -> int:
        b = pd.to_datetime(begin_date).date()
        e = pd.to_datetime(end_date).date()

        kwargs: Dict[str, Any] = {}
        if self.holidays:
            kwargs["holidays"] = np.array(self.holidays, dtype="datetime64[D]")
        if self.weekmask:
            kwargs["weekmask"] = self.weekmask

        if inclusive:
            e_np = np.datetime64(e, "D") + np.timedelta64(1, "D")
        else:
            e_np = np.datetime64(e, "D")

        val = int(np.busday_count(np.datetime64(b, "D"), e_np, **kwargs))
        return val

    def add_business_days(
            self,
            start_date: str | dt.date | pd.Timestamp,
            n_days: int,
            *,
            roll: str = "forward",
    ) -> np.datetime64:
        s = pd.to_datetime(start_date).date()
        kwargs: Dict[str, Any] = {"roll": roll}
        if self.holidays:
            kwargs["holidays"] = np.array(self.holidays, dtype="datetime64[D]")
        if self.weekmask:
            kwargs["weekmask"] = self.weekmask

        return np.busday_offset(np.datetime64(s, "D"), int(n_days), **kwargs)

    # -------- Dask API --------

    def calc_business_days_from_df(
            self,
            df: dd.DataFrame,
            begin_date_col: str,
            end_date_col: str,
            result_col: str = "business_days",
            *,
            inclusive: bool = False,
    ) -> dd.DataFrame:
        missing = {begin_date_col, end_date_col} - set(df.columns)
        if missing:
            self.logger.error(f"Missing columns: {missing}")
            raise ValueError("Required columns are missing from DataFrame")

        return df.assign(
            **{
                result_col: df.map_partitions(
                    _vectorized_busday_count,
                    begin_col=begin_date_col,
                    end_col=end_date_col,
                    holidays=self.holidays,
                    weekmask=self.weekmask,
                    inclusive=inclusive,
                    meta=(result_col, "f8"),
                )
            }
        )

    def calc_sla_end_date(
            self,
            df: dd.DataFrame,
            start_date_col: str,
            n_days_col: str,
            result_col: str = "sla_end_date",
            *,
            roll: str = "forward",
    ) -> dd.DataFrame:
        missing = {start_date_col, n_days_col} - set(df.columns)
        if missing:
            self.logger.error(f"Missing columns: {missing}")
            raise ValueError("Required columns are missing from DataFrame")

        return df.assign(
            **{
                result_col: df.map_partitions(
                    _vectorized_busday_offset,
                    start_col=start_date_col,
                    n_days_col=n_days_col,
                    holidays=self.holidays,
                    weekmask=self.weekmask,
                    roll=roll,
                    meta=(result_col, "datetime64[ns]"),
                )
            }
        )
