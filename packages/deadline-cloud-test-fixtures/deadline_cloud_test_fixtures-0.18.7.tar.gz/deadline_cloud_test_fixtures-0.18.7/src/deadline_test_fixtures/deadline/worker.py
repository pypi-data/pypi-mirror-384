# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
from __future__ import annotations

import abc
import botocore.client
import botocore.exceptions
import glob
import json
import logging
import os
import pathlib
import posixpath
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field, InitVar, replace
from typing import TYPE_CHECKING, Any, ClassVar, Optional, cast, Dict

from ..models import (
    PipInstall,
    PosixSessionUser,
)
from .resources import CloudWatchLogEvent, Fleet, WorkerLog
from ..util import call_api, wait_for, retry_with_predicate, is_instance_not_ready

if TYPE_CHECKING:
    from botocore.paginate import PageIterator, Paginator

LOG = logging.getLogger(__name__)

DOCKER_CONTEXT_DIR = os.path.join(os.path.dirname(__file__), "..", "containers", "worker")

DEFAULT_WAITER_CONFIG = {
    "Delay": 5,
    "MaxAttempts": 30,
}


@dataclass
class Ec2Tag:
    key: str
    value: str


class DeadlineWorker(abc.ABC):
    @abc.abstractmethod
    def start(self) -> None:
        pass

    @abc.abstractmethod
    def stop(self) -> None:
        pass

    @abc.abstractmethod
    def send_command(self, command: str) -> CommandResult:
        pass

    @abc.abstractmethod
    def get_worker_id(self) -> str:
        pass


@dataclass(frozen=True)
class WorkerLogConfig:
    cloudwatch_log_group: str
    """The name of the CloudWatch Log Group that the Agent log should be streamed to"""

    cloudwatch_log_stream: str
    """The name of the CloudWatch Log Stream that the Agent log should be streamed to"""


@dataclass(frozen=True)
class CommandResult:  # pragma: no cover
    exit_code: int
    stdout: str
    stderr: Optional[str] = None

    def __str__(self) -> str:
        return "\n".join(
            [
                f"exit_code: {self.exit_code}",
                "",
                "================================",
                "========= BEGIN stdout =========",
                "================================",
                "",
                self.stdout,
                "",
                "==============================",
                "========= END stdout =========",
                "==============================",
                "",
                "================================",
                "========= BEGIN stderr =========",
                "================================",
                "",
                str(self.stderr),
                "",
                "==============================",
                "========= END stderr =========",
                "==============================",
            ]
        )


class InstanceStartupError(Exception):
    """Custom exception for instance startup failures with diagnostics."""

    def __init__(self, message, diagnostics=None):
        self.message = message
        self.diagnostics = diagnostics

        # Format a more visually distinct error message with the diagnostics
        error_msg = [
            f"{message}",
            "=" * 80,  # Separator line
            "DIAGNOSTICS",
            "=" * 80,  # Separator line
        ]

        if diagnostics:
            error_msg.append(str(diagnostics))
        else:
            error_msg.append("No diagnostics available")

        error_msg.append("=" * 80)  # Separator line

        super().__init__("\n".join(error_msg))


@dataclass(frozen=True)
class DeadlineWorkerConfiguration:
    farm_id: str
    fleet: Fleet
    region: str
    allow_shutdown: bool
    worker_agent_install: PipInstall
    start_service: bool = True
    no_install_service: bool = False
    service_model_path: str | None = None
    no_local_session_logs: str | None = None
    disallow_instance_profile: str | None = None

    file_mappings: list[tuple[str, str]] | None = None
    """Mapping of files to copy from host environment to worker environment"""

    pre_install_commands: list[str] | None = None
    """Commands to run before installing the Worker agent"""

    job_user: str = field(default="job-user")
    agent_user: str = field(default="deadline-worker")
    windows_user_secret: str | None = None
    job_user_group: str = field(default="deadline-job-users")

    job_users: list[PosixSessionUser] = field(
        default_factory=lambda: [PosixSessionUser("job-user", "job-user")]
    )
    """Additional job users to configure for Posix workers"""

    windows_job_users: list = field(default_factory=lambda: ["job-user"])
    """Additional job users to configure for Windows workers"""

    session_root_dir: str | None = None
    """Path to parent directory of worker session directories"""

    worker_env_var: Dict[str, str] | None = None
    """Additional feature flag to configure for workers"""


