from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Type

import numpy as np
from crewai.llm import LLM

EmbeddingVector = np.ndarray


@dataclass
class Embedder(ABC):
    def __init__(self, model: str, **kwargs):
        self.model = model
        self.kwargs = kwargs

    @abstractmethod
    async def embed(
        self,
        input: Any,
        metadata: Optional[Dict[str, Any]],
    ) -> EmbeddingVector: ...

    @abstractmethod
    async def embed_batch(
        self,
        input: List[Any],
        metadata: Optional[Dict[str, Any]],
    ) -> List[EmbeddingVector]: ...

    @abstractmethod
    def get_dimensions(self) -> int:
        pass


# class BGEEmbedder:
#     def __init__(self):
#         self.model = "ollama/qllama/bge-small-en-v1.5"
#         self.dimensions = 384
#
#     async def embed(self, text: str) -> np.ndarray:
#         embedder = OllamaEmbeddings(model=self.model.replace("ollama/", ""))
#         result = embedder.embed_query(text)
#         # print("bge small", result)
#
#         return np.array(result)


@dataclass
class ModelConfig:
    name: str
    loader: Type[LLM] | Type[Embedder]
    temp: float = 0.0
    max_tokens: int = 1000
    is_hosted: bool = False
    base_url: Optional[str] = None
    lazy_load: bool = False
    stream: bool = False
    reasoning_effort: Optional[Literal["low", "medium", "high", "none", "auto"]] = None
    extras: Dict[str, Any] = field(default_factory=dict, init=False)


class LLMStore(ABC):
    @abstractmethod
    def register_model(
        self,
        model_intent: str,
        model_config: ModelConfig,
    ) -> "LLMStore": ...

    @abstractmethod
    def planner(self) -> LLM: ...

    @abstractmethod
    def executor(self) -> LLM: ...

    @abstractmethod
    def load(self, model_intent: str) -> LLM | Embedder: ...

    @abstractmethod
    async def embed(self, text: str) -> EmbeddingVector: ...

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[EmbeddingVector]: ...

    @abstractmethod
    def get_model(self, model_intent: str) -> Optional[ModelConfig]: ...


LLMExecutorIntent = "executor"
LLMPlannerIntent = "planner"
LLMThinkerIntent = "thinker"
LLMCritiqueIntent = "critique"
LLMSubScenePlannerIntent = "sub_scene_planner"
LLMVideoGenIntent = "video_gen"
LLMImageGenIntent = "image_gen"
LLMASRIntent = "asr"
LLMEmbedderIntent = "embedder"


