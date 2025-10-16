import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

os.environ["TOKENIZERS_PARALLELISM"] = "false"  # to avoid huggingface/tokenizers warning

PROJECT_ROOT = Path(__file__).parent.parent
embeddings_model_path = PROJECT_ROOT / "embeddings_model"


# Get environment variables


def getenv_type(name: str, default, type):
    value = os.getenv(name)
    if value is not None:
        return type(value)
    else:
        return default


EMBEDDINGS_MODEL = os.getenv("MCP_KEYPHRASES_EMBEDDINGS_MODEL") or "paraphrase-multilingual-MiniLM-L12-v2"

# It's hardcoded as project dependency, see pyproject.toml
SPACY_TOKENIZER_MODEL = os.getenv("MCP_KEYPHRASES_SPACY_TOKENIZER_MODEL") or "en_core_web_trf"

LOG_LEVEL = os.getenv("MCP_KEYPHRASES_LOG_LEVEL")

MAX_TEXT_LEN = getenv_type("MCP_KEYPHRASES_MAX_TEXT_LEN", default=6_000, type=int)

MAX_KEYPHRASES_COUNT = getenv_type("MCP_KEYPHRASES_MAX_KEYPHRASES_COUNT", default=200, type=int)

HTTP_PORT = getenv_type("MCP_KEYPHRASES_HTTP_PORT", default=8000, type=int)


allowed_dirs: list[str] = []


def set_allowed_dirs(dirs: list[str]):
    global allowed_dirs
    allowed_dirs = [str(Path(path).resolve()) for path in dirs]


def get_allowed_dirs() -> list[str]:
    global allowed_dirs
    return allowed_dirs
