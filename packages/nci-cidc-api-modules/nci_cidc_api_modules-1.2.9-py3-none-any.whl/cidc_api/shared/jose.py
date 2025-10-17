# external modules
import requests
from joserfc import jwt
from joserfc.jwk import RSAKey
from werkzeug.exceptions import Unauthorized
from cachetools import cached, TTLCache

# loacal modules
from ..config.settings import AUTH0_DOMAIN, AUTH0_CLIENT_ID


ALGORITHMS = ["RS256"]
TIMEOUT_IN_SECONDS = 20
PUBLIC_KEYS_CACHE = TTLCache(maxsize=3600, ttl=1024)  # 1 hour, 1 MB


@cached(cache=PUBLIC_KEYS_CACHE)
def get_jwks() -> list:
    # get jwks from our Auth0 domain
    return requests.get(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json", timeout=TIMEOUT_IN_SECONDS).json()


def decode_id_token(token: str) -> dict:
    """
    Decodes the token and checks it for validity.

    Args:
        token: the JWT to validate and decode

    Raises:
        Unauthorized:
            - if token is expired
            - if token has invalid claims (email, aud and iss)
            - if token signature is invalid

    Returns:
        dict: claims as a dictionary.
    """

    jwks = get_jwks()["keys"]
    if not jwks:
        raise Unauthorized("No public keys found")

    decoded_token = False

    for jwk in jwks:
        if decoded_token:
            continue
        try:
            key = RSAKey.import_key(jwk)
            decoded_token = jwt.decode(token, key, ALGORITHMS)
        except Exception as e:
            pass

    if decoded_token:
        claims = decoded_token.claims
    else:
        raise Unauthorized("No valid public key found")

    try:
        claims_requests = jwt.JWTClaimsRegistry(
            iss={"essential": True, "value": f"https://{AUTH0_DOMAIN}/"},
            aud={"essential": True, "value": AUTH0_CLIENT_ID},
            email={"essential": True},
        )
        claims_requests.validate(claims)
    except Exception as e:
        raise Unauthorized(str(e)) from e

    return claims