class GenerationHerd(LLMStore):
    _llm_store: Dict[str, ModelConfig | LLM | Embedder] = {}

    def _build_model_args(self, model_cfg: ModelConfig):
        model_args = {
            "model": model_cfg.name,
            "temperature": model_cfg.temp,
            "max_tokens": model_cfg.max_tokens,
            "stream": model_cfg.stream,
        }

        if model_cfg.reasoning_effort:
            model_args["reasoning_effort"] = model_cfg.reasoning_effort

        if model_cfg.is_hosted:
            assert (
                model_cfg.base_url is not None
            ), "hosted models need openai api compatible remote url"

            model_args["base_url"] = model_cfg.base_url

        return model_args

    def register_model(
        self, model_intent: str, model_config: ModelConfig, **kwargs
    ) -> "GenerationHerd":
        # if self._llm_store.get(model_intent, None) is not None:
        #     return self

        llmref = None

        if model_config.lazy_load:
            llmref = model_config

        elif model_config.loader == LLM:
            llmref = model_config.loader(**self._build_model_args(model_config))

        elif issubclass(model_config.loader, Embedder):
            llmref = model_config.loader(model=model_config.name, **kwargs)

        if llmref is None:
            raise Exception("Invalid LLM")

        self._llm_store[model_intent] = llmref

        return self

    def get_model(self, model_intent: str):
        model_config = self._llm_store.get(model_intent, None)
        if model_config is None:
            return None

        if isinstance(model_config, ModelConfig):
            return model_config

        if isinstance(model_config, LLM):
            return ModelConfig(
                name=model_config.model,
                temp=model_config.temperature or 0,
                loader=LLM,
            )

        return None

    def planner(self) -> LLM:
        model = self.load(LLMPlannerIntent)
        assert isinstance(model, LLM), "BadPlanner"

        return model

    def executor(self) -> LLM:
        model = self.load(LLMExecutorIntent)
        assert isinstance(model, LLM), "BadPlanner"

        return model

    def load(self, model_intent: str) -> LLM | Embedder:
        model_or_cfg = self._llm_store[model_intent]

        if isinstance(model_or_cfg, ModelConfig):
            # Rebuild every time — don't cache LLM instance
            model_args = self._build_model_args(model_or_cfg)

            if model_or_cfg.loader == LLM:
                return LLM(**model_args)
            elif issubclass(model_or_cfg.loader, Embedder):
                return model_or_cfg.loader(
                    model=model_or_cfg.name,
                    **model_args,
                )
            else:
                raise ValueError(f"Unsupported loader: {model_or_cfg.loader}")

        # If it's already an instance (e.g., Embedder), return as-is
        return model_or_cfg

    async def embed(self, text: str, **kwargs) -> EmbeddingVector:
        # model = SentenceTransformer("all-MiniLM-L6-v2")
        model = self.load(LLMEmbedderIntent)
        assert not isinstance(model, LLM), "Invalid embedder"

        kwargs["convert_to_numpy"] = True

        vec = await model.embed(text, **kwargs)
        assert isinstance(vec, EmbeddingVector), "NoEmbeddingResponse"

        return np.array(vec)

    async def embed_batch(self, *args, **kwargs) -> List[EmbeddingVector]:
        model = self.load(LLMEmbedderIntent)
        assert not isinstance(model, LLM), "Shouldn'tBeLLM"

        vectors = await model.embed(*args, **kwargs)

        return [np.array(vec) for vec in vectors]


OpenAiHerd = (
    GenerationHerd()
    .register_model(
        LLMPlannerIntent,
        ModelConfig(
            name="openai/gpt-4.1",
            is_hosted=False,
            temp=0.8,
            lazy_load=True,
            loader=LLM,
            max_tokens=22000,
        ),
    )
    .register_model(
        LLMThinkerIntent,
        ModelConfig(
            name="openai/gpt-4.1-mini",  # used by bookwriter, can be llama3.1 long writer
            is_hosted=False,
            temp=0.8,
            lazy_load=True,
            loader=LLM,
            max_tokens=30000,
            reasoning_effort="low",
        ),
    )
    .register_model(
        LLMExecutorIntent,
        ModelConfig(
            name="openai/gpt-4.1-mini",  # chapterbuilder, try llama3.1
            is_hosted=False,
            temp=0.0,
            loader=LLM,
            max_tokens=12000,
            reasoning_effort="medium",  # For prose-to-comic adaptation
        ),
    )
    .register_model(
        LLMVideoGenIntent,
        ModelConfig(
            name="openai/sora-2",
            loader=LLM,  # NOTE: override with api calls
            is_hosted=False,
        ),
    )
    .register_model(
        LLMASRIntent,
        ModelConfig(
            name="whisper",
            loader=LLM,  # NOTE: custom llm
            is_hosted=False,
        ),
    )
    .register_model(
        LLMImageGenIntent,
        ModelConfig(
            # name="gpt-5-mini-2025-08-07",
            name="gemini/gemini-2.5-flash-image-preview",
            loader=LLM,
            is_hosted=False,
        ),
    )
    .register_model(
        LLMCritiqueIntent,
        ModelConfig(
            name="gemini/gemini-2.5-pro",
            loader=LLM,
            is_hosted=False,
            max_tokens=22000,
        ),
    )
)

GeminiHerd = OpenAiHerd

