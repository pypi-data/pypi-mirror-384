from das.common.api import delete_data, get_data, post_data, put_data
from das.common.config import load_token

class EntriesService():
    def __init__(self, base_url):
        self.base_url = f"{base_url}/api/services/app/Entry"

    def get_entry(self, code: str):
        """Get an entry by its code (raw key values)."""
        token = load_token()

        if (token is None or token == ""):
            raise ValueError("Authorization token is required")

        headers = {
            "Authorization": f"Bearer {token}"
        }

        url = f"{self.base_url}/GetEntryByCode?code={code}"

        response = get_data(url, headers=headers)

        if response.get('success') == True:
            return response.get('result')
        else:
            raise ValueError(response.get('error'))

    def get(self, id: str = None, code: str = None):
        token = load_token()

        if (token is None or token == ""):
            raise ValueError("Authorization token is required")

        headers = {
            "Authorization": f"Bearer {token}"
        }

        url = ''

        if id is not None:
            url = f"{self.base_url}/GetById?id={id}"

        if code is not None:
            url = f"{self.base_url}/GetEntryByCode?code={code}"

        response = get_data(url, headers=headers)

        if response.get('success') == True:
            return response.get('result')
        elif 'error' in response and 'Invalid JSON' in str(response.get('error')):
            raw_content = response.get('raw_content', '')
            raise ValueError(f"API returned invalid JSON: {response.get('error')}\nResponse content: {raw_content}")
        else:
            raise ValueError(response.get('error') or "Unknown error occurred")
        
    def delete(self, code: str):
        """Delete an entry by its code."""
        token = load_token()

        if (token is None or token == ""):
            raise ValueError("Authorization token is required")

        headers = {
            "Authorization": f"Bearer {token}"
        }

        response_entry = self.get(code=code)  # Ensure entry exists before attempting deletion

        if response_entry is None:
            raise ValueError(f"Entry with code {code} not found")

        url = f"{self.base_url}/Delete?Id={response_entry.get('entry',{}).get('id')}&AttributeId={response_entry.get('attributeId')}"

        response = delete_data(url, headers=headers)

        if response.get('success') == True:
            return response
        else:
            raise ValueError(response.get('error'))     

    def create(self, attribute_id: int, entry: dict):
        """Create a new entry."""
        token = load_token()

        if (token is None or token == ""):
            raise ValueError("Authorization token is required")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        url = f"{self.base_url}/Create"

        payload = {
            "attributeId": attribute_id,
            "entry": entry
        }

        response = post_data(url, data=payload, headers=headers)

        if response.get('success') == True:
            return response.get('result')
        else:
            raise ValueError(response.get('error')) 
        
    def update(self, attribute_id: int, entry: dict):       
        """Update an existing entry."""
        token = load_token()

        if (token is None or token == ""):
            raise ValueError("Authorization token is required")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        url = f"{self.base_url}/Update"

        payload = {
            "attributeId": attribute_id,
            "entry": entry
        }

        response = put_data(url, data=payload, headers=headers)

        if response.get('success') == True:
            return response.get('result')
        else:
            raise ValueError(response.get('error'))

    def chown(self, new_user_id: int, entry_list_ids: list[str]):
        """Change the owner of a list of entries."""
        token = load_token()

        if (token is None or token == ""):
            raise ValueError("Authorization token is required")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        url = f"{self.base_url}/ChangeOwner"
        
        payload = {
            "newOwnerId": new_user_id,
            "entryIdList": entry_list_ids
        }

        response = post_data(url, data=payload, headers=headers)

        if response.get('success') == True:
            return response.get('result')
        else:
            raise ValueError(response.get('error'))

