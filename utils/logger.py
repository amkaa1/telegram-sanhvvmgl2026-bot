import logging
import sys
import io


def setup_logging(level: str = "INFO") -> None:
    stream = sys.stdout
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")
    elif hasattr(stream, "buffer"):
        stream = io.TextIOWrapper(stream.buffer, encoding="utf-8", errors="replace")

    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(stream)],
        force=True,
    )


logger = logging.getLogger("telegram_growth_bot")