# GeminiHerd = (
#     GenerationHerd()
#     .register_model(
#         LLMPlannerIntent,
#         ModelConfig(
#             name="gemini/gemini-2.5-flash-preview-09-2025",
#             is_hosted=False,
#             temp=0.8,
#             lazy_load=True,
#             loader=LLM,
#             max_tokens=22000,
#         ),
#     )
#     .register_model(
#         LLMThinkerIntent,
#         ModelConfig(
#             name="gemini/gemini-2.5-pro",
#             is_hosted=False,
#             temp=0.8,
#             lazy_load=True,
#             loader=LLM,
#             max_tokens=22000,
#             reasoning_effort="medium",
#         ),
#     )
#     .register_model(
#         LLMExecutorIntent,
#         ModelConfig(
#             name="gemini/gemini-2.5-flash-lite-preview-09-2025",
#             is_hosted=False,
#             temp=0.0,
#             loader=LLM,
#             max_tokens=12000,
#         ),
#     )
#     .register_model(
#         LLMVideoGenIntent,
#         ModelConfig(
#             name="gemini/veo-3.1-fast-generate-preview",
#             loader=LLM,  # NOTE: litellm: https://docs.litellm.ai/docs/videos
#             is_hosted=False,
#         ),
#     )
#     .register_model(
#         LLMASRIntent,
#         ModelConfig(
#             name="gemini/gemini-2.5-flash-preview-09-2025",
#             loader=LLM,  # NOTE: litellm support
#             is_hosted=False,
#         ),
#     )
#     .register_model(
#         LLMImageGenIntent,
#         ModelConfig(
#             name="gemini/gemini-2.5-flash-image-preview",
#             loader=LLM,
#             is_hosted=False,
#         ),
#     )
#     .register_model(
#         LLMCritiqueIntent,
#         ModelConfig(
#             name="openai/gpt-4.1",
#             loader=LLM,
#             is_hosted=False,
#             max_tokens=22000,
#         ),
#     )
# )

# OpenAiPlannerAndQwenExecutorHerd = (
#     GenerationHerd()
#     .register_model(
#         LLMExecutorIntent,
#         ModelConfig(
#             name="ollama/qwen2.5-coder:7b",
#             is_hosted=True,
#             base_url="http://localhost:11434",
#             temp=0.0,
#             lazy_load=True,
#             loader=LLM,
#         ),
#     )
#     .register_model(
#         LLMPlannerIntent,
#         ModelConfig(
#             name="openai/gpt-4.1-nano",
#             is_hosted=False,
#             temp=0.0,
#             lazy_load=True,
#             loader=LLM,
#         ),
#     )
#     .register_model(
#         LLMEmbedderIntent,
#         ModelConfig(
#             name="all-MiniLM-L6-v2",
#             is_hosted=True,
#             loader=SentenceTransformer,
#         ),
#     )
# )
#
#
# VLLMQwenPlannerAndExecutor = (
#     GenerationHerd()
#     .register_model(
#         LLMPlannerIntent,
#         ModelConfig(
#             name="hosted_vllm/Qwen/Qwen2.5-Coder-7B-Instruct",
#             is_hosted=True,
#             base_url="http://10.147.20.55:8181/{model}/v1",
#             temp=0.0,
#             lazy_load=True,
#             loader=LLM,
#         ),
#     )
#     .register_model(
#         LLMExecutorIntent,
#         ModelConfig(
#             name="hosted_vllm/Qwen/Qwen2.5-Coder-7B-Instruct",
#             is_hosted=True,
#             base_url="http://10.147.20.55:8181/{model}/v1",
#             temp=0.0,
#             lazy_load=True,
#             loader=LLM,
#         ),
#     )
#     .register_model(
#         LLMEmbedderIntent,
#         ModelConfig(
#             name="all-MiniLM-L6-v2",
#             is_hosted=True,
#             loader=SentenceTransformer,
#         ),
#     )
# )
