import time
from dataclasses import dataclass


@dataclass
class Token:
    access_token: str
    token_type: str
    expires_in: int
    created_at: float = time.time()

    def is_expired(self):
        return time.time() > self.created_at + self.expires_in
