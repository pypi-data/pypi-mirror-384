import json
import os
import io
import time
import shlex
from typing import Optional

import boto3
import zipfile
import sys

from emd.constants import (
    CODEPIPELINE_NAME,
    ENV_STACK_NAME,
    MODEL_DEFAULT_TAG,
    MODEL_STACK_NAME_PREFIX,
    VERSION,
    LOCAL_REGION,
    LOCAL_DEPLOY_PIPELINE_ZIP_DIR
)
from emd.utils.file_utils import mkdir_with_mode
from emd.models import Model
from emd.models.utils.constants import FrameworkType, ServiceType,InstanceType
from emd.models.utils.serialize_utils import dump_extra_params
from emd.utils.aws_service_utils import (
    check_cn_region,
    check_quota_availability,
    check_stack_exists,
    get_current_region,
    get_pipeline_active_executions,
)
from emd.utils.logger_utils import get_logger
from emd.utils.upload_pipeline import ziped_pipeline
from emd.utils.aws_service_utils import get_current_region

from .bootstrap import create_env_stack, get_bucket_name
from .status import get_pipeline_execution_status, get_pipeline_execution_status_with_retry
from emd.models.utils.constants import ServiceType

from rich.console import Console

console = Console()

logger = get_logger(__name__)


def _get_robust_status_info(execution_id: str, region: str) -> dict:
    """Get robust status information with enhanced retry and fallback handling"""
    try:
        # Use the enhanced retry function to handle AWS eventual consistency
        status_info = get_pipeline_execution_status_with_retry(
            pipeline_execution_id=execution_id,
            region=region
        )
        # Ensure all required fields are present with defaults
        return {
            "status": status_info.get("status", "InProgress"),
            "status_code": status_info.get("status_code", 1),
            "is_succeeded": status_info.get("is_succeeded", False),
            "stage_name": status_info.get("stage_name"),
            "status_summary": status_info.get("status_summary"),
            "pipeline_execution_id": status_info.get("pipeline_execution_id", execution_id)
        }

    except Exception as e:
        # Enhanced fallback: keep monitoring with informative status
        logger.warning(f"Enhanced retry failed for execution {execution_id}: {e}")
        return {
            "status": "InProgress",
            "status_code": 1,  # Keep monitoring
            "is_succeeded": False,
            "stage_name": "Initializing",
            "status_summary": f"Waiting for pipeline execution to become available: {str(e)}",
            "pipeline_execution_id": execution_id
        }


def parse_extra_params(extra_params=None):
    if extra_params is None:
        return {}

    if isinstance(extra_params, dict):
        return extra_params

    assert isinstance(extra_params, str), extra_params
    if os.path.exists(extra_params):
        with open(extra_params) as f:
            return json.load(f)

    return json.loads(extra_params)

    # raise ValueError(f"involid extrap_params; {extra_params}")


def prepare_deploy(
    model_id: str,
    model_tag=MODEL_DEFAULT_TAG,
    service_type=None,
    instance_type=None,
    region=None,
    dockerfile_local_path=None
):
    if dockerfile_local_path:
        model_stack_name = f"{MODEL_STACK_NAME_PREFIX}-{model_id}-{model_tag}"
    else:
        model: Model = Model.get_model(model_id)
        model_stack_name = model.get_model_stack_name_prefix(
            model_id, model_tag=model_tag
        )
    # check if model_id is inprogress in pipeline execution
    if check_stack_exists(model_stack_name):
        raise RuntimeError(
            f"A model with ID: {model_id} and tag: {model_tag} already exists. Please use a different tag to continue."
        )

    client = boto3.client("codepipeline", region_name=region)
    try:
        active_executuion_infos = get_pipeline_active_executions(
            pipeline_name=CODEPIPELINE_NAME,
            client=client,
            filter_stoped=True,
            filter_failed=True,
        )
        model_uid = Model.get_model_stack_name_prefix(model_id, model_tag)
        active_executuion_infos_d = {
            Model.get_model_stack_name_prefix(d["model_id"], d["model_tag"]): d
            for d in active_executuion_infos
        }

        if model_uid in active_executuion_infos_d:
            model_info = active_executuion_infos_d[model_uid]
            raise RuntimeError(
                f"model: {model_info['model_id']},tag: {model_info['model_tag']} is deploying, please wait for it to complete"
            )
    except client.exceptions.PipelineNotFoundException as e:
        pass

    # check quota
    if check_cn_region(region):
        return
    is_quota_sufficient, message = check_quota_availability(
        service_type, instance_type, desired_count=1, region=region
    )
    if not is_quota_sufficient:
        raise RuntimeError(message)


