import time
import threading
from typing import Callable

from src.infra.logger import LoggerProtocol


class LoggerStdout(LoggerProtocol):
    def print(self, message: str):
        print(message)

    def print_spinner(self, message: str) -> Callable[[str], None]:
        # Runing as CLI do animated console output
        def spinner():
            while not spinner_done:
                for ch in "|/-\\":
                    print(f"\r{message}{ch}\033[?25l", end="", flush=True)
                    time.sleep(0.1)

        spinner_done = False
        t = threading.Thread(target=spinner, daemon=True)
        t.start()

        def stop_spinner(message_postfix: str):
            nonlocal spinner_done
            spinner_done = True
            t.join()
            print(f"\r{message}\033[?25h", end="", flush=True)
            print(message_postfix)

        return stop_spinner
