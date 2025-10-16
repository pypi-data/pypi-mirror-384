import gzip
import os
import time
from typing import Literal

import pandas as pd
import tls_client
from typing_extensions import Optional, Union

from src import logger


def create_tls_session(proxy: str = None) -> tls_client.Session:
    """
    Create a TLS session with the given proxy, if applicable.
    :param proxy: Proxy string in the format https://user:pass@ip:port
    :return: tls_client.Session
    """
    session = tls_client.Session(
        client_identifier="chrome_120", random_tls_extension_order=True
    )
    if proxy:
        logger.debug("Setting proxy...")
        session.proxies = {"http": proxy, "https": proxy}

    return session


def make_tls_request(
    method: Literal["GET", "POST", "PUT", "DELETE"],
    url: str,
    session: tls_client.Session,
    params: Optional[dict] = None,
    data: Optional[Union[str, dict]] = None,
    headers: Optional[dict] = None,
    cookies: Optional[dict] = None,
    json: Optional[dict] = None,
    allow_redirects: Optional[bool] = False,
    insecure_skip_verify: Optional[bool] = False,
    timeout_seconds: Optional[int] = None,
    proxy: Optional[dict] = None,
):
    """
    Make a TLS request with the given parameters.
    :param method: The Method to use
    :param url: The URL to request
    :param session: The TLS session to use
    :param params: The parameters to send
    :param data: The data to send
    :param headers: The headers to send
    :param cookies: The cookies to send
    :param json: The JSON to send
    :param allow_redirects: allow_redirects parameter
    :param insecure_skip_verify: insecure_skip_verify parameter
    :param timeout_seconds: timeout_seconds parameter
    :param proxy: proxy parameter
    :return: The response content
    """
    response = session.execute_request(
        method,
        url,
        params=params,
        data=data,
        headers=headers,
        cookies=cookies,
        json=json,
        allow_redirects=allow_redirects,
        insecure_skip_verify=insecure_skip_verify,
        timeout_seconds=timeout_seconds,
        proxy=proxy,
    )

    if response.status_code <= 400:
        response_headers = response.headers
        if "application/json" in response_headers.get("Content-Type", ""):
            try:
                return response.json()
            except ValueError as e:
                logger.error("Response content is not valid JSON")
                raise e
        return response.content.decode(encoding="utf-8")

    raise ConnectionError(f"Request failed with status code {response.status_code}")


def read_data_compressed(file_name: str = "data.gz") -> str | None:
    # check if path exists
    path = f"./data/{file_name}"

    if not os.path.exists(path):
        return None

    with gzip.open(f"./data/{file_name}", "rt", encoding="utf-8") as f:
        return f.read()


def read_data_csv(file_name: str = "data.csv") -> pd.DataFrame | None:
    path = f"./data/{file_name}"

    if not os.path.exists(path):
        return None

    return pd.read_csv(path)


def save_data_compressed(data: str, file_name: str = "data.gz"):
    with gzip.open(f"./data/{file_name}", "wb") as f:
        f.write(data.encode())


def save_data_csv(data: pd.DataFrame, file_name: str = "data.csv"):
    data.to_csv(f"./data/{file_name}", index=False)


def save_healthcheck_file(file_name: str):
    with open(f"./data/{file_name}", "w") as f:
        f.write("OK")


def healthcheck(file_name: str, sleep_time_sec: int) -> bool:
    file_path = f"./data/{file_name}"
    if not os.path.exists(file_path):
        return False
    last_modified_time = os.path.getmtime(file_path)
    current_time = time.time()
    return (current_time - last_modified_time) <= (sleep_time_sec + 60)
