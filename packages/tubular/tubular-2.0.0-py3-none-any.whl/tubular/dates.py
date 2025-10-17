"""This module contains transformers for working with date columns"""

from __future__ import annotations

import copy
import datetime
import warnings
from enum import Enum
from typing import TYPE_CHECKING, Annotated, ClassVar, Literal, Optional, Union

import narwhals as nw
import numpy as np
import pandas as pd
from beartype import beartype
from beartype.vale import Is
from typing_extensions import deprecated

from tubular._utils import (
    _convert_dataframe_to_narwhals,
    _return_narwhals_or_native_dataframe,
)
from tubular.base import BaseTransformer
from tubular.mapping import MappingTransformer
from tubular.mixins import DropOriginalMixin, NewColumnNameMixin, TwoColumnMixin
from tubular.types import DataFrame

if TYPE_CHECKING:
    from narhwals.typing import FrameT

TIME_UNITS = ["us", "ns", "ms"]


class BaseGenericDateTransformer(
    NewColumnNameMixin,
    DropOriginalMixin,
    BaseTransformer,
):
    """
    Extends BaseTransformer for datetime/date scenarios

    Parameters
    ----------
    columns : List[str]
        List of 2 columns. First column will be subtracted from second.

    new_column_name : str
        Name for the new year column.

    drop_original : bool
        Flag for whether to drop the original columns.

    return_native: bool, default = True
        Controls whether transformer returns narwhals or native pandas/polars type

    **kwargs
        Arbitrary keyword arguments passed onto BaseTransformer.init method.

    Attributes
    ----------

    built_from_json: bool
        indicates if transformer was reconstructed from json, which limits it's supported
        functionality to .transform

    polars_compatible : bool
        class attribute, indicates whether transformer has been converted to polars/pandas agnostic narwhals framework

    return_native: bool, default = True
        Controls whether transformer returns narwhals or native pandas/polars type

    jsonable: bool
        class attribute, indicates if transformer supports to/from_json methods

    FITS: bool
        class attribute, indicates whether transform requires fit to be run first

    Example:
    --------
    >>> BaseGenericDateTransformer(
    ... columns=['a',  'b'],
    ... new_column_name='bla',
    ...    )
    BaseGenericDateTransformer(columns=['a', 'b'], new_column_name='bla')
    """

    polars_compatible = True

    FITS = False

    jsonable = False

    def __init__(
        self,
        columns: list[str],
        new_column_name: str | None = None,
        drop_original: bool = False,
        **kwargs: dict[str, bool],
    ) -> None:
        super().__init__(columns=columns, **kwargs)

        self.set_drop_original_column(drop_original)
        self.check_and_set_new_column_name(new_column_name)

    @beartype
    def check_columns_are_date_or_datetime(
        self,
        X: DataFrame,
        datetime_only: bool,
    ) -> None:
        """Checks the schema of the DataFrame to ensure that each column listed in
        self.columns is either a datetime or date type, depending on the datetime_only
        flag. If a column does not meet the expected type criteria, a TypeError is raised.

        Parameters
        ----------

        X: pd/pl.DataFrame
            Data to validate

        datetime_only: bool
            Indicates whether ONLY datetime types are accepted

        Raises
        ----------

        TypeError: if non date/datetime types are found

        TypeError: if mismatched date/datetime types are found,
        types should be consistent

        Example:
        --------
        >>> import polars as pl

        >>> transformer=BaseGenericDateTransformer(
        ... columns=["a",  "b"],
        ... new_column_name='bla',
        ...    )

        >>> test_df=pl.DataFrame(
        ... {
        ... "a": [datetime.date(1993, 9, 27), datetime.date(2005, 10, 7)],
        ... "b": [datetime.date(1991, 5, 22), datetime.date(2001, 12, 10)]
        ... },
        ... )

        >>> transformer.check_columns_are_date_or_datetime(
        ... test_df,
        ... datetime_only=False
        ... )

        """

        X = _convert_dataframe_to_narwhals(X)

        type_msg = ["Datetime"]
        date_type = nw.Date
        allowed_types = [nw.Datetime]
        if not datetime_only:
            allowed_types = [*allowed_types, date_type]
            type_msg += ["Date"]

        schema = X.schema

        for col in self.columns:
            is_datetime = False
            is_date = False
            if isinstance(schema[col], nw.Datetime):
                is_datetime = True

            elif schema[col] == nw.Date:
                is_date = True

            # first check for invalid types (non date/datetime)
            if (not is_datetime) and (not (not datetime_only and is_date)):
                msg = f"{self.classname()}: {col} type should be in {type_msg} but got {schema[col]}. Note, Datetime columns should have time_unit in {TIME_UNITS} and time_zones from zoneinfo.available_timezones()"
                raise TypeError(msg)

        # process datetime types for more readable error messages
        present_types = {
            dtype if not isinstance(dtype, nw.Datetime) else nw.Datetime
            for name, dtype in schema.items()
            if name in self.columns
        }

        valid_types = present_types.issubset(set(allowed_types))
        # convert to list and sort to ensure reproducible order
        present_types = {str(value) for value in present_types}
        present_types = list(present_types)
        present_types.sort()

        # next check for consistent types (all date or all datetime)
        if not valid_types or len(present_types) > 1:
            msg = rf"{self.classname()}: Columns fed to datetime transformers should be {type_msg} and have consistent types, but found {present_types}. Note, Datetime columns should have time_unit in {TIME_UNITS} and time_zones from zoneinfo.available_timezones(). Please use ToDatetimeTransformer to standardise."
            raise TypeError(
                msg,
            )

    @beartype
    def transform(
        self,
        X: DataFrame,
        datetime_only: bool = False,
        return_native_override: Optional[bool] = None,
    ) -> DataFrame:
        """Base transform method, calls parent transform and validates data.

        Parameters
        ----------
        X : pd/pl.DataFrame
            Data containing self.columns

        datetime_only: bool
            Indicates whether ONLY datetime types are accepted

        return_native_override: Optional[bool]
            option to override return_native attr in transformer, useful when calling parent
            methods

        Returns
        -------
        X : pd/pl.DataFrame
            Validated data

        Example:
        --------
        >>> import polars as pl
        >>> import datetime

        >>> transformer=BaseGenericDateTransformer(
        ... columns=["a",  "b"],
        ... new_column_name='bla',
        ...    )

        >>> test_df=pl.DataFrame(
        ... {
        ... "a": [datetime.date(1993, 9, 27), datetime.date(2005, 10, 7)],
        ... "b": [datetime.date(1991, 5, 22), datetime.date(2001, 12, 10)]
        ... },
        ... )

        >>> # base transform has no effect on data
        >>> transformer.transform(test_df)
        shape: (2, 2)
        ┌────────────┬────────────┐
        │ a          ┆ b          │
        │ ---        ┆ ---        │
        │ date       ┆ date       │
        ╞════════════╪════════════╡
        │ 1993-09-27 ┆ 1991-05-22 │
        │ 2005-10-07 ┆ 2001-12-10 │
        └────────────┴────────────┘
        """

        return_native = self._process_return_native(return_native_override)

        X = super().transform(X, return_native_override=False)

        X = _convert_dataframe_to_narwhals(X)

        self.check_columns_are_date_or_datetime(X, datetime_only=datetime_only)

        return _return_narwhals_or_native_dataframe(X, return_native)


