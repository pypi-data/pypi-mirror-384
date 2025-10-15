import json
import os
from pathlib import Path
from typing import Optional
import logging

from dotenv import load_dotenv
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings and errors by default
    format='%(message)s'    # Simplified format for cleaner output
)

# ---------- Config ----------

SERVICE_NAME = "Data-Archive-System"
DEFAULT_BASE_URL = "https://localhost:44301"  # ← change to your API
VERIFY_SSL = True  # Default is True for secure connections
TOKEN_FIELD = "accessToken"

def _config_dir() -> Path:
    if os.name == "nt":  # Windows
         base = Path(os.getenv("APPDATA", Path.home()))
    else:  # macOS and Linux
        base = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
    d = Path(base) / SERVICE_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d

CONFIG_FILE = _config_dir() / "config.json"

def save_api_url(api_url: str) -> None:
    config = {}
    if CONFIG_FILE.exists():
        try:
            config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            config = {}
    config["api_url"] = api_url
    CONFIG_FILE.write_text(json.dumps(config), encoding="utf-8")

def load_api_url() -> Optional[str]:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8")).get("api_url")
        except Exception:
            return None
    return None

def save_verify_ssl(verify: bool) -> None:
    """
    Save the VERIFY_SSL setting to the config file.
    
    Args:
        verify (bool): Whether to verify SSL certificates.
    """
    global VERIFY_SSL
    config = {}
    if CONFIG_FILE.exists():
        try:
            config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            config = {}
    config["verify_ssl"] = verify
    VERIFY_SSL = verify
    CONFIG_FILE.write_text(json.dumps(config), encoding="utf-8")

def load_verify_ssl() -> bool:
    """
    Load the VERIFY_SSL setting from the config file.
    
    Returns:
        bool: The VERIFY_SSL setting, defaults to True if not found.
    """
    global VERIFY_SSL
    if CONFIG_FILE.exists():
        try:
            config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            
            if os.getenv("VERIFY_SSL") is not None:
                VERIFY_SSL = os.getenv("VERIFY_SSL") == "True"
                if not VERIFY_SSL:
                    print("SSL certificate verification is disabled")
                return VERIFY_SSL

            verify = config.get("verify_ssl")
            if verify is not None:
                VERIFY_SSL = verify
                if not VERIFY_SSL:
                    print("SSL certificate verification is disabled")
                return verify
            else:
                raise ValueError("SSL certificate verification is not set")
        except Exception:
            pass
    return VERIFY_SSL

def _config_dir() -> Path:
    if os.name == "nt":  # Windows
         base = Path(os.getenv("APPDATA", Path.home()))
    else:  # macOS and Linux
        base = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
    d = Path(base) / SERVICE_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d

def _token_path() -> Path:
    return _config_dir() / "token.json"

def _openai_key_path() -> Path:
    return _config_dir() / "openai_key.json"


def _keyring_available() -> bool:
    try:
        import keyring  # noqa: F401
        return True
    except Exception:
        return False
    
def save_token(token: str) -> None:
    if _keyring_available():
        import keyring
        keyring.set_password(SERVICE_NAME, "default", token)
    else:
        p = _token_path()
        p.write_text(json.dumps({"token": token}), encoding="utf-8")
        if os.name != "nt":
            os.chmod(p, 0o600)    

def load_token() -> Optional[str]:
    if _keyring_available():
        import keyring
        return keyring.get_password(SERVICE_NAME, "default")
    p = _token_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8")).get("token")
        except Exception:
            return None
    return None            

def clear_token() -> None:
    if _keyring_available():
        import keyring
        try:
            keyring.delete_password(SERVICE_NAME, "default")
        except Exception:
            pass
    try:
        _token_path().unlink()
    except FileNotFoundError:
        pass

# ---------- OpenAI API Key management ----------

def save_openai_api_key(api_key: str) -> None:
    """Persist the OpenAI API key securely (keyring if available, else protected file)."""
    if _keyring_available():
        import keyring
        keyring.set_password(SERVICE_NAME, "openai_api_key", api_key)
    else:
        p = _openai_key_path()
        p.write_text(json.dumps({"api_key": api_key}), encoding="utf-8")
        if os.name != "nt":
            os.chmod(p, 0o600)

def load_openai_api_key() -> Optional[str]:
    """Retrieve the stored OpenAI API key, if present."""
    if _keyring_available():
        import keyring
        val = keyring.get_password(SERVICE_NAME, "openai_api_key")
        if val:
            return val
    p = _openai_key_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8")).get("api_key")
        except Exception:
            return None
    return None

def clear_openai_api_key() -> None:
    """Remove any stored OpenAI API key from secure storage and file fallback."""
    if _keyring_available():
        import keyring
        try:
            keyring.delete_password(SERVICE_NAME, "openai_api_key")
        except Exception:
            pass
    try:
        _openai_key_path().unlink()
    except FileNotFoundError:
        pass

# Initialize VERIFY_SSL from config file if available
load_verify_ssl()