# Encryption Sub-Package

**DealerTower Python Framework** — Simplifies password hashing and JSON Web Token handling with easy‑to‑use helpers.

## Overview

The `encryption` sub-package offers:

- **Password Hashing** using `passlib` (bcrypt) via a unified `Hash` class.
- **JWT Management** using `python-jose` for token creation and verification (`jwt_encrypt`, `jwt_decrypt`).
- **Consistent Data Encoding** for safe JSON serialization of claims.
- **Subject Validation** and optional expiration checks for robust token workflows.

This sub-package reduces boilerplate in securing microservice endpoints and user credentials.

## Installation

Install the `encryption` extra to include required dependencies:

```bash
pip install dtpyfw[encrypt]
```

## Password Hashing

### `Hash` Class

Provides static methods for password hashing and verification:

```python
from dtpyfw.encrypt.hashing import Hash

# Generate a bcrypt hash
hashed = Hash.crypt("my_secret_password")

# Verify plaintext against stored hash
is_valid = Hash.verify("my_secret_password", hashed)
```

**Methods:**

| Method                                                      | Description                                           |
|-------------------------------------------------------------|-------------------------------------------------------|
| `crypt(password: str) -> str`                               | Generate a bcrypt hash of the given password.         |
| `verify(plain_password: str, hashed_password: str) -> bool` | Check if a plain password matches the hashed value.   |

## JSON Web Tokens (JWT)

### `jwt_encrypt`

Create a signed JWT with custom claims and optional expiration:

```python
from datetime import timedelta
from dtpyfw.encrypt.encryption import jwt_encrypt

token = jwt_encrypt(
    tokens_secret_key="supersecret",
    encryption_algorithm="HS256",
    subject="user123",
    claims={"role": "admin"},
    expiration_timedelta=timedelta(hours=2)
)
```

**Parameters:**

- `tokens_secret_key` (`str`): Secret key for signing.
- `encryption_algorithm` (`str`): Algorithm name (e.g., `"HS256"`).
- `subject` (`str`): Subject claim stored under `"subject"`, typically a user identifier.
- `claims` (`dict`): Additional payload claims.
- `expiration_timedelta` (`timedelta`, optional): Time until expiration; if omitted, token never expires.

**Returns:**  
`str` — Encoded JWT token.

### `jwt_decrypt`

Verify and decode a JWT, ensuring subject matches and optionally enforcing expiration:

```python
from dtpyfw.encrypt.encryption import jwt_decrypt

decoded = jwt_decrypt(
    tokens_secret_key="supersecret",
    encryption_algorithm="HS256",
    token=token,
    subject="user123",
    check_exp=True
)
```

**Parameters:**

- `tokens_secret_key` (`str`): Secret key used to sign token.
- `encryption_algorithm` (`str`): Algorithm used (e.g., `"HS256"`).
- `token` (`str`): JWT string to decode.
- `subject` (`str`): Expected subject; mismatch raises `Exception('wrong_token_subject')`.
- `check_exp` (`bool`, default `True`): Enforce expiration (`exp`) claim.

**Returns:**  
`dict` — Decoded token data (claims including `subject` and any custom fields).

**Exceptions:**

- Raises generic `Exception('wrong_token_subject')` if `subject` claim differs.
- Propagates other `jwt` decoding exceptions for invalid or expired tokens.

## Example Workflow

```python
from datetime import timedelta
from dtpyfw.encrypt.hashing import Hash
from dtpyfw.encrypt.encryption import jwt_encrypt, jwt_decrypt

# 1. Hash user password
stored_hash = Hash.crypt("password123")

# 2. Verify at login
assert Hash.verify("password123", stored_hash)

# 3. Issue token
token = jwt_encrypt(
    tokens_secret_key="mykey",
    encryption_algorithm="HS256",
    subject="userid_42",
    claims={"scope": ["read", "write"]},
    expiration_timedelta=timedelta(minutes=30)
)

# 4. Decode on request
try:
    payload = jwt_decrypt("mykey", "HS256", token, subject="userid_42")
    print("Token valid, claims:", payload)
except Exception as err:
    print("Token error:", err)
```
