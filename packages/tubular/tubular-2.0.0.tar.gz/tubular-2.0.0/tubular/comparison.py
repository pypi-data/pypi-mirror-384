from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import deprecated

from tubular.base import BaseTransformer
from tubular.mixins import DropOriginalMixin, NewColumnNameMixin, TwoColumnMixin

if TYPE_CHECKING:
    import pandas as pd


# DEPRECATED TRANSFORMERS
@deprecated(
    """This transformer has not been selected for conversion to polars/narwhals,
    and so has been deprecated. If it is useful to you, please raise an issue
    for it to be modernised
    """,
)
class EqualityChecker(
    DropOriginalMixin,
    NewColumnNameMixin,
    TwoColumnMixin,
    BaseTransformer,
):
    """Transformer to check if two columns are equal.

    Parameters
    ----------
    columns: list
        List containing names of the two columns to check.

    new_column_name: string
        string containing the name of the new column.

    drop_original: boolean = False
        boolean representing dropping the input columns from X after checks.

    **kwargs:
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

    polars_compatible = False

    FITS = False

    jsonable = False

    def __init__(
        self,
        columns: list,
        new_column_name: str,
        drop_original: bool = False,
        **kwargs: dict[str, bool],
    ) -> None:
        super().__init__(columns=columns, **kwargs)

        self.check_two_columns(columns)
        self.set_drop_original_column(drop_original)
        self.check_and_set_new_column_name(new_column_name)

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Create a column which is populated by the boolean
        matching between two columns iterated over rows.

        Parameters
        ----------
        X : pd.DataFrame
            Data to apply mappings to.

        Returns
        -------
        X : pd.DataFrame
            Transformed input X with additional boolean column.

        """
        X = super().transform(X)

        X[self.new_column_name] = X[self.columns[0]] == X[self.columns[1]]

        # Drop original columns if self.drop_original is True
        return DropOriginalMixin.drop_original_column(
            self,
            X,
            self.drop_original,
            self.columns,
        )
