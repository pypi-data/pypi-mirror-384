import logging
import multiprocessing
import os
import threading
import time
from typing import List

from langchain_core.embeddings import Embeddings

logging.basicConfig(format="%(levelname)s: %(message)s")

# Global variables shared across main and worker processes
_model_kwargs = {}  # Stores model init args from the main process
_model = None  # Will hold the model instance in worker
_pool = None  # The singleton multiprocessing pool
_pool_lock = threading.Lock()  # Ensures thread-safe pool creation and cleanup
_last_used = 0  # Timestamp of last embedding request
_idle_timeout = 120  # Seconds before idle pool is shut down


def _init_model():
    from .codesage_embeddings import CodeSageEmbeddings

    global _model, _model_kwargs
    pid = os.getpid()
    logging.info(f"[PoolWorker-{pid}] Initializing ONNX model in worker process")
    _model = CodeSageEmbeddings(**_model_kwargs)
    logging.info(f"[PoolWorker-{pid}] Model ready")


def _embed_query(text: str):
    return _model.embed_query(text)


def _embed_documents(texts: List[str]):
    return _model.embed_documents(texts)


# Lazily creates and returns the global pool
# Resets idle timeout on every use
def _get_or_create_pool():
    global _pool, _last_used
    with _pool_lock:
        if _pool is None:
            pid = os.getpid()
            try:
                logging.info(f"[Main-{pid}] Creating multiprocessing pool with shared ONNX model")
                _pool = multiprocessing.Pool(1, initializer=_init_model)
                _start_idle_timer()
            except Exception as e:
                logging.error(f"[Main-{pid}] Failed to start multiprocessing pool: {e}")
                raise
        _last_used = time.time()
    return _pool


# Shuts down and resets the pool
# Called from the idle monitor thread
def _cleanup_pool():
    global _pool
    logging.info("[Main] Idle timeout reached, shutting down pool")
    _pool.close()
    _pool.join()
    _pool = None


# Background thread that shuts down pool after period of inactivity
def _start_idle_timer():
    def _monitor():
        global _pool, _last_used
        while True:
            time.sleep(_idle_timeout)
            with _pool_lock:
                if _pool and (time.time() - _last_used) > _idle_timeout:
                    _cleanup_pool()
                    break

    threading.Thread(target=_monitor, daemon=True).start()


class CodeSageMultiprocEmbeddings(Embeddings):
    def __init__(self, **kwargs):
        global _model_kwargs
        _model_kwargs.update(kwargs)

    def embed_query(self, text: str):
        pool = _get_or_create_pool()
        return pool.apply(_embed_query, (text,))

    def embed_documents(self, texts: List[str]):
        pool = _get_or_create_pool()
        return pool.apply(_embed_documents, (texts,))
