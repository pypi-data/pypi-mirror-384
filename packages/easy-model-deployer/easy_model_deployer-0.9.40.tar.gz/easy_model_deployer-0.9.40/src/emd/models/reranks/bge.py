from .. import Model
from ..engines import vllm_embedding_engine066
from ..services import sagemaker_service,local_service,ecs_service
from ..frameworks import fastapi_framework
from ..instances import (
    g4dn2xlarge_instance,
    g5dxlarge_instance,
    g5d2xlarge_instance,
    g5d4xlarge_instance,
    g5d8xlarge_instance,
    g5d12xlarge_instance,
    g5d16xlarge_instance,
    g5d24xlarge_instance,
    g5d48xlarge_instance,
    local_instance
)
from emd.models.utils.constants import ModelType
from ..model_series import BGE_SERIES

Model.register(
    dict(
        model_id = "bge-reranker-v2-m3",
        supported_engines=[vllm_embedding_engine066],
        supported_instances=[
            g4dn2xlarge_instance,
            g5dxlarge_instance,
            g5d2xlarge_instance,
            g5d4xlarge_instance,
            g5d8xlarge_instance,
            # g5d12xlarge_instance,
            g5d16xlarge_instance,
            local_instance
            # g5d24xlarge_instance,
            # g5d48xlarge_instance,
        ],
        supported_services=[
            sagemaker_service,
            ecs_service,
            local_service
        ],
        supported_frameworks=[
            fastapi_framework
        ],
        allow_china_region=True,
        huggingface_model_id="BAAI/bge-reranker-v2-m3",
        modelscope_model_id="BAAI/bge-reranker-v2-m3",
        require_huggingface_token=False,
        application_scenario="RAG",
        model_type=ModelType.RERANK,
        model_series=BGE_SERIES
    )
)



Model.register(
    dict(
        model_id = "bge-reranker-large",
        supported_engines=[vllm_embedding_engine066],
        supported_instances=[
            g4dn2xlarge_instance,
            g5dxlarge_instance,
            g5d2xlarge_instance,
            g5d4xlarge_instance,
            g5d8xlarge_instance,
            # g5d12xlarge_instance,
            g5d16xlarge_instance,
            local_instance
            # g5d24xlarge_instance,
            # g5d48xlarge_instance,
        ],
        supported_services=[
            sagemaker_service,
            ecs_service,
            local_service
        ],
        supported_frameworks=[
            fastapi_framework
        ],
        allow_china_region=True,
        huggingface_model_id="BAAI/bge-reranker-large",
        modelscope_model_id="BAAI/bge-reranker-large",
        require_huggingface_token=False,
        application_scenario="RAG",
        model_type=ModelType.RERANK,
        model_series=BGE_SERIES
    )
)
