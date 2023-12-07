import os
import requests
from typing import Union
from config import MAPILIO_API_ENDPOINT


def get_upload_token(email: str, password: str) -> dict:
    resp = requests.post(
        f"{MAPILIO_API_ENDPOINT}login",
        json={"email": email, "password": password},
    )
    # resp.raise_for_status()

    return resp.json()


def fetch_organization(
        user_access_token: str, organization_id: Union[int, str]
) -> requests.Response:
    resp = requests.get(
        f"{MAPILIO_API_ENDPOINT}{organization_id}",
        params={
            "fields": ",".join(["slug", "description", "name"]),
        },
        headers={
            "Authorization": f"OAuth {user_access_token}",
        },
    )
    resp.raise_for_status()
    return resp
