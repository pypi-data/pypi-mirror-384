import getpass
import keyring
import platform
import os

# Define service name for keyring
SERVICE_NAME = "das-cli"

def get_password(username, prompt="Password: "):
    """
    Get password securely using the appropriate method for the platform.
    
    Args:
        username (str): Username for associating with stored password
        prompt (str): Prompt text to display when asking for password
        
    Returns:
        str: The password entered by user or retrieved from keyring
    """
    try:
        # Try to get password from keyring first
        stored_pass = keyring.get_password(SERVICE_NAME, username)
        if stored_pass:
            return stored_pass
    except:
        # If keyring fails, continue to manual input
        pass
        
    # Get password from user input
    return getpass.getpass(prompt)

def store_credentials(username, password):
    """
    Store credentials securely in the system's keyring.
    
    Args:
        username (str): The username to store
        password (str): The password to store
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        keyring.set_password(SERVICE_NAME, username, password)
        return True
    except Exception as e:
        print(f"Warning: Could not store credentials securely ({e})")
        return False

def clear_stored_credentials(username):
    """
    Remove stored credentials from the system's keyring.
    
    Args:
        username (str): The username whose credentials should be removed
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        keyring.delete_password(SERVICE_NAME, username)
        return True
    except keyring.errors.PasswordDeleteError:
        # Password doesn't exist
        return True
    except Exception:
        return False
