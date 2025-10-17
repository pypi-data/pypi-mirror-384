__all__ = ["get_model_types_i", "get_models", "get_remote_model"]

from base64 import b64encode
from pathlib import Path
from typing import Sequence, cast

import pandas as pd
import tabeline as tl

from .._sdk import client
from .._sdk.exceptions import JobRuntimeError
from .._sdk.job import Job
from .._sdk.ode_model import OdeModelFromText, OdeModelTypes
from .._sdk.qsp_designer_model import QspDesignerModel, QspDesignerModelFromBytes
from .get_table import get_table
from .helper import DataFrameLike, PathLike


def get_models(model: DataFrameLike | PathLike) -> tl.DataFrame:
    match model:
        case str() | Path():
            models_path = Path(model)
            if not models_path.is_file():
                raise FileNotFoundError(f"{models_path} is not a file")

            if models_path.suffix == ".csv":
                return get_table(models_path)
            else:
                return get_table(pd.DataFrame(columns=["model"], data=[str(models_path)]))
        case tl.DataFrame() | pd.DataFrame():
            return get_table(model)
        case _:
            raise NotImplementedError(f"{type(model).__name__} is not a supported type for models")


def _get_remote_qsp_designer_model(path: Path, imports: dict[Path, str] = {}) -> Job[None, OdeModelTypes]:
    base64_content = b64encode(path.read_bytes()).decode("utf-8")
    definition = QspDesignerModelFromBytes(base64_content=base64_content, imports=imports)
    job = client.create_jobs([definition])[0]
    _ = client.create_contract(jobs=[job], wait=True)
    job: Job[QspDesignerModel, None] = job.refresh(include_output=True)
    try:
        model = job.output_or_raise()
    except JobRuntimeError as error:
        match error._type:
            case "MissingImportsError":
                pass
            case _:
                raise

        match error.payload:
            case {"missing_paths": missing_paths}:
                pass
            case _:
                raise

        # Look for the missing imports in the parent directory of path
        new_imports: dict[Path, str] = {}
        for dependency in cast(Sequence[str], missing_paths):
            job = _get_remote_qsp_designer_model(path.parent / dependency)
            new_imports[Path(dependency)] = job.id

        # All imports should be satisfied now.  Resubmit the model with them.
        new_definition = QspDesignerModelFromBytes(base64_content=base64_content, imports=new_imports)
        new_job = client.create_jobs([new_definition])[0]
        _ = client.create_contract(jobs=[new_job], wait=True)
        new_job: Job[QspDesignerModel, None] = new_job.refresh(include_output=True)
        model = new_job.output_or_raise()

    return model.store()


def get_remote_model(path: PathLike) -> Job[None, OdeModelTypes]:
    path = Path(path)
    match path.suffix:
        case ".txt" | ".model":
            return OdeModelFromText(text=path.read_text(encoding="utf-8"), format="reaction").parse().store()
        case ".sbml":
            return OdeModelFromText(text=path.read_text(encoding="utf-8"), format="sbml").parse().store()
        case ".qsp" | ".iqd":
            return _get_remote_qsp_designer_model(path)
        case _:
            raise NotImplementedError(f"File extension {path.suffix} is not supported")


def get_model_types_i(
    models: list[dict],
    model_map: dict[str, Job[None, OdeModelTypes]],
    labels: dict[str, str | float | int | bool],
) -> tuple[str, OdeModelTypes]:
    unique_models = {value["model"] for dictionary in models for value in dictionary.values()}

    # make sure that there is only one model for each simulation
    if len(models) > 1:
        if len(labels) == 0:
            raise ValueError(
                f"Multiple models found while there is no simulation table: {', '.join(sorted(unique_models))}"
            )
        else:
            raise ValueError(
                f"Multiple models found for label(s) {', '.join([f'{key}={value}' for key, value in labels.items()])}:"
                f" {', '.join(sorted(unique_models))}"
            )

    model_path = next(iter(models[0].values()))["model"]
    model = model_map[model_path]
    return model.id, model.types
