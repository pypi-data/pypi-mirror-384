from functools import lru_cache

import jwt
import yaml
from typing import NamedTuple, Optional
from datetime import datetime, timezone
from pathlib import Path


class UserSession(NamedTuple):
    """A class that loads, stores and checks whether the user JWT token is expired.
    """

    api_url: Optional[str] = None
    api_token: Optional[str] = None

    @property
    @lru_cache()
    def _token_data(self):
        if self.api_token is None:
            raise RuntimeError("The API token is not set")

        try:
            return jwt.decode(self.api_token, options={"verify_signature": False})
        except:
            raise Exception("Could not decode provided API token")

    def get_api_url(self):
        return self.api_url

    def get_api_token(self):
        return self.api_token

    def get_user_id(self):
        return self._token_data["sub"]

    def is_token_almost_expired(self, threshold=0.5) -> bool:
        """
        Returns true if the token is about to expire
        :param threshold: A number between 0 and 1. If less than (threshold * token validity period) is left until
                          expiration, the method will return True.
        """

        validity_period = self._token_data["exp"] - self._token_data["iat"]
        time_until_expiration = self._token_data["exp"] - \
            datetime.now(timezone.utc).timestamp()
        return validity_period * threshold > time_until_expiration

    def is_token_expired(self) -> bool:
        return self._token_data["exp"] <= datetime.now(timezone.utc).timestamp()

    def get_token_expiration_time(self) -> datetime:
        return datetime.fromtimestamp(self._token_data["exp"])

    def replace_token(self, new_token) -> 'UserSession':
        return self._replace(api_token=new_token)

    @classmethod
    def load(cls, config_path: Path):
        config = yaml.safe_load(config_path.open("r")) or {}
        return cls(**config)

    def store(self, config_path: Path):
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with config_path.open("w") as fp:
            yaml.dump(dict(self._asdict()), fp)
