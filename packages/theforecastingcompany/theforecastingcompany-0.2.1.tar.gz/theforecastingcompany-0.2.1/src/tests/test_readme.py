"""Tests for README.md examples.

This module tests all code examples from the README.md to ensure they work correctly.
These are end-to-end tests that make actual API calls and require a valid TFC_API_KEY.
"""

import datetime as dt

import numpy as np
import pandas as pd
import pytest

from theforecastingcompany import TFCClient
from theforecastingcompany.utils import TFCModels


@pytest.fixture
def sample_train_df():
    """Create sample training data matching README examples."""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=50, freq="D")

    # Create two time series
    df1 = pd.DataFrame({"unique_id": "store_1", "ds": dates, "target": 100 + np.cumsum(np.random.randn(50) * 2)})

    df2 = pd.DataFrame({"unique_id": "store_2", "ds": dates, "target": 200 + np.cumsum(np.random.randn(50) * 3)})

    return pd.concat([df1, df2], ignore_index=True)


@pytest.fixture
def sample_train_df_with_static():
    """Create sample training data with static variables."""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=50, freq="D")

    # Create two time series with static variables
    df1 = pd.DataFrame(
        {
            "unique_id": "store_1",
            "ds": dates,
            "target": 100 + np.cumsum(np.random.randn(50) * 2),
            "Group": "A",
            "Vendor": "V1",
            "Category": "Electronics",
        }
    )

    df2 = pd.DataFrame(
        {
            "unique_id": "store_2",
            "ds": dates,
            "target": 200 + np.cumsum(np.random.randn(50) * 3),
            "Group": "B",
            "Vendor": "V2",
            "Category": "Clothing",
        }
    )

    return pd.concat([df1, df2], ignore_index=True)


class TestReadmeBasicUsage:
    """Test basic usage examples from README."""

    def test_basic_forecast_example(self, sample_train_df):
        """Test the basic forecast example from README.

        Tests this README example:
        ```python
        timesfm_df = client.forecast(
            train_df,
            model=TFCModels.TimesFM_2,
            horizon=12,
            freq="W",
            quantiles=[0.5,0.1,0.9]
        )
        ```
        """
        # Resample to weekly for the test
        train_df = (
            sample_train_df.set_index("ds").groupby("unique_id").resample("W").agg({"target": "sum"}).reset_index()
        )

        client = TFCClient()
        result = client.forecast(train_df, model=TFCModels.TimesFM_2, horizon=12, freq="W", quantiles=[0.5, 0.1, 0.9])

        # Verify the result has expected structure
        assert isinstance(result, pd.DataFrame)
        assert "unique_id" in result.columns
        assert "ds" in result.columns
        assert "fcd" in result.columns
        assert "timesfm-2" in result.columns
        assert "timesfm-2_q0.1" in result.columns
        assert "timesfm-2_q0.5" in result.columns
        assert "timesfm-2_q0.9" in result.columns

        # Verify we get forecasts for both stores
        assert set(result["unique_id"].unique()) == {"store_1", "store_2"}

        # Verify we get 12 forecasts per store (horizon=12)
        assert len(result) == 24  # 12 * 2 stores

    def test_global_model_with_static_variables(self, sample_train_df_with_static):
        """Test global model example with static variables from README.

        Tests this README example:
        ```python
        tfc_global_df = client.forecast(
            train_df,
            model=TFCModels.TFCGlobal,
            horizon=12,
            freq="W",
            static_variables=["unique_id","Group","Vendor","Category"],
            add_holidays=True,
            add_events=True,
            country_isocode="US",
            partition_by=["Group"]
        )
        ```
        """
        # Resample to weekly for the test
        train_df = (
            sample_train_df_with_static.set_index("ds")
            .groupby(["unique_id", "Group", "Vendor", "Category"])
            .resample("W")
            .agg({"target": "sum"})
            .reset_index()
        )

        client = TFCClient()
        result = client.forecast(
            train_df,
            model=TFCModels.TFCGlobal,
            horizon=12,
            freq="W",
            static_variables=["unique_id", "Group", "Vendor", "Category"],
            add_holidays=True,
            add_events=True,
            country_isocode="US",
            partition_by=["Group"],
        )

        # Verify the result has expected structure
        assert isinstance(result, pd.DataFrame)
        assert "unique_id" in result.columns
        assert "ds" in result.columns
        assert "fcd" in result.columns
        assert "tfc-global" in result.columns

        # Verify we get forecasts for both stores
        assert set(result["unique_id"].unique()) == {"store_1", "store_2"}

        # Verify we get 12 forecasts per store
        assert len(result) == 24


