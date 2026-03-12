from __future__ import annotations

import base64
from io import BytesIO
from typing import List

import numpy as np
from PIL import Image
import cohere

from .base_embeddings import EmbeddingsProvider


def _image_to_base64_data_url(image_path: str, force_png: bool = False) -> str:
    """Convert to base64 data URL compatible with Cohere v2 API for embeddings."""
    with Image.open(image_path) as img:
        buffered = BytesIO()
        if force_png:
            img.save(buffered, format="PNG")
            mime = "image/png"
        else:
            # preserve original
            img.save(buffered, format=img.format)
            mime = f"image/{img.format.lower()}"
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        data_url = f"data:{mime};base64,{img_base64}"
        return data_url


class CohereEmbeddingsV4(EmbeddingsProvider):
    def __init__(
        self,
        api_key: str,
        model_id: str = "embed-v4.0",
        output_dimension: int = 1024,
        embedding_type: str = "float",
        batch_size: int = 32,
        use_inputs_object: bool = False,
    ):
        self._co = cohere.ClientV2(api_key=api_key)
        self._model = model_id
        self._output_dimension = output_dimension
        self._embedding_type = embedding_type
        self._batch_size = batch_size
        self._use_inputs_object = use_inputs_object

    @property
    def dim(self) -> int:
        return self._output_dimension

    def embed_images(self, image_paths: list[str]) -> np.ndarray:
        """Batch embed page images using Cohere embed-v4.0.

        Uses the 'images' parameter with input_type='image' (see Cohere docs).
        """
        all_vecs = []
        for i in range(0, len(image_paths), self._batch_size):
            batch = image_paths[i : i + self._batch_size]
            images_b64 = [_image_to_base64_data_url(p, force_png=True) for p in batch]
            res = self._co.embed(
                images=images_b64,
                model=self._model,
                embedding_types=[self._embedding_type],
                input_type="image",
                output_dimension=self._output_dimension,
            )
            # extract floats
            vecs = getattr(res.embeddings, self._embedding_type)
            all_vecs.extend(vecs)
        return np.asarray(all_vecs, dtype="float32")

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """Embed text queries with input_type='search_query' so they are comparable
        against image embeddings (same multimodal space)."""
        all_vecs = []
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i : i + self._batch_size]
            res = self._co.embed(
                model=self._model,
                texts=batch,
                input_type="search_query",
                embedding_types=[self._embedding_type],
                output_dimension=self._output_dimension,
            )
            vecs = getattr(res.embeddings, self._embedding_type)
            all_vecs.extend(vecs)
        return np.asarray(all_vecs, dtype="float32")
