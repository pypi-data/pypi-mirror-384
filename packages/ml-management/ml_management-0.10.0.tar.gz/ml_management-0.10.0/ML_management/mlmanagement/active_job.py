import traceback
from typing import Literal, Optional, Union

from sgqlc.operation import Operation

from ML_management import variables
from ML_management.graphql import schema
from ML_management.graphql.schema import ExecutionJob, JobCodeParams, JobParams
from ML_management.graphql.send_graphql_request import send_graphql_request
from ML_management.mlmanagement.batcher import Batcher
from ML_management.mlmanagement.metric_autostepper import MetricAutostepper
from ML_management.mlmanagement.visibility_options import VisibilityOptions
from ML_management.types.execution_job_type import ExecutionJobType
from ML_management.variables import DEFAULT_EXPERIMENT


class ActiveJob:
    """
    A context manager that allows for the execution of a task locally.

    This class provides a convenient way to run a job locally.

    """

    _job_type_map = {ExecutionJobType.CODE: JobCodeParams, ExecutionJobType.MLM: JobParams}

    def __init__(self, secret_uuid, job_type=ExecutionJobType.MLM):
        self.secret_uuid = secret_uuid
        self.job_type = job_type
        self.job = self._start()
        self.__is_distributed = self.job.params.is_distributed if self.job.params else False

    def __enter__(self) -> "ActiveJob":
        return self

    def _start(self) -> ExecutionJob:
        op = Operation(schema.Mutation)
        base_query = op.start_job(secret_uuid=self.secret_uuid)
        base_query.name()
        base_query.id()
        base_query.experiment.name()
        params = base_query.params().__as__(self._job_type_map[self.job_type])
        params.resources.gpu_number()
        params.is_distributed()
        if self.job_type == ExecutionJobType.MLM:
            _query_job_params(params)
        elif self.job_type == ExecutionJobType.CODE:
            params.bash_commands()
        job = send_graphql_request(op=op, json_response=False).start_job
        variables.secret_uuid = self.secret_uuid
        variables.active_job = True
        return job

    def __exit__(self, exc_type, exc_val, exc_tb):
        variables.active_job = False
        if self.__is_distributed:
            Batcher().wait_log_metrics()
            return
        exception_traceback = None
        message = None
        status = "SUCCESSFUL"
        if exc_type:
            exception_traceback = traceback.format_exc()
            message = ": ".join([exc_type.__name__, str(exc_val)])
            status = "FAILED"
        return stop_job(status, message, exception_traceback)


def start_job(
    job_name: Optional[str] = None,
    experiment_name: str = DEFAULT_EXPERIMENT,
    visibility: Union[Literal["private", "public"], VisibilityOptions] = VisibilityOptions.PRIVATE,
) -> ActiveJob:
    """
    Create local job.

    Usage::

        with start_job('my-beautiful-job') as job:
            mlmanagement.log_metric(...)
            mlmanagement.log_artifacts(...)


    Or::

        start_job('my-beautiful-job')
        mlmanagement.log_metric(...)
        mlmanagement.log_artifacts(...)
        stop_job()


    Parameters
    ----------
    job_name: str | None=None
        Name of the new job. If not passed, it will be generated.
    experiment_name: str = "Default"
        Name of the experiment. Default: "Default"
    visibility: Union[Literal['private', 'public'], VisibilityOptions]
        Visibility of this job to other users. Default: PRIVATE.

    Returns
    -------
    ActiveJob
        Active job.
    """
    visibility = VisibilityOptions(visibility)
    op = Operation(schema.Mutation)
    op.create_local_job(job_name=job_name, experiment_name=experiment_name, visibility=visibility.name)
    secret_uuid = send_graphql_request(op=op, json_response=False).create_local_job
    return ActiveJob(secret_uuid)


def stop_job(
    status: Literal["SUCCESSFUL", "FAILED"] = "SUCCESSFUL",
    message: Optional[str] = None,
    exception_traceback: Optional[str] = None,
) -> None:
    """
    Stop local job.

    Parameters
    ----------
    status: Literal["SUCCESSFUL", "FAILED"] = "SUCCESSFUL"
        Status of the job. If not passed, it will be SUCCESSFUL.
    message: Optional[str] = None
        Extra message for the job. Default: None
    exception_traceback: Optional[str] = None
        Error traceback of the job. Default: None

    Returns
    -------
    None
    """
    Batcher().wait_log_metrics()
    op = Operation(schema.Mutation)
    op.stop_job(
        secret_uuid=variables.get_secret_uuid(), status=status, message=message, exception_traceback=exception_traceback
    )
    try:
        _ = send_graphql_request(op=op, json_response=False).stop_job
    finally:
        variables.secret_uuid = None
        MetricAutostepper().clear()


def _query_job_params(params):
    params.list_role_model_params()
    params.list_role_data_params()
    params.list_role_data_params.data_params()
    params.list_role_data_params.role()
    params.list_role_model_params.model_params()
    params.list_role_model_params.upload_params()
    params.list_role_model_params.role()
    params.executor_params()
    params.executor_params.executor_method_params()
    params.executor_params.executor_version_choice()