class BaseDatetimeTransformer(BaseGenericDateTransformer):
    """
    Extends BaseTransformer for datetime scenarios

    Parameters
    ----------
    columns : List[str]
        List of 2 columns. First column will be subtracted from second.

    new_column_name : str
        Name for the new year column.

    drop_original : bool
        Flag for whether to drop the original columns.

    **kwargs
        Arbitrary keyword arguments passed onto BaseTransformer.init method.

    Attributes
    ----------

    built_from_json: bool
        indicates if transformer was reconstructed from json, which limits it's supported
        functionality to .transform

    polars_compatible : bool
        class attribute, indicates whether transformer has been converted to polars/pandas agnostic narwhals framework

    jsonable: bool
        class attribute, indicates if transformer supports to/from_json methods

    FITS: bool
        class attribute, indicates whether transform requires fit to be run first

    Example:
    --------
    >>> BaseDatetimeTransformer(
    ... columns=['a',  'b'],
    ... new_column_name='bla',
    ...    )
    BaseDatetimeTransformer(columns=['a', 'b'], new_column_name='bla')
    """

    polars_compatible = True

    FITS = False

    jsonable = False

    def __init__(
        self,
        columns: list[str],
        new_column_name: str | None = None,
        drop_original: bool = False,
        **kwargs: dict[str, bool],
    ) -> None:
        super().__init__(
            columns=columns,
            new_column_name=new_column_name,
            drop_original=drop_original,
            **kwargs,
        )

    @beartype
    def transform(
        self,
        X: DataFrame,
        return_native_override: Optional[bool] = None,
    ) -> DataFrame:
        """base transform method for transformers that operate exclusively on datetime columns

        Parameters
        ----------
        X : pd/pl.DataFrame
            Data containing self.columns

        return_native_override: Optional[bool]
            option to override return_native attr in transformer, useful when calling parent
            methods

        Returns
        -------
        X : pd/pl.DataFrame
            Validated data

        Example:
        --------
        >>> import polars as pl
        >>> import datetime

        >>> transformer=BaseDatetimeTransformer(
        ... columns=["a",  "b"],
        ... new_column_name='bla',
        ...    )

        >>> test_df=pl.DataFrame(
        ... {
        ... "a": [datetime.datetime(1993, 9, 27), datetime.datetime(2005, 10, 7)],
        ... "b": [datetime.datetime(1991, 5, 22), datetime.datetime(2001, 12, 10)]
        ... },
        ... )

        >>> # base transform has no effect on data
        >>> transformer.transform(test_df)
        shape: (2, 2)
        ┌─────────────────────┬─────────────────────┐
        │ a                   ┆ b                   │
        │ ---                 ┆ ---                 │
        │ datetime[μs]        ┆ datetime[μs]        │
        ╞═════════════════════╪═════════════════════╡
        │ 1993-09-27 00:00:00 ┆ 1991-05-22 00:00:00 │
        │ 2005-10-07 00:00:00 ┆ 2001-12-10 00:00:00 │
        └─────────────────────┴─────────────────────┘

        """

        return_native = self._process_return_native(return_native_override)

        X = _convert_dataframe_to_narwhals(X)

        X = super().transform(X, datetime_only=True, return_native_override=False)

        return _return_narwhals_or_native_dataframe(X, return_native)


class BaseDateTwoColumnTransformer(
    TwoColumnMixin,
    BaseGenericDateTransformer,
):
    """Extends BaseDateTransformer for transformers which accept exactly two columns

    Parameters
    ----------
    columns : list
        Either a list of str values or a string giving which columns in a input pandas.DataFrame the transformer
        will be applied to.

    new_column_name : str
        Name for the new year column.

    drop_original : bool
        Flag for whether to drop the original columns.

    **kwargs
        Arbitrary keyword arguments passed onto BaseTransformer.init method.

    Attributes
    ----------

    built_from_json: bool
        indicates if transformer was reconstructed from json, which limits it's supported
        functionality to .transform

    polars_compatible : bool
        class attribute, indicates whether transformer has been converted to polars/pandas agnostic narwhals framework

    jsonable: bool
        class attribute, indicates if transformer supports to/from_json methods

    FITS: bool
        class attribute, indicates whether transform requires fit to be run first

    """

    polars_compatible = True

    FITS = False

    jsonable = False

    def __init__(
        self,
        columns: list[str],
        new_column_name: str | None = None,
        drop_original: bool = False,
        **kwargs: dict[str, bool],
    ) -> None:
        super().__init__(
            columns=columns,
            new_column_name=new_column_name,
            drop_original=drop_original,
            **kwargs,
        )

        self.check_two_columns(columns)


