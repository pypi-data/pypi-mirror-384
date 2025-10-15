from das.common.config import load_token
from das.common.api import delete_data, get_data, post_data

class SearchService:
    def __init__(self, base_url):
        self.base_url = f"{base_url}/api/services/app/Search"

    def search_entries(self, **kwargs):
        """Search entries based on provided criteria."""
        token = load_token()

        if (token is None or token == ""):
            raise ValueError("Authorization token is required")

        headers = {
            "Authorization": f"Bearer {token}"
        }

        valid_params = ['attributeId', 'tableName', 'queryString', 'includeRelationsId', 'sorting', 'maxResultCount', 'skipCount']

        for key in kwargs.keys():
            if key not in valid_params:
                raise ValueError(f"Invalid search parameter: {key}")

        response = post_data(f"{self.base_url}/SearchEntries", data=kwargs, headers=headers)

        if response.get('success') == True:
            return response.get('result')
        elif 'error' in response and 'Invalid JSON' in str(response.get('error')):
            raw_content = response.get('raw_content', '')
            raise ValueError(f"API returned invalid JSON: {response.get('error')}\nResponse content: {raw_content}")
        else:
            raise ValueError(response.get('error') or "Unknown error occurred")
