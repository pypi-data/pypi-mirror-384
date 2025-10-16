from typing import Optional

import jwt
import requests


TOKEN = requests.get("https://public-keys.teamtv.nl/app.teamtv.nl.pub").content

DEFAULT_LEEWAY = 15 * 60


def decode(jwt_token: str, app_id: Optional[str] = None, verify: bool = True):
    options = None
    if not verify:
        options = {"verify_signature": False}

    audience = None
    if app_id:
        audience = f"app:{app_id}"

    return jwt.decode(
        jwt_token,
        TOKEN,
        algorithms="RS256",
        verify=verify,
        audience=audience,
        options=options,
        leeway=DEFAULT_LEEWAY,
    )
