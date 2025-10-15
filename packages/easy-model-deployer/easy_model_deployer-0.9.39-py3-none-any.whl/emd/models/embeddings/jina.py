from .. import Model
from ..engines import huggingface_embedding_engine449,vllm_embedding_engine091
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
from emd.models import ModelSeries
from ..model_series import JINA_SERIES



Model.register(
    dict(
        model_id = "jina-embeddings-v3",
        supported_engines=[huggingface_embedding_engine449],
        supported_instances=[
            # g4dn2xlarge_instance,
            g5dxlarge_instance,
            g5d2xlarge_instance,
            g5d4xlarge_instance,
            g5d8xlarge_instance,
            # g5d12xlarge_instance,
            g5d16xlarge_instance,
            local_instance,
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
        huggingface_model_id="jinaai/jina-embeddings-v3",
        modelscope_model_id="jinaai/jina-embeddings-v3",
        require_huggingface_token=False,
        application_scenario="RAG",
        model_type=ModelType.EMBEDDING,
        model_series=JINA_SERIES
    )
)

Model.register(
    dict(
        model_id = "jina-embeddings-v4-vllm-retrieval",
        supported_engines=[vllm_embedding_engine091],
        supported_instances=[
            g5dxlarge_instance,
            g5d2xlarge_instance,
            g5d4xlarge_instance,
            g5d8xlarge_instance,
            local_instance,
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
        huggingface_model_id="jinaai/jina-embeddings-v4-vllm-retrieval",
        modelscope_model_id="jinaai/jina-embeddings-v4-vllm-retrieval",
        require_huggingface_token=False,
        application_scenario="RAG",
        model_type=ModelType.EMBEDDING,
        description="jina-embeddings-v4 is a universal embedding model for multimodal and multilingual retrieval",
        model_series=JINA_SERIES
    )
)
