"""Embedding service for generating text embeddings using ONNX Runtime."""

from pathlib import Path
from typing import List, Optional

import httpx
import numpy as np
import onnxruntime as ort
from moss_core import MODEL_DOWNLOAD_URL
from transformers import AutoTokenizer


class EmbeddingService:
    """Service for creating and managing embeddings using ONNX models."""

    def __init__(
        self, model_id: str, normalize: bool = True, quantized: bool = False
    ) -> None:
        """
        Creates a new embedding service.

        Args:
            model_id: The model identifier to use for embeddings
            normalize: Whether to normalize the embeddings
            quantized: Whether to use quantized models (not implemented)
        """
        self.model_id = model_id
        self.normalize = normalize
        self.quantized = quantized
        self._tokenizer: Optional[AutoTokenizer] = None
        self._session: Optional[ort.InferenceSession] = None
        self._is_model_loaded = False

    async def load_model(self) -> None:
        """Loads the ONNX embedding model from Cloudflare R2."""
        if self._is_model_loaded:
            return

        try:
            # Set up cache directory
            cache_dir = Path.home() / ".cache" / "moss-models" / self.model_id
            cache_dir.mkdir(parents=True, exist_ok=True)

            # Download model files if not cached
            model_url = f"{MODEL_DOWNLOAD_URL.rstrip('/')}/{self.model_id}"

            # Files to download
            files_to_download = [
                ("config.json", "config.json"),
                ("tokenizer.json", "tokenizer.json"),
                ("tokenizer_config.json", "tokenizer_config.json"),
                ("onnx/model.onnx", "model.onnx"),
            ]

            async with httpx.AsyncClient() as client:
                for remote_path, local_filename in files_to_download:
                    local_path = cache_dir / local_filename
                    if not local_path.exists():
                        response = await client.get(f"{model_url}/{remote_path}")
                        response.raise_for_status()
                        local_path.write_bytes(response.content)

            # Load tokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(str(cache_dir))

            # Load ONNX model
            model_path = str(cache_dir / "model.onnx")
            self._session = ort.InferenceSession(model_path)

            self._is_model_loaded = True

        except Exception as e:
            raise RuntimeError(f"Error loading model: {e}") from e

    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Creates embeddings for the provided texts.

        Args:
            texts: Texts to embed

        Returns:
            Array of embeddings
        """
        if not self._is_model_loaded:
            await self.load_model()

        if self._tokenizer is None or self._session is None:
            raise RuntimeError("Model tokenizer or session is not initialized")

        # Tokenize the texts
        inputs = self._tokenizer(  # type: ignore[operator]
            texts,
            padding=True,
            truncation=True,
            return_tensors="np",
            max_length=512,
        )

        # Run inference
        input_ids = inputs["input_ids"].astype(np.int64)
        attention_mask = inputs["attention_mask"].astype(np.int64)

        onnx_inputs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
        }

        # Add token_type_ids if the model expects it
        if "token_type_ids" in inputs:
            onnx_inputs["token_type_ids"] = inputs["token_type_ids"].astype(np.int64)
        else:
            # Create default token_type_ids (all zeros)
            onnx_inputs["token_type_ids"] = np.zeros_like(input_ids, dtype=np.int64)

        outputs = self._session.run(None, onnx_inputs)
        embeddings = outputs[0]  # Assuming the first output is the embeddings

        # Apply mean pooling
        attention_mask_expanded = np.expand_dims(attention_mask, -1)
        masked_embeddings = embeddings * attention_mask_expanded
        summed = np.sum(masked_embeddings, axis=1)
        counts = np.sum(attention_mask, axis=1, keepdims=True)
        mean_pooled = summed / np.maximum(counts, 1e-9)

        # Normalize if requested
        if self.normalize:
            norms = np.linalg.norm(mean_pooled, axis=1, keepdims=True)
            mean_pooled = mean_pooled / np.maximum(norms, 1e-9)

        return mean_pooled.tolist()

    async def create_embedding(self, text: str) -> List[float]:
        """
        Creates a single embedding for a text.

        Args:
            text: Text to embed

        Returns:
            The embedding
        """
        embeddings = await self.create_embeddings([text])
        return embeddings[0]

    @property
    def is_loaded(self) -> bool:
        """Checks if the model is loaded."""
        return self._is_model_loaded
