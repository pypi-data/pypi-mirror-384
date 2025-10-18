import logging


def setup_logging() -> None:
    """Setup root logger once."""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s"
    )
