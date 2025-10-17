
"""
REST Countries mock requests
----------------------------------------------
- Prefer packaged per-URL JSONs under mock_requests/data.
- Else check user cache (~/.cache/mock_requests_rc).
- Else perform a live get, cache that JSON, then return.
"""

import os
import json
import hashlib
import requests

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

DEFAULT_USER_CACHE = os.path.join(os.path.expanduser("~"), ".cache", "mock_requests_rc")
USER_CACHE_DIR = os.getenv("MOCK_REQUESTS_USER_CACHE_DIR", DEFAULT_USER_CACHE)

if not os.path.isdir(USER_CACHE_DIR):
    os.makedirs(USER_CACHE_DIR, exist_ok=True)

ALLOWED_PREFIXES = ("https://restcountries.com/v3.1/", "http://restcountries.com/v3.1/")

TIMEOUT = 30

def hash_filename_for(url):
    """
    Turn a URL into a short filename using SHA-256.
    Keep the first 24 hex chars to balance uniqueness and brevity.
    """
    sha = hashlib.sha256(url.encode("utf-8")).hexdigest()
    name = "rc_" + sha[:24] + ".json"
    return name

def path_in_package(filename):
    """
    Build the absolute path to a packaged data file.
    """
    return os.path.join(DATA_DIR, filename)

def path_in_user_cache(filename):
    """
    Build the absolute path to a user-cache data file.
    """
    return os.path.join(USER_CACHE_DIR, filename)

class MockResponse:
    """
    Response wrapper with .json(), .text, .ok, .status_code
    """
    def __init__(self, filepath, status_code):
        self.filepath = filepath
        self.status_code = status_code
        self.text_cache = None

    def json(self):
        if not self.filepath:
            print("Error: Invalid File Path")
            return None
        with open(self.filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    @property
    def text(self):
        if self.text_cache is None:
            payload = self.json()
            self.text_cache = json.dumps(payload)
        return self.text_cache

    @property
    def ok(self):
        return 200 <= self.status_code < 300

    def __str__(self):
        return f"<Response [{self.status_code}]>"

def is_supported(url):
    """
    Confirm the URL matches REST Countries v3.1.
    """
    for prefix in ALLOWED_PREFIXES:
        if url.startswith(prefix):
            return True
    return False

def load_packaged_or_cached(url):
    """
    Try to use the URL from packaged data, then from user cache.
    Return a MockResponse if found; otherwise None.
    """
    filename = hash_filename_for(url)

    # Packaged data
    pkg_path = path_in_package(filename)
    if os.path.exists(pkg_path) and os.path.getsize(pkg_path) > 0:
        return MockResponse(pkg_path, 200)

    # User cache
    user_path = path_in_user_cache(filename)
    if os.path.exists(user_path) and os.path.getsize(user_path) > 0:
        return MockResponse(user_path, 200)

    return None

def live_fetch_and_cache(url):
    """
    Perform a live get request, save the JSON to user cache, return response.
    Return None if fetch fails.
    """

    filename = hash_filename_for(url)
    user_path = path_in_user_cache(filename)

    try:
        r = requests.get(url, timeout=TIMEOUT)
    except requests.RequestException:
        print("Exception: Request Exception")
        return None

    try:
        data = r.json()
    except ValueError:
        print("Exception: JSON Value Error")
        return None

    try:
        with open(user_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except OSError:
        print("Exception: Error writing to file")
        return None

    return MockResponse(user_path, r.status_code)

def get(url):
    """
    Mocks requests.get(url).
    """
    if not is_supported(url):
        return MockResponse("", 404)

    # Try first or second level cache
    found = load_packaged_or_cached(url)
    if found is not None:
        return found

    # Otherwise live fetch, then cache
    fetched = live_fetch_and_cache(url)
    if fetched is not None:
        return fetched

    # Return a 404 response if nothing worked
    return MockResponse("", 404)
