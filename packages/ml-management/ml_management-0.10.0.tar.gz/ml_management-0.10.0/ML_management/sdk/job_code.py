import os
from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel
from sgqlc.operation import Operation

from ML_management.graphql import schema
from ML_management.graphql.schema import EnvParamInput
from ML_management.graphql.send_graphql_request import send_graphql_request
from ML_management.mlmanagement.log_api import _open_pipe_send_request, _raise_error
from ML_management.mlmanagement.utils import calculate_hash_directory, hash_file
from ML_management.mlmanagement.visibility_options import VisibilityOptions
from ML_management.sdk.parameters import ResourcesForm
from ML_management.variables import DEFAULT_EXPERIMENT, get_log_service_url


class CodeMetaInfo(BaseModel):
    code_id: int
    experiment_name: str


def _get_code_hash(hash_code: str, visibility: VisibilityOptions) -> Optional[int]:
    op = Operation(schema.Query)
    op.get_code_with_hash(hash_code=hash_code, visibility=visibility.name)

    result = send_graphql_request(op=op, json_response=False)
    return result.get_code_with_hash


def add_custom_code_job(
    local_path: str,
    bash_commands: List[str],
    job_name: Optional[str] = None,
    env_variables: Optional[Dict[str, str]] = None,
    resources: Optional[ResourcesForm] = None,
    is_distributed: bool = False,
    experiment_name: Optional[str] = DEFAULT_EXPERIMENT,
    visibility: Union[Literal["private", "public"], VisibilityOptions] = VisibilityOptions.PRIVATE,
    additional_system_packages: Optional[List[str]] = None,
    verbose: bool = True,
):
    """
    Create execution job from arbitrary code.

    The job created by this function can be executed on an arbitrary number of nodes greater than or equal to 1.
    The computing cluster distributes all resources equally among the allocated nodes.
    If such an equal distribution is not possible, the job will be rejected.

    Parameters
    ----------
    local_path: str
    bash_commands: List[str]
    is_distributed: bool = False

    resources: ResourcesForm
        Resources required for job execution.
        They will be allocated on one node, if it is not possible, job will be rejected.
    experiment_name: str = "Default"
        Name of the experiment. Default: "Default"
    job_name: Optional[str] = None
        Name of the created job.
    visibility: Union[Literal['private', 'public'], VisibilityOptions]
        Visibility of this job to other users. Default: PRIVATE.
    additional_system_packages: Optional[List[str]] = None
        List of system libraries for Debian family distributions that need to be installed in the job. Default: None
    env_variables: Optional[Dict[str, str]] = None
        Environment variables that will be set before starting the job.
    verbose: bool = True
        Whether to disable the entire progressbar wrapper.

    Returns
    -------
    ExecutionJob
        Instance of the Job class.
    """
    visibility = VisibilityOptions(visibility)
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Path: {local_path} does not exist.")
    log_request = {}
    if experiment_name:
        log_request = {"visibility": visibility, "experiment_name": experiment_name}

    hash_code = calculate_hash_directory(local_path) if os.path.isdir(local_path) else hash_file(local_path)
    code_id = _get_code_hash(hash_code, visibility)

    if code_id is None:
        log_request["hash_code"] = hash_code
        response = _open_pipe_send_request(
            local_path, log_request, url=get_log_service_url("log_job_code"), verbose=verbose
        )
        _raise_error(response)
        result = response.json()
        info = CodeMetaInfo.model_validate(result)
        experiment_name = info.experiment_name
        code_id = info.code_id

    if resources is None:
        resources = ResourcesForm()
    resources = schema.ResourcesInput(
        cpus=resources.cpus,
        memory_per_node=resources.memory_per_node,
        gpu_number=resources.gpu_number,
        gpu_type=resources.gpu_type,
    )
    op = Operation(schema.Mutation)
    mutation = op.add_custom_code_job(
        form=schema.JobCodeParameters(
            code_id=code_id,
            bash_commands=bash_commands,
            experiment_name=experiment_name,
            visibility=VisibilityOptions(visibility).name,
            additional_system_packages=additional_system_packages,
            job_name=job_name,
            resources=resources,
            is_distributed=is_distributed,
            env_variables=[EnvParamInput(key=key, value=value) for key, value in env_variables.items()]
            if env_variables
            else None,
        )
    )

    mutation.name()
    mutation.id()

    job = send_graphql_request(op, json_response=False)

    return job.add_custom_code_job
