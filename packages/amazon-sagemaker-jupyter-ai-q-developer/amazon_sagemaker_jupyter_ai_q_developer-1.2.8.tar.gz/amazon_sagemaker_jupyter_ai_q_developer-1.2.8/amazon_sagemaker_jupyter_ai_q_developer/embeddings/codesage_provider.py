from jupyter_ai_magics.embedding_providers import BaseEmbeddingsProvider

from .codesage_multiproc import CodeSageMultiprocEmbeddings


class CodeSageEmbeddingsProvider(BaseEmbeddingsProvider):
    id = "codesage"
    name = "CodeSage"
    models = ["codesage-small"]
    model_id_key = "model_id"
    pypi_package_deps = ["onnxruntime", "transformers", "numpy"]
    auth_strategy = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.embeddings = CodeSageMultiprocEmbeddings(**kwargs)

    def embed_documents(self, texts):
        return self.embeddings.embed_documents(texts)

    def embed_query(self, text):
        return self.embeddings.embed_query(text)

    def __call__(self, text):
        """Make the provider callable, which is expected by some LangChain components."""
        return self.embed_query(text)
