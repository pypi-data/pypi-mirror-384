import click
import logging

from src.config import EMBEDDINGS_MODEL, SPACY_TOKENIZER_MODEL, HTTP_PORT, set_allowed_dirs
from src.core.extractor import dowload_embeddings_model, download_spacy_model, initialize_keybert
from src.file_processor import keyphrases_from_textfile
from src.infra.logger import LoggerProtocol
from src.infra.logger_stdout import LoggerStdout
from src.infra.logger_system import LoggerSystem, configure_logging


@click.command()
@click.option(
    "--allowed-dir",
    "-a",
    multiple=True,
    required=False,
    type=click.Path(exists=True, file_okay=False),
    help="Allowed directory to read files from. You can specify this option multiple times.",
)
@click.option(
    "--http",
    "-H",
    is_flag=True,
    default=False,
    help="Run the MCP server with Streamable HTTP transport. When flag is missing its STDIO transport.",
)
@click.option(
    "--download-models",
    "-dm",
    is_flag=True,
    default=False,
    help=(
        "Don't run the server, download the embeddings and spaCy models only. "
        "Useful during initial setup, f.e. in docker image. "
        "Returns immideately if the model has been already downloaded."
    ),
)
@click.option(
    "--file",
    "-f",
    "file_path",
    required=False,
    type=click.Path(exists=True),
    help="Extract keyphrases from the text file at the given path instead of starting the MCP server.",
)
@click.option(
    "--file-keyphrases-count",
    "-k",
    required=False,
    type=int,
    help="Set the number of keyphrases returned (only works with --file option).",
)
def main(
    allowed_dir: tuple[str],
    http: bool,
    download_models: bool,
    file_path: str | None,
    file_keyphrases_count: int | None,
):
    if file_path is not None:
        if file_keyphrases_count is None:
            raise ValueError("--file-keyphrases-count should be specified.")
        logger = LoggerStdout()
        common_init(logger, ())
        keyphrases = keyphrases_from_textfile(file_path, file_keyphrases_count, logger)
        logger.print('{"keyphrases": ' + str(keyphrases) + "}")
    elif download_models:
        configure_logging()
        logger = LoggerSystem(logging.getLogger(__name__))
        dowload_embeddings_model(
            lambda: logger.print_spinner("Downloading embeddings model ~500MB ..."),
            lambda stop_spinner: stop_spinner("Done."),
        )
        download_spacy_model(
            lambda: logger.print_spinner("Downloading spacy model ~500MB ..."),
            lambda stop_spinner: stop_spinner("Done."),
        )
    else:
        configure_logging()
        logger = LoggerSystem(logging.getLogger(__name__))
        if len(allowed_dir) == 0:
            raise ValueError("At least one --allowed-dir argument should be specified.")
        logger.print("Keyphrases MCP server")
        common_init(logger, allowed_dir)
        from src.server import mcp

        if http:
            mcp.run(transport="streamable-http", port=HTTP_PORT)
        else:
            mcp.run(show_banner=False)


def common_init(logger: LoggerProtocol, allowed_dirs: tuple):
    dirs_list = list(allowed_dirs)
    set_allowed_dirs(dirs_list)
    logger.print("Allowed to read documents in: " + ", ".join(dirs_list))

    dowload_embeddings_model(
        lambda: logger.print_spinner("Downloading embeddings model ~500MB ..."),
        lambda stop_spinner: stop_spinner("Done."),
    )

    download_spacy_model(
        lambda: logger.print_spinner("Downloading spacy model ~500MB ..."),
        lambda stop_spinner: stop_spinner("Done."),
    )

    stop_spinner = logger.print_spinner(
        f"🚀 Starting with {EMBEDDINGS_MODEL} embeddings model and {SPACY_TOKENIZER_MODEL} tokenizer model..."
    )
    keybert_device, spacy_mode = initialize_keybert()
    stop_spinner(f"Done. KeyBERT runs on {keybert_device}. Spacy runs on {spacy_mode}.")


if __name__ == "__main__":
    main()