def deploy(
    model_id: str,
    instance_type: str,
    engine_type: str,
    service_type: str,
    framework_type: str = FrameworkType.FASTAPI,
    model_tag=MODEL_DEFAULT_TAG,
    region: Optional[str] = None,
    model_stack_name=None,
    extra_params=None,
    env_stack_on_failure="ROLLBACK",
    force_env_stack_update=False,
    waiting_until_deploy_complete=True,
    dockerfile_local_path=None,
) -> dict:
    with console.status("[bold blue]Retrieving model deployment status... (Press Ctrl+C to return)[/bold blue]"):
    # Check if AWS environment is properly configured
        if service_type == ServiceType.SAGEMAKER_OLDER:
            service_type = ServiceType.SAGEMAKER
            logger.warning(
                f"Service type {ServiceType.SAGEMAKER_OLDER} is deprecated, please use {ServiceType.SAGEMAKER}"
            )

        assert (
            model_stack_name is None
        ), f"It is currently not supported to custom model stack name."
        region = get_current_region()
        prepare_deploy(
            model_id,
            model_tag=model_tag,
            service_type=service_type,
            instance_type=instance_type,
            region=region,
            dockerfile_local_path=dockerfile_local_path
        )
        if isinstance(extra_params, str):
            extra_params = json.loads(extra_params)
        else:
            extra_params = extra_params or {}
        if model_stack_name is None:
            # stack_name_suffix = random_suffix()
            model_stack_name = (
                f"{Model.get_model_stack_name_prefix(model_id,model_tag=model_tag)}"
            )
        # Check if CloudFormation stack exists for CodePipeline
        cfn = boto3.client("cloudformation", region_name=region)
        bucket_name = get_bucket_name(
            bucket_prefix="emd-env-artifactbucket", region=region
        )
        bootstrap_stack = cfn.describe_stacks(StackName=ENV_STACK_NAME)["Stacks"][0]
        # # Get the pipeline name from the bootstrap stack
        pipeline_resources = [
            resource
            for resource in cfn.describe_stack_resources(
                StackName=bootstrap_stack["StackName"]
            )["StackResources"]
            if resource["ResourceType"] == "AWS::CodePipeline::Pipeline"
        ]
        pipeline_name = pipeline_resources[0]["PhysicalResourceId"]

        if dockerfile_local_path:
            if not os.path.exists(dockerfile_local_path):
                raise FileNotFoundError(f"Dockerfile path {dockerfile_local_path} does not exist.")

            # Create a zip file of the dockerfile directory
            zip_buffer = zipped_dockerfile(dockerfile_local_path)

            # Upload the zip file to S3
            s3 = boto3.client('s3', region_name=region)
            s3_key = f"emd_models/{model_id}-{model_tag}.zip"
            s3.upload_fileobj(zip_buffer, bucket_name, s3_key)
            extra_params["model_params"] = extra_params.get("model_params", {})
            extra_params["model_params"]["custom_dockerfile_path"] = f"s3://{bucket_name}/{s3_key}"
            logger.info(f"extra_params: {extra_params}")
        else:
            model = Model.get_model(model_id)

            # check instance,service,engine
            supported_instances = model.supported_instance_types
            assert (
                instance_type in supported_instances
            ), f"Instance type {instance_type} is not supported for model {model_id}"

            supported_engines = model.supported_engine_types
            assert (
                engine_type in supported_engines
            ), f"Engine type {engine_type} is not supported for model {model_id}"

            supported_services = model.supported_service_types
            assert (
                service_type in supported_services
            ), f"Service type {service_type} is not supported for model {model_id}"

        # Start pipeline execution
        codepipeline = boto3.client("codepipeline", region_name=region)
        # stack_name_suffix = random_suffix()
        extra_params = dump_extra_params(extra_params)
        variables = [
            {"name": "ModelStackName", "value": model_stack_name},
            {"name": "ModelId", "value": model_id},
            {"name": "ModelTag", "value": model_tag},
            {"name": "ServiceType", "value": service_type},
            {"name": "InstanceType", "value": instance_type},
            {"name": "EngineType", "value": engine_type},
            {"name": "ExtraParams", "value": extra_params},
            {"name": "CreateTime", "value": f"{time.time()}"},
            {"name": "FrameworkType", "value": framework_type},
            {"name": "Region", "value": region},
        ]

        start_deploy_time = time.time()

        response = codepipeline.start_pipeline_execution(
            name=pipeline_name, variables=variables
        )
    logger.info(
        f"Model deployment pipeline started. Execution ID: {response['pipelineExecutionId']}"
    )
    execution_id = response["pipelineExecutionId"]
    ret = {
        "pipeline_execution_id": response["pipelineExecutionId"],
        "model_stack_name": model_stack_name,
        "model_id": model_id,
        "model_tag": model_tag,
        "service_type": service_type,
        "framework_type": framework_type,
        "instance_type": instance_type,
        "engine_type": engine_type,
        "extra_params": extra_params,
        "model_deploy_start_time": f"{start_deploy_time}",
    }

    is_succeeded = False
    if waiting_until_deploy_complete:
        logger.info(f"Monitoring deployment stack {model_stack_name}")
        client = boto3.client("codepipeline", region_name=region)

        while True:
            try:
                # Get robust status information
                status_info = _get_robust_status_info(execution_id, region)

                # Extract status information with safe defaults
                status = status_info["status"]
                status_code = status_info["status_code"]
                is_succeeded = status_info["is_succeeded"]
                stage_name = status_info.get("stage_name")
                status_summary = status_info.get("status_summary")

                # Build user-friendly log message (same format as original)
                log_info = f"Waiting for deployment to complete: model {model_id} (tag: {model_tag}, service: {service_type}, instance: {InstanceType.convert_instance_type(instance_type,service_type)}). Current status: {status}"

                # Add optional information if available
                if stage_name:
                    log_info += f"({stage_name})"
                if status_summary:
                    log_info += f", {status_summary}"


                # Add duration
                log_info += f". Duration: {int(time.time() - start_deploy_time)} seconds"

                # Display status to user
                logger.info(log_info)

                # Check if deployment is complete
                if status_code == 0:
                    break

                time.sleep(10)

            except client.exceptions.PipelineExecutionNotFoundException:
                logger.info("Waiting for pipeline execution to start...")
                time.sleep(10)
                continue

            except Exception as e:
                # Robust error handling - continue monitoring with basic status
                logger.info(f"waiting for model: {model_id} (tag: {model_tag}, service: {service_type}, instance: {InstanceType.convert_instance_type(instance_type,service_type)}) deployment pipeline execution to complete. Current status: InProgress, Duration time: {int(time.time() - start_deploy_time)}s")
                time.sleep(10)
                continue

        deploy_time = time.time() - start_deploy_time
        ret["model_deploy_elasped_time"] = deploy_time

        # Get final status with robust handling
        try:
            final_status_info = _get_robust_status_info(execution_id, region)
            is_succeeded = final_status_info["is_succeeded"]
        except Exception:
            # Fallback: assume success if we exited the monitoring loop
            is_succeeded = True

    if service_type == ServiceType.SAGEMAKER:
        ret["sagemaker_endpoint_name"] = f"{model_stack_name}-endpoint"
        if not waiting_until_deploy_complete or is_succeeded:
            logger.info(
                f"The output sagemaker endpoint name will be: {model_stack_name}-endpoint"
            )

    failed_info = f"Model: {model_id} (tag: {model_tag}) deployment pipeline execution failed. Execution ID: {execution_id},"
    if check_stack_exists(model_stack_name):
        failed_info += f" or watch error logs in stack: {model_stack_name}"
    if waiting_until_deploy_complete and not is_succeeded:
        logger.info(failed_info)

    if waiting_until_deploy_complete and is_succeeded:
        logger.info(
            f"Model: {model_id} (tag: {model_tag}) deployment pipeline execution succeeded. Execution ID: {execution_id}, elapsed time: {ret['model_deploy_elasped_time']}s"
        )
    return ret


