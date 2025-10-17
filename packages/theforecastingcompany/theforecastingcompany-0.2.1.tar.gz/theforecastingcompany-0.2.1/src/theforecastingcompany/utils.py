import asyncio
import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable, List, Literal

import httpx
import nest_asyncio
import numpy as np
import pandas as pd
from tqdm.asyncio import tqdm_asyncio

from .api import ForecastRequest, ForecastResponse, InputSerie, OutputSerie
from .errors import _handle_response

logger = logging.getLogger(__name__)


# Types definiton
ModelAlias = str


class IDForecastResponse(ForecastResponse):
    model: ModelAlias
    unique_id: str

    def __post_init__(self):
        # Only one series at a time, which can be easily transformed to df
        assert self.series is None or len(self.series) == 1, "IDForecastResponse should have exactly one series"

    def to_df(self) -> pd.DataFrame:
        raise NotImplementedError("IDForecastResponse.to_df is not implemented yet")


class IDForecastRequest(ForecastRequest):
    model: ModelAlias
    unique_ids: list[str] | None = None
    series: List[InputSerie] | None = None

    def add_serie(self, serie: InputSerie, unique_id: str) -> "IDForecastRequest":
        """This modifies the forecast request in place, adding a new series to it."""
        if self.series is None:
            self.series = []
        if self.unique_ids is None:
            self.unique_ids = []
        self.series.append(serie)
        self.unique_ids.append(unique_id)
        return self

    def replace_serie(self, serie: InputSerie, unique_id: str) -> "IDForecastRequest":
        """Creates a NEW forecast request with the given series and unique_id."""
        new_req = self.model_copy(deep=True)
        new_req.series = [serie]
        new_req.unique_ids = [unique_id]
        return new_req

    @property
    def ids_to_forecast(self) -> list[str]:
        if self.series is None or self.unique_ids is None:
            raise ValueError("Empty IDForecastRequest: series or unique_ids is None")
        return [idx for idx, serie in zip(self.unique_ids, self.series, strict=False) if not serie.only_as_context]

    @property
    def forecast_request(self) -> ForecastRequest:
        return ForecastRequest(**{k: v for k, v in self.model_dump().items() if k != "unique_id"})

    @property
    def payload(self) -> dict[str, dict | list]:
        # Validate everything by creating a ForecastRequets and then create the Dump
        return self.forecast_request.model_dump()


class TFCModels(StrEnum):
    """Utils Enum that defines the models available in TFC.
    For each model, it defines the type of covariates it can handle and whether it's a global model or not.
    """

    TimesFM_2 = "timesfm-2"
    TabPFN_TS = "tabpfn-ts"
    TFCGlobal = "tfc-global"
    ChronosBolt = "chronos-bolt"
    Moirai = "moirai"
    MoiraiMoe = "moirai-moe"

    @property
    def accept_future_variables(self) -> bool:
        return self.value in [
            TFCModels.TabPFN_TS,
            TFCModels.TFCGlobal,
            TFCModels.Moirai,
            TFCModels.MoiraiMoe,
        ]

    @property
    def accept_historical_variables(self) -> bool:
        return self.value in [
            TFCModels.TabPFN_TS,
            TFCModels.TFCGlobal,
            TFCModels.Moirai,
            TFCModels.MoiraiMoe,
        ]

    @property
    def accept_static_variables(self) -> bool:
        return self.value in [
            TFCModels.TabPFN_TS,
            TFCModels.TFCGlobal,
            TFCModels.Moirai,
            TFCModels.MoiraiMoe,
        ]

    @property
    def is_global(self) -> bool:
        return self.value == TFCModels.TFCGlobal


