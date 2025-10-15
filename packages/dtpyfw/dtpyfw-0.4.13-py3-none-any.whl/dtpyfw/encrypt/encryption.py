from datetime import datetime, timedelta

from jose import jwt

from ..core.jsonable_encoder import jsonable_encoder

__all__ = (
    "jwt_encrypt",
    "jwt_decrypt",
)


def jwt_encrypt(
    tokens_secret_key: str,
    encryption_algorithm: str,
    subject: str,
    claims: dict,
    expiration_timedelta: timedelta = None,
):
    data = {
        "subject": subject,
    }
    if expiration_timedelta:
        data["exp"] = (datetime.now() + expiration_timedelta).timestamp()

    data.update(claims)
    return jwt.encode(
        claims=jsonable_encoder(data),
        key=tokens_secret_key,
        algorithm=encryption_algorithm,
    )


def jwt_decrypt(
    tokens_secret_key: str,
    encryption_algorithm: str,
    token: str,
    subject: str,
    check_exp: bool = True,
):
    options = {}
    if check_exp:
        options["require_exp"] = True
        options["verify_exp"] = True
    else:
        options["require_exp"] = False
        options["verify_exp"] = False

    decoded_token = jwt.decode(
        token=token,
        key=tokens_secret_key,
        algorithms=encryption_algorithm,
        options=options if options else None,
    )

    if decoded_token.get("subject") != subject:
        raise Exception("wrong_token_subject")

    return decoded_token
