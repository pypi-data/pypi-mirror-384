import numpy as np
import pandas as pd
import pytest

from theforecastingcompany import TFCClient
from theforecastingcompany.utils import TFCModels


def generate_fake_timeseries(start_date, end_date, seed=None):
    """
    Generate a fake daily time series between start_date and end_date.

    Parameters:
        start_date (str): Start date in 'YYYY-MM-DD' format.
        end_date (str): End date in 'YYYY-MM-DD' format.
        seed (int, optional): Random seed for reproducibility.

    Returns:
        pd.DataFrame: DataFrame with columns 'date' and 'value'.
    """
    if seed is not None:
        np.random.seed(seed)

    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    values = np.random.normal(loc=0, scale=1, size=len(dates)).cumsum()

    df = pd.DataFrame({"ds": dates, "target": values})
    return df


@pytest.fixture
def train_df(request):
    same_end_date: bool = request.param
    df1 = generate_fake_timeseries("2023-11-01", "2023-12-19").assign(unique_id="series_1", static1="A", static2="X")
    df2 = generate_fake_timeseries("2023-12-02", "2023-12-19" if same_end_date else "2023-12-20").assign(
        unique_id="series_2", static1="B", static2="X"
    )
    return pd.concat([df1, df2], ignore_index=True)


@pytest.fixture
def future_df():
    df1 = generate_fake_timeseries("2024-01-01", "2024-01-12").assign(unique_id="series_1", static1="A", static2="X")
    df2 = generate_fake_timeseries("2024-01-06", "2024-01-17").assign(unique_id="series_2", static1="B", static2="X")
    return pd.concat([df1, df2], ignore_index=True)


@pytest.fixture
def future_df_new_products(future_df):
    return future_df.assign(unique_id=lambda df: df["unique_id"].map({"series_1": "series_3", "series_2": "series_4"}))


@pytest.mark.parametrize("train_df", [True], indirect=True)
def test_forecast_wrong_future_df(train_df, future_df):
    # This generates error cause there are gaps in the tie series being forecasted.
    client = TFCClient(api_key="test")
    with pytest.raises(ValueError, match="Missing unique_id x ds combinations in future_df"):
        client.forecast(
            train_df,
            model=TFCModels.TFCGlobal,
            horizon=12,
            freq="D",
            static_variables=["unique_id", "static1", "static2"],
            add_holidays=True,
            add_events=True,
            country_isocode="US",
            future_df=future_df,
        )

    with pytest.raises(ValueError, match="Missing unique_id x ds combinations in future_df"):
        # Same test as above, but without static_variables.
        client.forecast(
            train_df,
            model=TFCModels.TFCGlobal,
            horizon=12,
            freq="D",
            add_holidays=True,
            add_events=True,
            country_isocode="US",
            future_df=future_df,
        )


@pytest.mark.parametrize("train_df", [True], indirect=True)
def test_forecast_new_products(train_df, future_df_new_products):
    client = TFCClient(api_key="test")
    with pytest.raises(ValueError, match="Some items in future_df are not in train_df"):
        client.forecast(
            train_df,
            model=TFCModels.TabPFN_TS,
            horizon=12,
            freq="D",
            static_variables=["unique_id", "static1", "static2"],
            add_holidays=True,
            add_events=True,
            country_isocode="US",
            future_df=future_df_new_products,
        )
