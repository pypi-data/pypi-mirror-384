from datetime import datetime, timezone, timedelta

import jwt
import requests


class Client:
    def __init__(self, api_key: str, api_secret: str, base_uri: str = 'https://app.visual-layer.com/api/v1'):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_uri = base_uri
        self.jwt_algorithm = "HS256"
        self.jwt_header = {
            'alg': self.jwt_algorithm,
            'typ': 'JWT',
            'kid': api_key,
        }

    def _get_jwt(self) -> str:
        payload = {
            'sub': self.api_key,
            'iat': datetime.now(tz=timezone.utc),
            'exp': datetime.now(tz=timezone.utc) + timedelta(minutes=10),
            'iss': 'sdk'
        }
        return jwt.encode(payload=payload, key=self.api_secret, algorithm=self.jwt_algorithm, headers=self.jwt_header)

    def _get_headers(self) -> dict:
        return {
            'Authorization': f'Bearer {self._get_jwt()}'
        }

    def get_datasets(self) -> dict:
        return requests.get(f'{self.base_uri}/datasets', headers=self._get_headers()).json()


def run():
    key = '<API_KEY>'
    secret='<API_SECRET>'
    client = Client(key, secret, 'http://app.visual-layer.com/api/v1')
    print(client.get_datasets())


if __name__ == "__main__":
    run()