@dataclass
class EC2InstanceWorker(DeadlineWorker):

    subnet_id: str
    security_group_id: str
    instance_profile_name: str
    bootstrap_bucket_name: str
    s3_client: botocore.client.BaseClient
    ec2_client: botocore.client.BaseClient
    ssm_client: botocore.client.BaseClient
    deadline_client: botocore.client.BaseClient
    configuration: DeadlineWorkerConfiguration

    instance_type: str
    instance_shutdown_behavior: str

    additional_tags: list[Ec2Tag] = field(default_factory=list)

    instance_id: Optional[str] = field(init=False, default=None)
    worker_id: Optional[str] = field(init=False, default=None)

    """
    Option to override the AMI ID for the EC2 instance. If no override is provided, the default will depend on the subclass being instansiated. 
    """
    override_ami_id: InitVar[Optional[str]] = None

    def __post_init__(self, override_ami_id: Optional[str] = None):
        if override_ami_id:
            self._ami_id = override_ami_id

    @abc.abstractmethod
    def ami_ssm_param_name(self) -> str:
        raise NotImplementedError("'ami_ssm_param_name' was not implemented.")

    @abc.abstractmethod
    def ssm_document_name(self) -> str:
        raise NotImplementedError("'ssm_document_name' was not implemented.")

    @abc.abstractmethod
    def _setup_worker_agent(self) -> None:  # pragma: no cover
        raise NotImplementedError("'_setup_worker_agent' was not implemented.")

    @abc.abstractmethod
    def configure_worker_command(
        self, *, config: DeadlineWorkerConfiguration
    ) -> str:  # pragma: no cover
        raise NotImplementedError("'configure_worker_command' was not implemented.")

    @abc.abstractmethod
    def start_worker_service(self) -> None:  # pragma: no cover
        raise NotImplementedError("'_start_worker_service' was not implemented.")

    @abc.abstractmethod
    def stop_worker_service(self) -> None:  # pragma: no cover
        raise NotImplementedError("'_stop_worker_service' was not implemented.")

    @abc.abstractmethod
    def get_worker_id(self) -> str:
        raise NotImplementedError("'get_worker_id' was not implemented.")

    @abc.abstractmethod
    def userdata(self, s3_files) -> str:
        raise NotImplementedError("'userdata' was not implemented.")

    @abc.abstractmethod
    def ebs_devices(self) -> dict[str, int] | None:
        """DeviceName -> VolumeSize (in GiBs) mapping"""
        raise NotImplementedError("'ebs_devices' was not implemented.")

    def start(self) -> None:
        s3_files = self._stage_s3_bucket()
        self._launch_instance(s3_files=s3_files)
        self._setup_worker_agent()

    def stop(self) -> None:
        LOG.info(f"Terminating EC2 instance {self.instance_id}")
        self.ec2_client.terminate_instances(InstanceIds=[self.instance_id])

        self.instance_id = None

        # Only attempt worker-related cleanup if worker_id exists
        if not self.worker_id:
            LOG.info("No worker_id available, skipping worker cleanup")
            return

        if not self.configuration.fleet.autoscaling:
            try:
                self.wait_until_stopped()
            except TimeoutError:
                LOG.warning(
                    f"{self.worker_id} did not transition to a STOPPED status, forcibly stopping..."
                )
                self.set_stopped_status()

            try:
                self.delete()
            except botocore.exceptions.ClientError as error:
                LOG.exception(f"Failed to delete worker: {error}")
                raise

    def delete(self):
        try:
            self.deadline_client.delete_worker(
                farmId=self.configuration.farm_id,
                fleetId=self.configuration.fleet.id,
                workerId=self.worker_id,
            )
            LOG.info(f"{self.worker_id} has been deleted from {self.configuration.fleet.id}")
        except botocore.exceptions.ClientError as error:
            LOG.exception(f"Failed to delete worker: {error}")
            raise

    def wait_until_stopped(
        self, *, max_checks: int = 25, seconds_between_checks: float = 5
    ) -> None:
        self.wait_until_desired_worker_status(
            max_checks=max_checks,
            seconds_between_checks=seconds_between_checks,
            desired_status="STOPPED",
        )

    def wait_until_desired_worker_status(
        self,
        *,
        max_checks: int = 25,
        seconds_between_checks: float = 5,
        desired_status: str = "STOPPED",
    ) -> None:
        for _ in range(max_checks):
            response = self.deadline_client.get_worker(
                farmId=self.configuration.farm_id,
                fleetId=self.configuration.fleet.id,
                workerId=self.worker_id,
            )
            if response["status"] == desired_status:
                LOG.info(f"{self.worker_id} is {desired_status}")
                break
            time.sleep(seconds_between_checks)
            LOG.info(f"Waiting for {self.worker_id} to transition to {desired_status} status")
        else:
            raise TimeoutError

    def set_stopped_status(self):
        LOG.info(f"Setting {self.worker_id} to STOPPED status")
        try:
            self.deadline_client.update_worker(
                farmId=self.configuration.farm_id,
                fleetId=self.configuration.fleet.id,
                workerId=self.worker_id,
                status="STOPPED",
            )
        except botocore.exceptions.ClientError as error:
            LOG.exception(f"Failed to update worker status: {error}")
            raise

    def _get_worker_logs(self) -> Optional[WorkerLogConfig]:
        """Get the log group and log stream for the worker. Retain the API structure"""
        response = self.deadline_client.get_worker(
            farmId=self.configuration.farm_id,
            fleetId=self.configuration.fleet.id,
            workerId=self.worker_id,
        )
        if log_config := response.get("log"):
            LOG.info(f"Log Config structure {log_config}")
            if log_config_options := log_config.get("options"):
                log_group_name = log_config_options.get("logGroupName")
                log_stream_name = log_config_options.get("logStreamName")
                if log_group_name and log_stream_name:
                    return WorkerLogConfig(
                        cloudwatch_log_group=log_group_name, cloudwatch_log_stream=log_stream_name
                    )
        # Default, no log config yet.
        return None

    def get_logs(self, *, logs_client: botocore.client.BaseClient) -> WorkerLog:
        # Get the worker log group and stream from the service.
        log_config: Optional[WorkerLogConfig] = self._get_worker_logs()
        if not log_config:
            return WorkerLog(worker_id=self.worker_id, logs=[])  # type: ignore[arg-type]

        filter_log_events_paginator: Paginator = logs_client.get_paginator("filter_log_events")
        filter_log_events_pages: PageIterator = call_api(
            description=f"Fetching log events for worker {self.worker_id} in log group {log_config.cloudwatch_log_group}",
            fn=lambda: filter_log_events_paginator.paginate(
                logGroupName=log_config.cloudwatch_log_group,
                logStreamNames=[log_config.cloudwatch_log_stream],
            ),
        )
        log_events = filter_log_events_pages.build_full_result()
        log_events = [CloudWatchLogEvent.from_api_response(e) for e in log_events["events"]]
        # For debugging test cases.
        # LOG.info(log_events)

        return WorkerLog(worker_id=self.worker_id, logs=log_events)  # type: ignore[arg-type]

    @retry_with_predicate(
        max_attempts=3, predicate=lambda e: isinstance(e, botocore.exceptions.WaiterError)
    )
    @retry_with_predicate(max_attempts=60, delay=10, backoff=1, predicate=is_instance_not_ready)
    def send_command(
        self, command: str, ssm_waiter_config: dict[str, int] = DEFAULT_WAITER_CONFIG
    ) -> CommandResult:
        """Send a command via SSM to a shell on a launched EC2 instance. Once the command has fully
        finished the result of the invocation is returned.
        """
        ssm_waiter = self.ssm_client.get_waiter("command_executed")

        # To successfully send an SSM Command to an instance the instance must:
        #  1) Be in RUNNING state;
        #  2) Have the AWS Systems Manager (SSM) Agent running; and
        #  3) Have had enough time for the SSM Agent to connect to System's Manager
        #
        # If we send an SSM command then we will get an InvalidInstanceId error
        # if the instance isn't in that state.

        LOG.info(f"Sending SSM command to instance {self.instance_id}")
        try:
            send_command_response = self.ssm_client.send_command(
                InstanceIds=[self.instance_id],
                DocumentName=self.ssm_document_name(),
                Parameters={"commands": [command]},
            )
        except botocore.exceptions.ClientError as error:
            if error.response["Error"]["Code"] == "InvalidInstanceId":
                LOG.warning(
                    f"Instance {self.instance_id} is not ready for SSM command (received InvalidInstanceId error)."
                )
            raise

        command_id = send_command_response["Command"]["CommandId"]

        LOG.info(f"Waiting for SSM command {command_id} to reach a terminal state")
        try:
            ssm_waiter.wait(
                InstanceId=self.instance_id,
                CommandId=command_id,
                WaiterConfig=ssm_waiter_config,
            )
        except botocore.exceptions.WaiterError as e:  # pragma: no cover
            LOG.warning(f"WaiterError caught for command {command_id}:")
            LOG.warning(f"\tError reason: {str(e)}")
            LOG.warning(f"\tWaiter last response: {str(e.last_response)}")

            if isinstance(e, botocore.exceptions.WaiterError) and (
                "Undeliverable" in str(e) or "Undeliverable" in str(e.last_response)
            ):
                # if it wasn't delivered, retry. Otherwise let's check the command result.
                LOG.warning(
                    f"Unable to deliver command {command_id} to instance {self.instance_id} (received UndeliverableError)."
                )
                raise e
            pass

        ssm_command_result = self.ssm_client.get_command_invocation(
            InstanceId=self.instance_id,
            CommandId=command_id,
        )
        result = CommandResult(
            exit_code=ssm_command_result["ResponseCode"],
            stdout=ssm_command_result["StandardOutputContent"],
            stderr=ssm_command_result["StandardErrorContent"],
        )
        if result.exit_code == -1:  # pragma: no cover
            # Response code of -1 in a terminal state means the command was not received by the node
            LOG.error(f"Failed to send SSM command {command_id} to {self.instance_id}: {result}")

        LOG.info(f"SSM command {command_id} completed with exit code: {result.exit_code}")
        return result

    def _stage_s3_bucket(self) -> list[tuple[str, str]] | None:
        """Stages file_mappings to an S3 bucket and returns the mapping of S3 URI to dest path"""
        if not self.configuration.file_mappings:
            LOG.info("No file mappings to stage to S3")
            return None

        s3_to_src_mapping: dict[str, str] = {}
        s3_to_dst_mapping: dict[str, str] = {}
        for src_glob, dst in self.configuration.file_mappings:
            for src_file in glob.glob(src_glob):
                s3_key = f"worker/{os.path.basename(src_file)}"
                assert s3_key not in s3_to_src_mapping, (
                    "Duplicate S3 keys generated for file mappings. All source files must have unique "
                    + f"filenames. Mapping: {self.configuration.file_mappings}"
                )
                s3_to_src_mapping[s3_key] = src_file
                s3_to_dst_mapping[f"s3://{self.bootstrap_bucket_name}/{s3_key}"] = dst

        for key, local_path in s3_to_src_mapping.items():
            LOG.info(f"Uploading file {local_path} to s3://{self.bootstrap_bucket_name}/{key}")
            try:
                # self.s3_client.upload_file(local_path, self.bootstrap_bucket_name, key)
                with open(local_path, mode="rb") as f:
                    self.s3_client.put_object(
                        Bucket=self.bootstrap_bucket_name,
                        Key=key,
                        Body=f,
                    )
            except botocore.exceptions.ClientError as e:
                LOG.exception(
                    f"Failed to upload file {local_path} to s3://{self.bootstrap_bucket_name}/{key}: {e}"
                )
                raise

        return list(s3_to_dst_mapping.items())

    def _launch_instance(self, *, s3_files: list[tuple[str, str]] | None = None) -> None:
        assert (
            not self.instance_id
        ), "Attempted to launch EC2 instance when one was already launched"
        try:
            LOG.info("Launching EC2 instance")
            LOG.info(
                json.dumps(
                    {
                        "AMI_ID": self.ami_id,
                        "Instance Profile": self.instance_profile_name,
                        "User Data": self.userdata(s3_files),
                    },
                    indent=4,
                    sort_keys=True,
                )
            )

            tags = [
                {
                    "Key": "InstanceIdentification",
                    "Value": "DeadlineScaffoldingWorker",
                }
            ]

            for tag in self.additional_tags:
                tags.append({"Key": tag.key, "Value": tag.value})

            run_instance_request = {
                "MinCount": 1,
                "MaxCount": 1,
                "ImageId": self.ami_id,
                "InstanceType": self.instance_type,
                "IamInstanceProfile": {"Name": self.instance_profile_name},
                "SubnetId": self.subnet_id,
                "SecurityGroupIds": [self.security_group_id],
                "MetadataOptions": {"HttpTokens": "required", "HttpEndpoint": "enabled"},
                "TagSpecifications": [
                    {
                        "ResourceType": "instance",
                        "Tags": tags,
                    }
                ],
                "InstanceInitiatedShutdownBehavior": self.instance_shutdown_behavior,
                "UserData": self.userdata(s3_files),
            }

            devices = self.ebs_devices() or {}
            device_mappings = [
                {"DeviceName": name, "Ebs": {"VolumeSize": size}} for name, size in devices.items()
            ]
            if device_mappings:
                run_instance_request["BlockDeviceMappings"] = device_mappings

            run_instance_response = self.ec2_client.run_instances(**run_instance_request)

            self.instance_id = run_instance_response["Instances"][0]["InstanceId"]
            LOG.info(f"Launched EC2 instance {self.instance_id}")

            LOG.info(f"Waiting for EC2 instance {self.instance_id} status to be OK")
            instance_running_waiter = self.ec2_client.get_waiter("instance_status_ok")
            instance_running_waiter.wait(
                InstanceIds=[self.instance_id],
                WaiterConfig={"Delay": 15, "MaxAttempts": 75},
            )
            LOG.info(f"EC2 instance {self.instance_id} status is OK")
        except botocore.exceptions.WaiterError as e:
            diagnostics = self._collect_instance_diagnostics()
            raise InstanceStartupError(
                message=f"Failed to wait for instance status: {e}", diagnostics=diagnostics
            ) from e
        except Exception as e:
            LOG.error(f"Unexpected error during instance launch: {e}")
            raise

    def _collect_instance_diagnostics(self) -> str:
        """Collect diagnostic information about the instance"""
        if not self.instance_id:
            return "No instance_id available for diagnostics"

        diagnostic_info = []
        diagnostic_info.append(f"Collecting diagnostics for instance {self.instance_id}")

        # Get instance details
        try:
            instance_response = self.ec2_client.describe_instances(InstanceIds=[self.instance_id])
            instance = instance_response["Reservations"][0]["Instances"][0]

            # Log instance details
            diagnostic_info.append(f"Instance state: {instance['State']['Name']}")
            diagnostic_info.append(f"Instance type: {instance['InstanceType']}")
            diagnostic_info.append(f"Launch time: {instance['LaunchTime']}")
            diagnostic_info.append(
                f"Availability zone: {instance['Placement']['AvailabilityZone']}"
            )
        except Exception as e:
            diagnostic_info.append(f"Failed to get instance details: {e}")

        # Get instance status
        try:
            status_response = self.ec2_client.describe_instance_status(
                InstanceIds=[self.instance_id], IncludeAllInstances=True
            )
            if status_response["InstanceStatuses"]:
                status = status_response["InstanceStatuses"][0]
                diagnostic_info.append(
                    f"System status: {status.get('SystemStatus', {}).get('Status', 'unknown')}"
                )
                diagnostic_info.append(
                    f"Instance status: {status.get('InstanceStatus', {}).get('Status', 'unknown')}"
                )

                # Log status check details if available
                if "SystemStatus" in status and "Details" in status["SystemStatus"]:
                    for detail in status["SystemStatus"]["Details"]:
                        diagnostic_info.append(
                            f"System check {detail.get('Name')}: {detail.get('Status')}"
                        )

                if "InstanceStatus" in status and "Details" in status["InstanceStatus"]:
                    for detail in status["InstanceStatus"]["Details"]:
                        diagnostic_info.append(
                            f"Instance check {detail.get('Name')}: {detail.get('Status')}"
                        )
        except Exception as e:
            diagnostic_info.append(f"Failed to get instance status: {e}")
        return "\n".join(diagnostic_info)

    @property
    def ami_id(self) -> str:
        if not hasattr(self, "_ami_id"):
            response = call_api(
                description=f"Getting latest {type(self)} AMI ID from SSM parameter {self.ami_ssm_param_name()}",
                fn=lambda: self.ssm_client.get_parameters(Names=[self.ami_ssm_param_name()]),
            )

            parameters = response.get("Parameters", [])
            assert (
                len(parameters) == 1
            ), f"Received incorrect number of SSM parameters. Expected 1, got response: {response}"
            self._ami_id = parameters[0]["Value"]
            LOG.info(f"Using latest {type(self)} AMI {self._ami_id}")

        return self._ami_id