def deploy_local(
    model_id: str,
    instance_type: str,
    service_type: str,
    engine_type: str,
    framework_type: str = FrameworkType.FASTAPI,
    model_tag=MODEL_DEFAULT_TAG,
    # region: Optional[str] = None,
    # model_stack_name=None,
    extra_params=None,
    pipeline_zip_local_path=os.path.join(
        LOCAL_DEPLOY_PIPELINE_ZIP_DIR,
        "pipeline.zip"
    ),
    # env_stack_on_failure = "ROLLBACK",
    # force_env_stack_update = False,
    # waiting_until_deploy_complete = True
) -> dict:
    # cp pipeline to tmp
    extra_params = parse_extra_params(extra_params)
    logger.info(f"parsed extra_params: {extra_params}")
    extra_params = dump_extra_params(extra_params or {})
    dir = os.path.dirname(pipeline_zip_local_path)

    mkdir_with_mode(dir, exist_ok=True,mode=0o777)
    # os.makedirs(dir, exist_ok=True,mode=0o777)
    with open(pipeline_zip_local_path, "wb") as f:
        buffer = ziped_pipeline()
        f.write(buffer.read())

    # unzip the zip
    import zipfile

    with zipfile.ZipFile(pipeline_zip_local_path, "r") as zip_ref:
        zip_ref.extractall(dir)

    # assert os.system(f"chmod -R 777 {dir}") == 0, f"chmod -R 777 {dir} failed"

    pipeline_cmd = (
        f"cd {dir}/pipeline && {sys.executable} pipeline.py "
        f" --model_id {model_id}"
        f" --model_tag {model_tag}"
        f" --instance_type {instance_type}"
        f" --service_type {service_type}"
        f" --backend_type {engine_type}"
        f" --framework_type {framework_type}"
        f" --region '{LOCAL_REGION}'"
        f" --extra_params {shlex.quote(extra_params)}"
    )
    logger.info(f"pipeline cmd: {pipeline_cmd}")
    assert (
        os.system(pipeline_cmd) == 0
    ), f"run pipeline cmd failed: {pipeline_cmd}"

def zipped_dockerfile(dockerfile_local_path):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED) as zipf:
        dockerfile_dir = os.path.dirname(dockerfile_local_path)
        for root, dirs, files in os.walk(dockerfile_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, dockerfile_dir)
                zipf.write(file_path, arcname)
    zip_buffer.seek(0)
    return zip_buffer
