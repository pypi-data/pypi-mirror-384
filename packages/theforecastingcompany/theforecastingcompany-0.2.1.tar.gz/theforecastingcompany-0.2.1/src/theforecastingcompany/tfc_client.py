import os
from typing import Literal, Optional

import pandas as pd

from .utils import ModelConfig, TFCModels, cross_validate_models


class TFCClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        max_concurrent: int = 200,
        max_tries: int = 5,
        cloud: Literal["aws", "gcp", "oci"] | None = None,
    ):
        self.base_url = base_url
        self.api_key = api_key if api_key else os.getenv("TFC_API_KEY", None)
        self.max_concurrent = max_concurrent
        self.max_tries = max_tries
        if cloud is not None and cloud not in ["aws", "gcp", "oci"]:
            raise ValueError(f"Invalid cloud provider '{cloud}'. Must be one of: aws, gcp, oci")
        self.cloud = cloud

        if self.api_key is None:
            raise ValueError("No API key provided")

    def _validate_inputs(
        self,
        train_df: pd.DataFrame,
        future_df: pd.DataFrame | None,
        future_variables: list[str],
        static_variables: list[str],
        hist_variables: list[str],
        id_col: str,
        model: TFCModels,
    ) -> None:
        if any(not isinstance(arg, list) for arg in [future_variables, static_variables, hist_variables]):
            raise ValueError("Future, static and historical variables should be lists of columns names.")

        if future_df is not None:
            # TODO: Add checks in TFCModels to make sure only supported variables are provided.
            # TODO: static variables don't need to be stored in the future_df, unless I want to predict new items (in which case at leats the mapping should be provided).
            if not all(col in future_df.columns for col in future_variables):
                raise ValueError("All future variables must be present in future_df")
            static_in_future = [col for col in static_variables if col in future_df.columns if col != id_col]
            # If not static feature is in future_df: I will predict for all items in train_df
            # If I have ALL static features in future_df, I will only predict for the items in there.
            if len(static_in_future) > 0 and not all(col in future_df.columns for col in static_variables):
                raise ValueError(
                    "Some static variables are not in future_df. Either provide all static_variables (necessary if there are new items) or None (These will be added automatically). Missing static variables in future_df:",
                    [col for col in static_variables if col not in future_df.columns],
                )

            future_items = set(future_df[id_col])
            train_items = set(train_df[id_col])
            new_items = future_items.difference(train_items)
            # Check if new items are in future_df
            if new_items and model != TFCModels.TFCGlobal:
                raise ValueError(
                    f"Some items in future_df are not in train_df. Only {TFCModels.TFCGlobal} can handle new items."
                )

            if train_items.difference(future_items) and model != TFCModels.TFCGlobal:
                raise ValueError(
                    f"Some items in train_df are not in future_df. Remove these items from training if you do not want their forecast. Only {TFCModels.TFCGlobal} can have only_as_context items."
                )

            future_variables = future_variables or []
            if new_items and not all(col in future_df.columns for col in static_variables):
                raise ValueError(
                    "New items detected in future_df. All static variables columns should be provided in future_df."
                )

        # TODO: Add support for static variables (not yet supported by TFC) and historical variables (need to populate them in send_async_requests).
        if len(set(future_variables)) != len(future_variables):
            raise ValueError("Future variables contain duplicates")
        if len(set(static_variables)) != len(static_variables):
            raise ValueError("Static variables contain duplicates")
        if len(set(hist_variables)) != len(hist_variables):
            raise ValueError("Historical variables contain duplicates")
        if len(set(future_variables + static_variables + hist_variables)) != len(
            future_variables + static_variables + hist_variables
        ):
            raise ValueError("Future, static and historical variables contain duplicates")
        if future_df is None and future_variables:
            raise ValueError("Future variables provided but no future_df provided")

    @staticmethod
    def _get_freq(train_df: pd.DataFrame, freq: str, date_col: str) -> str:
        myfreq = "7D" if freq == "W" else freq
        if myfreq == "M":
            if train_df[date_col].dt.day.max() < 28:
                myfreq = "MS"
            else:
                myfreq = "ME"

        return myfreq

    def make_future_df(
        self,
        train_df: pd.DataFrame,
        future_df: pd.DataFrame | None,
        freq: str,
        horizon: int,
        id_col: str = "unique_id",
        date_col: str = "ds",
    ) -> pd.DataFrame:
        """Helper function to generate the expected dates per time series. The output is a dataframe where dates are computed as follows:
        - $horizon dates following the last training one
        - for new products, these should be $horizon consecutive dates following the first date in future_df.

        Args:
            train_df (pd.DataFrame): Dataframe with historical target and features' values.
            freq (str): Frequency Alias of the time series, e.g., H, D, W, M, Q, Y.
            horizon (int): Number of steps to forecast.
            future_df (pd.DataFrame | None, optional): Dataframe with future target and features' values. Defaults to None.
            id_col (str, optional): Column name in train_df and future_df containing the unique identifier of each time series. Defaults to "unique_id".
            date_col (str, optional): Column name in train_df and future_df containing the date of each time series. Defaults to "ds".

        Returns:
            pd.DataFrame: Dataframe with all unique_id to be forecasted, corresponding static features and future_variables.
        """
        # TODO: make sure this is not too slow
        start_fc_dict: dict[str, pd.Timestamp] = train_df.groupby(id_col)[date_col].max().to_dict()
        myfreq = self._get_freq(train_df, freq, date_col)
        # Start forecasting from following period.
        start_fc_dict = {key: date + pd.tseries.frequencies.to_offset(myfreq) for key, date in start_fc_dict.items()}

        if future_df is not None:
            new_items = set(future_df[id_col].unique()) - set(start_fc_dict.keys())
            if new_items:
                first_dates_dict = future_df.query(f"{id_col} in @new_items").groupby(id_col)[date_col].min().to_dict()
                start_fc_dict = start_fc_dict | first_dates_dict

        # For each idx in last_date_df
        dfs = [
            pd.DataFrame(
                {
                    date_col: pd.date_range(start=last_date, periods=horizon, freq=myfreq),
                }
            ).assign(**{id_col: idx})
            for idx, last_date in start_fc_dict.items()
        ]
        myfuture_df = pd.concat(dfs, ignore_index=True, axis=0)

        if future_df is None:
            return myfuture_df

        # Keep only unique_ids in future_df
        return myfuture_df.merge(future_df[[id_col]].drop_duplicates(), on=id_col, how="inner")

    def _validate_future_df(
        self,
        train_df: pd.DataFrame,
        future_df: pd.DataFrame | None,
        freq: str,
        horizon: int,
        id_col: str = "unique_id",
        date_col: str = "ds",
        future_variables: list[str] | None = None,
        static_variables: list[str] | None = None,
    ) -> pd.DataFrame:
        """Check all expected dates are in future_df. Add static variables if needed.

        Args:
            train_df (pd.DataFrame): Dataframe with historical target and features' values.
            freq (str): Frequency Alias of the time series, e.g., H, D, W, M, Q, Y.
            horizon (int): Number of steps to forecast.
            future_df (pd.DataFrame | None, optional): Dataframe with future target and features' values. Defaults to None.
            id_col (str, optional): Column name in train_df and future_df containing the unique identifier of each time series. Defaults to "unique_id".
            date_col (str, optional): Column name in train_df and future_df containing the date of each time series. Defaults to "ds".
            future_variables (list[str], optional): Future variables to be used by the model. Defaults to []. If future_variables are provided,
            this method is used to add the static variables to the future_df, if not already present.
            static_variables (list[str], optional): Static variables to be used by the model. Defaults to [].
        """
        if static_variables is None:
            static_variables = []
        if future_variables is None:
            future_variables = []

        myfuture_df = self.make_future_df(train_df, future_df, freq, horizon, id_col, date_col)
        if future_df is None:
            future_df = myfuture_df
        else:
            # Test all expected dates per id_col are in future_df
            myfuture_df = myfuture_df[[id_col, date_col]].merge(
                future_df[[id_col, date_col]], on=[id_col, date_col], how="left", indicator=True
            )
            if not (myfuture_df["_merge"] == "both").all():
                raise ValueError(
                    f"Missing {id_col} x {date_col} combinations in future_df. Use TFCClient.make_future_df() to generate expected {date_col} per {id_col}"
                )

        # Add static variables if not already in future_df. This cannot happen I there are new products, as I make the check in validate_inputs().
        static_feat_cols = [id_col] + [col for col in static_variables if col != id_col]
        static_feat_df = train_df[static_feat_cols].drop_duplicates(keep="last")
        if len(static_feat_cols) > 1 and not all(col in future_df.columns for col in static_feat_cols):
            future_df = future_df.merge(static_feat_df, on=id_col, how="left")

        return future_df

    def forecast(
        self,
        train_df: pd.DataFrame,
        model: TFCModels,
        horizon: int,
        freq: str,
        add_holidays: bool = False,
        add_events: bool = False,
        country_isocode: str | None = None,
        future_df: pd.DataFrame | None = None,
        future_variables: list[str] | None = None,
        historical_variables: list[str] | None = None,
        static_variables: list[str] | None = None,
        quantiles: list[float] | None = None,
        id_col: str = "unique_id",
        date_col: str = "ds",
        target_col: str = "target",
        partition_by: list[str] | None = None,
    ) -> pd.DataFrame:
        """Given a context dataframe train_df, compute forecast over the specified horizon.

        Args:
            train_df (pd.DataFrame): Context dataframe, containing history for all time series to be predicted.
            model (TFCModels): Model to be used for forecasting. See https://api.retrocast.com/docs/routes/index for a list of model
            identifiers. You can also use the tfc_client.utils.TFCModels enum.
            horizon (int): Number of steps to forecast.
            freq (str): Frequency Alias of the time series, e.g., H, D, W, M, Q, Y.
            add_holidays (bool, optional): Whether to include TFC-holidays as features. Defaults to False.
            add_events (bool, optional): Whether to include TFC-events as features. Defaults to False.
            country_isocode (str | None, optional): ISO (eg, US, GB,..) code of the country for which the forecast is requested. This is used for fetching the right
            holidays and events. Defaults to None.
            future_df (pd.DataFrame | None, optional): Future dataframe. Defaults to None. Should contain all the future_variables needed to forecast.
            future_variables (list[str] | None, optional): Future variables to be used by the model. Defaults to None.
            historical_variables (list[str] | None, optional): Historical variables to be used by the model. Defaults to None.
            static_variables (list[str] | None, optional): Static variables to be used by the model. Defaults to None.
            id_col (str, optional): Column name in train_df and future_df containing the unique identifier of each time series. Defaults to "unique_id".
            date_col (str, optional): Column name in train_df and future_df containing the date of each time series. Defaults to "ds".
            target_col (str, optional): Column name in train_df containing the target of each time series. Defaults to "target".
            partition_by (list[str] | None, optional): List of columns to partition the train_df by. Defaults to None (No partitioning). Note: Only global models support partitioning.
        Returns:
            pd.DataFrame: Forecast dataframe, containing the forecast for all time series.
        """
        # TODO: Find better fix.
        if future_variables is None:
            future_variables = []
        if static_variables is None:
            static_variables = []
        if historical_variables is None:
            historical_variables = []
        self._validate_inputs(
            train_df,
            future_df,
            future_variables,
            static_variables,
            historical_variables,
            id_col=id_col,
            model=model,
        )
        new_items = None
        fcds = []
        if future_df is not None or static_variables:
            # Add static variables if necessary
            # Build future_df is this is None
            future_df = self._validate_future_df(
                train_df,
                future_df,
                freq,
                horizon,
                id_col,
                date_col,
                future_variables,
                static_variables,
            )
            # Fill Targets and Historical variables with 0 for the future. These values won't be used thanks to te FCD index.
            future_df = pd.DataFrame(
                future_df.assign(**{col: 0 for col in train_df.columns if col not in future_df.columns})[
                    train_df.columns
                ]  # Make sure to have the same column order
            )
            full_df = pd.concat([train_df, future_df], axis=0)
            new_items = set(future_df[id_col]) - set(train_df[id_col])
            fcds = future_df.groupby(id_col)[date_col].min().to_dict()
        else:
            assert len(future_variables) == 0, "Future variables provided but no future_df provided."
            full_df = train_df

        return cross_validate_models(
            full_df,
            fcds,
            models=[
                ModelConfig(
                    model=model,
                    add_holidays=add_holidays,
                    add_events=add_events,
                    country_isocode=country_isocode,
                    future_variables=future_variables,
                    historical_variables=historical_variables,
                    static_variables=static_variables,
                )
            ],
            horizon=horizon,
            freq=freq,
            max_concurrent=self.max_concurrent,
            max_retries=self.max_tries,
            api_key=self.api_key,
            url=self.base_url,
            id_col=id_col,
            date_col=date_col,
            target_col=target_col,
            new_ids=new_items,
            cloud=self.cloud,
            quantiles=quantiles,
            partition_by=partition_by,
        )

    def cross_validate(
        self,
        train_df: pd.DataFrame,
        model: TFCModels,
        horizon: int,
        freq: str,
        fcds: list[pd.Timestamp],
        add_holidays: bool = False,
        add_events: bool = False,
        country_isocode: str | None = None,
        future_variables: list[str] | None = None,
        historical_variables: list[str] | None = None,
        static_variables: list[str] | None = None,
        quantiles: list[float] | None = None,
        id_col: str = "unique_id",
        date_col: str = "ds",
        target_col: str = "target",
        partition_by: list[str] | None = None,
    ) -> pd.DataFrame:
        """Given a context dataframe train_df, compute forecast over the specified horizon.

        Args:
            train_df (pd.DataFrame): Context dataframe, containing history for all time series to be predicted.
            model (TFCModels): Model to be used for forecasting. See https://api.retrocast.com/docs/routes/index for a list of model
            identifiers. You can also use the tfc_client.utils.TFCModels enum.
            horizon (int): Number of steps to forecast.
            freq (str): Frequency Alias of the time series, e.g., H, D, W, M, Q, Y.
            fcds (list[pd.Timestamp]): Forecast creation dates, ie, cutoff dates to determine the crossvalidation splits.
            add_holidays (bool, optional): Whether to include TFC-holidays as features. Defaults to False.
            add_events (bool, optional): Whether to include TFC-events as features. Defaults to False.
            country_isocode (str | None, optional): ISO (eg, US, GB,..) code of the country for which the forecast is requested. This is used for fetching the right
            holidays and events. Defaults to None.
            future_variables (list[str] | None, optional): Future variables to be used by the model. Defaults to None.
            historical_variables (list[str] | None, optional): Historical variables to be used by the model. Defaults to None.
            static_variables (list[str] | None, optional): Static variables to be used by the model. Defaults to None.
            id_col (str, optional): Column name in train_df and future_df containing the unique identifier of each time series. Defaults to "unique_id".
            date_col (str, optional): Column name in train_df and future_df containing the date of each time series. Defaults to "ds".
            target_col (str, optional): Column name in train_df containing the target of each time series. Defaults to "target".
            partition_by (list[str] | None, optional): List of columns to partition the train_df by. Defaults to None (No partitioning). Note: Only global models support partitioning.
        Returns:
            pd.DataFrame: Forecast dataframe, containing the forecast for all time series.
        """
        fcds = sorted({pd.Timestamp(fcd) for fcd in fcds})
        if not fcds:
            raise ValueError("No valid cutoff dates provided.")
        offset = pd.tseries.frequencies.to_offset(self._get_freq(train_df, freq, date_col))
        last_test_dt = fcds[-1] + offset * (horizon - 1)
        start_dt_dict: dict[str, pd.Timestamp] = train_df.groupby(id_col)[date_col].min().to_dict()
        end_dt_dict: dict[str, pd.Timestamp] = train_df.groupby(id_col)[date_col].max().to_dict()
        # make sure all items have enough data to go over the entire testing horizon, otherwise remove these items.
        items_too_recent = [
            item for item, start_dt in start_dt_dict.items() if start_dt > fcds[0]
        ]  # this excludes new items.
        items_too_old = [item for item, end_dt in end_dt_dict.items() if end_dt < last_test_dt]
        if len(items_too_recent) > 0:
            raise ValueError(
                f"Some items' first date is after the first cutoff date. Remove these items: {items_too_recent[:10]}..."
            )
        if len(items_too_old) > 0:
            raise ValueError(
                f"Some items' last date is before the last test date {last_test_dt}. Remove these items: {items_too_old[:10]}..."
            )

        # this can be relaxed in the future for the global model, automatically detecting only_as_contexct and new items for each test window.
        cvdf = cross_validate_models(
            train_df,
            fcds,
            models=[
                ModelConfig(
                    model=model,
                    add_holidays=add_holidays,
                    add_events=add_events,
                    country_isocode=country_isocode,
                    future_variables=future_variables,
                    historical_variables=historical_variables,
                    static_variables=static_variables,
                )
            ],
            horizon=horizon,
            freq=freq,
            max_concurrent=self.max_concurrent,
            max_retries=self.max_tries,
            api_key=self.api_key,
            url=self.base_url,
            id_col=id_col,
            date_col=date_col,
            target_col=target_col,
            new_ids=None,
            cloud=self.cloud,
            quantiles=quantiles,
            partition_by=partition_by,
        )

        # The merge below, needed to add the actual target values, does not work and raises the error when running chronos and timesfm on weekly data, cause those models output the wrong dates and the merge fails.
        # TODO: compute the cutoff dates automatically, to make sure they're all within the train_df.
        # cvdf = cvdf.merge(train_df[[id_col, date_col, target_col]], on=[id_col, date_col], how="left")
        # if cvdf[target_col].isna().any():
        #     raise ValueError("Some target values are missing in the training data")
        return cvdf
