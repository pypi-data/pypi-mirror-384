import time

from src.core.extractor import extract_keyphrases
from src.infra.logger import LoggerProtocol


def keyphrases_from_textfile(file_path: str, keyphrases_count: int, logger: LoggerProtocol) -> list[str]:
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    text_len = len(text)
    stop_spinner = logger.print_spinner(
        f"🔧 Extracting {keyphrases_count} keyphrases from the file: {file_path} of {text_len} characters..."
    )
    start_time = time.time()
    keyphrases = extract_keyphrases(text, [], keyphrases_count)
    elapsed_time = time.time() - start_time
    stop_spinner(f"Done in {elapsed_time:.2f} seconds.\n")
    return keyphrases
