from __future__ import annotations

from dataclasses import dataclass

import tabeline as tl


@dataclass
class LabelSet:
    """A set of labels that can be used to filter a DataFrame.
    The main reason for this class is to standardize the labels as strings

    Attributes:
    __________
    labels: dict[str, str | float | int | bool]
    original_labels: dict[str, str | float | int | bool] | None = None
        Preserve the original labels for returning later
    columns

    """

    labels: dict[str, str | float | int | bool]
    original_labels: dict[str, str | float | int | bool]

    def __init__(
        self,
        labels: dict[str, str | float | int | bool],
        original_labels: dict[str, str | float | int | bool] | None,
    ):
        """Standardize labels as strings"""

        # Copy the label dict into the original values
        object.__setattr__(self, "labels", labels)
        if original_labels is None:
            object.__setattr__(self, "original_labels", self.labels.copy())
        else:
            object.__setattr__(self, "original_labels", original_labels)

        # remove Nones from the labels
        none_labels = [k for k, v in self.labels.items() if v is None]
        for k in none_labels:
            del self.labels[k]

        # Standardize labels as strings
        for key, value in self.labels.items():
            match value:
                case int():
                    self.labels[key] = str(value)
                case float():
                    self.labels[key] = f"{value:.6g}"
                case str():
                    try:
                        value_float = float(value)
                        self.labels[key] = f"{value_float:.6g}"
                    except ValueError:
                        self.labels[key] = value
                case _:
                    raise ValueError(f"Invalid type for label {key}: {type(value)}")

    @staticmethod
    def from_df(df: tl.DataFrame) -> list[LabelSet]:
        """Create a list of LabelSet objects from a DataFrame of labels."""

        if df.width == 0:
            records = [{}] * df.height
        else:
            height = df.height
            records = [df[i, :].to_dict() for i in range(height)]
        return [LabelSet(record, record) for record in records]

    @property
    def columns(self) -> list[str]:
        """Labels in the LabelSet"""

        return list(self.labels.keys())