@dataclass
class ModelConfig:
    """
    Represents the configuration of a model for which forecasts are requested.

    Attributes:
        model (TFCModels): string identifier of the model.
        model_alias (str): alias of the model. This will be the name of the column in the result df containing the forecasts.
        future_variables (list[str]): list of future variables to be used by the model.
        with_holidays (bool): whether to include TFC-holidays in the forecast.
        with_events (bool): whether to include TFC-events in the forecast.
        country_isocode (str): ISO code of the country for which the forecast is requested. This is used for fetching the right
        holidays and events.
        historical_variables (list[str]): list of historical variables to be used by the model.
        static_variables (list[str]): list of static variables to be used by the model.
    """

    model: TFCModels
    model_alias: ModelAlias | None = None
    historical_variables: list[str] | None = None
    static_variables: list[str] | None = None
    future_variables: list[str] | None = None
    add_holidays: bool = False
    add_events: bool = False
    country_isocode: str | None = None

    def __post_init__(self) -> None:
        # Validate and possibly convert str to TFCModels
        self.model = TFCModels(self.model)
        if self.future_variables and not self.model.accept_future_variables:
            raise ValueError(f"Model {self.model} does not accept future variables")
        if any([self.add_holidays, self.add_events, self.country_isocode]) and not self.model.accept_future_variables:
            raise ValueError(f"Model {self.model} does not accept holidays or events")
        if self.historical_variables and not self.model.accept_historical_variables:
            raise ValueError(f"Model {self.model} does not accept historical variables")
        if self.static_variables and not self.model.accept_static_variables:
            raise ValueError(f"Model {self.model} does not accept static variables")
        if self.model_alias is None:
            self.model_alias = self.model.value

    def get_covariates(self):
        if not (self.add_holidays or self.add_events):
            return None
        if self.country_isocode is None:
            raise ValueError("holidays and events need a countryisocode or `Global` for global events.")

        cov = []
        if self.add_holidays:
            cov += [{"type": "holidays", "config": {"country": self.country_isocode}}]
        if self.add_events:
            # Add by default also Global events.
            cov += [{"type": "events", "config": {"country": self.country_isocode}}]
            cov += [{"type": "events", "config": {"country": "Global"}}]
        return cov


def extract_forecast_df_from_model_idresponse(
    responses: list[IDForecastResponse],
    fcds: list[pd.Timestamp] | dict[str, list[pd.Timestamp]],
    id_col: str = "unique_id",
    date_col: str = "ds",
) -> pd.DataFrame:
    """Bild a DataFrame with the Forecasts from each TFCModel.

    responses: For each ModelAlias, a list of IDForecastResponse, one per time series (unique_id) to be forecasted.
    fcds: the forecast creation date
    id_col: the column name for the time series id
    date_col: the column name for the forecast date
    """
    models = set(response.model for response in responses)
    grouped_responses = {model: [response for response in responses if response.model == model] for model in models}
    model_dfs = []
    for model_name, response_list in grouped_responses.items():
        dfs = []
        for response in response_list:
            unique_id = response.unique_id
            if response.series is None:
                raise ValueError(
                    f"Response series is None: this means the model failed to generate a forecast for serie:{unique_id}"
                )
            series: list[list[OutputSerie]] = response.series
            for serie in series:
                if isinstance(fcds, list):
                    unique_id_fcds = fcds
                elif isinstance(fcds, dict):
                    unique_id_fcds = fcds.get(unique_id, [])
                    if not isinstance(unique_id_fcds, list):
                        unique_id_fcds = [unique_id_fcds]
                else:
                    raise ValueError("fcds must be a list[pd.Timestamp] or a dict[str, list[pd.Timestamp]]")
                assert len(serie) == len(unique_id_fcds) or (len(serie) == 1 and len(unique_id_fcds) == 0), (
                    "Wrong number of fcds. Expected %d, got %d" % (len(serie), len(unique_id_fcds))
                )
                if len(serie) == 1 and len(unique_id_fcds) == 0:
                    # get the fcd from the serie index
                    unique_id_fcds = [pd.Timestamp(serie[0].index[0])]
                for fcd, pred in zip(unique_id_fcds, serie, strict=False):
                    df = pd.DataFrame()
                    df[model_name] = pred.prediction["mean"]
                    df[date_col] = pred.index
                    df[id_col] = unique_id
                    df["fcd"] = fcd
                    # Add quantile predictions
                    df = df.assign(
                        **{
                            f"{model_name}_q{key}": pred.prediction[key]
                            for key in pred.prediction.keys()
                            if key != "mean"
                        }
                    )
                    dfs.append(df)
        model_dfs.append(
            pd.concat(dfs, axis=0)
            .assign(
                **{
                    date_col: lambda df: pd.to_datetime(df[date_col]),
                    "fcd": lambda df: pd.to_datetime(df["fcd"]),
                    id_col: lambda df: df[id_col].astype(str),
                }
            )
            .sort_values([id_col, "fcd", date_col])
        )
    if not all(len(df) == len(model_dfs[0]) for df in model_dfs):
        raise ValueError("All model dfs must have the same number of rows")

    res = pd.concat(model_dfs, axis=1)
    if len(res) != len(model_dfs[0]):
        raise ValueError(
            "Concatenation of model forecasts resulted in more rows than expected. Indexes unique_id, ds, fcd must be the same for all models."
        )

    return res