class DateDifferenceTransformer(BaseDateTwoColumnTransformer):
    """Class to transform calculate the difference between 2 date fields in specified units.

    Parameters
    ----------
    columns : List[str]
        List of 2 columns. First column will be subtracted from second.
    new_column_name : str, default = None
        Name given to calculated datediff column. If None then {column_upper}_{column_lower}_datediff_{units}
        will be used.
    units : str, default = 'D'
        Accepted values are "week", "fortnight", "lunar_month", "common_year", "custom_days", 'D', 'h', 'm', 's'
    copy : bool, default = False
        Should X be copied prior to transform? Copy argument no longer used and will be deprecated in a future release
    verbose: bool, default = False
        Control level of detail in printouts
    drop_original:
        Boolean flag indicating whether to drop original columns.
    custom_days_divider:
        Integer value for the "custom_days" unit
    Attributes
    ----------

    built_from_json: bool
        indicates if transformer was reconstructed from json, which limits it's supported
        functionality to .transform

    polars_compatible : bool
        class attribute, indicates whether transformer has been converted to polars/pandas agnostic narwhals framework

    jsonable: bool
        class attribute, indicates if transformer supports to/from_json methods

    FITS: bool
        class attribute, indicates whether transform requires fit to be run first

    Example:
    --------
    >>> DateDifferenceTransformer(
    ... columns=['a',  'b'],
    ... new_column_name='bla',
    ... units='common_year',
    ...    )
    DateDifferenceTransformer(columns=['a', 'b'], new_column_name='bla',
                              units='common_year')
    """

    polars_compatible = True

    FITS = False

    jsonable = False

    def __init__(
        self,
        columns: list[str],
        new_column_name: str | None = None,
        units: Literal[
            "week",
            "fortnight",
            "lunar_month",
            "common_year",
            "custom_days",
            "D",
            "h",
            "m",
            "s",
        ] = "D",
        copy: bool = False,
        verbose: bool = False,
        drop_original: bool = False,
        custom_days_divider: Optional[int] = None,
        **kwargs: dict[str, bool],
    ) -> None:
        accepted_values_units = [
            "week",
            "fortnight",
            "lunar_month",
            "common_year",
            "custom_days",
            "D",
            "h",
            "m",
            "s",
        ]

        if units not in accepted_values_units:
            msg = f"{self.classname()}: units must be one of {accepted_values_units}, got {units}"
            raise ValueError(msg)

        self.units = units
        self.custom_days_divider = custom_days_divider

        super().__init__(
            columns=columns,
            new_column_name=new_column_name,
            drop_original=drop_original,
            copy=copy,
            verbose=verbose,
            **kwargs,
        )

        # This attribute is not for use in any method, use 'columns' instead.
        # Here only as a fix to allow string representation of transformer.
        self.column_lower = columns[0]
        self.column_upper = columns[1]

    @beartype
    def transform(self, X: DataFrame) -> DataFrame:
        """Calculate the difference between the given fields in the specified units.

        Parameters
        ----------
        X : pd/pl.DataFrame
            Data containing self.columns

        Example:
        --------
        >>> import polars as pl
        >>> import datetime

        >>> transformer=DateDifferenceTransformer(
        ... columns=["a",  "b"],
        ... new_column_name='a_b_difference_years',
        ... units='common_year',
        ...    )

        >>> test_df=pl.DataFrame(
        ... {
        ... "a": [datetime.date(1993, 9, 27), datetime.date(2005, 10, 7)],
        ... "b": [datetime.date(1991, 5, 22), datetime.date(2001, 12, 10)]
        ... },
        ... )

        >>> transformer.transform(test_df)
        shape: (2, 3)
        ┌────────────┬────────────┬──────────────────────┐
        │ a          ┆ b          ┆ a_b_difference_years │
        │ ---        ┆ ---        ┆ ---                  │
        │ date       ┆ date       ┆ f64                  │
        ╞════════════╪════════════╪══════════════════════╡
        │ 1993-09-27 ┆ 1991-05-22 ┆ -2.353425            │
        │ 2005-10-07 ┆ 2001-12-10 ┆ -3.827397            │
        └────────────┴────────────┴──────────────────────┘
        """

        X = _convert_dataframe_to_narwhals(X)

        X = super().transform(X, return_native_override=False)

        # mapping for units and corresponding timedelta arg values
        UNITS_TO_TIMEDELTA_PARAMS = {
            "week": (7, "D"),
            "fortnight": (14, "D"),
            "lunar_month": (
                int(29.5 * 24),
                "h",
            ),  # timedelta values need to be whole numbers so (29.5, 'D') cannot be used
            "common_year": (365, "D"),
            "D": (1, "D"),
            "h": (1, "h"),
            "m": (1, "m"),
            "s": (1, "s"),
        }

        # list of units that require time truncation
        UNITS_TO_TRUNCATE_TIME_FOR = [
            "week",
            "fortnight",
            "lunar_month",
            "common_year",
            "custom_days",
            "D",
        ]

        start_date_col = nw.col(self.columns[0])
        end_date_col = nw.col(self.columns[1])

        # truncating time for specific units
        if self.units in UNITS_TO_TRUNCATE_TIME_FOR:
            start_date_col = start_date_col.dt.truncate("1d")
            end_date_col = end_date_col.dt.truncate("1d")

        if self.units == "custom_days":
            timedelta_value, timedelta_format = self.custom_days_divider, "D"
            denominator = np.timedelta64(timedelta_value, timedelta_format)
        else:
            timedelta_value, timedelta_format = UNITS_TO_TIMEDELTA_PARAMS[self.units]
            denominator = np.timedelta64(timedelta_value, timedelta_format)

        X = X.with_columns(
            ((end_date_col - start_date_col) / denominator).alias(self.new_column_name),
        )

        # Drop original columns if self.drop_original is True
        X = DropOriginalMixin.drop_original_column(
            self,
            X,
            self.drop_original,
            self.columns,
            return_native=False,
        )

        return _return_narwhals_or_native_dataframe(X, self.return_native)


class ToDatetimeTransformer(BaseGenericDateTransformer):
    """Class to transform convert specified columns to datetime.

    Class simply uses the pd.to_datetime method on the specified columns.

    Parameters
    ----------
    columns : List[str]
        List of names of the column to convert to datetime.

    time_format: str
        str indicating format of time to parse, e.g. '%d/%m/%Y'

    **kwargs
        Arbitrary keyword arguments passed onto pd.to_datetime().

    Attributes
    ----------

    built_from_json: bool
        indicates if transformer was reconstructed from json, which limits it's supported
        functionality to .transform

    polars_compatible : bool
        class attribute, indicates whether transformer has been converted to polars/pandas agnostic narwhals framework

    jsonable: bool
        class attribute, indicates if transformer supports to/from_json methods

    FITS: bool
        class attribute, indicates whether transform requires fit to be run first

    Example:
    --------
    >>> ToDatetimeTransformer(
    ... columns='a',
    ... time_format='%d/%m/%Y',
    ...    )
    ToDatetimeTransformer(columns=['a'], time_format='%d/%m/%Y')
    """

    polars_compatible = True

    FITS = False

    jsonable = False

    @beartype
    def __init__(
        self,
        columns: Union[str, list[str]],
        time_format: Optional[str] = None,
        **kwargs: dict[str, bool],
    ) -> None:
        if not time_format:
            warnings.warn(
                "time_format arg has not been provided, so datetime format will be inferred",
                stacklevel=2,
            )

        self.time_format = time_format

        super().__init__(
            columns=columns,
            # new_column_name is not actually used
            new_column_name="dummy",
            **kwargs,
        )

    @nw.narwhalify
    def transform(self, X: FrameT) -> FrameT:
        """Convert specified column to datetime using pd.to_datetime.

        Parameters
        ----------
        X : pd/pl.DataFrame
            Data with column to transform.

        Example:
        --------
        >>> import polars as pl

        >>> transformer=ToDatetimeTransformer(
        ... columns='a',
        ... time_format='%d/%m/%Y',
        ...    )

        >>> test_df = pl.DataFrame({'a': ["01/02/2020", "10/12/1996"], 'b': [1,2]})

        >>> transformer.transform(test_df)
        shape: (2, 2)
        ┌─────────────────────┬─────┐
        │ a                   ┆ b   │
        │ ---                 ┆ --- │
        │ datetime[μs]        ┆ i64 │
        ╞═════════════════════╪═════╡
        │ 2020-02-01 00:00:00 ┆ 1   │
        │ 1996-12-10 00:00:00 ┆ 2   │
        └─────────────────────┴─────┘
        """
        # purposely avoid BaseDateTransformer method, as uniquely for this transformer columns
        # are not yet date/datetime
        X = nw.from_native(BaseTransformer.transform(self, X))

        return X.with_columns(
            nw.col(col).str.to_datetime(format=self.time_format) for col in self.columns
        )


