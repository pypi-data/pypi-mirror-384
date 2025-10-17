from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from functools import cached_property, singledispatch
from math import isnan

import numpy as np
import tabeline as tl

from ._helper.parameter import Parameter, ScanParameter
from ._sdk.expression import Unit


@dataclass(frozen=True)
class FilledScan:
    name: str
    value: float
    float: float
    unit: str


@dataclass(frozen=True)
class Scan:
    def __add__(self, other):
        if not isinstance(other, Scan):
            return NotImplemented
        return AddScan(self, other)

    def __or__(self, other):
        if not isinstance(other, Scan):
            return NotImplemented
        if len(self.list) != len(other.list):
            raise ValueError(f"Cannot zip scans of different length but got {len(self)} and {len(other)}")
        return ZipScan(self, other)

    def __mul__(self, other):
        if not isinstance(other, Scan):
            return NotImplemented
        return ProductScan(self, other)

    # ToDo: Implement __repr__ for all subclasses of Scan
    def __repr__(self):
        return self.__repr__(self)

    def __len__(self):
        return len(self.list)

    def evaluate(self, values: dict[str, Parameter]) -> list[dict[str, ScanParameter]]:
        return evaluate(self, values)

    @cached_property
    def list(self) -> list[list[Scan]]:
        return scans_to_list(self)

    @cached_property
    def table(self) -> tl.DataFrame:
        return scans_to_df(self.list)

    @cached_property
    def parameters(self) -> list[str]:
        return set(self.table[:, "parameter"])

    @cached_property
    # ToDo: this code (and also PSF v1) fails for cases like this:
    # scans = (value_scan(V_L=[0.1, 0.2]) * value_scan(kon_nMs=[1, 2, 3])) + value_scan(Kd_nM=[0.1, 0.2])
    # The reason is the product part of the scan comes with two scan parameters and then the addition part comes with
    # only one scan parameter. Polars cannot create this table with the following error:
    # exceptions.ShapeError: could not create a new dataframe: series "param_scan_0" has length 8 while series
    # "param_scan_1" has length 6
    def label_columns(self) -> tl.DataFrame:
        df = self.table.group_by("scan_id").mutate(par_no="row_index0()").ungroup()
        param_nums = df[:, "par_no"]
        param_names = df[:, "parameter"]
        param_values = df[:, "value"]
        param_folds = df[:, "fold"]
        new_column_map = defaultdict(list)
        for pi, pn, pv, pf in zip(param_nums, param_names, param_values, param_folds, strict=True):
            new_column_map[f"param_scan_{pi}"].append(f"{pn}")
            new_column_map[f"scan_{pi}_value"].append(pv)
            new_column_map[f"scan_{pi}_fold"].append(pf)
            if isnan(pf):
                new_column_map[f"scan_{pi}_type"].append("value")
            else:
                new_column_map[f"scan_{pi}_type"].append("fold")

        return tl.DataFrame(**new_column_map)


@dataclass(frozen=True, slots=True)
class NoScan(Scan):
    pass


@dataclass(frozen=True, slots=True)
class ValueScan(Scan):
    name: str
    value: float
    unit: Unit | None = None


@dataclass(frozen=True, slots=True)
class FoldScan(Scan):
    name: str
    fold: float


@dataclass(frozen=True, slots=True)
class AddScan(Scan):
    left: Scan
    right: Scan


@dataclass(frozen=True, slots=True)
class ZipScan(Scan):
    left: Scan
    right: Scan


@dataclass(frozen=True, slots=True)
class ProductScan(Scan):
    left: Scan
    right: Scan


@singledispatch
def evaluate(self: Scan, values: dict[str, Parameter]) -> list[dict[str, ScanParameter]]:
    raise NotImplementedError(f"evaluate not implemented for type {type(self).__name__}")


@evaluate.register(NoScan)
def evaluate_empty_scan(self: NoScan, values: dict[str, Parameter]) -> list[dict[str, ScanParameter]]:
    return [{}]


@evaluate.register(ValueScan)
def evaluate_value_scan(self: ValueScan, values: dict[str, Parameter]) -> list[dict[str, ScanParameter]]:
    return [{self.name: ScanParameter(value=self.value, unit=self.unit, fold=self.value / values[self.name].value)}]


