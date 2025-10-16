import requests
import os
from swai.utils.log import logger
from swai.const import SWAI_API_URL, USER_LOGIN_ROUTE, USER_API_KEY_PATH


# API_KEY = ""
# curl -sS -c cookies.txt -H 'Content-Type: application/json' \
#   -d "{\"api_key\":\"$API_KEY\"}" \
#   "$API/auth/login"

class User:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if os.path.exists(USER_API_KEY_PATH):
            with open(USER_API_KEY_PATH, "r") as f:
                self.api_key = f.read().strip()
        else:
            logger.error("Please login first")
            exit(0)

    @staticmethod
    def _check_cache_api_key(login_api_key: str):
        if os.path.exists(USER_API_KEY_PATH):
            with open(USER_API_KEY_PATH, "r") as f:
                cached_api_key = f.read().strip()
            if cached_api_key == login_api_key:
                return True
            else:
                # 重新登录，需要询问是否使用缓存的apikey
                use_cache_api_key = input(f"Found cached API key, but it's not the same as the login API key. Use cached API key? (Y/n): ").strip().lower()
                while use_cache_api_key not in ["y", "n"]:
                    use_cache_api_key = input(f"Found cached API key, but it's not the same as the login API key. Use cached API key? (Y/n): ").strip().lower()
                if use_cache_api_key == "y":
                    return True
                else:
                    return False
        return False
        

    @staticmethod
    def login(api_key: str):
        assert api_key is not None, "api_key must be provided"
        assert isinstance(api_key, str), "api_key must be a string"
        assert len(api_key) > 0, "api_key must be a non-empty string"

        if User._check_cache_api_key(api_key):
            
            logger.info(f"Login success")
            
            return api_key
        
        url = f"{SWAI_API_URL}{USER_LOGIN_ROUTE}"
        try:
            response = requests.post(url, json={"api_key": api_key})
            meta = response.json()
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Login failed: {e}, maybe network connection error")
            return None
        
        if meta.get("status") == "error":
            # api key 错误
            logger.error(f"Login failed: {meta.get('msg')}, maybe incorrect apikey or registration needed")
            return None
        elif meta.get("status") == "success":
            with open(USER_API_KEY_PATH, "w") as f:
                f.write(api_key)
            logger.info(f"Login success")
            return api_key 
        else:
            logger.error(f"Invalid response: {meta=}")
        return None