@dataclass
class WindowsInstanceWorkerBase(EC2InstanceWorker):
    """Base class from which Windows ec2 test instances are derived.

    The methods in this base class are written with two cases of worker hosts in mind:
    1. A host that is based on a stock Windows server AMI, with no Deadline-anything installed, that
       must install the worker agent and the like during boot-up.
    2. A host that already has the worker agent, job/agent users, and the like baked into
       the host AMI in a location & manner that may differ from case (1).
    """

    def ebs_devices(self) -> dict[str, int] | None:
        """DeviceName -> VolumeSize (in GiBs) mapping"""
        # defaults to 60GB to match SMF, aws gives 30GB by default
        return {"/dev/sda1": 60}

    def ssm_document_name(self) -> str:
        return "AWS-RunPowerShellScript"

    def _setup_worker_agent(self) -> None:
        assert self.instance_id
        LOG.info(f"Sending SSM command to configure Worker agent on instance {self.instance_id}")

        cmd_result = self.send_command(
            f"{self.configure_worker_command(config=self.configuration)}",
            {"Delay": 5, "MaxAttempts": 48},
        )
        assert cmd_result.exit_code == 0, f"Failed to configure Worker agent: {cmd_result}"
        LOG.info("Successfully configured Worker agent")

        if self.configuration.start_service:
            LOG.info(
                f"Sending SSM command to start Windows Worker agent on instance {self.instance_id}"
            )
            self.start_worker_service()
            LOG.info("Successfully started Worker agent")

    def configure_worker_common(self, *, config: DeadlineWorkerConfiguration) -> str:
        """Get the command to configure the Worker. This must be run as Administrator.
        This cannot assume that the agent user exists.
        """

        cmds = ["$ErrorActionPreference = 'Stop'"]

        if config.service_model_path:
            cmds.append(
                f"aws configure add-model --service-model file://{config.service_model_path} --service-name deadline; "
                f"Copy-Item -Path ~\\.aws\\* -Destination C:\\Users\\Administrator\\.aws\\models -Recurse; "
                f"Copy-Item -Path ~\\.aws\\* -Destination C:\\Users\\{config.job_user}\\.aws\\models -Recurse"
            )

        if config.no_local_session_logs:
            cmds.append(
                "[System.Environment]::SetEnvironmentVariable('DEADLINE_WORKER_LOCAL_SESSION_LOGS', 'false', [System.EnvironmentVariableTarget]::Machine); "
                "$env:DEADLINE_WORKER_LOCAL_SESSION_LOGS = [System.Environment]::GetEnvironmentVariable('DEADLINE_WORKER_LOCAL_SESSION_LOGS','Machine')",
            )

        if os.environ.get("DEADLINE_WORKER_ALLOW_INSTANCE_PROFILE"):
            LOG.info(
                f"Using DEADLINE_WORKER_ALLOW_INSTANCE_PROFILE: {os.environ.get('DEADLINE_WORKER_ALLOW_INSTANCE_PROFILE')}"
            )
            cmds.append(
                f"[System.Environment]::SetEnvironmentVariable('DEADLINE_WORKER_ALLOW_INSTANCE_PROFILE', '{os.environ.get('DEADLINE_WORKER_ALLOW_INSTANCE_PROFILE')}', [System.EnvironmentVariableTarget]::Machine); "
                "$env:DEADLINE_WORKER_ALLOW_INSTANCE_PROFILE = [System.Environment]::GetEnvironmentVariable('DEADLINE_WORKER_ALLOW_INSTANCE_PROFILE','Machine')",
            )

        if os.environ.get("AWS_ENDPOINT_URL_DEADLINE"):
            LOG.info(
                f"Using AWS_ENDPOINT_URL_DEADLINE: {os.environ.get('AWS_ENDPOINT_URL_DEADLINE')}"
            )
            cmds.append(
                f"[System.Environment]::SetEnvironmentVariable('AWS_ENDPOINT_URL_DEADLINE', '{os.environ.get('AWS_ENDPOINT_URL_DEADLINE')}', [System.EnvironmentVariableTarget]::Machine); "
                "$env:AWS_ENDPOINT_URL_DEADLINE = [System.Environment]::GetEnvironmentVariable('AWS_ENDPOINT_URL_DEADLINE','Machine')",
            )

        if config.worker_env_var:
            for key, value in config.worker_env_var.items():
                cmds.append(
                    f"[System.Environment]::SetEnvironmentVariable('{key}', '{value}', [System.EnvironmentVariableTarget]::Machine); "
                    f"$env:{key} = [System.Environment]::GetEnvironmentVariable('{value}','Machine')",
                )

        return "; ".join(cmds)

    def start_worker_service(self):
        LOG.info("Sending command to start the Worker Agent service")

        cmd_result = self.send_command(
            " ; ".join(
                [
                    'Start-Service -Name "DeadlineWorker"',
                    "echo 'Running Get-Process to check if the agent is running'",
                    'for($i=1; $i -le 30 -and "" -ne $err ; $i++){sleep $i; Get-Process pythonservice -ErrorVariable err}',
                    "IF(Get-Process pythonservice){echo '+++SERVICE IS RUNNING+++'}ELSE{echo '+++SERVICE NOT RUNNING+++'; Get-Content -Encoding utf8 C:\\ProgramData\\Amazon\\Deadline\\Logs\\worker-agent-bootstrap.log,C:\\ProgramData\\Amazon\\Deadline\\Logs\\worker-agent.log; exit 1}",
                ]
            ),
        )

        assert cmd_result.exit_code == 0, f"Failed to start Worker Agent service: : {cmd_result}"

        self.worker_id = self.get_worker_id()

    def stop_worker_service(self):
        LOG.info("Sending command to stop the Worker Agent service")
        cmd_result = self.send_command('Stop-Service -Name "DeadlineWorker"')

        assert cmd_result.exit_code == 0, f"Failed to stop Worker Agent service: : {cmd_result}"

    def get_worker_id(self) -> str:
        LOG.info(f"Sending SSM command to get the worker ID on instance {self.instance_id}")
        cmd_result = self.send_command(
            " ; ".join(
                [
                    'for($i=1; $i -le 20 -and "" -ne $err ; $i++){sleep $i; Get-Item C:\\ProgramData\\Amazon\\Deadline\\Cache\\worker.json -ErrorVariable err 1>$null}',
                    "$worker=Get-Content -Raw C:\\ProgramData\\Amazon\\Deadline\\Cache\\worker.json | ConvertFrom-Json",
                    "echo $worker.worker_id",
                ]
            ),
            {"Delay": 5, "MaxAttempts": 36},
        )
        assert cmd_result.exit_code == 0, f"Failed to get Worker ID: {cmd_result}"

        worker_id = cmd_result.stdout.rstrip("\n\r")
        assert re.match(
            r"^worker-[0-9a-f]{32}$", worker_id
        ), f"Got nonvalid Worker ID from command stdout: {cmd_result}"

        LOG.info(f"Obtained Worker ID: {worker_id}")
        return worker_id

    def get_windows_user_secret_cmd(self, secret_id: str) -> str:
        """
        Returns a PowerShell command string that will retrieve and use the secret on the worker instance itself.

        Args:
            secret_id: The ID of the secret in Secrets Manager

        Returns:
            str: PowerShell command to fetch and extract the password from the secret
        """
        return (
            "aws secretsmanager get-secret-value "
            f"--secret-id {secret_id} "
            "--query 'SecretString' --output text | "
            "ConvertFrom-Json | "
            "Select-Object -ExpandProperty password"
        )


