from sibi_dst.df_helper import ParquetReader

class BaseParquetReader(ParquetReader):
    """
    Base class for Parquet readers that merges configuration parameters and handles
    debug and logger initialization.
    """
    config = {
        'backend': 'parquet'
    }
    def __init__(self, parquet_start_date, parquet_end_date, **kwargs):
        # Merge the class-level config with any additional keyword arguments,
        # and include debug and logger.
        kwargs = {**self.config,**kwargs}
        super().__init__(
            parquet_start_date=parquet_start_date,
            parquet_end_date=parquet_end_date,
            **kwargs
        )

__all__ = ['BaseParquetReader']