@evaluate.register(FoldScan)
def evaluate_fold_scan(self: FoldScan, values: dict[str, Parameter]) -> list[dict[str, ScanParameter]]:
    return [
        {
            self.name: ScanParameter(
                value=self.fold * values[self.name].value, unit=values[self.name].unit, fold=self.fold
            )
        }
    ]


@evaluate.register(AddScan)
def evaluate_add_scans(self: AddScan, values: dict[str, Parameter]) -> list[dict[str, ScanParameter]]:
    ev_left = evaluate(self.left, values)
    ev_right = evaluate(self.right, values)

    return ev_left + ev_right


@evaluate.register(ZipScan)
def evaluate_zip_scans(self: ZipScan, values: dict[str, int | float]) -> list[dict[str, ScanParameter]]:
    ev_left = evaluate(self.left, values)
    ev_right = evaluate(self.right, values)

    return [left | right for left, right in zip(ev_left, ev_right, strict=True)]


@evaluate.register(ProductScan)
def evaluate_product_scans(self: ProductScan, values: dict[str, int | float]) -> list[dict[str, ScanParameter]]:
    ev_left = evaluate(self.left, values)
    ev_right = evaluate(self.right, values)

    return [left | right for left in ev_left for right in ev_right]


@singledispatch
def scans_to_list(self: Scan) -> list[list[ValueScan | FoldScan]]:
    raise NotImplementedError(f"scans_to_list not implemented for type {type(self).__name__}")


@scans_to_list.register(NoScan)
def scans_to_list_empty_scan(self: NoScan) -> list:
    return [[]]


@scans_to_list.register(ValueScan)
def scans_to_list_value_scan(self: ValueScan) -> list[list[ValueScan]]:
    return [[self]]


@scans_to_list.register(FoldScan)
def scans_to_list_fold_scan(self: FoldScan) -> list[list[FoldScan]]:
    return [[self]]


@scans_to_list.register(AddScan)
def scans_to_list_add_scans(self: AddScan) -> list[list[ValueScan | FoldScan]]:
    list_left = scans_to_list(self.left)
    list_right = scans_to_list(self.right)

    return list_left + list_right


@scans_to_list.register(ZipScan)
def scans_to_list_zip_scans(self: ZipScan) -> list[list[ValueScan | FoldScan]]:
    list_left = scans_to_list(self.left)
    list_right = scans_to_list(self.right)

    if len(list_left) != len(list_right):
        raise ValueError(
            f"Cannot make list of zipscans of different length but got {len(list_left)} and {len(list_right)}"
        )

    return [[*left, *right] for left, right in zip(list_left, list_right, strict=True)]


@scans_to_list.register(ProductScan)
def scans_to_list_product_scans(self: ProductScan) -> list[list[ValueScan | FoldScan]]:
    list_left = scans_to_list(self.left)
    list_right = scans_to_list(self.right)

    return [[*left, *right] for left in list_left for right in list_right]


def scans_to_df(
    scans: list[Scan],
    index: int | None = None,
) -> tl.DataFrame:
    table: tl.DataFrame = tl.DataFrame(
        scan_id=np.ndarray(0, dtype=int),
        parameter=np.ndarray(0, dtype=str),
        value=np.ndarray(0, dtype=float),
        fold=np.ndarray(0, dtype=float),
        unit=np.ndarray(0, dtype=str),
    )
    for i, scan in enumerate(scans):
        if index is None:
            scan_id = i
        else:
            scan_id = index
        if isinstance(scan, ValueScan):
            table = tl.concatenate_rows(
                table,
                tl.DataFrame(
                    scan_id=[scan_id],
                    parameter=[scan.name],
                    value=float(scan.value),
                    fold=[np.nan],
                    unit=[scan.unit if scan.unit is not None else "1"],
                ),
            )
        elif isinstance(scan, FoldScan):
            table = tl.concatenate_rows(
                table,
                tl.DataFrame(
                    scan_id=[scan_id], parameter=[scan.name], value=[np.nan], fold=[float(scan.fold)], unit=[""]
                ),
            )
        else:
            table = tl.concatenate_rows(table, scans_to_df(scan, i))
    return table