@dataclass
class WindowsInstanceBuildWorker(WindowsInstanceWorkerBase):
    """
    This class represents a Windows EC2 Worker Host.
    Any commands must be written in Powershell.
    """

    WIN2022_AMI_NAME: ClassVar[str] = "Windows_Server-2022-English-Full-Base"

    def configure_worker_command(self, *, config: DeadlineWorkerConfiguration) -> str:
        """Get the command to configure the Worker. This must be run as Administrator."""

        cmds = [
            "Set-PSDebug -trace 1",
            self.configure_worker_common(config=config),
            config.worker_agent_install.install_command_for_windows,
            *(config.pre_install_commands or []),
            # fmt: off
            (
                "install-deadline-worker "
                + "-y "
                + f"--farm-id {config.farm_id} "
                + f"--fleet-id {config.fleet.id} "
                + f"--region {config.region} "
                + f"--user {config.agent_user} "
                + (f"--password $({self.get_windows_user_secret_cmd(secret_id=config.windows_user_secret)}) " if config.windows_user_secret else "")
                + f"{'--allow-shutdown ' if config.allow_shutdown else ''}"
                + f"{'--disallow-instance-profile ' if config.disallow_instance_profile else ''}"
                + (f"--session-root-dir {config.session_root_dir} " if config.session_root_dir is not None else '')
            ),
            # fmt: on
        ]

        if config.service_model_path:
            cmds.append(
                f"Copy-Item -Path ~\\.aws\\* -Destination C:\\Users\\{config.agent_user}\\.aws\\models -Recurse; "
            )

        if config.start_service:
            cmds.append('Start-Service -Name "DeadlineWorker"')

        return "; ".join(cmds)

    def userdata(self, s3_files) -> str:
        copy_s3_command = ""
        job_users_cmds = []

        if s3_files:
            copy_s3_command = " ; ".join([f"aws s3 cp {s3_uri} {dst}" for s3_uri, dst in s3_files])

        if self.configuration.windows_job_users:
            for job_user in self.configuration.windows_job_users:
                job_users_cmds.append(
                    f"New-LocalUser -Name {job_user} -Password $password -FullName {job_user} -Description {job_user}"
                )
                job_users_cmds.append(
                    f"$Cred = New-Object System.Management.Automation.PSCredential {job_user}, $password"
                )
                job_users_cmds.append(
                    'Start-Process cmd.exe -Credential $Cred -ArgumentList "/C" -LoadUserProfile -NoNewWindow'
                )

        configure_job_users = "\n".join(job_users_cmds)

        userdata = f"""<powershell>
$ProgressPreference = 'SilentlyContinue'
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe" -OutFile "C:\\python-3.12.10-amd64.exe"
$installerHash=(Get-FileHash "C:\\python-3.12.10-amd64.exe" -Algorithm "MD5")
$expectedHash="5eddb0b6f12c852725de071ae681dde4"
if ($installerHash.Hash -ne $expectedHash) {{ throw "Could not verify Python installer." }}
Start-Process -FilePath "C:\\python-3.12.10-amd64.exe" -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 AppendPath=1" -Wait
Invoke-WebRequest -Uri "https://awscli.amazonaws.com/AWSCLIV2.msi" -Outfile "C:\\AWSCLIV2.msi"
Start-Process msiexec.exe -ArgumentList "/i C:\\AWSCLIV2.msi /quiet" -Wait
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine")
$secret = aws secretsmanager get-secret-value --secret-id WindowsPasswordSecret --query SecretString --output text | ConvertFrom-Json
$password = ConvertTo-SecureString -String $($secret.password) -AsPlainText -Force
{copy_s3_command}
{configure_job_users}
</powershell>"""

        return userdata

    def ami_ssm_param_name(self) -> str:
        # Grab the latest Windows Server 2022 AMI
        # https://aws.amazon.com/blogs/mt/query-for-the-latest-windows-ami-using-systems-manager-parameter-store/
        ami_ssm_param: str = (
            f"/aws/service/ami-windows-latest/{WindowsInstanceBuildWorker.WIN2022_AMI_NAME}"
        )
        return ami_ssm_param


