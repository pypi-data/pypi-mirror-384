# The Forecasting Company Python SDK

[![PyPI version](https://img.shields.io/pypi/v/theforecastingcompany)](https://pypi.org/project/theforecastingcompany/)
[![API status](https://api.checklyhq.com/v1/badges/groups/2038018?style=flat&theme=default)](https://status.retrocast.com)

The python SDK provides a simple interface to make forecasts using the TFC API.

## Documentation

The REST API documentation can be found on [https://api.retrocast.com/docs](https://api.retrocast.com/docs).

To get an API key, visit the [Authentication docs](https://api.retrocast.com/docs/routes#authentication). In the **API Keys** section you will find an option to _Sign in_ or, if you already signed in, a box containing your API key.

## Installation

```sh
# install from PyPI
pip install theforecastingcompany
```

## Usage

```python
# By default it will look for api_key in os.getenv("TFC_API_KEY"). Otherwise you can explicity set the api_key argument
client = TFCClient()

# Compute forecast for a single model
timesfm_df = client.forecast(
    train_df,
    model=TFCModels.TimesFM_2 # StrEnum defined in utils. You can also pass the model name as a string, eg timesfm-2
    horizon=12,
    freq="W",
    quantiles=[0.5,0.1,0.9]
)

# Global Model with static variables
tfc_global_df = client.forecast(
        train_df,
        model=TFCModels.TFCGlobal,
        horizon=12,
        freq="W",
        static_variables=["unique_id","Group","Vendor","Category"],
        add_holidays=True,
        add_events=True,
        country_isocode = "US",
        # Fit a separate global model for each group.
        # If None, a single global model is fitted to all timeseries.
        partition_by=["Group"]
    )
```

If future_variables are available, make sure to pass also a `future_df` when forecasting, and setting the `future_variables` argument. **Important**: The same `future_variables` columns must be present in both `train_df` and `future_df`. For example, if you specify `future_variables=["price", "promotion"]`, both columns must exist in the historical data (`train_df`) and in the future data (`future_df`).

The `cross_validate` function is basically the same, but takes a `fcds` argument to define the FCDs to use for cross-validation. It also returns the target column in the output dataframe. 

### Data Structure Requirements

Both `train_df` and `future_df` must contain the following columns:

- **`unique_id`** (or custom `id_col`): Unique identifier for each time series
- **`ds`** (or custom `date_col`): Date/timestamp column (must be datetime format)
- **`target`** (or custom `target_col`): The values to forecast

You can customize column names using the `id_col`, `date_col`, and `target_col` parameters if your data uses different naming conventions.

**Example `train_df`** with historical data, static variables (`region`, `store_type`), and future variables (`price`, `promotion`):

```python
import pandas as pd

train_df = pd.DataFrame({
    "unique_id": ["store_1", "store_1", "store_1", "store_2", "store_2", "store_2"],
    "ds": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-01", "2024-01-02", "2024-01-03"]),
    "target": [100, 105, 110, 200, 195, 205],
    "region": ["North", "North", "North", "South", "South", "South"],  # static variable
    "store_type": ["Premium", "Premium", "Premium", "Standard", "Standard", "Standard"],  # static variable
    "price": [9.99, 9.99, 9.99, 12.99, 12.99, 12.99],  # future variable (must be in train_df too!)
    "promotion": [0, 1, 0, 1, 0, 1]  # future variable (must be in train_df too!)
})
```

**Example `future_df`** with the same future variables `price` and `promotion`:

```python
future_df = pd.DataFrame({
    "unique_id": ["store_1", "store_1", "store_2", "store_2"],
    "ds": pd.to_datetime(["2024-01-04", "2024-01-05", "2024-01-04", "2024-01-05"]),
    "price": [9.99, 8.99, 12.99, 11.99],  # future variable
    "promotion": [1, 0, 0, 1]  # future variable
})

# Forecasting with future variables
forecast_df = client.forecast(
    train_df,
    future_df=future_df,
    model=TFCModels.TFCGlobal,
    horizon=2,
    freq="D",
    static_variables=["region", "store_type"],
    future_variables=["price", "promotion"]  # These columns must exist in both train_df and future_df
)
```

**Using custom column names**:

```python
# If your data uses different column names
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
    id_col="item_id",      # specify your ID column
    date_col="date",       # specify your date column
    target_col="sales"     # specify your target column
)
```

## Versioning

This package generally follows [SemVer](https://semver.org/spec/v2.0.0.html) conventions, though certain backwards-incompatible changes may be released as minor versions:

1. Changes that only affect static types, without breaking runtime behavior.
2. Changes to library internals which are technically public but not intended or documented for external use. _(Please open a GitHub issue to let us know if you are relying on such internals.)_
3. Changes that we do not expect to impact the vast majority of users in practice.

We take backwards-compatibility seriously and work hard to ensure you can rely on a smooth upgrade experience.

We are keen for your feedback; please open an [issue](https://www.github.com/openai/openai-python/issues) with questions, bugs, or suggestions.

### Determining the installed version

If you've upgraded to the latest version but aren't seeing any new features you were expecting then your python environment is likely still using an older version.

You can determine the version that is being used at runtime with:

```py
import theforecastingcompany
print(theforecastingcompany.__version__)
```

## Requirements

Python 3.11 or higher.
