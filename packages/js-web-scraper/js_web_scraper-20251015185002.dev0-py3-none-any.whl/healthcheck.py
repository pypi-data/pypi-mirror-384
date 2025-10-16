import os

from dotenv import load_dotenv

from src.scrapers import generic

if __name__ == "__main__":
    load_dotenv()
    sleep_time_sec = int(os.environ["SLEEP_TIME_SEC"])
    scraper = os.environ.get("SCRAPER", "")
    match scraper:
        case "text":
            up_to_date = generic.healthcheck(".text_healthcheck", sleep_time_sec)
        case "diff":
            up_to_date = generic.healthcheck(".diff_healthcheck", sleep_time_sec)
        case "cars_com":
            up_to_date = generic.healthcheck(".cars_com_healthcheck", sleep_time_sec)
        case _:
            up_to_date = False

    if not up_to_date:
        exit(1)