@dataclass
class PosixInstanceWorkerBase(EC2InstanceWorker):
    """Base class from which posix (i.e. Linux) ec2 test instances are derived.

    The methods in this base class are written with two cases of worker hosts in mind:
    1. A host that is based on a stock linux AMI, with no Deadline-anything installed, that
       must install the worker agent and the like during boot-up.
    2. A host that already has the worker agent, job/agent users, and the like baked into
       the host AMI in a location & manner that may differ from case (1).
    """

    def ebs_devices(self) -> dict[str, int] | None:
        """DeviceName -> VolumeSize (in GiBs) mapping"""
        # defaults to 30GB to match SMF, aws gives 8GB by default
        return {"/dev/xvda": 30}

    def ssm_document_name(self) -> str:
        return "AWS-RunShellScript"

    def send_command(
        self, command: str, ssm_waiter_config: dict[str, int] = DEFAULT_WAITER_CONFIG
    ) -> CommandResult:
        return super().send_command("set -eou pipefail; " + command, ssm_waiter_config)

    def _setup_worker_agent(self) -> None:
        assert self.instance_id
        LOG.info(
            f"Starting worker for farm: {self.configuration.farm_id} and fleet: {self.configuration.fleet.id}"
        )
        LOG.info(f"Sending SSM command to configure Worker agent on instance {self.instance_id}")

        cmd_result = self.send_command(self.configure_worker_command(config=self.configuration))
        assert cmd_result.exit_code == 0, f"Failed to configure Worker agent: {cmd_result}"
        LOG.info("Successfully configured Worker agent")

        if self.configuration.start_service:
            LOG.info(
                f"Sending SSM command to configure Worker agent on instance {self.instance_id}"
            )
            self.start_worker_service()
            LOG.info("Successfully started worker agent")

    def configure_agent_user_environment(
        self, config: DeadlineWorkerConfiguration
    ) -> str:  # pragma: no cover
        """Get the command to configure the Worker. This must be run as root.
        This can assume that the agent user exists.
        """

        cmds = []

        if config.service_model_path:
            cmds.append(
                f"runuser -l {config.agent_user} -s /bin/bash -c 'aws configure add-model --service-model file://{config.service_model_path}'"
            )

        allow_instance_profile = os.environ.get("DEADLINE_WORKER_ALLOW_INSTANCE_PROFILE", None)
        endpoint_url_deadline = os.environ.get("AWS_ENDPOINT_URL_DEADLINE", None)

        # Create a systemd drop-in config file to apply the configuration
        # See https://wiki.archlinux.org/title/Systemd#Drop-in_files
        cmds.extend(
            [
                "mkdir -p /etc/systemd/system/deadline-worker.service.d/",
                'echo "[Service]" >> /etc/systemd/system/deadline-worker.service.d/config.conf',
                # Configure the region
                f'echo "Environment=AWS_REGION={config.region}" >> /etc/systemd/system/deadline-worker.service.d/config.conf',
                f'echo "Environment=AWS_DEFAULT_REGION={config.region}" >> /etc/systemd/system/deadline-worker.service.d/config.conf',
            ]
        )

        if allow_instance_profile is not None:
            LOG.info(f"Using DEADLINE_WORKER_ALLOW_INSTANCE_PROFILE: {allow_instance_profile}")
            cmds.append(
                f'echo "Environment=DEADLINE_WORKER_ALLOW_INSTANCE_PROFILE={allow_instance_profile}" >> /etc/systemd/system/deadline-worker.service.d/config.conf',
            )

        if endpoint_url_deadline is not None:
            LOG.info(f"Using AWS_ENDPOINT_URL_DEADLINE: {endpoint_url_deadline}")
            cmds.append(
                f'echo "Environment=AWS_ENDPOINT_URL_DEADLINE={endpoint_url_deadline}" >> /etc/systemd/system/deadline-worker.service.d/config.conf',
            )

        if config.no_local_session_logs:
            cmds.append(
                'echo "Environment=DEADLINE_WORKER_LOCAL_SESSION_LOGS=false" >> /etc/systemd/system/deadline-worker.service.d/config.conf',
            )

            cmds.append("systemctl daemon-reload")
        if config.worker_env_var:
            for key, value in config.worker_env_var.items():
                cmds.append(
                    f"echo 'Environment=\"{key}={value}\"' >> /etc/systemd/system/deadline-worker.service.d/config.conf",
                )
            cmds.append("systemctl daemon-reload")

        return " && ".join(cmds)

    def start_worker_service(self):
        LOG.info("Sending command to start the Worker Agent service")

        cmd_result = self.send_command(
            " && ".join(
                [
                    "systemctl start deadline-worker",
                    "sleep 5",
                    "systemctl is-active deadline-worker",
                    "if test $? -ne 0; then echo '+++AGENT NOT RUNNING+++'; cat /var/log/amazon/deadline/worker-agent-bootstrap.log /var/log/amazon/deadline/worker-agent.log; exit 1; fi",
                ]
            )
        )

        assert cmd_result.exit_code == 0, f"Failed to start Worker Agent service: {cmd_result}"

        self.worker_id = self.get_worker_id()

    def stop_worker_service(self):
        LOG.info("Sending command to stop the Worker Agent service")
        cmd_result = self.send_command("systemctl stop deadline-worker")

        assert cmd_result.exit_code == 0, f"Failed to stop Worker Agent service: {cmd_result}"

    def get_worker_id(self) -> str:
        # There can be a race condition, so we may need to wait a little bit for the status file to be written.

        worker_state_filename = "/var/lib/deadline/worker.json"
        cmd_result = self.send_command(
            " && ".join(
                [
                    f"t=0 && while [ $t -le 10 ] && ! (test -f {worker_state_filename}); do sleep $t; t=$[$t+1]; done",
                    f"cat {worker_state_filename} | jq -r '.worker_id'",
                ]
            )
        )
        assert cmd_result.exit_code == 0, f"Failed to get Worker ID: {cmd_result}"

        worker_id = cmd_result.stdout.rstrip("\n\r")
        LOG.info(f"Worker ID: {worker_id}")
        assert re.match(
            r"^worker-[0-9a-f]{32}$", worker_id
        ), f"Got nonvalid Worker ID from command stdout: {cmd_result}"
        return worker_id


