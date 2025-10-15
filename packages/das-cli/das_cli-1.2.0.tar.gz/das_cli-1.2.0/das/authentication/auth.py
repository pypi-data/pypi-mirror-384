from das.common.api import post_data
from das.common.config import save_token


class Auth:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        # Don't store password as an instance variable for security
        self.token = None

        # Pass password directly to authenticate method
        self.authenticate(password)

    def authenticate(self, password):
        """
        Authenticate the user and obtain an access token.
        
        Args:
            password (str): The password to authenticate with
        """
        url = f"{self.base_url}/api/TokenAuth/Authenticate"
        data = {
            "userNameOrEmailAddress": self.username,
            "password": password
        }
        response = post_data(url, data=data)
        if response.get("error"):
            print(f"Authentication failed: {response['error']}")
        else:
            self.token = response.get("result").get("accessToken")
            save_token(self.token)
            # Return silently, let the CLI handle success messages
            return self.token

if __name__ == "__main__":
    # Example for testing authentication
    import getpass
    base_url = input("Base URL: ")
    username = input("Username: ")
    password = getpass.getpass("Password: ")
    auth = Auth(base_url=base_url, username=username, password=password)
    print(f"Token obtained: {bool(auth.token)}")