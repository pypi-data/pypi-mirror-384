__all__ = ["ToLatexOdeModel"]

from dataclasses import dataclass
from pathlib import Path

from serialite import serializable

from .ode_model_reference import OdeModelReference


@serializable
@dataclass(frozen=True, kw_only=True)
class ToLatexOdeModel:
    """Object for creating a LateX script for a model.

    Attributes
    ----------
    model : `OdeModelReference`
        The `OdeModelReference` to be exported to LaTeX. The `OdeModelReference` specifies the
        model and any parameter or route schedule changes to the model.
    inlined : `bool`
        Specifies if the right hand side of the equations are inlined. Default is False
    name_map: `dict[str, str] | None`
        A dictionary where the keys are parameter, assignment, or state names from the model
        and the values are the preferred name in LaTeX format.
        for example {'v_central': 'v_{c}', 'SECONDS_PER_MINUTE': r'\frac{sec}{min}'}
    """

    model: OdeModelReference
    inlined: bool = False
    name_map: dict[str, str] | None = None


def to_latex(
    path: str | Path,
    model: OdeModelReference,
    inlined: bool = False,
    name_map: dict[str, str] | None = None,
) -> None:
    from . import client

    if isinstance(path, str):
        path = Path(path)

    to_latex_ode_model = ToLatexOdeModel(model=model, inlined=inlined, name_map=name_map)

    jobs = client.create_jobs([to_latex_ode_model])
    client.create_contract(jobs)
    output = jobs[0].output_or_raise()

    parent_dir = path.parent
    parent_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(output, encoding="utf-8")