@dataclass
class PosixInstanceBuildWorker(PosixInstanceWorkerBase):
    """
    This class represents a Linux EC2 Worker Host.
    Any commands must be written in Bash.
    """

    AL2023_AMI_NAME: ClassVar[str] = "al2023-ami-kernel-6.1-x86_64"

    def configure_worker_command(
        self, config: DeadlineWorkerConfiguration
    ) -> str:  # pragma: no cover
        """Get the command to configure the Worker. This must be run as root."""
        cmds = [
            "set -x",
            "source /opt/deadline/worker/bin/activate",
            f"AWS_DEFAULT_REGION={self.configuration.region}",
            config.worker_agent_install.install_command_for_linux,
            *(config.pre_install_commands or []),
            # fmt: off
            (
                "install-deadline-worker "
                + "-y "
                + f"--farm-id {config.farm_id} "
                + f"--fleet-id {config.fleet.id} "
                + f"--region {config.region} "
                + f"--user {config.agent_user} "
                + f"--group {config.job_user_group} "
                + f"{'--allow-shutdown ' if config.allow_shutdown else ''}"
                + f"{'--no-install-service ' if config.no_install_service else ''}"
                + f"{'--disallow-instance-profile ' if config.disallow_instance_profile else ''}"
                + (f"--session-root-dir {config.session_root_dir} " if config.session_root_dir is not None else '')
            ),
            # fmt: on
            f"runuser --login {self.configuration.agent_user} --command 'echo \"source /opt/deadline/worker/bin/activate\" >> $HOME/.bashrc'",
        ]

        for job_user in self.configuration.job_users:
            cmds.append(f"usermod -a -G {job_user.group} {self.configuration.agent_user}")

        sudoer_rule_users = ",".join(
            [
                self.configuration.agent_user,
                *[job_user.user for job_user in self.configuration.job_users],
            ]
        )
        cmds.append(
            f'echo "{self.configuration.agent_user} ALL=({sudoer_rule_users}) NOPASSWD: ALL" > /etc/sudoers.d/{self.configuration.agent_user}'
        )

        cmds.append(self.configure_agent_user_environment(config))

        return " && ".join(cmds)

    def userdata(self, s3_files) -> str:
        copy_s3_command = ""
        job_users_cmds = []

        if s3_files:
            copy_s3_command = " && ".join(
                [f"aws s3 cp {s3_uri} {dst} && chmod o+rx {dst}" for s3_uri, dst in s3_files]
            )
        for job_user in self.configuration.job_users:
            job_users_cmds.append(f"groupadd {job_user.group}")
            job_users_cmds.append(
                f"useradd --create-home --system --shell=/bin/bash --groups={self.configuration.job_user_group} -g {job_user.group} {job_user.user}"
            )

        configure_job_users = "\n".join(job_users_cmds)

        userdata = f"""#!/bin/bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
set -x
groupadd --system {self.configuration.job_user_group}
{configure_job_users}
{copy_s3_command}

mkdir /opt/deadline
python3 -m venv /opt/deadline/worker
"""

        return userdata

    def ami_ssm_param_name(self) -> str:
        # Grab the latest AL2023 AMI
        # https://aws.amazon.com/blogs/compute/query-for-the-latest-amazon-linux-ami-ids-using-aws-systems-manager-parameter-store/
        ami_ssm_param: str = (
            f"/aws/service/ami-amazon-linux-latest/{PosixInstanceBuildWorker.AL2023_AMI_NAME}"
        )
        return ami_ssm_param