async def send_request_with_retries(
    forecast_request: IDForecastRequest,
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    api_key: str,
    url: str,
    max_retries: int = 3,
    retry_delay: int = 2,  # nb seconds before retrying.
) -> List[IDForecastResponse] | None:
    """
    Send a request to the Retrocast API for a single time series. Return one separate ForecastResponse per OutputSerie
    """
    if max_retries < 1:
        raise ValueError("max retries should be >= 1")
    if forecast_request.unique_ids is None:
        raise ValueError("Empty ForecastRequest: unique_ids is None")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    def _extract_response(
        response: ForecastResponse, unique_ids: list[str], model: ModelAlias
    ) -> list[IDForecastResponse]:
        """
        Separate all series in a forecast response and associate each to the corresponding
        model and unique_id.
        """
        assert response.series is None or len(unique_ids) == len(response.series), (
            "nb of forecasted unique ids and nb of series in the response do not match."
        )
        if response.series is None:
            return [
                IDForecastResponse(model=model, unique_id=unique_id, status=response.status) for unique_id in unique_ids
            ]

        return [
            IDForecastResponse(
                model=model,
                unique_id=unique_id,
                status=response.status,
                series=[serie],
            )
            for unique_id, serie in zip(unique_ids, response.series, strict=False)
        ]

    response = None
    for _ in range(max_retries):
        async with semaphore:
            response = await client.post(url, json=forecast_request.payload, headers=headers)
        if response.status_code == 200:
            return _extract_response(
                ForecastResponse(**response.json()), forecast_request.ids_to_forecast, forecast_request.model
            )
        await asyncio.sleep(retry_delay)  # Wait before retrying

    _handle_response(response)


def _get_ts_df(train_df: pd.DataFrame, unique_id: str, id_col: str, date_col: str, target_col: str):
    """Extract the time series dataframe, handling edge cases were the time series has only one observation.

    Args:
        train_df: The training dataframe
        unique_id: The unique id of the time series
        id_col: The column name for the unique id
        date_col: The column name for the date
        target_col: The column name for the target
    """

    ts_df = train_df.loc[unique_id]
    if isinstance(ts_df, pd.Series):
        # When unique_id has only one row in train_df, train_df.loc[unique_id] returns a Series
        # and not a dataframe.
        ts_df = (
            ts_df.to_frame()
            .T.reset_index()
            .rename(columns={"index": id_col})
            .assign(**{date_col: lambda df: pd.to_datetime(df[date_col])})
            .astype({target_col: float})
        )
    else:
        ts_df = ts_df.reset_index()
    return ts_df


def _build_input_serie(
    ts_df: pd.DataFrame,
    is_new: bool,
    fcds: list[pd.Timestamp] | dict[str, pd.Timestamp | list[pd.Timestamp]],
    model_config: ModelConfig,
    id_col: str,
    date_col: str,
    target_col: str,
) -> InputSerie:
    """Build the input series for the API request.

    Args:
        ts_df: The time series dataframe
        is_new: Whether the time series is new, ie, it's only in the test set but not in the train set.
        model_config: The model configuration
        id_col: The column name for the unique id
        date_col: The column name for the date
        target_col: The column name for the target
    """
    # Convert to string, because API doesn't accept datetime objects
    index = ts_df[date_col].dt.strftime("%Y-%m-%d %H:%M:%S").to_list()
    target = ts_df[target_col].to_list()
    unique_id = ts_df[id_col].iloc[0]

    # TODO: Treat future_vars and static_vars separately in the future.
    future_vars = model_config.future_variables[:] if model_config.future_variables else []
    if model_config.static_variables:
        future_vars += model_config.static_variables
    if future_vars:
        future_variables_index = ts_df[date_col].dt.strftime("%Y-%m-%d %H:%M:%S").to_list()
        future_dict = {col: ts_df[col].to_list() for col in future_vars}
    else:
        future_variables_index = []
        future_dict = {}
    if model_config.historical_variables:
        hist_variables_dict = {col: ts_df[col].to_list() for col in model_config.historical_variables}
    else:
        hist_variables_dict = {}

    if (
        # Only global model supports only_as_context=True
        not model_config.model.is_global
        # If fcds is a list, all time series will be predicte with same FCDs
        or isinstance(fcds, list)
        # If fcds is a dict, it contains the FCDs for the time that needs to be forecasted
        or unique_id in fcds
    ):
        only_as_context = False
    else:
        only_as_context = True

    return InputSerie(
        **{
            "future_variables": future_dict,
            "future_variables_index": future_variables_index,
            "hist_variables": hist_variables_dict,
            "index": index,
            "static_variables": {},
            "target": target,
            "fcds": _compute_fcds_idx(unique_id, is_new, fcds, index),
            "only_as_context": only_as_context,
        }
    )


