"""Integration tests for the TFC SDK.

These tests verify end-to-end functionality of the SDK against the API.
They require a valid TFC_API_KEY environment variable to run.
"""

import datetime as dt

import numpy as np
import pandas as pd
import pytest

from theforecastingcompany import TFCClient
from theforecastingcompany.utils import TFCModels


def fake_data(seed: int = 42) -> pd.DataFrame:
    """Generate fake time series data for testing.

    Creates a year of daily data with trend, seasonality, and noise.
    """
    np.random.seed(seed)
    n_points = 365  # One year of daily data
    dates = pd.date_range("2023-01-01", periods=n_points, freq="D")

    # Create sinusoidal pattern with trend and noise
    time_idx = np.arange(n_points)
    trend = 0.01 * time_idx  # Small upward trend
    seasonal = 10 * np.sin(2 * np.pi * time_idx / 365.25)  # Annual seasonality
    noise = np.random.normal(0, 2, n_points)  # Random noise

    # Combine components
    values = 50 + trend + seasonal + noise

    # Create DataFrame
    ts_data = pd.DataFrame({"date": dates, "value": values})
    return ts_data


@pytest.fixture
def ts_data():
    """Generate fake time series data."""
    return fake_data()


@pytest.fixture
def train_data(ts_data):
    """Get training data (before 2023-11-01)."""
    return ts_data.query("date < '2023-11-01'").copy()


@pytest.fixture
def test_data(ts_data):
    """Get test data (from 2023-11-01 onwards)."""
    return ts_data.query("date >= '2023-11-01'").copy()


class TestCrossValidate:
    """Tests for the cross_validate method."""

    def test_cross_validate_basic(self, ts_data):
        """Test basic cross-validation functionality."""
        client = TFCClient(max_concurrent=2)

        res = client.cross_validate(
            ts_data.assign(unique_id="unique_id"),
            model=TFCModels.TimesFM_2,
            horizon=60,
            freq="D",
            fcds=[dt.date(2023, 7, 1), dt.date(2023, 11, 1)],
            date_col="date",
            target_col="value",
            quantiles=[0.4, 0.8],
        )

        # Verify forecast cutoff dates are present (converted to datetime)
        assert dt.datetime(2023, 7, 1) in res["fcd"].unique()
        assert dt.datetime(2023, 11, 1) in res["fcd"].unique()

        # Verify expected columns exist
        assert "timesfm-2" in res.columns
        assert "date" in res.columns
        assert "unique_id" in res.columns
        assert "fcd" in res.columns
        assert "timesfm-2_q0.4" in res.columns
        assert "timesfm-2_q0.8" in res.columns
        assert "timesfm-2_q0.5" in res.columns


class TestForecast:
    """Tests for the forecast method."""

    def test_forecast_basic(self, train_data):
        """Test basic forecast functionality."""
        client = TFCClient(max_concurrent=2)

        res = client.forecast(
            train_data.assign(unique_id="unique_id"),
            model=TFCModels.TimesFM_2,
            horizon=365,
            freq="D",
            date_col="date",
            target_col="value",
            quantiles=[0.4, 0.8],
        )

        # Verify expected columns exist
        assert "timesfm-2" in res.columns
        assert "date" in res.columns
        assert "unique_id" in res.columns
        assert "fcd" in res.columns
        assert "timesfm-2_q0.4" in res.columns
        assert "timesfm-2_q0.8" in res.columns
        assert "timesfm-2_q0.5" in res.columns

        # Verify we get the expected number of forecast points
        assert len(res) == 365

    def test_forecast_tabpfn(self, train_data):
        """Test forecast with TabPFN model."""
        client = TFCClient()

        res = client.forecast(
            train_data.assign(unique_id="unique_id"),
            model=TFCModels.TabPFN_TS,
            horizon=365,
            freq="D",
            date_col="date",
            target_col="value",
        )

        # Verify expected columns exist
        assert "tabpfn-ts" in res.columns
        assert len(res) == 365

    def test_forecast_with_holidays(self, train_data):
        """Test forecast with holiday features."""
        client = TFCClient()

        res = client.forecast(
            train_data.assign(unique_id="unique_id"),
            model=TFCModels.TabPFN_TS,
            horizon=365,
            freq="D",
            date_col="date",
            target_col="value",
            add_holidays=True,
            country_isocode="FR",
        )

        # Verify we got results
        assert "tabpfn-ts" in res.columns
        assert len(res) == 365

    def test_forecast_with_future_variables(self, train_data, test_data):
        """Test forecast with future variables."""
        client = TFCClient()

        # Add dummy future variable
        train_with_var = train_data.assign(
            unique_id="unique_id", is_Christmas=np.random.choice([0, 1], size=len(train_data))
        )
        future_with_var = test_data.assign(
            unique_id="unique_id", is_Christmas=np.random.choice([0, 1], size=len(test_data))
        )

        res = client.forecast(
            train_with_var,
            model=TFCModels.TabPFN_TS,
            horizon=len(test_data),
            freq="D",
            date_col="date",
            target_col="value",
            future_variables=["is_Christmas"],
            future_df=future_with_var,
        )

        # Verify we got results
        assert "tabpfn-ts" in res.columns
        assert len(res) == len(test_data)


