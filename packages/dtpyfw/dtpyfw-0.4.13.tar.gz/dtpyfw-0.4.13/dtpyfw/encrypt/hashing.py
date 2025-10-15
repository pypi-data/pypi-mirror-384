from passlib.context import CryptContext

pwd_cxt = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated=["bcrypt"],
    bcrypt__truncate_error=False,
)


__all__ = ("Hash",)


class Hash:

    @staticmethod
    def crypt(password: str):
        return pwd_cxt.hash(password)

    @staticmethod
    def verify(plain_password: str, hashed_password: str):
        return pwd_cxt.verify(plain_password, hashed_password)

    @staticmethod
    def needs_update(hashed_password: str):
        return pwd_cxt.needs_update(hashed_password)
    