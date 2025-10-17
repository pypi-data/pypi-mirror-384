from . import ModelSeries
from .utils.constants import ModelSeriesType

QWEN2D5_SERIES = ModelSeries(
    model_series_name = ModelSeriesType.QWEN2D5,
    description="Qwen2.5 language models, including pretrained and instruction-tuned models of 7 sizes, including 0.5B, 1.5B, 3B, 7B, 14B, 32B, and 72B.",
    reference_link="https://github.com/QwenLM/Qwen2.5"
)

QWEN3_SERIES = ModelSeries(
    model_series_name = ModelSeriesType.QWEN3,
    description="the latest addition to the Qwen family of large language models. These models represent our most advanced and intelligent systems to date, improving from our experience in building QwQ and Qwen2.5. We are making the weights of Qwen3 available to the public, including both dense and Mixture-of-Expert (MoE) models.",
    reference_link="https://github.com/QwenLM/Qwen3"
)


GLM4_SERIES = ModelSeries(
    model_series_name = ModelSeriesType.GLM4,
    description="The GLM-4 series includes the latest generation of pre-trained models launched by Zhipu AI.",
    reference_link="https://github.com/THUDM/GLM-4"
)

INTERLM2d5_SERIES = ModelSeries(
    model_series_name=ModelSeriesType.INTERLM2d5,
    description="""InternLM2.5 has open-sourced a 20 billion parameter base model and a chat model tailored for practical scenarios. The model has the following characteristics:
- Outstanding reasoning capability: State-of-the-art performance on Math reasoning, surpassing models like Llama3 and Gemma2-27B.

- Stronger tool use: InternLM2.5 supports gathering information from more than 100 web pages, corresponding implementation has be released in MindSearch. InternLM2.5 has better tool utilization-related capabilities in instruction following, tool selection and reflection. See examples.""",
    reference_link="https://github.com/InternLM/InternLM"
)

WHISPER_SERIES = ModelSeries(
    model_series_name=ModelSeriesType.WHISPER,
    description="Whisper includes both English-only and multilingual checkpoints for ASR and ST, ranging from 38M params for the tiny models to 1.5B params for large.",
    reference_link="https://github.com/openai/whisper"
)

BGE_SERIES = ModelSeries(
    model_series_name=ModelSeriesType.BGE,
    description="BGE (BAAI General Embedding) focuses on retrieval-augmented LLMs, it currently includes kinds of embedding/rerank models.",
    reference_link="https://github.com/FlagOpen/FlagEmbedding"
)

BCE_SERIES = ModelSeries(
    model_series_name=ModelSeriesType.BCE,
    description="BCEmbedding: Bilingual and Crosslingual Embedding for RAG.",
    reference_link="https://huggingface.co/maidalun1020/bce-embedding-base_v1"
)

JINA_SERIES = ModelSeries(
    model_series_name=ModelSeriesType.JINA,
    description="Search foundation models: embeddings, rerankers, small LMs for better search",
    reference_link="https://huggingface.co/jinaai"
)

QWNE_EMBEDDING = ModelSeries(
    model_series_name=ModelSeriesType.JINA,
    description="Search foundation models: embeddings, rerankers, small LMs for better search",
    reference_link="https://huggingface.co/jinaai"
)

QWEN2VL_SERIES = ModelSeries(
    model_series_name=ModelSeriesType.QWEN2VL,
    description="""Qwen2-VL is the latest version of the vision language models in the Qwen model families.

Key Enhancements:
- SoTA understanding of images of various resolution & ratio: Qwen2-VL achieves state-of-the-art performance on visual understanding benchmarks, including MathVista, DocVQA, RealWorldQA, MTVQA, etc.

- Understanding videos of 20min+: with the online streaming capabilities, Qwen2-VL can understand videos over 20 minutes by high-quality video-based question answering, dialog, content creation, etc.

- Agent that can operate your mobiles, robots, etc.: with the abilities of complex reasoning and decision making, Qwen2-VL can be integrated with devices like mobile phones, robots, etc., for automatic operation based on visual environment and text instructions.

- Multilingual Support: to serve global users, besides English and Chinese, Qwen2-VL now supports the understanding of texts in different languages inside images, including most European languages, Japanese, Korean, Arabic, Vietnamese, etc.""",
    reference_link="https://github.com/QwenLM/Qwen2-VL"
)


AGENT_SERIES = ModelSeries(
    model_series_name=ModelSeriesType.AGENT,
    description="""LLM or VLM models for Agentic tasks, e.g. computer-use,brower-use""",
    reference_link=""
)

INTERNVL25_SERIES = ModelSeries(
    model_series_name=ModelSeriesType.INTERNVL25,
    description="""InternVL2.5 is an advanced multimodal large language model (MLLM) series with parameter coverage ranging from 1B to 78B. InternVL2_5-78B is the first open-source MLLMs to achieve over 70% on the MMMU benchmark, matching the performance of leading closed-source commercial models like GPT-4o.""",
    reference_link="https://github.com/OpenGVLab/InternVL"
)

COMFYUI_SERIES = ModelSeries(
    model_series_name=ModelSeriesType.COMFYUI,
    description="ComfyUI is a series of models that can be used to generate images from text prompts.",
    reference_link=""
)

QWEN_REASONING_MODEL = ModelSeries(
    model_series_name=ModelSeriesType.QWEN_REASONING_MODEL,
    description="Qwen Reasoning Model is a series of models that can be used to solve reasoning problems launched by Qwen team.",
    reference_link="https://qwenlm.github.io/zh/blog/qwq-32b-preview/\nhttps://qwenlm.github.io/zh/blog/qvq-72b-preview/"
)

