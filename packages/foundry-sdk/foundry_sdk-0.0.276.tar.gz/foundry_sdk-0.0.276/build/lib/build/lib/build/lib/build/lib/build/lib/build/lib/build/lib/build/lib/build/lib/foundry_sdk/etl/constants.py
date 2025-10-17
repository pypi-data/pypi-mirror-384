import types
from enum import Enum


class DatasetTypes(Enum):
    DUMMY = "dummy"
    SYNTHETIC = "synthetic"
    COMPETITION = "competition"
    DDOP = "ddop"
    PILOT = "pilot"
    OTHER_REAL = "other_real"


class DummyNames(Enum):
    DUMMY_PRODUCT = "dummy_product"
    DUMMY_CATEGORY_LEVEL = "dummy_category_level"
    DUMMY_CATEGORY = "dummy_category"
    DUMMY_STORE = "dummy_store"


class FlagLevels(Enum):
    MISSING_VALUE = "missing_value"
    NOT_FOR_SALE = "not_for_sale"
    OUT_OF_STOCK = "out_of_stock"


class VariableTypes(Enum):
    CONTINUOUS = "continuous"
    BINARY = "binary"
    CATEGORICAL = "categorical"
    TEXT = "text"


class TimeDataStrategy(Enum):
    APPEND = "append"
    UPDATE = "update"
    IGNORE = "ignore"


# Immutable frequency mapping for validation
FREQUENCY_MAPPING = types.MappingProxyType({"daily": 1, "weekly": 2, "monthly": 3, "quarterly": 4, "yearly": 5})


# Feature type mappings for separating numeric vs text features
NUMERIC_VAR_TYPES = frozenset(
    [
        VariableTypes.CONTINUOUS.value,
        VariableTypes.BINARY.value,
    ]
)

TEXT_VAR_TYPES = frozenset(
    [
        VariableTypes.CATEGORICAL.value,
        VariableTypes.TEXT.value,
    ]
)