class TestReadmeDataStructure:
    """Test data structure examples from README."""

    def test_train_df_structure(self):
        """Test the train_df example from README.

        Tests this README example:
        ```python
        train_df = pd.DataFrame({
            "unique_id": ["store_1", "store_1", "store_1", "store_2", "store_2", "store_2"],
            "ds": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03",
                                  "2024-01-01", "2024-01-02", "2024-01-03"]),
            "target": [100, 105, 110, 200, 195, 205]
        })
        ```
        """
        train_df = pd.DataFrame(
            {
                "unique_id": ["store_1", "store_1", "store_1", "store_2", "store_2", "store_2"],
                "ds": pd.to_datetime(
                    ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-01", "2024-01-02", "2024-01-03"]
                ),
                "target": [100, 105, 110, 200, 195, 205],
            }
        )

        # Verify structure
        assert list(train_df.columns) == ["unique_id", "ds", "target"]
        assert len(train_df) == 6
        assert train_df["unique_id"].nunique() == 2
        assert pd.api.types.is_datetime64_any_dtype(train_df["ds"])

    def test_future_df_structure(self):
        """Test the future_df example from README.

        Tests this README example:
        ```python
        future_df = pd.DataFrame({
            "unique_id": ["store_1", "store_1", "store_2", "store_2"],
            "ds": pd.to_datetime(["2024-01-04", "2024-01-05", "2024-01-04", "2024-01-05"]),
            "price": [9.99, 8.99, 12.99, 11.99],
            "promotion": [1, 0, 0, 1]
        })
        ```
        """
        future_df = pd.DataFrame(
            {
                "unique_id": ["store_1", "store_1", "store_2", "store_2"],
                "ds": pd.to_datetime(["2024-01-04", "2024-01-05", "2024-01-04", "2024-01-05"]),
                "price": [9.99, 8.99, 12.99, 11.99],
                "promotion": [1, 0, 0, 1],
            }
        )

        # Verify structure
        assert "unique_id" in future_df.columns
        assert "ds" in future_df.columns
        assert "price" in future_df.columns
        assert "promotion" in future_df.columns
        assert len(future_df) == 4
        assert pd.api.types.is_datetime64_any_dtype(future_df["ds"])


class TestReadmeCustomColumns:
    """Test custom column name examples from README."""

    def test_custom_column_names(self):
        """Test custom column names example from README.

        Tests this README example:
        ```python
        my_data = pd.DataFrame({
            "item_id": ["A", "A", "B", "B"],
            "date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-01", "2024-01-02"]),
            "sales": [50, 55, 30, 32]
        })

        forecast_df = client.forecast(
            my_data,
            model=TFCModels.TimesFM_2,
            horizon=7,
            freq="D",
            id_col="item_id",
            date_col="date",
            target_col="sales"
        )
        ```
        """
        # Create more data for a meaningful forecast
        np.random.seed(42)
        dates = pd.date_range("2024-01-01", periods=30, freq="D")

        my_data = pd.DataFrame(
            {
                "item_id": ["A"] * 30 + ["B"] * 30,
                "date": dates.tolist() * 2,
                "sales": np.concatenate(
                    [50 + np.cumsum(np.random.randn(30) * 2), 30 + np.cumsum(np.random.randn(30) * 1.5)]
                ),
            }
        )

        client = TFCClient()
        forecast_df = client.forecast(
            my_data,
            model=TFCModels.TimesFM_2,
            horizon=7,
            freq="D",
            id_col="item_id",
            date_col="date",
            target_col="sales",
        )

        # Verify the result uses the custom column names
        assert isinstance(forecast_df, pd.DataFrame)
        assert "item_id" in forecast_df.columns
        assert "date" in forecast_df.columns
        assert len(forecast_df) == 14  # 7 periods * 2 items

        # Verify forecasts for both items
        assert set(forecast_df["item_id"].unique()) == {"A", "B"}