class TestCloudProviders:
    """Tests for different cloud provider options."""

    def test_forecast_aws(self, ts_data):
        """Test forecast with AWS cloud provider."""
        client = TFCClient(cloud="aws")

        res = client.forecast(
            ts_data.assign(unique_id="unique_id"),
            model=TFCModels.TimesFM_2,
            horizon=10,
            freq="D",
            date_col="date",
            target_col="value",
        )

        # Verify we got results
        assert "timesfm-2" in res.columns
        assert len(res) == 10

    @pytest.mark.skip(reason="Test requires GCP cloud access")
    def test_forecast_gcp(self, ts_data):
        """Test forecast with GCP cloud provider."""
        client = TFCClient(cloud="gcp")

        res = client.forecast(
            ts_data.assign(unique_id="unique_id"),
            model=TFCModels.TimesFM_2,
            horizon=10,
            freq="D",
            date_col="date",
            target_col="value",
        )

        # Verify we got results
        assert "timesfm-2" in res.columns
        assert len(res) == 10

    @pytest.mark.skip(reason="Test requires OCI cloud access")
    def test_forecast_oci(self, ts_data):
        """Test forecast with OCI cloud provider."""
        client = TFCClient(cloud="oci")

        res = client.forecast(
            ts_data.assign(unique_id="unique_id"),
            model=TFCModels.TimesFM_2,
            horizon=10,
            freq="D",
            date_col="date",
            target_col="value",
        )

        # Verify we got results
        assert "timesfm-2" in res.columns
        assert len(res) == 10


class TestPartitioning:
    """Tests for partition_by functionality."""

    @pytest.fixture
    def partitioned_data(self):
        """Create data with multiple partitions."""
        df = pd.concat(
            [
                fake_data().assign(partition_col="christmas", unique_id="A"),
                fake_data()[["date", "value"]].assign(partition_col="fake", unique_id="B"),
            ],
            ignore_index=True,
        )
        return df

    def test_forecast_without_partitioning(self, partitioned_data):
        """Test forecast on multiple series without partitioning."""
        client = TFCClient()

        res_timesfm = client.forecast(
            partitioned_data,
            model=TFCModels.TimesFM_2,
            horizon=10,
            freq="D",
            date_col="date",
            target_col="value",
        )

        res_tfcglobal = client.forecast(
            partitioned_data,
            model=TFCModels.TFCGlobal,
            horizon=10,
            freq="D",
            date_col="date",
            target_col="value",
            add_holidays=True,
            add_events=True,
            country_isocode="FR",
        )

        # Verify results for both unique_ids
        assert set(res_timesfm["unique_id"].unique()) == {"A", "B"}
        assert set(res_tfcglobal["unique_id"].unique()) == {"A", "B"}
        assert len(res_timesfm) == 20  # 10 forecasts per unique_id
        assert len(res_tfcglobal) == 20

    def test_forecast_with_partitioning(self, partitioned_data):
        """Test forecast with partition_by parameter."""
        client = TFCClient()

        res = client.forecast(
            partitioned_data,
            model=TFCModels.TFCGlobal,
            horizon=10,
            freq="D",
            date_col="date",
            target_col="value",
            partition_by=["partition_col"],
            add_holidays=True,
            add_events=True,
            country_isocode="FR",
        )

        # Verify results for both unique_ids
        assert set(res["unique_id"].unique()) == {"A", "B"}
        assert len(res) == 20  # 10 forecasts per unique_id
