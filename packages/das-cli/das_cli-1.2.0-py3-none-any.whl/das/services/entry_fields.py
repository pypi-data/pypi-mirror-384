from das.common.api import get_data, post_data
from das.common.config import load_token


class EntryFieldsService():
    def __init__(self, base_url):
        self.base_url = f"{base_url}/api/services/app/EntryField"

    def get_entry_fields(self, attribute_id: int, display_type: int = 2):
        token = load_token()

        if (attribute_id is None):
            raise ValueError("Attribute ID parameter must be provided")

        if (token is None or token == ""):
            raise ValueError("Authorization token is required")

        headers = {
            "Authorization": f"Bearer {token}"
        }

        url = f"{self.base_url}/GetAll?AttributeId={attribute_id}&DisplayType={display_type}"

        response = get_data(url, headers=headers)

        if response.get('success') == True:
            return response
        elif 'error' in response and 'Invalid JSON' in str(response.get('error')):
            raw_content = response.get('raw_content', '')
            raise ValueError(f"API returned invalid JSON: {response.get('error')}\nResponse content: {raw_content}")
        else:
            error_msg = response.get('error')
            raise ValueError(error_msg if error_msg else "Unknown error in entry fields request")        