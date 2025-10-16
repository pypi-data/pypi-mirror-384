from src import logger
from src.email_sender import send_email_str
from src.scrapers import generic
from src.scrapers.generic import (
    read_data_compressed,
    save_data_compressed,
    save_healthcheck_file,
)
from difflib import ndiff


def scrape(url: str, percentage: float = 10):
    session = generic.create_tls_session()

    old_data = read_data_compressed()

    data = generic.make_tls_request("GET", url, session)

    save_data_compressed(data)

    if old_data is None:
        logger.info("No old data found")
        return

    diff_percentage = compare(old_data, data)

    if diff_percentage >= percentage:
        logger.info("Change in data")
        send_email_str(f"Change in data: {data}")

    save_healthcheck_file(".diff_healthcheck")


def compare(old: str, new: str) -> float:
    diff = list(ndiff(old.splitlines(), new.splitlines()))
    changes = sum(1 for line in diff if line.startswith("+ ") or line.startswith("- "))
    total_lines = max(len(old.splitlines()), len(new.splitlines()))
    difference_percentage = (changes / total_lines) * 100 if total_lines > 0 else 0
    logger.debug(
        f"Changes: {changes}, Total lines: {total_lines}, Difference percentage: {difference_percentage}"
    )
    return difference_percentage