class BetweenDatesTransformer(BaseGenericDateTransformer):
    """Transformer to generate a boolean column indicating if one date is between two others.

    If not all column_lower values are less than or equal to column_upper when transform is run
    then a warning will be raised.

    Parameters
    ----------
    columns : list[str]
        List of columns for comparison, in format [lower, to_compare, upper]

    new_column_name : str
        Name for new column to be added to X.

    drop_original: bool
        indicates whether to drop original columns.

    lower_inclusive : bool, defualt = True
        If lower_inclusive is True the comparison to column_lower will be column_lower <=
        column_between, otherwise the comparison will be column_lower < column_between.

    upper_inclusive : bool, defualt = True
        If upper_inclusive is True the comparison to column_upper will be column_between <=
        column_upper, otherwise the comparison will be column_between < column_upper.

    **kwargs
        Arbitrary keyword arguments passed onto BaseTransformer.__init__().

    Attributes
    ----------

    built_from_json: bool
        indicates if transformer was reconstructed from json, which limits it's supported
        functionality to .transform

    column_lower : str
        Name of date column to subtract. This attribute is not for use in any method,
        use 'columns' instead. Here only as a fix to allow string representation of transformer.

    column_upper : str
        Name of date column to subtract from. This attribute is not for use in any method,
        use 'columns instead. Here only as a fix to allow string representation of transformer.

    column_between : str
        Name of column to check if it's values fall between column_lower and column_upper. This attribute
        is not for use in any method, use 'columns instead. Here only as a fix to allow string representation of transformer.

    columns : list
        Contains the names of the columns to compare in the order [column_lower, column_between
        column_upper].

    new_column_name : str
        new_column_name argument passed when initialising the transformer.

    lower_inclusive : bool
        lower_inclusive argument passed when initialising the transformer.

    upper_inclusive : bool
        upper_inclusive argument passed when initialising the transformer.

    drop_original: bool
        indicates whether to drop original columns.

    polars_compatible : bool
        class attribute, indicates whether transformer has been converted to polars/pandas agnostic narwhals framework

    jsonable: bool
        class attribute, indicates if transformer supports to/from_json methods

    FITS: bool
        class attribute, indicates whether transform requires fit to be run first

    Example:
    --------
    >>> BetweenDatesTransformer(
    ... columns=['a', 'b', 'c'],
    ... new_column_name='b_between_a_c',
    ... lower_inclusive=True,
    ... upper_inclusive=True,
    ...    )
    BetweenDatesTransformer(columns=['a', 'b', 'c'],
                            new_column_name='b_between_a_c')
    """

    polars_compatible = True

    FITS = False

    jsonable = False

    def __init__(
        self,
        columns: list[str],
        new_column_name: str,
        drop_original: bool = False,
        lower_inclusive: bool = True,
        upper_inclusive: bool = True,
        **kwargs: dict[str, bool],
    ) -> None:
        if type(lower_inclusive) is not bool:
            msg = f"{self.classname()}: lower_inclusive should be a bool"
            raise TypeError(msg)

        if type(upper_inclusive) is not bool:
            msg = f"{self.classname()}: upper_inclusive should be a bool"
            raise TypeError(msg)

        self.lower_inclusive = lower_inclusive
        self.upper_inclusive = upper_inclusive

        super().__init__(
            columns=columns,
            new_column_name=new_column_name,
            drop_original=drop_original,
            **kwargs,
        )

        if len(columns) != 3:
            msg = f"{self.classname()}: This transformer works with three columns only"
            raise ValueError(msg)

        # This attribute is not for use in any method, use 'columns' instead.
        # Here only as a fix to allow string representation of transformer.
        self.column_lower = columns[0]
        self.column_upper = columns[2]
        self.column_between = columns[2]

    @nw.narwhalify
    def transform(self, X: FrameT) -> FrameT:
        """Transform - creates column indicating if middle date is between the other two.

        If not all column_lower values are less than or equal to column_upper when transform is run
        then a warning will be raised.

        Parameters
        ----------
        X : pd/pl.DataFrame
            Data to transform.

        Returns
        -------
        X : pd/pl.DataFrame
            Input X with additional column (self.new_column_name) added. This column is
            boolean and indicates if the middle column is between the other 2.

        Example:
        --------
        >>> import polars as pl
        >>> import datetime

        >>> transformer = BetweenDatesTransformer(
        ... columns=['a', 'b', 'c'],
        ... new_column_name='b_between_a_c',
        ... lower_inclusive=True,
        ... upper_inclusive=True,
        ...    )

        >>> test_df=pl.DataFrame(
        ... {
        ... "a": [datetime.date(1990, 9, 27), datetime.date(2005, 10, 7)],
        ... "b": [datetime.date(1991, 5, 22), datetime.date(2001, 12, 10)],
        ... "c": [datetime.date(1993, 4, 20), datetime.date(2007, 11, 8)],
        ... },
        ... )

        >>> transformer.transform(test_df)
        shape: (2, 4)
        ┌────────────┬────────────┬────────────┬───────────────┐
        │ a          ┆ b          ┆ c          ┆ b_between_a_c │
        │ ---        ┆ ---        ┆ ---        ┆ ---           │
        │ date       ┆ date       ┆ date       ┆ bool          │
        ╞════════════╪════════════╪════════════╪═══════════════╡
        │ 1990-09-27 ┆ 1991-05-22 ┆ 1993-04-20 ┆ true          │
        │ 2005-10-07 ┆ 2001-12-10 ┆ 2007-11-08 ┆ false         │
        └────────────┴────────────┴────────────┴───────────────┘
        """
        X = nw.from_native(super().transform(X))

        if not (
            X.select((nw.col(self.columns[0]) <= nw.col(self.columns[2])).all()).item()
        ):
            warnings.warn(
                f"{self.classname()}: not all {self.columns[2]} are greater than or equal to {self.columns[0]}",
                stacklevel=2,
            )

        lower_comparison = (
            nw.col(self.columns[0]) <= nw.col(self.columns[1])
            if self.lower_inclusive
            else nw.col(self.columns[0]) < nw.col(self.columns[1])
        )

        upper_comparison = (
            nw.col(self.columns[1]) <= nw.col(self.columns[2])
            if self.upper_inclusive
            else nw.col(self.columns[1]) < nw.col(self.columns[2])
        )

        X = X.with_columns(
            (lower_comparison & upper_comparison).alias(self.new_column_name),
        )

        # Drop original columns if self.drop_original is True
        return DropOriginalMixin.drop_original_column(
            self,
            X,
            self.drop_original,
            self.columns,
        )


class DatetimeInfoOptions(str, Enum):
    __slots__ = ()

    TIME_OF_DAY = "timeofday"
    TIME_OF_MONTH = "timeofmonth"
    TIME_OF_YEAR = "timeofyear"
    DAY_OF_WEEK = "dayofweek"


DatetimeInfoOptionStr = Annotated[
    str,
    Is[lambda s: s in DatetimeInfoOptions._value2member_map_],
]
DatetimeInfoOptionList = Annotated[
    list,
    Is[
        lambda list_value: all(
            entry in DatetimeInfoOptions._value2member_map_ for entry in list_value
        )
    ],
]


