from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from typing import List

from dataclasses_json import config
from dataclasses_json import dataclass_json
from dataclasses_json import LetterCase
from dataclasses_json import Undefined

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'
DATETIME_DAY_FORMAT = '%Y-%m-%d'


def date_from_string(date_str) -> datetime:
    return datetime.strptime(date_str, DATETIME_FORMAT)


def date_from_string_day(date_str) -> datetime:
    return datetime.strptime(date_str, DATETIME_DAY_FORMAT)


def case_field(case: LetterCase, *args, **kwargs):
    return field(
        *args,
        metadata={'dataclasses_json': {'letter_case': case}},
        **kwargs
    )


def pascal_field(*args, **kwargs):
    return case_field(LetterCase.PASCAL, *args, **kwargs)


def camel_field(*args, **kwargs):
    return case_field(LetterCase.CAMEL, *args, **kwargs)


@dataclass_json(letter_case=LetterCase.CAMEL, undefined=Undefined.EXCLUDE)
@dataclass
class EnergyPrediction:
    cost: float
    value: float


@dataclass_json(letter_case=LetterCase.CAMEL, undefined=Undefined.EXCLUDE)
@dataclass
class PredictionTotal:
    start_billing_date: datetime = field(
        metadata=config(decoder=date_from_string)
    )
    end_billing_date: datetime = field(
        metadata=config(decoder=date_from_string)
    )
    energy_prediction: EnergyPrediction
    contracted_power_cost: float
    tax: float
    audiovisual_contribution: float
    audiovisual_contribution_tax: float
    total: float
    d_g_e_g_exploration_tax: float = pascal_field()


@dataclass_json(letter_case=LetterCase.CAMEL, undefined=Undefined.EXCLUDE)
@dataclass
class EnergyValue:
    real_value: float
    prediction_value: float


@dataclass_json(letter_case=LetterCase.CAMEL, undefined=Undefined.EXCLUDE)
@dataclass
class EnergyCost:
    real_cost: float
    prediction_cost: float


@dataclass_json(letter_case=LetterCase.CAMEL, undefined=Undefined.EXCLUDE)
@dataclass
class Prediction:
    date: datetime = field(metadata=config(decoder=date_from_string_day))
    value: EnergyValue
    cost: EnergyCost


@dataclass_json(letter_case=LetterCase.CAMEL, undefined=Undefined.EXCLUDE)
@dataclass
class PredictionGraph:
    start_billing_date: datetime = field(
        metadata=config(decoder=date_from_string)
    )
    end_billing_date: datetime = field(
        metadata=config(decoder=date_from_string)
    )
    billing_period: str
    prediction_chart: List[Prediction]