class TestReadmeClientInitialization:
    """Test client initialization examples from README."""

    def test_client_init_from_env(self):
        """Test that client can initialize from environment variable.

        Tests this README statement:
        "By default it will look for api_key in os.getenv('TFC_API_KEY')"
        """
        # This should work if TFC_API_KEY is set in environment
        client = TFCClient()
        assert client.api_key is not None
        assert isinstance(client.api_key, str)

    def test_client_init_explicit_key(self):
        """Test explicit API key initialization.

        Tests this README statement:
        "Otherwise you can explicitly set the api_key argument"
        """
        client = TFCClient(api_key="explicit_test_key")
        assert client.api_key == "explicit_test_key"


class TestReadmeModelNames:
    """Test that model names from README examples work correctly."""

    def test_model_enum_usage(self):
        """Verify TFCModels enum contains models mentioned in README."""
        # Models mentioned in README
        assert hasattr(TFCModels, "TimesFM_2")
        assert hasattr(TFCModels, "TFCGlobal")

        # Verify string values
        assert TFCModels.TimesFM_2.value == "timesfm-2"
        assert TFCModels.TFCGlobal.value == "tfc-global"

    def test_model_string_usage(self, sample_train_df):
        """Test that models can be passed as strings.

        Tests this README statement:
        "You can also pass the model name as a string, eg timesfm-2"
        """
        client = TFCClient()

        # Test with string instead of enum
        result = client.forecast(
            sample_train_df,
            model="timesfm-2",  # String instead of TFCModels.TimesFM_2
            horizon=7,
            freq="D",
        )

        assert isinstance(result, pd.DataFrame)
        assert "timesfm-2" in result.columns


class TestReadmeFutureVariables:
    """Test future variables example from README."""

    def test_future_variables_usage(self):
        """Test the future variables statement from README.

        Tests this README statement:
        "If future_variables are available, make sure to pass also a `future_df`
        when forecasting, and setting the `future_variables` argument."
        """
        # Create training data with a future variable
        np.random.seed(42)
        train_dates = pd.date_range("2024-01-01", periods=30, freq="D")

        train_df = pd.DataFrame(
            {
                "unique_id": ["store_1"] * 30,
                "ds": train_dates,
                "target": 100 + np.cumsum(np.random.randn(30) * 2),
                "price": 9.99 + np.random.randn(30) * 0.5,
            }
        )

        # Create future data with the same variable
        future_dates = pd.date_range("2024-01-31", periods=7, freq="D")
        future_df = pd.DataFrame(
            {"unique_id": ["store_1"] * 7, "ds": future_dates, "price": 9.99 + np.random.randn(7) * 0.5}
        )

        client = TFCClient()
        result = client.forecast(
            train_df,
            model=TFCModels.TabPFN_TS,  # TabPFN supports future variables
            horizon=7,
            freq="D",
            future_variables=["price"],
            future_df=future_df,
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 7
        assert "unique_id" in result.columns
        assert "ds" in result.columns


class TestReadmeVersioning:
    """Test versioning example from README."""

    def test_version_check(self):
        """Test that version can be checked as shown in README.

        Tests this README example:
        ```python
        import theforecastingcompany
        print(theforecastingcompany.__version__)
        ```
        """
        import theforecastingcompany

        # Verify version attribute exists
        assert hasattr(theforecastingcompany, "__version__")
        assert isinstance(theforecastingcompany.__version__, str)

        # Verify it follows a version pattern (e.g., "1.2.3" or "0.1.0")
        version = theforecastingcompany.__version__
        parts = version.split(".")
        assert len(parts) >= 2  # At least major.minor


class TestReadmeCrossValidate:
    """Test cross-validation functionality mentioned in README."""

    def test_cross_validate_basic(self, sample_train_df):
        """Test cross-validation mentioned in README.

        Tests this README statement:
        "The `cross_validate` function is basically the same, but takes a `fcds`
        argument to define the FCDs to use for cross-validation."
        """
        client = TFCClient()

        # Use dates that are within the training data range
        fcds = [dt.date(2024, 1, 25), dt.date(2024, 2, 5)]

        result = client.cross_validate(
            sample_train_df, model=TFCModels.TimesFM_2, horizon=10, freq="D", fcds=fcds, quantiles=[0.5, 0.1, 0.9]
        )

        # Verify the result has expected structure
        assert isinstance(result, pd.DataFrame)
        assert "unique_id" in result.columns
        assert "ds" in result.columns
        assert "fcd" in result.columns
        assert "timesfm-2" in result.columns

        # Verify we have forecasts for both cutoff dates
        assert set(pd.to_datetime(fcds)) == set(result["fcd"].unique())
