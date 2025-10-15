from das.common.api import delete_data, get_data, post_data, put_data
from das.common.config import load_token

class UsersService:
    def __init__(self, base_url):
        self.base_url = f"{base_url}/api/services/app/User"

    def get_user(self, user_name: str):
        token = load_token()

        if (token is None or token == ""):
            raise ValueError("Authorization token is required")

        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        url = f"{self.base_url}/GetUsers?filter={user_name}"

        response = get_data(url, headers=headers)

        if response.get('success') == True:
            return response.get('result').get('items')[0]
        else:
            raise ValueError(response.get('error'))