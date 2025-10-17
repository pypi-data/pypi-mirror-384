from __future__ import annotations

__all__ = ["Client"]

import importlib.metadata
import json
import os
import sys
import tomllib
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from itertools import batched, chain
from pathlib import Path
from types import NoneType
from typing import Generator

import httpx
import pandas as pd
from IPython.display import HTML, Pretty, display
from serialite import DeserializationFailure, serializable, serializer

from .._helper.display import Display
from .assess import (
    AssessParameterScan1D,
    AssessParameterScan1DResult,
    AssessParameterScan2D,
    AssessParameterScan2DResult,
    AssessSimulation,
    AssessSimulationResult,
)
from .contract import Contract
from .data_frame import DataFrame
from .data_pipe import DataPipe
from .distribution_sample import DistributionSample
from .job import Job, JobDefinition, JobDescriptor, JobOutput, JobTypes
from .ode_fisher_information_matrix import OdeFisherInformationMatrix
from .ode_gradient import OdeGradient
from .ode_measurement_likelihood_sample import OdeMeasurementLikelihoodSample
from .ode_model import OdeModel, OdeModelFromText, OdeModelTypes
from .ode_optimization import OdeOptimization
from .ode_optimization_batch import OdeOptimizationBatch
from .ode_optimization_result import OdeOptimizationResult, UnittedValue
from .ode_parameter_posterior_sample import OdeParameterPosteriorSample
from .ode_prediction import OdePrediction, ScenarioPredictions
from .ode_proposal_population_sample import OdeProposalPopulationSample
from .ode_residual import OdeResidual, ScenarioResiduals
from .ode_residual_batch import OdeResidualBatch
from .ode_simulation import OdeSimulation
from .ode_simulation_batch import OdeSimulationBatch
from .ode_value import OdeValue, OdeValueResult
from .ode_virtual_population_sample import OdeVirtualPopulationSample
from .progress import DisplayJobProgressOptimization
from .qsp_designer_model import QspDesignerModel, QspDesignerModelFromBytes
from .scenario import Scenario
from .time_course import TimeCourse
from .to_latex_ode_model import ToLatexOdeModel
from .to_matlab_ode_simulation import ToMatlabOdeSimulation
from .to_simbiology_ode_simulation import ToSimbiologyOdeSimulation

global_config_path = Path("/etc/abm/client.toml")
user_config_path = Path(os.getenv("XDG_CONFIG_HOME", "~/.config")).joinpath("abm/client.toml").expanduser()


@serializable
@dataclass(frozen=True)
class ClientConfiguration:
    api_origin: str
    auth_token_path: Path | None = None


def load_configuration() -> ClientConfiguration:
    if global_config_path.exists():
        config_path = global_config_path
    elif user_config_path.exists():
        config_path = user_config_path
    else:
        raise RuntimeError(
            "Expected ./abm/client.toml configuration file at /etc/ or $XDG_CONFIG_HOME "
            "or ~/.config/, but no configuration file was found."
        )

    configuration_data = tomllib.loads(config_path.read_text(encoding="utf-8"))

    maybe_configuration = ClientConfiguration.from_data(configuration_data)

    if isinstance(maybe_configuration, DeserializationFailure):
        raise RuntimeError(f"In configuration file {config_path}\n{maybe_configuration.error}")

    return maybe_configuration.or_die()


def raise_for_http_status(response: httpx.Response) -> None:
    if response.status_code >= 400:
        try:
            # Try to turn the response into a nice message
            response.read()
            data = response.json()
            if isinstance(data, str):
                error_text = data
            elif isinstance(data, dict) and "exception" in data:
                error_text = "".join(data["exception"]["traceback"])
            else:
                error_text = json.dumps(data, indent=2)
        except json.JSONDecodeError:
            # Otherwise, just dump the text
            error_text = response.text

        raise ClientError(error_text, response=response)


