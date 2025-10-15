from das.common.api import get_data
from das.common.config import load_token


class AttributesService():

    def __init__(self, base_url):
        self.base_url = f"{base_url}/api/services/app/Attribute"

    def get_attribute(self, id: int = None, name: str = None, alias: str = None, table_name: str = None):
        token = load_token()

        if (id is None and name is None and alias is None and table_name is None):
            raise ValueError("At least one parameter must be provided")

        if (token is None or token == ""):
            raise ValueError("Authorization token is required")

        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        if (id is not None):
            url = f"{self.base_url}/GetAll?id={id}"
        elif (name is not None):
            url = f"{self.base_url}/GetAll?name={name}"
        elif (alias is not None):
            url = f"{self.base_url}/GetAll?alias={alias}"
        elif (table_name is not None):
            url = f"{self.base_url}/GetAll?tableName={table_name}"

        response = get_data(url, headers=headers)

        if response.get('success') == True:
            return response
        else:
            raise ValueError(response.get('error'))
        
    def get_name(self, id: int)-> str:
        token = load_token()

        if (id is None):
            raise ValueError("ID parameter must be provided")

        if (token is None or token == ""):
            raise ValueError("Authorization token is required")

        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        url = f"{self.base_url}/GetAll?id={id}"

        response = get_data(url, headers=headers)

        if response.get('success') == True:
            return response.get('result').get('items')[0].get('name')
        else:
            raise ValueError(response.get('error'))
        
    def get_id(self, name: str)-> int:
        token = load_token()

        if (name is None):
            raise ValueError("Name parameter must be provided")

        if (token is None or token == ""):
            raise ValueError("Authorization token is required")

        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        url = f"{self.base_url}/GetAll?name={name}"

        response = get_data(url, headers=headers)

        if response.get('success') == True:
            return response.get('result').get('items')[0].get('id')
        else:
            raise ValueError(response.get('error'))