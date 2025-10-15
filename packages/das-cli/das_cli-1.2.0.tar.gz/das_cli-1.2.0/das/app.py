from das.authentication.auth import Auth
from das.services.attributes import AttributesService
from das.services.cache import CacheService
from das.services.entries import EntriesService
from das.services.entry_fields import EntryFieldsService
from das.services.hangfire import HangfireService
from das.services.search import SearchService
from das.common.config import save_api_url

#  $env:PYTHONPATH="C:\Workspace\das-cli"  

class Das:
    def __init__(self, base_url: str):
        if base_url is None or base_url == "":
            raise ValueError("You must be authenticated.")
        save_api_url(base_url)
        self.base_url = base_url
        self.attributes = AttributesService(base_url)
        self.cache = CacheService(base_url)
        self.entries = EntriesService(base_url)
        self.hangfire = HangfireService(base_url)
        self.entry_fields = EntryFieldsService(base_url)
        self.search = SearchService(base_url)        

    def authenticate(self, username: str, password: str) -> str:
        """
        Authenticate with the DAS API and return the token.
        
        Args:
            username (str): The username to authenticate with
            password (str): The password to authenticate with
            
        Returns:
            str: The authentication token or None if authentication fails
        """
        auth = Auth(self.base_url, username, password)
        return auth.token