LLAMA3_SERIES = ModelSeries(
    model_series_name=ModelSeriesType.LLAMA,
    description="""Llama is an accessible, open large language model (LLM) designed for developers, researchers, and businesses to build, experiment, and responsibly scale their generative AI ideas. Part of a foundational system, it serves as a bedrock for innovation in the global community. A few key aspects:

- Open access: Easy accessibility to cutting-edge large language models, fostering collaboration and advancements among developers, researchers, and organizations
- Broad ecosystem: Llama models have been downloaded hundreds of millions of times, there are thousands of community projects built on Llama and platform support is broad from cloud providers to startups - the world is building with Llama!
- Trust & safety: Llama models are part of a comprehensive approach to trust and safety, releasing models and tools that are designed to enable community collaboration and encourage the standardization of the development and usage of trust and safety tools for generative AI
Our mission is to empower individuals and industry through this opportunity while fostering an environment of discovery and ethical AI advancements. The model weights are licensed for researchers and commercial entities, upholding the principles of openness.""",
    reference_link="https://github.com/meta-llama/llama-models"
)

Gemma3_SERIES = ModelSeries(
    model_series_name=ModelSeriesType.GEMMA3,
    description="Gemma 3 is Google’s latest open-source multimodal AI model, supporting text, image, and video processing with up to 128K tokens of context. It comes in 1B, 4B, 12B, and 27B parameter sizes, offering high efficiency, with the largest model running on a single H100 GPU. Ranking among top AI models, Gemma 3 excels in multilingual tasks, function calling, and long-document understanding, making it ideal for diverse AI applications.",
    reference_link="https://blog.google/technology/developers/gemma-3/"
)

TXGEMMA_SERIES = ModelSeries(
    model_series_name=ModelSeriesType.TXGEMMA,
    description="TXGemma is a series of open models to accelerate the development of therapeutics.",
    reference_link="https://huggingface.co/collections/google/txgemma-release-67dd92e931c857d15e4d1e87"
)

MEDGEMMA_SERIES = ModelSeries(
    model_series_name=ModelSeriesType.MEDGEMMA,
    description="MedGemma is a collection of Gemma 3 variants that are trained for performance on medical text and image comprehension.",
    reference_link="https://huggingface.co/collections/google/medgemma-release-680aade845f90bec6a3f60c4"
)

MISTRAL_SERIES = ModelSeries(
    model_series_name=ModelSeriesType.MISTRAL,
    description="LLMs and VLMs provided by MISTRAL AI.",
    reference_link="https://huggingface.co/mistralai"
)

DEEPSEEK_REASONING_MODEL = ModelSeries(
    model_series_name=ModelSeriesType.DEEPSEEK_REASONING_MODEL,
    description="DeepSeek-R1-Zero and DeepSeek-R1 are innovative reasoning models, with the former showcasing strong performance through reinforcement learning alone, while the latter enhances reasoning capabilities by incorporating cold-start data, achieving results comparable to OpenAI-o1 and setting new benchmarks with its distilled versions.",
    reference_link="https://github.com/deepseek-ai/DeepSeek-R1"
)

DEEPSEEK_V3_SERIES = ModelSeries(
    model_series_name=ModelSeriesType.DEEPSEEK_v3,
    description="DeepSeek-R1-Zero and DeepSeek-R1 are innovative reasoning models, with the former showcasing strong performance through reinforcement learning alone, while the latter enhances reasoning capabilities by incorporating cold-start data, achieving results comparable to OpenAI-o1 and setting new benchmarks with its distilled versions.",
    reference_link="https://github.com/deepseek-ai/DeepSeek-R1"
)

BAICHAUN_SERIES= ModelSeries(
    model_series_name=ModelSeriesType.BAICHUAN,
    description="Baichuan Intelligent Technology.",
    reference_link="https://github.com/baichuan-inc"
)

GME_SERIES = ModelSeries(
    model_series_name=ModelSeriesType.GME,
    description="General Multimodal Embedding (GME) models based on Qwen2-VL architecture, designed for unified multimodal representation learning supporting text, image, and image-text pair inputs for retrieval and search applications.",
    reference_link="https://huggingface.co/Alibaba-NLP/gme-Qwen2-VL-7B-Instruct"
)

GPTOSS_SERIES = ModelSeries(
    model_series_name=ModelSeriesType.GPTOSS,
    description="GPT-OSS (GPT Open Source Software) is OpenAI's initiative to provide open-source AI models, making advanced language models accessible to developers, researchers, and organizations for building, experimenting, and scaling generative AI applications. These models are designed to foster innovation and collaboration in the open-source AI community.",
    reference_link="https://openai.com/index/introducing-gpt-oss/"
)

DOTS_OCR_SERIES = ModelSeries(
    model_series_name=ModelSeriesType.DOTS_OCR,
    description="dots.ocr is a powerful, multilingual document parser that unifies layout detection and content recognition within a single vision-language model while maintaining good reading order. Despite its compact 1.7B-parameter LLM foundation, it achieves state-of-the-art(SOTA) performance on text, tables, and reading order tasks with multilingual support for over 100 languages.",
    reference_link="https://github.com/rednote-hilab/dots.ocr"
)

HIGGS_AUDIO_SERIES = ModelSeries(
    model_series_name=ModelSeriesType.HIGGS_AUDIO,
    description="Higgs Audio v2 Generation is a powerful multimodal audio generation model that supports voice cloning, smart voice generation, and multi-speaker synthesis. Built on advanced neural architectures, it provides high-quality text-to-speech capabilities with support for various audio generation tasks including voice cloning and multi-speaker scenarios.",
    reference_link="https://huggingface.co/bosonai/higgs-audio-v2-generation-3B-base"
)