class ClientError(Exception):
    def __init__(self, text, response=None):
        super().__init__(text)
        self.text = text
        self.response = response


class Client:
    def __init__(self, host: str | None = None, root: str = "/api/v1"):
        self.configuration = load_configuration()
        self.httpx_client = httpx.Client(
            timeout=300,
            event_hooks={"request": [self.add_jwt_to_request], "response": [raise_for_http_status]},
            base_url=(host if host is not None else self.configuration.api_origin) + root,
        )
        self.thread_pool = ThreadPoolExecutor(max_workers=8)  # TODO: figure out a way to calculate the ideal number

        self.job_descriptors: dict[str, JobDescriptor[JobDefinition, JobOutput, JobTypes]] = {
            "assess-legacy-parameter-scan-1d": JobDescriptor[AssessParameterScan1D, AssessParameterScan1DResult, None](
                definition=AssessParameterScan1D,
                output=AssessParameterScan1DResult,
            ),
            "assess-legacy-parameter-scan-2d": JobDescriptor[AssessParameterScan2D, AssessParameterScan2DResult, None](
                definition=AssessParameterScan2D,
                output=AssessParameterScan2DResult,
            ),
            "assess-legacy-simulation": JobDescriptor[AssessSimulation, AssessSimulationResult, None](
                definition=AssessSimulation,
                output=AssessSimulationResult,
            ),
            "data-frame": JobDescriptor[DataFrame, None, None](
                definition=DataFrame,
                output=serializer(NoneType),
            ),
            "data-pipe": JobDescriptor[DataPipe, DataFrame, None](
                definition=DataPipe,
                output=DataFrame,
            ),
            "distribution-sample": JobDescriptor[DistributionSample, DataFrame, None](
                definition=DistributionSample,
                output=DataFrame,
            ),
            "ode-fisher-information-matrix": JobDescriptor[
                OdeFisherInformationMatrix, dict[str, dict[str, UnittedValue]], None
            ](
                definition=OdeFisherInformationMatrix,
                output=serializer(dict[str, dict[str, UnittedValue]]),
            ),
            "ode-gradient": JobDescriptor[OdeGradient, dict[str, UnittedValue], None](
                definition=OdeGradient,
                output=serializer(dict[str, UnittedValue]),
            ),
            "ode-measurement-likelihood-sample": JobDescriptor[OdeMeasurementLikelihoodSample, Scenario, None](
                definition=OdeMeasurementLikelihoodSample,
                output=Scenario,
            ),
            "ode-model": JobDescriptor[OdeModel, None, OdeModelTypes](
                definition=OdeModel,
                output=serializer(NoneType),
                types=OdeModelTypes,
            ),
            "ode-model-from-text": JobDescriptor[OdeModelFromText, OdeModel, None](
                definition=OdeModelFromText,
                output=OdeModel,
            ),
            "ode-optimization": JobDescriptor[OdeOptimization, OdeOptimizationResult, None](
                definition=OdeOptimization,
                output=OdeOptimizationResult,
                display_job_progress=DisplayJobProgressOptimization,
            ),
            "ode-optimization-batch": JobDescriptor[OdeOptimizationBatch, list[str], None](
                definition=OdeOptimizationBatch,
                output=serializer(list[str]),
            ),
            "ode-parameter-posterior-sample": JobDescriptor[OdeParameterPosteriorSample, DataFrame, None](
                definition=OdeParameterPosteriorSample,
                output=DataFrame,
            ),
            "ode-prediction": JobDescriptor[OdePrediction, ScenarioPredictions, None](
                definition=OdePrediction,
                output=ScenarioPredictions,
            ),
            "ode-proposal-population-sample": JobDescriptor[OdeProposalPopulationSample, DataFrame, None](
                definition=OdeProposalPopulationSample,
                output=DataFrame,
            ),
            "ode-residual": JobDescriptor[OdeResidual, ScenarioResiduals, None](
                definition=OdeResidual,
                output=ScenarioResiduals,
            ),
            "ode-residual-batch": JobDescriptor[OdeResidualBatch, list[str], None](
                definition=OdeResidualBatch,
                output=serializer(list[str]),
            ),
            "ode-simulation": JobDescriptor[OdeSimulation, TimeCourse, None](
                definition=OdeSimulation,
                output=TimeCourse,
            ),
            "ode-simulation-batch": JobDescriptor[OdeSimulationBatch, list[str], None](
                definition=OdeSimulationBatch,
                output=serializer(list[str]),
            ),
            "ode-value": JobDescriptor[OdeValue, OdeValueResult, None](
                definition=OdeValue,
                output=OdeValueResult,
            ),
            "ode-virtual-population-sample": JobDescriptor[OdeVirtualPopulationSample, DataFrame, None](
                definition=OdeVirtualPopulationSample,
                output=DataFrame,
            ),
            "qsp-designer-model-from-bytes": JobDescriptor[QspDesignerModelFromBytes, QspDesignerModel, None](
                definition=QspDesignerModelFromBytes,
                output=QspDesignerModel,
            ),
            "to-latex-ode-model": JobDescriptor[ToLatexOdeModel, str, None](
                definition=ToLatexOdeModel,
                output=serializer(str),
            ),
            "to-matlab-ode-simulation": JobDescriptor[ToMatlabOdeSimulation, str, None](
                definition=ToMatlabOdeSimulation,
                output=serializer(str),
            ),
            "to-simbiology-ode-simulation": JobDescriptor[ToSimbiologyOdeSimulation, str, None](
                definition=ToSimbiologyOdeSimulation,
                output=serializer(str),
            ),
        }
        for task_name, descriptor in self.job_descriptors.items():
            descriptor.definition._task_name = task_name

    def add_jwt_to_request(self, request: httpx.Request) -> None:
        # h11, used by httpx, doesn't allow trailing spaces in HTTP headers, such as "Bearer ". So, instead of returning
        # an empty string if there isn't a token available, we return a string that will fail auth on the server when
        # auth is enabled.
        if self.configuration.auth_token_path is None:
            jwt = "not_a_real_token"
        elif self.configuration.auth_token_path.exists():
            jwt = self.configuration.auth_token_path.read_text().strip()
        else:
            # Better hope this is a dev machine with auth turned off
            jwt = "not_a_real_token"
        request.headers.update({"Authorization": f"Bearer {jwt}"})

    def client_version(self) -> str:
        """Get the version of the client.

        Returns
        `str`: e.g. "0.1.0"
        """
        return importlib.metadata.version("abm")

    def server_version(self) -> str:
        """Get the version of the server.

        Returns
        `str`: e.g. "0.1.0"
        """
        response = self.httpx_client.get("/version/").json()
        return response["version"]

    def create_jobs(
        self,
        definitions: list[JobDefinition],
        *,
        deduplicate: bool = True,
        include_types: bool = False,
    ) -> list[Job]:
        def create(definitions: list[JobDefinition]) -> list[Job]:
            jobs = []
            for definition in definitions:
                task_name = definition._task_name
                descriptor = self.job_descriptors[task_name]
                payload = {
                    "definition": descriptor.definition.to_data(definition),
                    "deduplicate": deduplicate,
                    "task_name": task_name,
                }
                params = {"include_types": include_types}
                response = self.httpx_client.post("/jobs/", json=payload, params=params).json()
                job = Job(**response)

                if include_types:
                    descriptor = self.job_descriptors[job.task_name]
                    if descriptor.types is not None:
                        types = descriptor.types.from_data(job.types).or_die()
                        object.__setattr__(job, "types", types)

                jobs.append(job)
            return jobs

        batches = batched(definitions, self.thread_pool._max_workers)
        return list(chain.from_iterable(self.thread_pool.map(create, batches)))

    def create_contract(
        self,
        jobs: list[Job],
        *,
        interval: float = 5.0,
        progress: bool = False,
        timeout: float = 3600,
        wait: bool = True,
    ) -> Contract:
        if progress:
            contract_progress = Display()
            if len(jobs) == 1:
                job = jobs[0]
                descriptor = self.job_descriptors[job.task_name]
                job_progress = descriptor.display_job_progress(job)

        if not wait:
            interval = 0

        # Limit interval to 4 minutes since our infrastructure supports opened HTTP connections for up to 5 minutes.
        interval = min(4 * 60, interval)

        payload = {"job_ids": [job.id for job in jobs], "timeout": timeout}
        response = self.httpx_client.post("/contracts/", json=payload, params={"wait": interval}).json()
        contract = Contract(**response)

        if wait:
            try:
                while not contract.fulfilled and not contract.deleted:
                    if progress:
                        contract_progress.display(Pretty(contract.progress()))
                        if len(jobs) == 1:
                            job_progress.display()
                    contract = contract.refresh(interval=interval, wait=wait)
            except KeyboardInterrupt:
                warning_message = """
                    <div style=padding: 10px; margin: 10px 0;">
                        <h3 style="margin: 0;">Warning: Jobs Stopped</h3>
                        <p style="margin: 10px 0 0 0;">Your jobs submitted by this Notebook cell were stopped because
                            you stopped your Notebook kernel.</p>
                    </div>
                """
                display(HTML(warning_message))
                contract.stop()
                sys.exit("KeyboardInterrupt: Execution stopped.")

        if progress:
            contract_progress.display(Pretty(contract.progress()))
            if len(jobs) == 1:
                job_progress.display()

        if contract.deleted:
            raise RuntimeError(
                f"Your jobs were stopped because the contract {contract.id} was cancelled. This can happen in two situations:\n"
                "1. The contract was manually cancelled by the user.\n"
                f"2. The contract was automatically cancelled because the contract's timeout of {timeout} seconds was reached."
            )

        return contract

    def list_contracts(
        self,
        users: list[str] | None = None,
        deleted: bool = False,
        fulfilled: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> Contracts:
        """List contracts by status and user.

        Parameters
        ----------
        users : `list[str]` or None, default=None
            List of users to filter contracts by.
            If the special value `["*"]` is passed, all users are included.
            If an empty list is passed or None, only contracts for the current user are included.

            Deprecation: passing a list of users will be ignored and only contracts for the current user will be
            included. The special value `["*"]` is still supported.
        deleted : `bool`, default=False
            Whether to include deleted contracts.
        fulfilled : `bool`, default=False
            Whether to include fulfilled contracts. Fulfillment happens when all jobs in a contract have finished,
            either successfully or not.
        offset : `int`, default=0
            Offset into list of returned contracts, skips the first `offset` records in list.
        limit : `int`, default=100
            Maximum number of contracts returned.

        Returns
        -------
        `Contracts`: e.g. `contracts = list_contracts().to_pandas()` or `display(list_contracts())`
        """
        params = {
            "deleted": deleted,
            "fulfilled": fulfilled,
            "offset": offset,
            "limit": limit,
        }
        if users is None:
            params["user_filter"] = json.dumps([])
        else:
            params["user_filter"] = json.dumps(users)

        response = self.httpx_client.get("/contracts/", params=params).json()
        return Contracts(contracts=[Contract(**contract) for contract in response])


@dataclass(frozen=True, kw_only=True, slots=True)
class Contracts:
    contracts: list[Contract]

    def __iter__(self) -> Generator[Contract, None, None]:
        return iter(self.contracts)

    def __len__(self) -> int:
        return len(self.contracts)

    def __str__(self) -> str:
        return str(self.to_pandas())

    def _repr_html_(self) -> str:
        return self.to_pandas()._repr_html_()

    def to_pandas(self) -> pd.DataFrame:
        return pd.DataFrame.from_dict(self.contracts)

    def stop(self) -> None:
        for contract in self.contracts:
            contract.stop()
