import dask.dataframe as dd
import datetime
import pandas as pd
from typing import Optional
from sibi_dst.utils import Logger
from sibi_dst.utils.dask_utils import dask_is_empty

today = datetime.date.today()
yesterday = today - datetime.timedelta(days=1)
TODAY_STR = today.strftime('%Y-%m-%d')
YESTERDAY_STR = yesterday.strftime('%Y-%m-%d')


class HybridDataLoader:
    """
    A generic data loader that orchestrates loading from a historical
    source and an optional live source.
    """

    def __init__(self, start_date: str, end_date: str, historical_reader, live_reader, date_field: str, **kwargs):
        self.start_date = self._validate_date_format(start_date)
        self.end_date = self._validate_date_format(end_date)
        self.historical_reader = historical_reader
        self.live_reader = live_reader
        self.date_field = date_field

        self.logger = kwargs.get('logger', Logger.default_logger(logger_name=__name__))
        self.debug = kwargs.get('debug', False)
        self.logger.set_level(Logger.DEBUG if self.debug else Logger.INFO)

        # Validate date range
        self._validate_date_range()

        # Determine loading strategy
        self._should_read_live = self.end_date == TODAY_STR
        self._is_single_today = (self.start_date == TODAY_STR and self.end_date == TODAY_STR)
        self._is_single_historical = (self.start_date == self.end_date and self.end_date != TODAY_STR)

    def _validate_date_format(self, date_str: str) -> str:
        """Validate that date string is in correct format."""
        try:
            datetime.datetime.strptime(date_str, '%Y-%m-%d')
            return date_str
        except ValueError:
            raise ValueError(f"Date '{date_str}' is not in valid YYYY-MM-DD format")

    def _validate_date_range(self):
        """Validate that start date is not after end date."""
        start = datetime.datetime.strptime(self.start_date, '%Y-%m-%d').date()
        end = datetime.datetime.strptime(self.end_date, '%Y-%m-%d').date()
        if end < start:
            raise ValueError(f"End date ({self.end_date}) cannot be before start date ({self.start_date})")

    def _align_schema_to_live(self, historical_df: dd.DataFrame, live_df: dd.DataFrame) -> dd.DataFrame:
        """Forces the historical dataframe schema to match the live one."""
        self.logger.debug("Aligning historical schema to match live schema.")
        historical_cols = set(historical_df.columns)
        live_cols = set(live_df.columns)

        # Add missing columns to historical dataframe
        for col in live_cols - historical_cols:
            historical_df[col] = None

        # Reorder columns to match live dataframe
        return historical_df[list(live_df.columns)]

    def _create_empty_dataframe(self) -> dd.DataFrame:
        """Create an empty dask dataframe with proper structure."""
        return dd.from_pandas(pd.DataFrame(), npartitions=1)

    async def _load_today_data(self, **kwargs) -> Optional[dd.DataFrame]:
        """Load today's data from the live reader."""
        self.logger.debug(f"Loading today's live data...")
        date_filter = {f"{self.date_field}__date": TODAY_STR}
        filters = {**kwargs, **date_filter}

        try:
            today_df = await self.live_reader(
                logger=self.logger,
                debug=self.debug
            ).aload(**filters)
            return today_df
        except Exception as e:
            self.logger.error(f"Failed to load today's data: {e}")
            if not self.debug:
                return None
            raise

    async def _load_historical_data(self, start_date: str, end_date: str, **kwargs) -> dd.DataFrame:
        """Load historical data from the historical reader."""
        self.logger.debug(f"Loading historical data from {start_date} to {end_date}...")

        try:
            return await self.historical_reader(
                parquet_start_date=start_date,
                parquet_end_date=end_date,
                logger=self.logger,
                debug=self.debug
            ).aload(**kwargs)
        except Exception as e:
            self.logger.error(f"Failed to load historical data from {start_date} to {end_date}: {e}")
            if not self.debug:
                return self._create_empty_dataframe()
            raise

    async def aload(self, **kwargs) -> dd.DataFrame:
        """
        Loads data from the historical source and, if required, the live source,
        then concatenates them.
        """
        # Case 1: Only today's data requested
        if self._is_single_today:
            today_df = await self._load_today_data(**kwargs)
            return today_df if today_df is not None else self._create_empty_dataframe()

        # Case 2: Pure historical data (end date is not today)
        if not self._should_read_live:
            return await self._load_historical_data(self.start_date, self.end_date, **kwargs)

        # Case 3: Mixed historical + live scenario (end date is today)
        # Load historical data up to yesterday
        historical_df = await self._load_historical_data(self.start_date, YESTERDAY_STR, **kwargs)

        # Load today's data
        today_df = await self._load_today_data(**kwargs)

        # Combine dataframes
        if today_df is not None and not dask_is_empty(today_df):
            # Align schemas if needed
            if len(historical_df.columns) > 0 and len(today_df.columns) > 0:
                try:
                    historical_df = self._align_schema_to_live(historical_df, today_df)
                except Exception as e:
                    self.logger.warning(f"Failed to align schemas: {e}")

            return dd.concat([historical_df, today_df], ignore_index=True)
        else:
            return historical_df

    def __repr__(self):
        return (f"HybridDataLoader(start_date='{self.start_date}', "
                f"end_date='{self.end_date}', "
                f"loading_live={self._should_read_live})")

