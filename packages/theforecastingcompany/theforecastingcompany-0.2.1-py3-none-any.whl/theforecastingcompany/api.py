from datetime import date, datetime, time
from typing import Annotated, Dict, List, Literal, Optional, TypeAlias, Union

from pydantic import BaseModel, ValidationInfo
from pydantic.fields import Field
from pydantic.functional_validators import field_validator

Numeric: TypeAlias = Union[float, int]
Array: TypeAlias = List[Numeric | str]
Index: TypeAlias = Union[List[str], List[date], List[datetime], List[time], List[int]]


class HolidayConfig(BaseModel):
    country: str = Field(
        ...,
        description="ISO country code for holidays",
        examples=["US", "GB", "FR", "DE"],
        min_length=2,
        max_length=2,
    )


# TODO: Add events_type and superclass Holidays and SportsEvents etc
class EventConfig(BaseModel):
    country: str = Field(
        ...,
        description="ISO country code for events (2-char code or 'Global')",
        examples=["US", "GB", "FR", "DE", "Global"],
    )

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: str) -> str:
        if v == "Global":
            return v
        if isinstance(v, str) and len(v) == 2:
            return v
        raise ValueError("country must be a 2-character string or the literal 'Global'")


class FloatConfig(BaseModel):
    data_source: str
    column: str = Field(..., description="Column for the data source", min_length=1, max_length=100)


class TemporalFeaturesConfig(BaseModel):
    pass


class HolidaysCovariate(BaseModel):
    type: Literal["holidays"] = Field(..., examples=["holidays"])
    config: HolidayConfig = Field(..., examples=[{"country": "US"}])


class EventsCovariate(BaseModel):
    type: Literal["events"] = Field(..., examples=["events"])
    config: EventConfig = Field(..., examples=[{"country": "US"}])


class FloatDataSourceCovariate(BaseModel):
    type: Literal["float"] = Field(..., examples=["float"])
    config: FloatConfig = Field(..., examples=[{"column": "SomeColumn"}])


class TemporalFeaturesCovariate(BaseModel):
    type: Literal["temporal_features"] = Field(..., examples=["temporal_features"])
    config: TemporalFeaturesConfig = Field(..., examples=[{}])


Covariate = Union[
    HolidaysCovariate,
    FloatDataSourceCovariate,
    EventsCovariate,
    TemporalFeaturesCovariate,
]


class InputSerie(BaseModel):
    target: Array = Field(..., description="A list of numeric target values.")
    index: Index = Field(..., description="A list of dates, datetimes, times, or integers.")
    hist_variables: Dict[str, Array] = Field(
        default={},
        description="A dictionary mapping string keys to lists of historical numeric values, e.g. recorded temperatures.",
    )
    future_variables_index: Index = Field(default=[], description="A list of dates, datetimes, times, or integers.")
    future_variables: Dict[str, Array] = Field(
        default={},
        description="A dictionary mapping string keys to lists of numeric values that have the length of the target plus the horizon, e.g. forecasted temperatures.",
    )
    static_variables: Dict[str, Numeric] = Field(
        default={},
        description="A dictionary mapping string keys to static numeric values, e.g. a SKU.",
    )
    fcds: List[int] | None = Field(
        default=None,
        description="A list of indexes representing the forecast creation dates, indexing the target. If not provided the forecast creation date is the latest possible date. This can be used to get multiple forecasts from the same series at once (e.g. for backtesting).",
    )

    only_as_context: bool = Field(
        default=False,
        description="If True, the series will be used only as context (ie, not forecasted). This should always be False unless a global model is used.",
    )

    @field_validator("future_variables")
    @classmethod
    def validate_future_variables_length(cls, v: Dict[str, Array], info: ValidationInfo) -> Dict[str, Array]:
        future_variables_index = info.data.get("future_variables_index")
        if future_variables_index is None:
            raise ValueError("future_variables_index must be set if including future_variables")

        expected_length = len(future_variables_index)
        for var_name, array in v.items():
            if len(array) != expected_length:
                raise ValueError(
                    f"Array '{var_name}' in future_variables has length {len(array)}, "
                    f"but should have length {expected_length} to match future_variables_index"
                )
        return v


