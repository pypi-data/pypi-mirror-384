"""Embedding helpers for EmbeddingGemma integration."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Iterable, List, Sequence

LOGGER = logging.getLogger(__name__)

REMOTE_ENV_VAR = "EMBEDDING_GEMMA_ENDPOINT"
MODEL_PATH_ENV_VAR = "EMBEDDING_GEMMA_MODEL_PATH"
MAX_LENGTH_ENV_VAR = "EMBEDDING_GEMMA_MAX_LENGTH"
STUB_ENV_VAR = "EMBEDDING_GEMMA_STUB"
DEFAULT_MAX_LENGTH = 2048


class EmbeddingBackend:
    """Interface all embedding backends must implement."""

    def embed_many(self, texts: Sequence[str]) -> List[List[float]]:  # pragma: no cover - interface only
        raise NotImplementedError


class StubEmbeddingBackend(EmbeddingBackend):
    """Returns zero vectors without performing any model inference."""

    def __init__(self, dim: int):
        self.dim = dim

    def embed_many(self, texts: Sequence[str]) -> List[List[float]]:
        LOGGER.warning("EmbeddingGemma stub backend active; returning zero vectors")
        return [[0.0] * self.dim for _ in texts]


@dataclass
class RemoteEmbeddingBackend(EmbeddingBackend):
    """HTTP client for a remote EmbeddingGemma-compatible endpoint."""

    endpoint: str
    model: str
    timeout: float = 60.0

    def embed_many(self, texts: Sequence[str]) -> List[List[float]]:
        if not texts:
            return []
        try:
            import requests
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise RuntimeError(
                "The 'requests' package is required for remote embedding calls. "
                "Install it or unset EMBEDDING_GEMMA_ENDPOINT."
            ) from exc

        payload = {"model": self.model, "input": list(texts)}
        LOGGER.debug("Embedding %s texts via remote endpoint %s", len(texts), self.endpoint)
        response = requests.post(self.endpoint, json=payload, timeout=self.timeout)
        try:
            response.raise_for_status()
        except Exception as exc:  # pragma: no cover - network errors
            raise RuntimeError(f"Remote embedding request failed: {exc}") from exc

        try:
            data = response.json()
        except ValueError as exc:  # pragma: no cover - invalid JSON
            raise RuntimeError("Remote embedding response was not valid JSON") from exc

        vectors = data.get("vectors")
        if vectors is None and "data" in data:
            records = data["data"]
            if isinstance(records, list):
                vectors = [record.get("embedding") for record in records]
        if not isinstance(vectors, list):
            raise RuntimeError("Remote embedding response missing 'vectors' data")

        if len(vectors) != len(texts):
            raise RuntimeError(
                f"Remote embedding length mismatch: expected {len(texts)} vectors, got {len(vectors)}"
            )

        parsed: List[List[float]] = []
        for idx, vec in enumerate(vectors):
            if not isinstance(vec, (list, tuple)):
                raise RuntimeError(f"Remote embedding #{idx} was not a list of floats")
            parsed.append([float(x) for x in vec])
        return parsed


class LocalEmbeddingBackend(EmbeddingBackend):
    """Local EmbeddingGemma runner using HuggingFace Transformers."""

    def __init__(self, model: str, dim: int, quantize: int, max_length: int = DEFAULT_MAX_LENGTH):
        self.model_name = self._resolve_model_path(model)
        self.dim = dim
        self.quantize = quantize
        self.max_length = max_length
        self._tokenizer = None
        self._model = None
        self._device = None
        self._use_device_map = False

    def _resolve_model_path(self, model: str) -> str:
        override = os.getenv(MODEL_PATH_ENV_VAR)
        if override:
            LOGGER.info("Using EmbeddingGemma model override from %s", MODEL_PATH_ENV_VAR)
            return override
        return model

    def _ensure_model(self) -> None:
        if self._model is not None:
            return
        try:
            import torch
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise RuntimeError(
                "PyTorch is required for local EmbeddingGemma inference. "
                "Install torch or set EMBEDDING_GEMMA_ENDPOINT."
            ) from exc

        try:
            from transformers import AutoModel, AutoTokenizer
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise RuntimeError(
                "transformers is required for local EmbeddingGemma inference. "
                "Install transformers or set EMBEDDING_GEMMA_ENDPOINT."
            ) from exc

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        LOGGER.info("Loading EmbeddingGemma model '%s' on device %s", self.model_name, device)
        tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)

        attempt_quantized = bool(self.quantize and self.quantize <= 8)
        load_kwargs = {}
        if attempt_quantized:
            load_kwargs = {"load_in_8bit": True, "device_map": "auto"}
            LOGGER.info("Attempting to load model in 8-bit quantized mode")

        def _load_model(kwargs: dict) -> object:
            try:
                return AutoModel.from_pretrained(self.model_name, **kwargs)
            except Exception as exc:  # pragma: no cover - dependency guard
                raise exc

        model = None
        if attempt_quantized:
            try:
                model = _load_model(load_kwargs)
                self._use_device_map = True
            except Exception as exc:
                LOGGER.warning("8-bit load failed (%s); retrying without quantization", exc)
                load_kwargs = {}

        if model is None:
            try:
                import torch
            except ImportError as exc:  # pragma: no cover - dependency guard
                raise RuntimeError(
                    "PyTorch is required for local EmbeddingGemma inference."
                ) from exc
            dtype = torch.float16 if device.type == "cuda" else torch.float32
            load_kwargs["torch_dtype"] = dtype
            try:
                model = _load_model(load_kwargs)
            except Exception as exc:  # pragma: no cover - dependency guard
                raise RuntimeError(f"Failed to load EmbeddingGemma model '{self.model_name}': {exc}") from exc
            model = model.to(device)
            self._use_device_map = False

        model.eval()
        self._tokenizer = tokenizer
        self._model = model
        self._device = device

    def embed_many(self, texts: Sequence[str]) -> List[List[float]]:
        if not texts:
            return []
        self._ensure_model()

        import torch

        assert self._tokenizer is not None and self._model is not None  # for type checkers
        tokenizer = self._tokenizer
        model = self._model

        encoded = tokenizer(
            list(texts),
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )

        if not self._use_device_map:
            encoded = {k: v.to(self._device) for k, v in encoded.items()}

        with torch.no_grad():
            outputs = model(**encoded)
            if not hasattr(outputs, "last_hidden_state"):
                raise RuntimeError("EmbeddingGemma model output missing last_hidden_state")
            hidden = outputs.last_hidden_state
            attention_mask = encoded["attention_mask"].to(hidden.device)
            mask = attention_mask.unsqueeze(-1)
            masked_hidden = hidden * mask
            summed = masked_hidden.sum(dim=1)
            counts = mask.sum(dim=1).clamp(min=1)
            pooled = summed / counts
            pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
            vectors = pooled.detach().cpu().to(torch.float32)

        actual_dim = vectors.shape[1]
        if self.dim and self.dim != actual_dim:
            if actual_dim > self.dim:
                LOGGER.debug("Truncating embeddings from %s to %s dims", actual_dim, self.dim)
                vectors = vectors[:, : self.dim]
            else:
                LOGGER.debug("Padding embeddings from %s to %s dims", actual_dim, self.dim)
                pad_width = self.dim - actual_dim
                vectors = torch.nn.functional.pad(vectors, (0, pad_width))

        return vectors.tolist()


class EmbeddingClient:
    """Thin wrapper that selects local or remote EmbeddingGemma backends."""

    def __init__(self, model: str, dim: int, quantize: int, remote_override: str | None = None):
        self.model = model
        self.dim = dim
        self.quantize = quantize
        self.remote_endpoint = remote_override or os.getenv(REMOTE_ENV_VAR)
        self.max_length = int(os.getenv(MAX_LENGTH_ENV_VAR, DEFAULT_MAX_LENGTH))
        self.stub_enabled = os.getenv(STUB_ENV_VAR)
        self._backend: EmbeddingBackend | None = None

    def _ensure_backend(self) -> EmbeddingBackend:
        if self._backend is not None:
            return self._backend

        if self.stub_enabled:
            LOGGER.info("EmbeddingGemma stub mode enabled via %s", STUB_ENV_VAR)
            self._backend = StubEmbeddingBackend(dim=self.dim)
        elif self.remote_endpoint:
            LOGGER.info("EmbeddingGemma remote endpoint configured: %s", self.remote_endpoint)
            self._backend = RemoteEmbeddingBackend(endpoint=self.remote_endpoint, model=self.model)
        else:
            LOGGER.info("Using local EmbeddingGemma runtime for model %s", self.model)
            self._backend = LocalEmbeddingBackend(
                model=self.model,
                dim=self.dim,
                quantize=self.quantize,
                max_length=self.max_length,
            )
        return self._backend

    def embed_many(self, texts: Iterable[str]) -> List[List[float]]:
        text_list = list(texts)
        if not text_list:
            return []
        backend = self._ensure_backend()
        return backend.embed_many(text_list)
