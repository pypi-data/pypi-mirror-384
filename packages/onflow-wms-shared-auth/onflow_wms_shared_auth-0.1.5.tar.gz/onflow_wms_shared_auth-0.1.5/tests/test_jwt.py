from shared_auth.jwt_handler import create_access_token, decode_access_token

def test_jwt_roundtrip():
    payload = {"user_id": 1, "username": "tester"}
    token = create_access_token(payload)
    decoded = decode_access_token(token)
    assert decoded["user_id"] == 1
