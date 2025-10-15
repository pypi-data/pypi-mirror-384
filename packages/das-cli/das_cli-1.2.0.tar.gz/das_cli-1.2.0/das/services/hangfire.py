from das.common.api import get_data, post_data
from das.common.config import load_token

class HangfireService:
    def __init__(self, base_url):
        self.base_url = f"{base_url}/api/services/app/Hangfire"

    def sync_doi(self, id: str):
        """Trigger a DOI synchronization task."""
        token = load_token()

        if (token is None or token == ""):
            raise ValueError("Authorization token is required")

        headers = {
            "Authorization": f"Bearer {token}"
        }

        url = f"{self.base_url}/TriggerProcessDigitalObjectIdentifier?id={id}"

        response = post_data(url, headers=headers)

        if response.get('success') == True:
            return response.get('result')
        else:
            raise ValueError(response.get('error'))