def _compute_fcds_idx(
    unique_id: str,
    is_new: bool,
    fcds: list[pd.Timestamp] | dict[str, pd.Timestamp | list[pd.Timestamp]],
    index: list[str],
) -> list[int] | None:
    """Compute the index of the forecast creation dates in the index list.

    Args:
        unique_id: The unique id of the time series
        is_new: Whether the time series is new, ie, it's only in the test set but not in the train set.
        fcds: List of forecast creation dates or dictionary of forecast creation dates per unique_id.
            If fcds is a list, the same FCD is used for all time series.
            If fcds is a dict, a different FCD is used for each time series.
            If fcds is an empty list, the forecast is created from the period following the last observation.
        index: List of dates in the time series

    Returns:
        List of indices of the forecast creation dates in the index list
    """
    if is_new:
        # Support only single forecast for a new series. If several FCD needs to be tried, at the moment these need to be separate calls
        return [0]

    unique_id_fcds = fcds if isinstance(fcds, list) else fcds.get(unique_id, [])
    if not isinstance(unique_id_fcds, list):
        unique_id_fcds = [unique_id_fcds]
    if unique_id_fcds and not isinstance(unique_id_fcds[0], str):
        unique_id_fcds = [c.strftime("%Y-%m-%d %H:%M:%S") for c in unique_id_fcds]

    idxs = np.nonzero(np.isin(np.array(index), unique_id_fcds))[0].tolist()
    # TODO: test this function and that ir raises errors when expected.
    # Test forecast: FCD > max(index) --> fcds = [] passed to the API
    # Backtest forecast: FCD <= max(index) --> fcds = [] will be passed to the API but this is wrong, cause
    # FCD > max(index) will be used in this case.
    if len(idxs) != len(unique_id_fcds) and max(unique_id_fcds) < max(index):
        # TODO: I should check for each fcd to be more precise, cause I can have some fcd that re smaller
        # and some fcds that are bigger than max(index)
        raise ValueError(f"Not all fcds found in among given dates for id={unique_id}")

    return idxs if idxs else None  # TimesFM and Chronos do not handle correctly fcds=[]