class DatetimeInfoExtractor(BaseDatetimeTransformer):
    """Transformer to extract various features from datetime var.

    Parameters
    ----------
    columns : str or list
        datetime columns to extract information from

    include : list of str, default = ["timeofday", "timeofmonth", "timeofyear", "dayofweek"]
        Which datetime categorical information to extract

    datetime_mappings : dict, default = {}
        Optional argument to define custom mappings for datetime values.
        Keys of the dictionary must be contained in `include`.
        All possible values of each feature must be included in the mappings,
        ie, a mapping for `dayofweek` must include all values 1-7;
        datetime_mappings = {
                             "dayofweek": {
                                           **{i: "week" for i in range(1,6)},
                                           **{i: "week" for i in range(6,8)}
                                           }
                            }

        The required ranges for each mapping are:
            timeofday: 0-23
            timeofmonth: 1-31
            timeofyear: 1-12
            dayofweek: 1-7

        If an option is present in 'include' but no mappings are provided,
        then default values from cls.DEFAULT_MAPPINGS will be used for this
        option.

    drop_original: str
        indicates whether to drop provided columns post transform

    **kwargs
        Arbitrary keyword arguments passed onto BaseTransformer.init method.

    Attributes
    ----------
    columns: List[str]
        List of columns for processing

    include : list of str, default = ["timeofday", "timeofmonth", "timeofyear", "dayofweek"]
        Which datetime categorical information to extract

    datetime_mappings : dict, default = None
        Optional argument to define custom mappings for datetime values.

    drop_original: str
        indicates whether to drop provided columns post transform

    built_from_json: bool
        indicates if transformer was reconstructed from json, which limits it's supported
        functionality to .transform

    polars_compatible : bool
        class attribute, indicates whether transformer has been converted to polars/pandas agnostic narwhals framework

    jsonable: bool
        class attribute, indicates if transformer supports to/from_json methods

    FITS: bool
        class attribute, indicates whether transform requires fit to be run first

    Example:
    --------
    >>> DatetimeInfoExtractor(
    ... columns='a',
    ... include='timeofday',
    ...    )
    DatetimeInfoExtractor(columns=['a'], include=['timeofday'])
    """

    polars_compatible = True

    FITS = False

    jsonable = False

    DEFAULT_MAPPINGS: ClassVar[dict[str, dict[int, str]]] = {
        DatetimeInfoOptions.TIME_OF_DAY: {
            **dict.fromkeys(range(6), "night"),  # Midnight - 6am
            **dict.fromkeys(range(6, 12), "morning"),  # 6am - Noon
            **dict.fromkeys(range(12, 18), "afternoon"),  # Noon - 6pm
            **dict.fromkeys(range(18, 24), "evening"),  # 6pm - Midnight
        },
        DatetimeInfoOptions.TIME_OF_MONTH: {
            **dict.fromkeys(range(1, 11), "start"),
            **dict.fromkeys(range(11, 21), "middle"),
            **dict.fromkeys(range(21, 32), "end"),
        },
        DatetimeInfoOptions.TIME_OF_YEAR: {
            **dict.fromkeys(range(3, 6), "spring"),  # Mar, Apr, May
            **dict.fromkeys(range(6, 9), "summer"),  # Jun, Jul, Aug
            **dict.fromkeys(range(9, 12), "autumn"),  # Sep, Oct, Nov
            **dict.fromkeys([12, 1, 2], "winter"),  # Dec, Jan, Feb
        },
        DatetimeInfoOptions.DAY_OF_WEEK: {
            1: "monday",
            2: "tuesday",
            3: "wednesday",
            4: "thursday",
            5: "friday",
            6: "saturday",
            7: "sunday",
        },
    }

    INCLUDE_OPTIONS: ClassVar[list[str]] = list(DEFAULT_MAPPINGS.keys())

    RANGE_TO_MAP: ClassVar[dict[str, set[int]]] = {
        DatetimeInfoOptions.TIME_OF_DAY: set(range(24)),
        DatetimeInfoOptions.TIME_OF_MONTH: set(range(1, 32)),
        DatetimeInfoOptions.TIME_OF_YEAR: set(range(1, 13)),
        DatetimeInfoOptions.DAY_OF_WEEK: set(range(1, 8)),
    }

    DATETIME_ATTR: ClassVar[dict[str, str]] = {
        DatetimeInfoOptions.TIME_OF_DAY: "hour",
        DatetimeInfoOptions.TIME_OF_MONTH: "day",
        DatetimeInfoOptions.TIME_OF_YEAR: "month",
        DatetimeInfoOptions.DAY_OF_WEEK: "weekday",
    }

    @beartype
    def __init__(
        self,
        columns: Union[str, list[str]],
        include: Optional[Union[DatetimeInfoOptionList, DatetimeInfoOptionStr]] = None,
        datetime_mappings: Optional[dict[DatetimeInfoOptionStr, dict[int, str]]] = None,
        drop_original: Optional[bool] = False,
        **kwargs: dict[str, bool],
    ) -> None:
        if include is None:
            include = self.INCLUDE_OPTIONS

        super().__init__(
            columns=columns,
            drop_original=drop_original,
            new_column_name="dummy",
            **kwargs,
        )

        if isinstance(include, str):
            include = [include]

        self.include = include
        self.datetime_mappings = datetime_mappings
        self._process_provided_mappings(datetime_mappings=datetime_mappings)

        # this is a situation where we know the values our mappings allow,
        # so enum type is more appropriate than categorical and we
        # will cast to this at the end
        self.enums = {
            include_option: nw.Enum(
                sorted(set(self.final_datetime_mappings[include_option].values())),
            )
            for include_option in self.include
        }

        self.mapping_transformer = MappingTransformer(
            mappings={
                col + "_" + include_option: self.final_datetime_mappings[include_option]
                for col in self.columns
                for include_option in self.include
            },
            return_dtypes={
                col + "_" + include_option: "Categorical"
                for col in self.columns
                for include_option in self.include
            },
        )

    def _process_provided_mappings(
        self,
        datetime_mappings: Optional[dict[DatetimeInfoOptionStr, dict[int, str]]],
    ) -> None:
        """Method to process user provided mappings. Sets datetime_mappings attribute, then validates against RANGE_TO_MAP.

        Returns
        -------
        None

        Example:
        --------
        >>> transformer = DatetimeInfoExtractor(
        ... columns='a',
        ... include='timeofday',
        ...    )

        >>> transformer._process_provided_mappings(
        ... {
        ... 'timeofday': {
        ... **{i: 'start' for i in range(0,12)},
        ... **{i: 'end' for i in range(12,24)},
        ... }
        ... }
        ... )
        """

        # initialise mappings attr with defaults,
        # and overwrite with user provided mappings
        # where possible
        self.final_datetime_mappings = copy.deepcopy(self.DEFAULT_MAPPINGS)
        if datetime_mappings:
            for key in datetime_mappings:
                if key not in self.include:
                    msg = f"{self.classname()}: keys in datetime_mappings should be in include"
                    raise ValueError(msg)
                self.final_datetime_mappings[key] = copy.deepcopy(
                    datetime_mappings[key],
                )

        for include_option in self.include:
            # check provided mappings fit required format
            if (
                set(self.final_datetime_mappings[include_option].keys())
                != self.RANGE_TO_MAP[include_option]
            ):
                msg = f"{self.classname()}: {include_option.value} mapping dictionary should contain mapping for all values between {min(self.RANGE_TO_MAP[include_option])}-{max(self.RANGE_TO_MAP[include_option])}. {self.RANGE_TO_MAP[include_option] - set(self.final_datetime_mappings[include_option].keys())} are missing"
                raise ValueError(msg)

    @beartype
    def transform(self, X: DataFrame) -> DataFrame:
        """Transform - Extracts new features from datetime variables.

        Parameters
        ----------
        X : pd/pl.DataFrame
            Data with columns to extract info from.

        Returns
        -------
        X : pd/pl.DataFrame
            Transformed input X with added columns of extracted information.

        Example:
        --------
        >>> import polars as pl
        >>> import datetime

        >>> transformer = DatetimeInfoExtractor(
        ... columns='a',
        ... include='timeofmonth',
        ...    )

        >>> test_df=pl.DataFrame(
        ... {
        ... "a": [datetime.datetime(1993, 9, 27), datetime.datetime(2005, 10, 7)],
        ... "b": [datetime.datetime(1991, 5, 22), datetime.datetime(2001, 12, 10)]
        ... },
        ... )

        >>> transformer.transform(test_df)
        shape: (2, 3)
        ┌─────────────────────┬─────────────────────┬───────────────┐
        │ a                   ┆ b                   ┆ a_timeofmonth │
        │ ---                 ┆ ---                 ┆ ---           │
        │ datetime[μs]        ┆ datetime[μs]        ┆ enum          │
        ╞═════════════════════╪═════════════════════╪═══════════════╡
        │ 1993-09-27 00:00:00 ┆ 1991-05-22 00:00:00 ┆ end           │
        │ 2005-10-07 00:00:00 ┆ 2001-12-10 00:00:00 ┆ start         │
        └─────────────────────┴─────────────────────┴───────────────┘
        """
        X = super().transform(X, return_native_override=False)

        transform_dict = {
            col + "_" + include_option: (
                getattr(
                    nw.col(col).dt,
                    self.DATETIME_ATTR[include_option],
                )().replace_strict(
                    self.mapping_transformer.mappings[col + "_" + include_option],
                )
            )
            for col in self.columns
            for include_option in self.include
        }

        # final casts
        transform_dict = {
            col + "_" + include_option: transform_dict[col + "_" + include_option].cast(
                self.enums[include_option],
            )
            for col in self.columns
            for include_option in self.include
        }

        X = X.with_columns(
            **transform_dict,
        )

        # Drop original columns if self.drop_original is True
        X = DropOriginalMixin.drop_original_column(
            self,
            X,
            self.drop_original,
            self.columns,
            return_native=False,
        )

        return _return_narwhals_or_native_dataframe(X, self.return_native)


