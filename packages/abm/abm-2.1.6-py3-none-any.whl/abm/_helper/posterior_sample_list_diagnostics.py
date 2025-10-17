from typing import Literal

import numpy as np

from .._sdk.data_frame import DataFrame
from .._sdk.job import Job
from .._sdk.status import Status


def divergences(
    samples: list[Job[DataFrame, None]],
    *,
    on_failure: Literal["error", "fill_nan"] = "error",
) -> list[float]:
    divergences = []
    for sample in samples:
        sample = sample.refresh()
        match sample.status:
            case Status.succeeded:
                divergences.append(sample.progress()[0]["n_divergence"])
            case Status.failed if on_failure == "fill_nan":
                divergences.append(np.NaN)
            case Status.failed if on_failure == "error":
                sample.output_or_raise()
            case Status.submitted:
                raise RuntimeError("Waited for sample to finish but its status is still submitted.")

    return divergences
