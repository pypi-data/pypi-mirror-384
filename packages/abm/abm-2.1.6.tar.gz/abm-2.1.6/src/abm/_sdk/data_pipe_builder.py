from __future__ import annotations

__all__ = ["DataPipeBuilder", "concatenate_columns", "concatenate_rows"]

from abc import abstractmethod
from typing import TYPE_CHECKING

from .expression import Expression, StaticExpression

if TYPE_CHECKING:
    from .data_pipe import ConcatenateColumnsElement, ConcatenateRowsElement, DataPipe


class DataPipeBuilder:
    @abstractmethod
    def to_data_pipe(self):
        raise NotImplementedError()

    def slice0(self, indexes: list[int]) -> DataPipe:
        """Keep rows with the provided zero-based indexes.

        Parameters
        ----------
        indexes : `List[int]`
            Indexes of the rows to keep. First row is 0, like Python.

        Returns
        -------
        `DataPipe`
            A new `DataPipe` containing only the rows specified by the provided
            indices. The original `DataPipe` object is not altered.
        """
        from .data_pipe import Slice0Element

        data_pipe = self.to_data_pipe()
        return Slice0Element(data_pipe, indexes)

    def slice1(self, indexes: list[int]) -> DataPipe:
        """Keep rows with the provided one-based indexes.

        Parameters
        ----------
        indexes : `List[int]`
            Indexes of the rows to keep. First row is 1, like Matlab and R.

        Returns
        -------
        `DataPipe`
            A new `DataPipe` containing only the rows specified by the provided
            indices. The original `DataPipe` object is not altered.
        """
        from .data_pipe import Slice1Element

        data_pipe = self.to_data_pipe()
        return Slice1Element(data_pipe, indexes)

    def filter(self, filter: Expression) -> DataPipe:
        """Keep rows for which the provided expression is true.

        Parameters
        ----------
        filter : `Expression`
            Expression used to filter the rows of the table. Columns are
            referred to by their names.

        Returns
        -------
        `DataPipe`
            A new `DataPipe` containing only the filtered rows. The original
            `DataPipe` object is not altered.
        """
        from .data_pipe import FilterElement

        data_pipe = self.to_data_pipe()
        return FilterElement(data_pipe, filter)

    def sort(self, *columns: str) -> DataPipe:
        """Sort rows based on the provided columns.

        Parameters
        ----------
        *columns : `str`
            Names of columns to use to sort the table. Rows are rearranged based
            on the column names provided. If more than one column name provided,
            the second will be used to break ties for the first and third
            for the second, and so on.

        Returns
        -------
        `DataPipe`
            A new `DataPipe` with rearranged rows bases on the provided columns.
             The original `DataPipe` object is not altered.
        """
        from .data_pipe import SortElement

        data_pipe = self.to_data_pipe()
        return SortElement(data_pipe, list(columns))

    def inner_join(self, other: DataPipe, /, *, by: list[tuple[str, str]] | None = None):
        """Join rows, dropping unmatched rows.

        Parameters
        ----------
        other : `DataPipe`
            The other table to join. Rows on either side that are missing a
            corresponding row on the other side are dropped. Rows on either side
            that have multiple matches on the other side are duplicated.
        by: `List[Tuple[str, str]]` or `None`, default=`None`
            The column pairs that are used to join.

        Returns
        -------
        `DataPipe`
            A new `DataPipe` with columns from both data pipes joined based on the
            provided columns. The original `DataPipe` object is not altered.
        """
        from .data_pipe import InnerJoinElement

        data_pipe = self.to_data_pipe()
        other_data_pipe = other.to_data_pipe()
        return InnerJoinElement(data_pipe, other_data_pipe, by)

    def distinct(self, *columns: str) -> DataPipe:
        """Keep rows with unique combinations of values across the indicated
        columns.

        Parameters
        ----------
        *columns : `str`
            Names of columns to use to filter the table. Rows are kept that have
            the first occurrence of each unique combination of values in these
            columns.
        """
        from .data_pipe import DistinctElement

        data_pipe = self.to_data_pipe()
        return DistinctElement(data_pipe, list(columns))

    def unique(self) -> DataPipe:
        """Keep rows with unique combinations of values across all columns."""
        from .data_pipe import UniqueElement

        data_pipe = self.to_data_pipe()
        return UniqueElement(data_pipe)

    def select(self, *columns: str) -> DataPipe:
        """Keep columns that have the indicated names.

        Parameters
        ----------
        *columns : `str`
            Names of columns to keep.
        """
        from .data_pipe import SelectElement

        data_pipe = self.to_data_pipe()
        return SelectElement(data_pipe, list(columns))

    def deselect(self, *columns: str) -> DataPipe:
        """Remove columns that have the indicated names.

        Parameters
        ----------
        *columns : `str`
            Names of columns to remove.
        """
        from .data_pipe import DeselectElement

        data_pipe = self.to_data_pipe()
        return DeselectElement(data_pipe, list(columns))

    def rename(self, **columns: str) -> DataPipe:
        """Rename columns.

        Parameters
        ----------
        **columns : `str`
            Keywords are the new column names, and the values are the old column
            names. For example, `rename(dose_mg = "dose")` would rename the
            "dose" column to "dose_mg".
        """
        from .data_pipe import RenameElement

        data_pipe = self.to_data_pipe()
        return RenameElement(data_pipe, columns)

    def mutate(self, **columns: Expression) -> DataPipe:
        """Add new columns derived from other columns.

        Parameters
        ----------
        **columns : `Expression`
            Keywords are the names of the new columns to create, and the values
            are the expressions that determine the new columns' values. For
            example, `mutate(new = "old*2")` would create a column named "new"
            that is equal to column "old" times 2. Scalar values are assigned to
            all rows. Later new columns can refer to earlier new columns.
        """
        from .data_pipe import MutateElement

        data_pipe = self.to_data_pipe()
        return MutateElement(data_pipe, columns)

    def transmute(self, **columns: Expression) -> DataPipe:
        """Create new columns from other columns, discarding all old columns.

        Parameters
        ----------
        **columns : `Expression`
            Keywords are the names of the new columns to create, and the values
            are the expressions that determine the new columns' values. For
            example, `transmute(new = "old*2")` would create a column named
            "new" that is equal to column "old" times 2. Later new columns can
            refer to earlier new columns and old columns are not removed until
            all the new columns' expressions have been evaluated. Scalar values
            are assigned to all rows.
        """
        from .data_pipe import TransmuteElement

        data_pipe = self.to_data_pipe()
        return TransmuteElement(data_pipe, columns)

    def group_by(self, *groupers: str) -> DataPipe:
        """Group by the indicated columns in preparation for `.summarize`.

        Note that `.group_by` does not change the content of the table. It only
        changes the internal representation of the table, impacting which
        columns are treated as group variables in a subsequent call to
        `.summarize`.

        Parameters
        ----------
        *groupers : `str`
            Columns used to determine the groups. Each unique combination of
            values among the indicated columns will define a group.

        `.group_by` can be called more than once to add multiple group levels to
        the table.

        See Also
        --------
        .summarize: Calculate values per group.
        """
        from .data_pipe import GroupByElement

        data_pipe = self.to_data_pipe()
        return GroupByElement(data_pipe, list(groupers))

    def ungroup(self) -> DataPipe:
        """Remove one level of grouping."""
        from .data_pipe import UngroupElement

        data_pipe = self.to_data_pipe()
        return UngroupElement(data_pipe)

    def summarize(self, **columns: Expression) -> DataPipe:
        """Calculate values per group.

        Parameters
        ----------
        **columns : `Expression`
            Keywords are the names of the new columns, and the values are the
            expressions used to calculate the new columns. The expressions
            must evaluate to a scalar value. The resulting table will have one
            row per group and will have the group columns and the specified
            keyword columns.
        """
        from .data_pipe import SummarizeElement

        data_pipe = self.to_data_pipe()
        return SummarizeElement(data_pipe, columns)

    def gather(self, key: str, value: str, *columns: str, unit: str | None = None) -> DataPipe:
        """Reshape a wide table into a tall table.

        Parameters
        ----------
        key : `str`
            The name of the new column indicating which of the `*columns`
            was the source of each value.
        value : `str`
            The name of the new column containing the values from
            `*columns`.
        *columns : `str`
            Columns to reshape. Columns not in `*columns` are copied instead of
            reshaped.
        """
        from .data_pipe import GatherElement

        data_pipe = self.to_data_pipe()
        return GatherElement(data_pipe, key, value, list(columns), unit=unit)

    def spread(self, key: str, value: str, *, fill: StaticExpression | None = None) -> DataPipe:
        """Reshape a tall table into a wide table.

        Parameters
        ----------
        key : `str`
            The name of the column that contains the names of the new columns.
        value : `str`
            The name of the column containing the values that will be stored
            in the new columns.
        fill : `StaticExpression`, default=`None`
            Rows and columns with no value specified by the input table will be
            filled by the value provided in `fill`. If `None`, an exception
            will be raised if any values are not specified.

        In the output table, the "other" columns (those not named in `key` or
        `value`) contain the unique combinations of values found in the input
        table. The input table's `value` column values are placed in the output
        table row with the matching values in the "other" columns. If more than
        one value is assigned to the same row and column, an exception is
        raised.
        """
        from .data_pipe import SpreadElement

        data_pipe = self.to_data_pipe()
        return SpreadElement(data_pipe, key, value, fill)


def concatenate_rows(*tables: DataPipeBuilder) -> ConcatenateRowsElement:
    """Vertically concatenate rows of tables.

    Parameters
    ----------
    *tables
        Tables to concatenate.
    """
    from .data_pipe import ConcatenateRowsElement

    data_pipes = [table.to_data_pipe() for table in tables]
    return ConcatenateRowsElement(data_pipes)


def concatenate_columns(*tables: DataPipeBuilder) -> ConcatenateColumnsElement:
    """Horizontally concatenate columns of tables.

    Parameters
    ----------
    *tables
        Tables to concatenate.
    """
    from .data_pipe import ConcatenateColumnsElement

    data_pipes = [table.to_data_pipe() for table in tables]
    return ConcatenateColumnsElement(data_pipes)
