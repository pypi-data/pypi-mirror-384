from dataclasses import dataclass
import json

from bs4 import BeautifulSoup
import pandas as pd
from pandas import DataFrame

from src import logger
from src.email_sender import send_email
from src.scrapers import generic
from src.scrapers.generic import save_data_csv, save_healthcheck_file


@dataclass
class Car:
    listing_id: str
    listing_url: str
    dealer_url: str
    listing_name: str
    price: str
    location: str

    def as_dict(self):
        return {
            "listing_id": self.listing_id,
            "listing_url": self.listing_url,
            "dealer_url": self.dealer_url,
            "listing_name": self.listing_name,
            "price": self.price,
            "location": self.location,
        }


def parse(data: str) -> list[Car]:
    cars_dict = []

    soup = BeautifulSoup(data, "html.parser")

    cars = json.loads(
        soup.find("div", {"class": "sds-page-section listings-page"})[
            "data-site-activity"
        ]
    )["vehicleArray"]

    for car in cars:
        location = car["dealer_zip"]
        dealer_link = car["dealer_name"]
        title = car["canonical_mmt"]
        price = car["msrp"]
        car_dict = Car(
            listing_id=car["listing_id"],
            listing_url=f"https://www.cars.com/vehicledetail/{car['listing_id']}",
            dealer_url=dealer_link,
            listing_name=title,
            price=price,
            location=location,
        )

        cars_dict.append(car_dict)

    return cars_dict


def check_new_listings(previous_cars: DataFrame, new_cars: list[Car]) -> DataFrame:
    new_cars_df = pd.DataFrame([x.as_dict() for x in new_cars])
    if len(previous_cars.columns) > 0:
        return new_cars_df[~new_cars_df["listing_id"].isin(previous_cars["listing_id"])]
    return new_cars_df


def scrape(url: str):
    session = generic.create_tls_session()

    old_data = generic.read_data_csv("cars_com.csv")
    if old_data is None:
        old_data = pd.DataFrame()

    data = generic.make_tls_request("GET", url, session)

    cars = parse(data)

    new_data = check_new_listings(old_data, cars)

    cars_df = pd.DataFrame([x.as_dict() for x in cars])

    save_data_csv(cars_df, "cars_com.csv")

    if new_data.shape[0] > 0:
        logger.info("Found new listings")
        send_email(new_data)

    save_healthcheck_file(".cars_com_healthcheck")
