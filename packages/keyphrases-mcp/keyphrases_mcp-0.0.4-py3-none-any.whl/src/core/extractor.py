from importlib.util import find_spec
import os
import shutil
from typing import Callable, cast, TYPE_CHECKING

if TYPE_CHECKING:
    from keybert import KeyBERT
    from sklearn.feature_extraction.text import CountVectorizer

from src.config import embeddings_model_path, EMBEDDINGS_MODEL, SPACY_TOKENIZER_MODEL

# Initialize global variables
keybert_instance: "KeyBERT | None" = None
default_stop_words: set[str] = set()


def dowload_embeddings_model(on_start: Callable[[], Callable], on_stop: Callable[[Callable], None]):
    config_path = embeddings_model_path / "config.json"

    # check if model is already downloaded
    load_model = not os.path.exists(str(config_path))
    if os.path.exists(str(config_path)):
        config = open(config_path, "r", encoding="utf-8").read()
        load_model = EMBEDDINGS_MODEL not in config

    if load_model:
        # Remove the directory and all its contents if it exists
        try:
            shutil.rmtree(embeddings_model_path)
        except FileNotFoundError:
            pass

        embeddings_model_path.mkdir(exist_ok=True)

        fun = on_start()

        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(f"sentence-transformers/{EMBEDDINGS_MODEL}")
        model.save(str(embeddings_model_path))

        on_stop(fun)


def download_spacy_model(on_start: Callable[[], Callable], on_stop: Callable[[Callable], None]):
    """Download the spacy model if not already installed."""
    if not find_spec(SPACY_TOKENIZER_MODEL):
        # Model not found, download it
        fun = on_start()

        import spacy.cli

        # Download the spaCy model without showing the animated progress bar
        spacy.cli.download(SPACY_TOKENIZER_MODEL)

        on_stop(fun)


def initialize_keybert() -> tuple[str, str]:
    global keybert_instance, default_stop_words
    if keybert_instance is not None:
        return "", ""

    import spacy
    import torch
    from keybert import KeyBERT
    from sentence_transformers import SentenceTransformer

    # Determine the best available device
    if torch.backends.mps.is_available():
        keybert_device = "mps"
    elif torch.cuda.is_available():
        keybert_device = "cuda"
    else:
        keybert_device = "cpu"

    # Configure spaCy to use GPU if available
    spacy_device = "cpu"
    if keybert_device == "cuda":
        # Try to use GPU for spaCy
        gpu_id = spacy.prefer_gpu()
        if gpu_id >= 0:
            spacy_device = "gpu"

    # Initialize SentenceTransformer with the specified device
    sentence_model = SentenceTransformer(str(embeddings_model_path), device=keybert_device)

    # Initialize KeyBERT with the device-enabled model
    keybert_instance = KeyBERT(model=sentence_model)

    # Load spaCy model after GPU configuration
    default_stop_words = spacy.load(SPACY_TOKENIZER_MODEL).Defaults.stop_words

    return keybert_device, spacy_device


def extract_keyphrases(text: str, stop_words: list[str], keyphrases_count: int) -> list[str]:
    if keybert_instance is None:
        raise RuntimeError("KeyBERT not initialized. Call common_init() first.")

    all_stop_words = default_stop_words.copy()
    all_stop_words.update(stop_words)

    from keyphrase_vectorizers import KeyphraseCountVectorizer

    vectorizer = KeyphraseCountVectorizer(
        lowercase=False,
        stop_words=list(all_stop_words),
        spacy_pipeline=SPACY_TOKENIZER_MODEL,
    )

    keyphrase_weights = keybert_instance.extract_keywords(
        docs=text,
        vectorizer=cast("CountVectorizer", vectorizer),
        top_n=keyphrases_count,
        use_mmr=True,
    )
    keyphrases = [str(phrase) for phrase, _weight in keyphrase_weights]
    keyphrases.sort()

    return keyphrases
