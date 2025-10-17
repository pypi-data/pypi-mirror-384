# more-sso-auth — Lightweight SSO for Python

A small, easy-to-use Single Sign-On (SSO) helper for Python apps and AWS Lambda.

**What it gives you**

* RS256 JWT validation using a public key fetched from a URL.
* In-memory caching for public keys (no constant network calls).
* A header-based decorator `@auth_required` for quick route protection.
* A `root_auth_required` decorator suitable for Lambda handlers.
* Programmatic and environment-variable configuration.
* An extensible permission system via `BasePermission` so you can write custom rules.

---

## Quick start (3 minutes)

1. **Install**

```bash
pip install more-sso-auth
pip install PyJWT
pip install cryptography
```

2. **Configure** (either method)

**Programmatic**

```python
from more_sso import init_sso_config

init_sso_config(
    public_key_uri="<your-kms-id>",
    audience="<your-app>"
)
```

**Environment variables**

```bash
export PUBLIC_KEY_URI="<your-kms-id>"
export AUDIENCE="<your-app>"
```

3. **Protect a function**

```python
from more_sso import auth_required

@auth_required(permission="pma.role", value="admin")
def my_func(event, *args, **kwargs):
    user = event["requestContext"]["user"]
    return {"ok": True}
```

> The decorator will validate the bearer JWT from the `Authorization` header and inject the decoded payload consistently into `event["requestContext"]["user"]`.

---

## Core Concepts

### Token validation

Use `validate_token(token)` to validate a JWT programmatically. It raises `JWTValidationError` on invalid tokens.

```python
from more_sso import validate_token, JWTValidationError
try:
    user = validate_token(token)
except JWTValidationError as e:
    # handle unauthenticated
    print("Invalid token:", str(e))
```

`validate_token` performs usual checks: signature (RS256), audience (the `AUDIENCE` you configured), and token expiry.

### Decorators

* `@auth_required(...)` — decorator for fine-grained route enforcement. It supports either a simple permission check or a custom permission class. After validation it injects the decoded token into `event["requestContext"]["user"]`.
* `@root_auth_required` — a simple decorator for Lambda handlers that enforces authentication at the top level and injects the decoded user into `event["requestContext"]["user"]`. If authentication fails, the decorator returns a 401 response (for AWS Lambda-style handlers).

**Example: root-level Lambda**

```python
from more_sso import root_auth_required

@root_auth_required
def lambda_handler(event, context):
    user = event["requestContext"]["user"]
    return {"statusCode": 200, "body": f"Hello {user['sub']}"}
```

### Permissions

There are two ways to enforce authorization with `auth_required`:

1. **Simple claim check** — pass `permission` and `value`.

   * `permission` is a dotted path into the decoded JWT payload (for example: `pma.role` will look up `user['permissions']["pma"]["role"]`).
   * `value` is the expected value.
    * the `user` claims will also contain the `permissions` as a json with app specific roles and permisson attributes 
```python
@auth_required(permission="my_app.role", value="admin")
def handler(event, *args, **kwargs):
    user = event["requestContext"].get("user", {})
    # ...
```

2. **Custom permission class** — extend `BasePermission` and implement `has_access()`.

```python
from more_sso import BasePermission, auth_required, AccessDeniedError

class CustomPermission(BasePermission):
    def __init__(self,*args,**kwargs):
        super.__init__(*args,**kwargs)
        self.extras = kwargs

    def check_something(self )
        if self.extras['id'] == self.user['permissions']['id']
            return "something"
        ...
    # to be implemented
    def has_access(self) -> bool:

        # example: allow only admins
        if self.check_something() =='something' 
            return self.user['permissions'].get("role") == "admin"


@auth_required(permission_class=CustomPermission,**kwargs)
# kwargs are stored in self.extras of permission class which can be accessed in has_access 
def admin_only(event, *args, **kwargs):
    return {"ok": "admin access granted"}

# caller example
try:
    admin_only()
except AccessDeniedError:
    # return 403
    pass
```

**Behavior:** when permission check fails the decorator raises `AccessDeniedError` (or returns an appropriate 403 when used as a top-level Lambda decorator if configured that way).

---

## AWS Lambda patterns

**Top-level enforcement** (recommended for simple APIs):

```python
from more_sso import root_auth_required

@root_auth_required
def lambda_handler(event, context):
    user = event["requestContext"]["user"]
    # authorized
    return {"statusCode": 200, "body": "ok"}
```

**Function-level enforcement** (fine-grained):

```python
from more_sso import auth_required, AccessDeniedError

@auth_required(permission="my_app.role", value="admin")
def admin_action(event, *args, **kwargs):
    return {"ok": True}

def lambda_handler(event, context):
    try:
        return admin_action(event)
    except AccessDeniedError:
        return {"statusCode": 403, "body": "Access denied"}
```

Note: Both `auth_required` and `root_auth_required` inject the decoded token consistently into `event["requestContext"]["user"]`.

---

## API reference (quick)

* `init_sso_config(public_key_uri: str, audience: str)` — initialize the library programmatically.
* `validate_token(token: str) -> dict` — validate token and return decoded payload. Raises `JWTValidationError` on failure.
* `auth_required(permission: str = None, value: Any = None, permission_class: Type[BasePermission] = None)` — decorator to protect functions. Injects user into `event["requestContext"]["user"]`.
* `root_auth_required` — decorator for Lambda handlers.
* `BasePermission` — extend this and implement `has_access(self) -> bool` for custom checks. The class has access to `self.user`.
* `JWTValidationError` — raised for invalid JWTs.
* `AccessDeniedError` — raised when permission checks fail.

---

## Security notes

* Always validate `aud` (audience) and `exp` (expiry). `more-sso-auth` checks these by default when configured.
* Rotate keys at the Identity Provider (IdP) and ensure the IdP exposes the new public key at the configured `PUBLIC_KEY_URI`.

---

## Troubleshooting & FAQ

**Q: Where does the library read the token from?**
A: From the `Authorization: Bearer <token>` header in incoming requests.

**Q: How do I check complex permissions (lists, nested claims)?**
A: Use a `BasePermission` subclass and implement `has_access()` — you have full access to the decoded payload and can evaluate arbitrarily complex logic.

---

## Contributing & License

* Source: `https://github.com/more-retail/moresso`
* License: MIT

Contributions are welcome via PRs. Please follow the repository's contribution guidelines for tests and code style.
