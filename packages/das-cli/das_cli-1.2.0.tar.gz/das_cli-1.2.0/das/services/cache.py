from das.common.api import get_data, post_data
from das.common.config import load_token

class CacheService():
    def __init__(self, base_url):
        self.base_url = f"{base_url}/api/services/app/Caching"

    def clear_all(self):
        """Clear all cached data."""
        token = load_token()

        if (token is None or token == ""):
            raise ValueError("Authorization token is required")

        headers = {
            "Authorization": f"Bearer {token}"
        }

        url = f"{self.base_url}/ClearAllCaches"

        response = post_data(url, headers=headers)

        if response.get('success') == True:
            return response
        else:
            raise ValueError(response.get('error'))
        
    def get_all(self):
        """Get all cache entries."""
        token = load_token()

        if (token is None or token == ""):
            raise ValueError("Authorization token is required")

        headers = {
            "Authorization": f"Bearer {token}"
        }

        url = f"{self.base_url}/GetAllCaches"

        response = get_data(url, headers=headers)

        if response.get('success') == True:
            return response.get('result')
        else:
            raise ValueError(response.get('error'))     

    def clear_cache(self, name: str):
        """Clear a specific cache by name."""
        token = load_token()

        if (token is None or token == ""):
            raise ValueError("Authorization token is required")

        headers = {
            "Authorization": f"Bearer {token}"
        }

        data = {
            "id": name
        }

        url = f"{self.base_url}/ClearCache"

        response = post_data(url, headers=headers, data=data)

        if response.get('success') == True:
            return response
        else:
            raise ValueError(response.get('error'))