class DatetimeSinusoidCalculator(BaseDatetimeTransformer):
    """Transformer to derive a feature in a dataframe by calculating the
    sine or cosine of a datetime column in a given unit (e.g hour), with the option to scale
    period of the sine or cosine to match the natural period of the unit (e.g. 24).

    Parameters
    ----------
    columns : str or list
        Columns to take the sine or cosine of. Must be a datetime[64] column.

    method : str or list
        Argument to specify which function is to be calculated. Accepted values are 'sin', 'cos' or a list containing both.

    units : str or dict
        Which time unit the calculation is to be carried out on. Accepted values are 'year', 'month',
        'day', 'hour', 'minute', 'second', 'microsecond'.  Can be a string or a dict containing key-value pairs of column
        name and units to be used for that column.

    period : int, float or dict, default = 2*np.pi
        The period of the output in the units specified above. To leave the period of the sinusoid output as 2 pi, specify 2*np.pi (or leave as default).
        Can be a string or a dict containing key-value pairs of column name and period to be used for that column.

    Attributes
    ----------
    columns : str or list
        Columns to take the sine or cosine of.

    method : str or list
        The function to be calculated; either sin, cos or a list containing both.

    units : str or dict
        Which time unit the calculation is to be carried out on. Will take any of 'year', 'month',
        'day', 'hour', 'minute', 'second', 'microsecond'. Can be a string or a dict containing key-value pairs of column
        name and units to be used for that column.

    period : str, float or dict, default = 2*np.pi
        The period of the output in the units specified above. Can be a string or a dict containing key-value pairs of column
        name and units to be used for that column.

    built_from_json: bool
        indicates if transformer was reconstructed from json, which limits it's supported
        functionality to .transform

    polars_compatible : bool
        class attribute, indicates whether transformer has been converted to polars/pandas agnostic narwhals framework

    jsonable: bool
        class attribute, indicates if transformer supports to/from_json methods

    FITS: bool
        class attribute, indicates whether transform requires fit to be run first

    Example:
    --------
    >>> DatetimeSinusoidCalculator(
    ... columns='a',
    ... method='sin',
    ... units='month',
    ...    )
    DatetimeSinusoidCalculator(columns=['a'], method=['sin'], units='month')
    """

    polars_compatible = True

    FITS = False

    jsonable = False

    def __init__(
        self,
        columns: str | list[str],
        method: str | list[str],
        units: str | dict,
        period: float | dict = 2 * np.pi,
        verbose: bool = False,
        drop_original: bool = False,
    ) -> None:
        super().__init__(
            columns=columns,
            drop_original=drop_original,
            new_column_name="dummy",
            verbose=verbose,
        )

        if not isinstance(method, str) and not isinstance(method, list):
            msg = f"{self.classname()}: method must be a string or list but got {type(method)}"
            raise TypeError(msg)

        if not isinstance(units, str) and not isinstance(units, dict):
            msg = f"{self.classname()}: units must be a string or dict but got {type(units)}"
            raise TypeError(msg)

        if (
            (not isinstance(period, int))
            and (not isinstance(period, float))
            and (not isinstance(period, dict))
        ) or (isinstance(period, bool)):
            msg = f"{self.classname()}: period must be an int, float or dict but got {type(period)}"
            raise TypeError(msg)

        if isinstance(units, dict) and (
            not all(isinstance(item, str) for item in list(units.keys()))
            or not all(isinstance(item, str) for item in list(units.values()))
        ):
            msg = f"{self.classname()}: units dictionary key value pair must be strings but got keys: { ({type(k) for k in units}) } and values: { ({type(v) for v in units.values()}) }"
            raise TypeError(msg)

        if isinstance(period, dict) and (
            not all(isinstance(item, str) for item in list(period.keys()))
            or (
                not all(isinstance(item, int) for item in list(period.values()))
                and not all(isinstance(item, float) for item in list(period.values()))
            )
            or any(isinstance(item, bool) for item in list(period.values()))
        ):
            msg = f"{self.classname()}: period dictionary key value pair must be str:int or str:float but got keys: { ({type(k) for k in period}) } and values: { ({type(v) for v in period.values()}) }"
            raise TypeError(msg)

        valid_method_list = ["sin", "cos"]

        method_list = [method] if isinstance(method, str) else method

        for method in method_list:
            if method not in valid_method_list:
                msg = f'{self.classname()}: Invalid method {method} supplied, should be "sin", "cos" or a list containing both'
                raise ValueError(msg)

        valid_unit_list = [
            "year",
            "month",
            "day",
            "hour",
            "minute",
            "second",
            "microsecond",
        ]

        if isinstance(units, dict):
            if not set(units.values()).issubset(valid_unit_list):
                msg = f"{self.classname()}: units dictionary values must be one of 'year', 'month', 'day', 'hour', 'minute', 'second', 'microsecond' but got {set(units.values())}"
                raise ValueError(msg)
        elif units not in valid_unit_list:
            msg = f"{self.classname()}: Invalid units {units} supplied, should be in {valid_unit_list}"
            raise ValueError(msg)

        self.method = method_list
        self.units = units
        self.period = period

        if isinstance(units, dict) and sorted(units.keys()) != sorted(self.columns):
            msg = f"{self.classname()}: unit dictionary keys must be the same as columns but got {set(units.keys())}"
            raise ValueError(msg)

        if isinstance(period, dict) and sorted(period.keys()) != sorted(self.columns):
            msg = f"{self.classname()}: period dictionary keys must be the same as columns but got {set(period.keys())}"
            raise ValueError(msg)

    @beartype
    def transform(
        self,
        X: DataFrame,
        return_native_override: Optional[bool] = None,
    ) -> DataFrame:
        """Transform - creates column containing sine or cosine of another datetime column.

        Which function is used is stored in the self.method attribute.

        Parameters
        ----------
        X : pd/pl.DataFrame
            Data to transform.

        return_native_override: Optional[bool]
            Option to override return_native attr in transformer, useful when calling parent
            methods

        Returns
        -------
        X : pd/pl.DataFrame
            Input X with additional columns added, these are named "<method>_<original_column>"

        Example:
        --------
        >>> import polars as pl
        >>> import datetime

        >>> transformer = DatetimeSinusoidCalculator(
        ... columns='a',
        ... method='sin',
        ... units='month',
        ...    )

        >>> test_df=pl.DataFrame(
        ... {
        ... "a": [datetime.datetime(1993, 9, 27), datetime.datetime(2005, 10, 7)],
        ... "b": [datetime.datetime(1991, 5, 22), datetime.datetime(2001, 12, 10)]
        ... },
        ... )

        >>> transformer.transform(test_df)
        shape: (2, 3)
        ┌─────────────────────┬─────────────────────┬───────────────────────────────┐
        │ a                   ┆ b                   ┆ sin_6.283185307179586_month_a │
        │ ---                 ┆ ---                 ┆ ---                           │
        │ datetime[μs]        ┆ datetime[μs]        ┆ f64                           │
        ╞═════════════════════╪═════════════════════╪═══════════════════════════════╡
        │ 1993-09-27 00:00:00 ┆ 1991-05-22 00:00:00 ┆ 0.412118                      │
        │ 2005-10-07 00:00:00 ┆ 2001-12-10 00:00:00 ┆ -0.544021                     │
        └─────────────────────┴─────────────────────┴───────────────────────────────┘
        """
        X = _convert_dataframe_to_narwhals(X)
        return_native = self._process_return_native(return_native_override)

        X = super().transform(X, return_native_override=False)

        exprs = {}
        for column in self.columns:
            if not isinstance(self.units, dict):
                desired_units = self.units
            elif isinstance(self.units, dict):
                desired_units = self.units[column]
            if not isinstance(self.period, dict):
                desired_period = self.period
            elif isinstance(self.period, dict):
                desired_period = self.period[column]

            for method in self.method:
                new_column_name = f"{method}_{desired_period}_{desired_units}_{column}"

                # Calculate the sine or cosine of the column in the desired unit
                expr = getattr(
                    nw.col(column).dt,
                    desired_units,
                )() * (2 * np.pi / desired_period)

                expr = (
                    expr.map_batches(
                        lambda s: np.sin(
                            s.to_numpy(),
                        ),
                        return_dtype=nw.Float64,
                    )
                    if method == "sin"
                    else expr.map_batches(
                        lambda s: np.cos(
                            s.to_numpy(),
                        ),
                        return_dtype=nw.Float64,
                    )
                )
                expr = expr.alias(new_column_name)
                exprs[new_column_name] = expr

        X = X.with_columns(**exprs)
        # Drop original columns if self.drop_original is True
        X = DropOriginalMixin.drop_original_column(
            self,
            X,
            self.drop_original,
            self.columns,
            return_native=False,
        )
        return _return_narwhals_or_native_dataframe(X, return_native)


