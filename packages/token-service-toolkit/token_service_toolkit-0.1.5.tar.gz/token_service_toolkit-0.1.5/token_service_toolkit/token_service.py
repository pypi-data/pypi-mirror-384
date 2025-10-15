import requests

class TokenService:
    """
    A lightweight TokenService to fetch an Azure AD access token dynamically.
    No logger, no .env dependency — all values are passed as parameters.
    """

    def __init__(self, client_id: str, client_secret: str, tenant_id: str, scope: str, token_url: str, grant_type: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.scope = scope
        self.token_url = token_url
        self.grant_type = grant_type

        missing = [
            name for name, value in {
                "client_id": client_id,
                "client_secret": client_secret,
                "tenant_id": tenant_id,
                "scope": scope,
                "token_url": token_url,
                "grant_type" : grant_type,
            }.items() if not value
        ]

        if missing:
            raise ValueError(f"Missing required parameters: {', '.join(missing)}")

    def get_access_token(self) -> str:
        """
        Fetch an OAuth2 access token using the provided credentials.
        """
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.scope,
            "grant_type": self.grant_type,
        }

        response = requests.post(self.token_url, data=data)
        if response.status_code != 200:
            raise Exception(
                f"Failed to get token. Status: {response.status_code}, Response: {response.text}"
            )

        token = response.json().get("access_token")
        if not token:
            raise Exception("Token not found in response.")

        return token
