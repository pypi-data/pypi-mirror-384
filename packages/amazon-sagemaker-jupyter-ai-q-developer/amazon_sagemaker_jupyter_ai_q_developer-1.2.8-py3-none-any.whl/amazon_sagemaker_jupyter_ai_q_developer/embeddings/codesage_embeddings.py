import logging
import os
from typing import Any, List

import numpy as np
import onnxruntime as ort
from langchain_core.embeddings import Embeddings
from pydantic import BaseModel, Field
from transformers import PreTrainedTokenizerFast

logging.basicConfig(format="%(levelname)s: %(message)s")


class CodeSageEmbeddings(BaseModel, Embeddings):
    model_id: str = "codesage-small"
    max_length: int = 1023  # Reserving 1 token for EOS
    session: Any = Field(default=None, exclude=True)
    tokenizer: Any = Field(default=None, exclude=True)
    eos_token: str = "<|endoftext|>"
    max_threads: int = 2  # Control CPU usage

    def __init__(self, **data):
        super().__init__(**data)
        self._load_model_and_tokenizer()

    def _load_model_and_tokenizer(self):
        base_path = os.path.join(os.path.dirname(__file__), "codesage", "codesage-small")
        model_path = os.path.join(
            base_path, "codesage-small-model.onnx.preprocessed.quantize_dynamic"
        )
        tokenizer_path = os.path.join(base_path, "tokenizer.json")

        # Load tokenizer
        if not os.path.exists(tokenizer_path):
            raise FileNotFoundError(f"Tokenizer file not found at {tokenizer_path}")

        try:
            self.tokenizer = PreTrainedTokenizerFast(
                tokenizer_file=tokenizer_path, eos_token=self.eos_token
            )
            self.tokenizer.add_special_tokens({"pad_token": "[PAD]"})
        except Exception as e:
            logging.error(f"Failed to load tokenizer: {str(e)}")
            raise

        # Load ONNX model
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}")

        providers = ort.get_available_providers()
        session_options = ort.SessionOptions()
        session_options.intra_op_num_threads = min(self.max_threads, os.cpu_count() or 1)
        session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        try:
            self.session = ort.InferenceSession(
                model_path, sess_options=session_options, providers=providers
            )
        except Exception as e:
            logging.info(f"Falling back to CPU execution provider. Error: {e}")
            self.session = ort.InferenceSession(
                model_path,
                sess_options=session_options,
                providers=["CPUExecutionProvider"],
            )

    def batch_encode_embeddings(self, text: str):
        """
        Process a single text through the model, handling it in chunks if needed.
        For texts longer than max_length, splits into chunks and averages embeddings.
        """

        all_embeddings = []

        # Use max_length as batch size for chunking text
        chunk_size = self.max_length
        for i in range(0, len(text), chunk_size):
            chunk_text = text[i : i + chunk_size]
            inputs = self.tokenizer(
                chunk_text,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="pt",
            )

            input_dict = {
                "input_ids": inputs["input_ids"].numpy(),
                "attention_mask": inputs["attention_mask"].numpy(),
            }

            outputs = self.session.run(None, input_dict)
            embeddings = np.mean(outputs[0], axis=1)
            all_embeddings.append(embeddings)

        # If we had chunks, concatenate them
        if all_embeddings:
            return np.concatenate(all_embeddings, axis=0)[0]
        return np.array([])

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        return [self.batch_encode_embeddings(text).tolist() for text in texts]

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query text."""
        return self.batch_encode_embeddings(text).tolist()