@dataclass
class DockerContainerWorker(DeadlineWorker):
    configuration: DeadlineWorkerConfiguration

    _container_id: Optional[str] = field(init=False, default=None)

    def __post_init__(self) -> None:
        # Do not install Worker agent service since it's recommended to avoid systemd usage on Docker containers
        self.configuration = replace(self.configuration, no_install_service=True)

    def start(self) -> None:
        self._tmpdir = pathlib.Path(tempfile.mkdtemp())

        assert (
            len(self.configuration.job_users) == 1
        ), f"Multiple job users not supported on Docker worker: {self.configuration.job_users}"
        # Environment variables for "run_container.sh"
        run_container_env = {
            **os.environ,
            "FARM_ID": self.configuration.farm_id,
            "FLEET_ID": self.configuration.fleet.id,
            "AGENT_USER": self.configuration.agent_user,
            "SHARED_GROUP": self.configuration.job_user_group,
            "JOB_USER": self.configuration.job_users[0].user,
            "CONFIGURE_WORKER_AGENT_CMD": self.configure_worker_command(
                config=self.configuration,
            ),
        }

        LOG.info(f"Staging Docker build context directory {str(self._tmpdir)}")
        shutil.copytree(DOCKER_CONTEXT_DIR, str(self._tmpdir), dirs_exist_ok=True)

        if self.configuration.file_mappings:
            # Stage a special dir with files to copy over to a temp folder in the Docker container
            # The container is responsible for copying files from that temp folder into the final destinations
            file_mappings_dir = self._tmpdir / "file_mappings"
            os.makedirs(str(file_mappings_dir))

            # Mapping of files in temp Docker container folder to their final destination
            docker_file_mappings: dict[str, str] = {}
            for src, dst in self.configuration.file_mappings:
                src_file_name = os.path.basename(src)

                # The Dockerfile copies the file_mappings dir in the build context to "/file_mappings" in the container
                # Build up an array of mappings from "/file_mappings" to their final destination
                src_docker_path = posixpath.join("/file_mappings", src_file_name)
                assert src_docker_path not in docker_file_mappings, (
                    "Duplicate paths generated for file mappings. All source files must have unique "
                    + f"filenames. Mapping: {self.configuration.file_mappings}"
                )
                docker_file_mappings[src_docker_path] = dst

                # Copy the file over to the stage directory
                staged_dst = str(file_mappings_dir / src_file_name)
                LOG.info(f"Copying file {src} to {staged_dst}")
                shutil.copyfile(src, staged_dst)

            run_container_env["FILE_MAPPINGS"] = json.dumps(docker_file_mappings)

        # Build and start the container
        LOG.info("Starting Docker container")
        try:
            proc = subprocess.Popen(
                args="./run_container.sh",
                cwd=str(self._tmpdir),
                env=run_container_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
            )

            # Live logging of Docker build
            assert proc.stdout
            with proc.stdout:
                for line in iter(proc.stdout.readline, ""):
                    LOG.info(line.rstrip("\r\n"))
        except Exception as e:  # pragma: no cover
            LOG.exception(f"Failed to start Worker agent Docker container: {e}")
            _handle_subprocess_error(e)
            raise
        else:
            exit_code = proc.wait(timeout=60)
            assert exit_code == 0, f"Process failed with exit code {exit_code}"

        # Grab the container ID from --cidfile
        try:
            self._container_id = subprocess.check_output(
                args=["cat", ".container_id"],
                cwd=str(self._tmpdir),
                text=True,
                encoding="utf-8",
                timeout=1,
            ).rstrip("\r\n")
        except Exception as e:  # pragma: no cover
            LOG.exception(f"Failed to get Docker container ID: {e}")
            _handle_subprocess_error(e)
            raise
        else:
            LOG.info(f"Started Docker container {self._container_id}")

    def stop(self) -> None:
        assert (
            self._container_id
        ), "Cannot stop Docker container: Container ID is not set. Has the Docker container been started yet?"

        LOG.info(f"Terminating Worker agent process in Docker container {self._container_id}")
        try:
            self.send_command(f"pkill --signal term -f {self.configuration.agent_user}")
        except Exception as e:  # pragma: no cover
            LOG.exception(f"Failed to terminate Worker agent process: {e}")
            raise
        else:
            LOG.info("Worker agent process terminated")

        LOG.info(f"Stopping Docker container {self._container_id}")
        try:
            subprocess.check_output(
                args=["docker", "container", "stop", self._container_id],
                cwd=str(self._tmpdir),
                text=True,
                encoding="utf-8",
                timeout=30,
            )
        except Exception as e:  # pragma: noc over
            LOG.exception(f"Failed to stop Docker container {self._container_id}: {e}")
            _handle_subprocess_error(e)
            raise
        else:
            LOG.info(f"Stopped Docker container {self._container_id}")
            self._container_id = None

    def configure_worker_command(
        self, config: DeadlineWorkerConfiguration
    ) -> str:  # pragma: no cover
        """Get the command to configure the Worker. This must be run as root."""

        return ""

    def send_command(self, command: str, *, quiet: bool = False) -> CommandResult:
        assert (
            self._container_id
        ), "Container ID not set. Has the Docker container been started yet?"

        if not quiet:  # pragma: no cover
            LOG.info(f"Sending command '{command}' to Docker container {self._container_id}")
        try:
            result = subprocess.run(
                args=[
                    "docker",
                    "exec",
                    self._container_id,
                    "/bin/bash",
                    "-euo",
                    "pipefail",
                    "-c",
                    command,
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
            )
        except Exception as e:
            if not quiet:  # pragma: no cover
                LOG.exception(f"Failed to run command: {e}")
                _handle_subprocess_error(e)
            raise
        else:
            return CommandResult(
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )

    def get_worker_id(self) -> str:
        cmd_result: Optional[CommandResult] = None

        def got_worker_id() -> bool:
            nonlocal cmd_result
            try:
                cmd_result = self.send_command(
                    "cat /var/lib/deadline/worker.json | jq -r '.worker_id' || (cat /var/log/amazon/deadline/worker.log; false)",
                    quiet=True,
                )
            except subprocess.CalledProcessError as e:
                LOG.warning(f"Worker ID retrieval failed: {e}")
                return False
            else:
                return cmd_result.exit_code == 0

        wait_for(
            description="retrieval of worker ID from /var/lib/deadline/worker.json",
            predicate=got_worker_id,
            interval_s=10,
            max_retries=6,
        )

        assert isinstance(cmd_result, CommandResult)
        cmd_result = cast(CommandResult, cmd_result)
        assert cmd_result.exit_code == 0, f"Failed to get Worker ID: {cmd_result}"

        worker_id = cmd_result.stdout.rstrip("\r\n")
        assert re.match(
            r"^worker-[0-9a-f]{32}$", worker_id
        ), f"Got nonvalid Worker ID from command stdout: {cmd_result}"

        return worker_id

    @property
    def container_id(self) -> str | None:
        return self._container_id


def _handle_subprocess_error(e: Any) -> None:  # pragma: no cover
    if hasattr(e, "stdout"):
        LOG.error(f"Command stdout: {e.stdout}")
    if hasattr(e, "stderr"):
        LOG.error(f"Command stderr: {e.stderr}")