async def send_async_requests_multiple_models(
    train_df: pd.DataFrame,
    fcds: list[pd.Timestamp] | dict[str, pd.Timestamp | list[pd.Timestamp]],
    models: list[ModelConfig],
    horizon: int = 13,
    freq: str = "W",
    max_retries: int = 5,
    max_concurrent: int = 10,
    api_key: str | None = None,
    url: str | None = None,
    id_col: str = "unique_id",
    date_col: str = "ds",
    target_col: str = "target",
    new_ids: Iterable[str] | None = None,
    cloud: Literal["aws", "gcp", "oci"] | None = None,
    quantiles: list[float] | None = None,
    partition_by: list[str] | None = None,
) -> list[IDForecastResponse]:
    """Sends request for each unique_id (timeseries) asynchronously to the Retrocast API.
    Returns a list of responses.

    Args:
        train_df: DataFrame with columns [id_col, date_col, target_col]
        fcds: List of forecast creation dates or dictionary of forecast creation dates per unique_id
        models: List of ModelConfig objects
        horizon: Forecast horizon
        freq: Frequency of the time series
        max_retries: Maximum number of retries
        max_concurrent: Maximum number of concurrent requests
        api_key: API key for authentication
        url: URL for the API
        id_col: Column name for unique_id
        date_col: Column name for date
        target_col: Column name for target
        new_ids: List of new unique_ids to be predicted
        partition_by: List of columns to partition by. Only global models support partitioned context.
    """
    if api_key is None:
        raise ValueError("api_key must be provided")

    if new_ids is None:
        new_ids = set()

    if quantiles and 0.5 not in quantiles:
        # TODO: needed eg in TabPFN-TS to compute default metrics such as WAPE. This however should be computed based on the selected prediction output.
        quantiles = quantiles + [0.5]

    if partition_by is not None:
        if not all(model.model.is_global for model in models):
            raise ValueError("Only global models support partitioned context.")
        if not all(col in train_df.columns for col in partition_by):
            raise ValueError(
                f"All columns in partition_by must be present in train_df. Missing columns: {set(partition_by) - set(train_df.columns)}"
            )
        if any(col == id_col for col in partition_by):
            raise ValueError(
                f"ID Column {id_col} cannot be in partition_by, as it is used to identify time series. Use a local model rather than tfc-global."
            )
        unique_ids_to_iter = train_df[partition_by + [id_col]].groupby(partition_by)[id_col].agg(set).to_dict()
    else:
        unique_ids_to_iter = {"all": train_df[id_col].unique()}

    train_df = train_df.sort_values(by=[id_col, date_col]).set_index(id_col)
    semaphore = asyncio.Semaphore(max_concurrent)
    async with httpx.AsyncClient(timeout=httpx.Timeout(connect=120, read=600, pool=600, write=120)) as client:
        tasks = []
        for model_config in models:
            model_url = url if url else f"https://api.retrocast.com/forecast?model={model_config.model.value}"
            if cloud:
                model_url = f"{model_url}&cloud={cloud}"
            if model_config.model not in model_url:
                raise ValueError(f"Wrong url provided: {model_config.model} not found in url {model_url}")
            for partition in unique_ids_to_iter.values():
                forecast_request = IDForecastRequest(
                    model=model_config.model_alias,
                    horizon=horizon,
                    freq=freq,
                    context=None,
                    covariates=model_config.get_covariates(),
                    quantiles=quantiles if quantiles else ForecastRequest.model_fields["quantiles"].default,
                )
                # Loop over unique_ids (time series) and send one request for each.
                for unique_id in partition:
                    # Extract time series
                    ts_df = _get_ts_df(train_df, unique_id, id_col, date_col, target_col)
                    is_new = unique_id in new_ids

                    input_serie = _build_input_serie(ts_df, is_new, fcds, model_config, id_col, date_col, target_col)

                    if not model_config.model.is_global:
                        tasks.append(
                            asyncio.create_task(
                                send_request_with_retries(
                                    forecast_request.replace_serie(input_serie, unique_id),
                                    client=client,
                                    semaphore=semaphore,
                                    api_key=api_key,
                                    url=model_url,
                                    max_retries=max_retries,
                                )
                            )
                        )
                    else:
                        forecast_request.add_serie(input_serie, unique_id)
                if model_config.model.is_global:
                    tasks.append(
                        asyncio.create_task(
                            send_request_with_retries(
                                forecast_request,
                                client=client,
                                semaphore=semaphore,
                                api_key=api_key,
                                url=model_url,
                                max_retries=max_retries,
                            )
                        )
                    )

        responses: list[list[IDForecastResponse]] = await tqdm_asyncio.gather(
            *tasks, desc=f"Sending {len(tasks)} requests"
        )

        # Chain the responses from different models/batches into one single list
        return [item for sublist in responses for item in sublist]


def cross_validate_models(
    train_df: pd.DataFrame,
    fcds: list[pd.Timestamp] | dict[str, pd.Timestamp],
    models: list[ModelConfig],
    horizon: int,
    freq: str,
    max_retries: int = 5,
    max_concurrent: int = 100,
    api_key: str | None = None,
    url: str | None = None,
    id_col: str = "unique_id",
    date_col: str = "ds",
    target_col: str = "target",
    new_ids: Iterable[str] | None = None,
    cloud: Literal["aws", "gcp", "oci"] | None = None,
    quantiles: list[float] | None = None,
    partition_by: list[str] | None = None,
) -> pd.DataFrame:
    async def _run():
        return await send_async_requests_multiple_models(
            train_df,
            fcds,
            models,
            horizon,
            freq,
            max_retries,
            max_concurrent,
            api_key,
            url,
            id_col,
            date_col,
            target_col,
            new_ids,
            cloud,
            quantiles,
            partition_by,
        )

    try:
        return extract_forecast_df_from_model_idresponse(asyncio.run(_run()), fcds, id_col, date_col)
    except RuntimeError as e:
        if "asyncio.run() cannot be called" in str(e) or "This event loop is already running" in str(e):
            nest_asyncio.apply()
            loop = asyncio.get_event_loop()
            return extract_forecast_df_from_model_idresponse(loop.run_until_complete(_run()), fcds, id_col, date_col)
        else:
            raise
