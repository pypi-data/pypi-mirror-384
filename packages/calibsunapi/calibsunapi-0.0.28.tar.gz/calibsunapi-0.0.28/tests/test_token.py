import time

import pytest

from calibsunapi.token import Token


def test_token_initialization():
    token = Token(access_token="abc123", token_type="Bearer", expires_in=3600)
    assert token.access_token == "abc123"
    assert token.token_type == "Bearer"
    assert token.expires_in == 3600
    assert isinstance(token.created_at, float)


def test_token_is_expired():
    token = Token(access_token="abc123", token_type="Bearer", expires_in=1.5)
    assert not token.is_expired()
    time.sleep(1.5)
    assert token.is_expired()
