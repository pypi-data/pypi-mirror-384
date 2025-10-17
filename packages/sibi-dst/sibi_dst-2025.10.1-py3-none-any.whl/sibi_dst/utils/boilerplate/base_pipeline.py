from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Type, Any, Callable, List

import pandas as pd
import dask.dataframe as dd

from sibi_dst.utils import ManagedResource, ParquetSaver
from sibi_dst.df_helper import ParquetReader
from sibi_dst.utils.dask_utils import dask_is_empty


class DateRangeHelper:
    @staticmethod
    def generate_daily_ranges(start_date: str, end_date: str, date_format: str = "%Y-%m-%d") -> List[str]:
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        return [d.strftime(date_format) for d in pd.date_range(start, end, freq="D")]

    @staticmethod
    def generate_monthly_ranges(start_date: str, end_date: str, date_format: str = "%Y-%m-%d") -> List[tuple[str, str]]:
        """
        Generate (start_date, end_date) tuples for each calendar month in range.
        Always includes the first and last month, even if partial.
        """
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        ranges = []
        current = start.replace(day=1)
        while current <= end:
            month_end = (current + pd.offsets.MonthEnd(0)).normalize()
            ranges.append((
                current.strftime(date_format),
                min(month_end, end).strftime(date_format)
            ))
            current += pd.DateOffset(months=1)
        return ranges

class BasePipeline(ManagedResource):
    def __init__(
        self,
        start_date: str,
        end_date: str,
        dataset_cls: Type,
        parquet_storage_path: str,
        *,
        fs: Any,
        filename: str = "dataset",
        date_field: str = "date",
        max_workers: int = 4,
        dataset_kwargs: dict = None,
        **kwargs,
    ):
        kwargs["fs"] = fs
        super().__init__(**kwargs)

        self.start_date = start_date
        self.end_date = end_date
        self.fs = fs
        self.filename = filename
        self.date_field = date_field
        self.max_workers = max_workers
        self.storage_path = parquet_storage_path.rstrip("/")
        self.df: dd.DataFrame | None = None

        self.ds = dataset_cls(
            start_date=self.start_date,
            end_date=self.end_date,
            debug=self.debug,
            logger=self.logger,
            **(dataset_kwargs or {}),
        )

    def _get_storage_path_for_date(self, date: pd.Timestamp) -> str:
        return f"{self.storage_path}/{date.year}/{date.month:02d}/{date.day:02d}"

    def _get_output_filename(self, fmt: str = "parquet") -> str:
        return f"{self.filename}.{fmt}"

    async def aload(self, **kwargs) -> dd.DataFrame:
        await self.emit("status", message="Loading dataset...", progress=5)
        self.df = await self.ds.aload(**kwargs)
        return self.df

    async def to_parquet(self, **kwargs) -> None:
        df = await self.aload(**kwargs)
        if dask_is_empty(df):
            self.logger.warning("No data to save.")
            return

        df[self.date_field] = dd.to_datetime(df[self.date_field], errors="coerce")
        df["partition_date"] = df[self.date_field].dt.date.astype(str)

        out_path = self.storage_path.rstrip("/")
        self.logger.info("Saving dataset to %s", out_path)
        ps = ParquetSaver(
            df_result=df,
            parquet_storage_path=out_path,
            engine="pyarrow",
            fs=self.fs,
            partition_on=["partition_date"],
            write_index=False,
        )
        ps.save_to_parquet()
        await self.emit("complete", message="All partitions written.")

    async def from_parquet(self, **kwargs) -> dd.DataFrame:
        reader = ParquetReader(
            parquet_start_date=self.start_date,
            parquet_end_date=self.end_date,
            parquet_storage_path=self.storage_path,
            fs=self.fs,
            debug=self.debug,
            logger=self.logger,
        )
        return await reader.aload(**kwargs)

    async def to_clickhouse(self, clk_conf: dict, **kwargs):
        """
        Writes daily-partitioned data to ClickHouse using concurrent threads.
        """
        from sibi_dst.utils import ClickHouseWriter

        df = await self.from_parquet(**kwargs)
        if dask_is_empty(df):
            self.logger.warning("No data to write to ClickHouse.")
            return

        df[self.date_field] = dd.to_datetime(df[self.date_field], errors="coerce")
        df = df.persist()

        unique_dates = df[self.date_field].dt.date.dropna().unique().compute()
        if len(unique_dates)==0:
            self.logger.warning("No valid dates found for partitioning.")
            return

        clk_conf['table'] = self.filename
        clk = ClickHouseWriter(**clk_conf)
        loop = asyncio.get_running_loop()
        tasks = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for date in unique_dates:
                df_day = df[df[self.date_field].dt.date == date]
                if dask_is_empty(df_day):
                    self.logger.info(f"[ClickHouse] No data for {date}, skipping.")
                    continue

                self.logger.info(f"[ClickHouse] Writing {len(df_day)} rows for {date}")

                tasks.append(
                    loop.run_in_executor(executor, clk.save_to_clickhouse, df_day)
                )

            await asyncio.gather(*tasks)

        self.logger.info(f"ClickHouse write complete for {len(unique_dates)} daily partitions.")


__all__ = ["BasePipeline"]