# Custom type for quantile levels as strings
def validate_quantile_level(v: str) -> str:
    try:
        float_val = float(v)
        if 0 < float_val < 1:
            return v
    except ValueError:
        pass
    raise ValueError("QuantileLevelStr must be a string representing a float between 0 and 1.")


QuantileLevel = Annotated[str, field_validator("QuantileLevelStr", mode="before")(validate_quantile_level)]


class Metrics(BaseModel):
    mae: float | None = Field(default=None, ge=0)
    mape: float | None = Field(default=None, ge=0)
    crps: float | None = Field(default=None, ge=0)


class OutputSerie(BaseModel):
    prediction: Dict[str, Array] = Field(
        ...,
        examples=[
            {
                "mean": [1, 2, 3],
                "0.1": [1, 2, 3],
                "0.9": [1, 2, 3],
            }
        ],
    )
    index: Index = Field(..., examples=[])
    metrics: Optional[Metrics] = None

    @field_validator("prediction")
    def validate_prediction_keys(cls, v):
        for key in v.keys():
            if key not in ["mean", "samples"]:
                validate_quantile_level(key)
        return v


class ForecastResponse(BaseModel):
    series: Optional[List[List[OutputSerie]]] = None  # if job is processing
    status: Literal["completed"] | Literal["in_progress"] = "completed"


class ForecastRequest(BaseModel):
    """
    API request model for the model inference endpoint.
    """

    series: List[InputSerie] = Field(
        examples=[
            [
                {
                    "target": [
                        125,
                        120,
                        140,
                        135,
                        133,
                    ],
                    "index": [
                        "2001-01-06",
                        "2001-01-07",
                        "2001-01-08",
                        "2001-01-09",
                        "2001-01-10",
                    ],
                    "hist_variables": {
                        "temperature": [74, 72, 79, 77, 75],
                    },
                    "future_variables_index": [
                        "2001-01-06",
                        "2001-01-07",
                        "2001-01-08",
                        "2001-01-09",
                        "2001-01-10",
                        "2001-01-11",
                        "2001-01-12",
                        "2001-01-13",
                        "2001-01-14",
                        "2001-01-15",
                    ],
                    "future_variables": {
                        "local_attendance_forecast": [
                            125,
                            75,
                            200,
                            122,
                            123,
                            150,
                            100,
                            120,
                            121,
                            119,
                        ],
                    },
                    "static_variables": {"Population": 100000},
                },
            ]
        ]
    )

    horizon: int = Field(
        ...,
        ge=1,
        le=1000,
        examples=[5],
        description="Number of steps to forecast given the frequency.",
    )
    freq: Literal["H", "D", "W", "M", "Q", "Y", "5min", "15min", "30min"] = Field(
        ..., examples=["D"], description="Frequency of the time series."
    )
    context: int | None = Field(
        default=None,
        ge=1,
        examples=[20],
        description="The amount of history to use when forecasting. This is the number of steps to look back in the target series. More history can improve the forecast accuracy, but can also increase the computation time. By default this is set to the max of model capability or the length of the provided target series, whichever is shorter.",
    )
    quantiles: List[float] = Field(default=[0.1, 0.9, 0.4, 0.5])
    covariates: List[Covariate] | None = Field(
        default=None,
        description="Apply additional co-variates provided by TFC. Only supported by the following models: Navi, Moirai, Moriai-MoE and TabPFN-TS.",
        examples=[[{"type": "holidays'", "config": {"country": "US"}}]],
    )


if __name__ == "__main__":
    # NOTE: can copy these to the gateway schemas
    # Ideally we'd have it automated with github actions eventually
    import json

    with open("ForecastRequest.json", "w") as f:
        json.dump(ForecastRequest.model_json_schema(), f, indent=2)

    with open("ForecastResponse.json", "w") as f:
        json.dump(ForecastResponse.model_json_schema(), f, indent=2)
