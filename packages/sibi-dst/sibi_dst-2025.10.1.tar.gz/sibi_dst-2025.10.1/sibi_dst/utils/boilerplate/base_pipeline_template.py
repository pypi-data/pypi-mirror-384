from __future__ import annotations

import pandas as pd

from sibi_dst.utils.boilerplate import BasePipeline


class PipelineTemplate:
    """
    A reusable base class for executing product-related pipelines end-to-end.
    """

    def __init__(
        self,
        start_date: str,
        end_date: str,
        fs_instance,
        storage_path: str,
        dataset_cls,
        filename: str,
        date_field: str = "last_activity_dt",
        **kwargs
    ):
        self.start_date = start_date
        self.end_date = end_date
        self.max_workers = kwargs.pop('max_workers', 4)
        self.fs = fs_instance
        self.storage_path = storage_path

        self.pipeline = BasePipeline(
            start_date=self.start_date,
            end_date=self.end_date,
            dataset_cls=dataset_cls,
            parquet_storage_path=self.storage_path,
            fs=self.fs,
            filename=filename,
            date_field=date_field,
            max_workers=self.max_workers,
        )

    async def to_parquet(self, **kwargs) -> pd.DataFrame:
        await self.pipeline.to_parquet(**kwargs)
        df = await self.pipeline.from_parquet(**kwargs)
        return df

    async def from_parquet(self, **kwargs) -> pd.DataFrame:
        df = await self.pipeline.from_parquet(**kwargs)
        return df

    async def to_clickhouse(self, clickhouse_conf, **kwargs) -> None:
        cnf = clickhouse_conf.copy()
        cnf["table"] = self.pipeline.filename
        cnf["overwrite"] = True
        await self.pipeline.to_clickhouse(cnf, **kwargs)