# DEPRECATED TRANSFORMERS


@deprecated(
    "This Transformer is deprecated, use DateDifferenceTransformer instead. "
    "If you prefer this transformer to DateDifferenceTransformer, "
    "let us know through a github issue",
)
class DateDiffLeapYearTransformer(BaseDateTwoColumnTransformer):
    """Transformer to calculate the number of years between two dates.

    !!! warning "Deprecated"
        This transformer is now deprecated; use `DateDifferenceTransformer` instead.

    Parameters
    ----------
    columns : List[str]
        List of 2 columns. First column will be subtracted from second.

    new_column_name : str
        Name for the new year column.

    drop_original : bool
        Flag for whether to drop the original columns.

    missing_replacement : int/float/str
        Value to output if either the lower date value or the upper date value are
        missing. Default value is None.

    **kwargs
        Arbitrary keyword arguments passed onto BaseTransformer.init method.

    Attributes
    ----------
    columns : List[str]
        List of 2 columns. First column will be subtracted from second.

    new_column_name : str, default = None
        Name given to calculated datediff column. If None then {column_upper}_{column_lower}_datediff
        will be used.

    drop_original : bool
        Indicator whether to drop old columns during transform method.

    built_from_json: bool
        indicates if transformer was reconstructed from json, which limits it's supported
        functionality to .transform

    polars_compatible : bool
        class attribute, indicates whether transformer has been converted to polars/pandas agnostic narwhals framework

    jsonable: bool
        class attribute, indicates if transformer supports to/from_json methods

    FITS: bool
        class attribute, indicates whether transform requires fit to be run first

    """

    polars_compatible = True

    FITS = False

    jsonable = False

    def __init__(
        self,
        columns: list[str],
        new_column_name: str | None = None,
        missing_replacement: float | str | None = None,
        drop_original: bool = False,
        **kwargs: dict[str, bool],
    ) -> None:
        super().__init__(
            columns=columns,
            new_column_name=new_column_name,
            drop_original=drop_original,
            **kwargs,
        )

        if (missing_replacement) and (
            type(missing_replacement) not in [int, float, str]
        ):
            msg = f"{self.classname()}: if not None, missing_replacement should be an int, float or string"
            raise TypeError(msg)

        self.missing_replacement = missing_replacement

        # This attribute is not for use in any method, use 'columns' instead.
        # Here only as a fix to allow string representation of transformer.
        self.column_lower = columns[0]
        self.column_upper = columns[1]

    @nw.narwhalify
    def transform(self, X: FrameT) -> FrameT:
        """Calculate year gap between the two provided columns.

        New column is created under the 'new_column_name', and optionally removes the
        old date columns.

        Parameters
        ----------
        X : pd/pl.DataFrame
            Data containing self.columns

        Returns
        -------
        X : pd/pl.DataFrame
            Data containing self.columns

        """

        X = nw.from_native(super().transform(X))

        # Create a helping column col0 for the first date. This will convert the date into an integer in a format or YYYYMMDD
        X = X.with_columns(
            (
                nw.col(self.columns[0]).cast(nw.Date).dt.year().cast(nw.Int64) * 10000
                + nw.col(self.columns[0]).cast(nw.Date).dt.month().cast(nw.Int64) * 100
                + nw.col(self.columns[0]).cast(nw.Date).dt.day().cast(nw.Int64)
            ).alias("col0"),
        )
        # Create a helping column col1 for the second date. This will convert the date into an integer in a format or YYYYMMDD
        X = X.with_columns(
            (
                nw.col(self.columns[1]).cast(nw.Date).dt.year().cast(nw.Int64) * 10000
                + nw.col(self.columns[1]).cast(nw.Date).dt.month().cast(nw.Int64) * 100
                + nw.col(self.columns[1]).cast(nw.Date).dt.day().cast(nw.Int64)
            ).alias("col1"),
        )

        # Compute difference between integers and if the difference is negative then adjust.
        # Finally devide by 10000 to get the years.
        X = X.with_columns(
            nw.when(nw.col("col1") < nw.col("col0"))
            .then(((nw.col("col0") - nw.col("col1")) // 10000) * (-1))
            .otherwise((nw.col("col1") - nw.col("col0")) // 10000)
            .cast(nw.Int64)
            .alias(self.new_column_name),
        ).drop(["col0", "col1"])

        # When we get a missing then replace with missing_replacement otherwise return the above calculation
        if self.missing_replacement is not None:
            X = X.with_columns(
                nw.when(
                    (nw.col(self.columns[0]).is_null())
                    | (nw.col(self.columns[1]).is_null()),
                )
                .then(
                    self.missing_replacement,
                )
                .otherwise(
                    nw.col(self.new_column_name),
                )
                .cast(nw.Int64)
                .alias(self.new_column_name),
            )

        # Drop original columns if self.drop_original is True
        return DropOriginalMixin.drop_original_column(
            self,
            X,
            self.drop_original,
            self.columns,
        )


@deprecated(
    """This transformer has not been selected for conversion to polars/narwhals,
    and so has been deprecated. If aspects of it have been useful to you, please raise an issue
    for it to be replaced with more specific transformers
    """,
)
class SeriesDtMethodTransformer(BaseDatetimeTransformer):
    """Tranformer that applies a pandas.Series.dt method.

    Transformer assigns the output of the method to a new column. It is possible to
    supply other key word arguments to the transform method, which will be passed to the
    pandas.Series.dt method being called.

    Be aware it is possible to supply incompatible arguments to init that will only be
    identified when transform is run. This is because there are many combinations of method, input
    and output sizes. Additionally some methods may only work as expected when called in
    transform with specific key word arguments.

    Parameters
    ----------
    new_column_name : str
        The name of the column to be assigned to the output of running the pandas method in transform.

    pd_method_name : str
        The name of the pandas.Series.dt method to call.

    column : str
        Column to apply the transformer to. If a str is passed this is put into a list. Value passed
        in columns is saved in the columns attribute on the object. Note this has no default value so
        the user has to specify the columns when initialising the transformer. This is avoid likely
        when the user forget to set columns, in this case all columns would be picked up when super
        transform runs.

    pd_method_kwargs : dict, default = {}
        A dictionary of keyword arguments to be passed to the pd.Series.dt method when it is called.

    drop_original: bool
        Indicates whether to drop self.column post transform

    **kwargs
        Arbitrary keyword arguments passed onto BaseTransformer.__init__().

    Attributes
    ----------
    column : str
        Name of column to apply transformer to. This attribute is not for use in any method,
        use 'columns instead. Here only as a fix to allow string representation of transformer.

    columns : str
        Column name for transformation.

    new_column_name : str
        The name of the column or columns to be assigned to the output of running the
        pandas method in transform.

    pd_method_name : str
        The name of the pandas.DataFrame method to call.

    pd_method_kwargs : dict
        Dictionary of keyword arguments to call the pd.Series.dt method with.

    drop_original: bool
        Indicates whether to drop self.column post transform

    built_from_json: bool
        indicates if transformer was reconstructed from json, which limits it's supported
        functionality to .transform

    polars_compatible : bool
        class attribute, indicates whether transformer has been converted to polars/pandas agnostic narwhals framework

    jsonable: bool
        class attribute, indicates if transformer supports to/from_json methods

    FITS: bool
        class attribute, indicates whether transform requires fit to be run first

    """

    polars_compatible = False

    FITS = False

    jsonable = False

    def __init__(
        self,
        new_column_name: str,
        pd_method_name: str,
        columns: list[str],
        pd_method_kwargs: dict[str, object] | None = None,
        drop_original: bool = False,
        **kwargs: dict[str, bool],
    ) -> None:
        super().__init__(
            columns=columns,
            new_column_name=new_column_name,
            drop_original=drop_original,
            **kwargs,
        )

        if len(self.columns) > 1:
            msg = rf"{self.classname()}: column should be a str or list of len 1, got {self.columns}"
            raise ValueError(
                msg,
            )

        if type(pd_method_name) is not str:
            msg = f"{self.classname()}: unexpected type ({type(pd_method_name)}) for pd_method_name, expecting str"
            raise TypeError(msg)

        if pd_method_kwargs is None:
            pd_method_kwargs = {}
        else:
            if type(pd_method_kwargs) is not dict:
                msg = f"{self.classname()}: pd_method_kwargs should be a dict but got type {type(pd_method_kwargs)}"
                raise TypeError(msg)

            for i, k in enumerate(pd_method_kwargs.keys()):
                if type(k) is not str:
                    msg = f"{self.classname()}: unexpected type ({type(k)}) for pd_method_kwargs key in position {i}, must be str"
                    raise TypeError(msg)

        self.pd_method_name = pd_method_name
        self.pd_method_kwargs = pd_method_kwargs

        try:
            ser = pd.Series(
                [datetime.datetime(2020, 12, 21, tzinfo=datetime.timezone.utc)],
            )
            getattr(ser.dt, pd_method_name)

        except Exception as err:
            msg = f'{self.classname()}: error accessing "dt.{pd_method_name}" method on pd.Series object - pd_method_name should be a pd.Series.dt method'
            raise AttributeError(msg) from err

        if callable(getattr(ser.dt, pd_method_name)):
            self._callable = True

        else:
            self._callable = False

        # This attribute is not for use in any method, use 'columns' instead.
        # Here only as a fix to allow string representation of transformer.
        self.column = self.columns[0]

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform specific column on input pandas.DataFrame (X) using the given pandas.Series.dt method and
        assign the output back to column in X.

        Any keyword arguments set in the pd_method_kwargs attribute are passed onto the pd.Series.dt method
        when calling it.

        Parameters
        ----------
        X : pd.DataFrame
            Data to transform.

        Returns
        -------
        X : pd.DataFrame
            Input X with additional column (self.new_column_name) added. These contain the output of
            running the pd.Series.dt method.

        """
        X = super().transform(X)

        if self._callable:
            X[self.new_column_name] = getattr(
                X[self.columns[0]].dt,
                self.pd_method_name,
            )(**self.pd_method_kwargs)

        else:
            X[self.new_column_name] = getattr(
                X[self.columns[0]].dt,
                self.pd_method_name,
            )

        # Drop original columns if self.drop_original is True
        return DropOriginalMixin.drop_original_column(
            self,
            X,
            self.drop_original,
            self.columns,
        )
