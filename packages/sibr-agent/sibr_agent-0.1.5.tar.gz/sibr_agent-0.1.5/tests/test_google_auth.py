import asyncio
from datetime import timedelta


class DummyDB:
    def collection(self, name):
        class Ref:
            pass
        return Ref()


def test_create_access_token_and_decode():
    from sibr_agent.google_auth import GoogleAuth
    import jwt

    auth = GoogleAuth(db=DummyDB(), secret_key="secret", algorithm="HS256", access_token_expire_minutes=5)
    token = auth.create_access_token({"sub": "user123"}, expires_delta=timedelta(minutes=5))

    decoded = jwt.decode(token, "secret", algorithms=["HS256"])  # stubbed in conftest
    assert decoded.get("sub") == "user123"
    assert "exp" in decoded


def test_get_current_user_with_valid_token():
    from sibr_agent.google_auth import GoogleAuth
    import jwt

    auth = GoogleAuth(db=DummyDB(), secret_key="secret", algorithm="HS256", access_token_expire_minutes=5)
    token = jwt.encode({"sub": "abc"}, "secret", algorithm="HS256")

    user_id = asyncio.get_event_loop().run_until_complete(auth.get_current_user(token=token))
    assert user_id == "abc"
