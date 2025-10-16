import appdirs
from pathlib import Path
import os

from .client import Client
from .helpers.user_session import UserSession

config_dir = Path(appdirs.user_config_dir("recodex"))
data_dir = Path(appdirs.user_data_dir("recodex"))
session_path = data_dir / "context.yaml"


def get_client_from_credentials(api_url: str, username: str, password: str, verbose=False) -> Client:
    """Creates a client object. If the session file is missing or expired,
    the file will be recreated using the provided credentials.

    Args:
        api_url (str): The URL of the API.
        username (str): ReCodEx username.
        password (str): ReCodEx password.
        verbose (bool, optional): Whether status messages should be printed to stdin. Defaults to False.

    Returns:
        Client: Returns a client object.
    """

    remove_session()
    session = create_session_from_credentials(api_url, username, password, verbose)
    return _create_client_from_session(session)


def get_client_from_token(api_url: str, api_token: str, verbose=False) -> Client:
    """Creates a client object. If the session file is missing or expired,
    the file will be recreated using the provided credentials.

    Args:
        api_url (str): The URL of the API.
        api_token (str): Authentication token for ReCodEx.
        verbose (bool, optional): Whether status messages should be printed to stdin. Defaults to False.

    Returns:
        Client: Returns a client object.
    """

    remove_session()
    session = create_session_from_token(api_url, api_token, verbose)
    return _create_client_from_session(session)


def get_client_from_session() -> Client:
    """Creates a client object from a session file. If the file is missing or expired,
    an exception will be thrown.

    Raises:
        Exception: Thrown when the session file is missing or expired.

    Returns:
        Client: Returns a client object.
    """
    return _load_session_and_create_client()


def load_session() -> UserSession | None:
    """Creates a UserSession object from a file if it exists.

    Returns:
        (UserSession | None): Returns the loaded UserSession, or None if there is no file.
    """

    if not session_path.exists():
        return None
    return UserSession.load(session_path)


def create_session_from_token(api_url: str, api_token: str, verbose=False) -> UserSession:
    """Retrieves an API token and creates a session file from the provided credentials.

    Args:
        api_url (str): The URL of the API.
        api_token (str): Authentication token for ReCodEx.
        verbose (bool, optional): Whether status messages should be printed to stdin. Defaults to False.

    Returns:
        UserSession: Returns a session object used to create a client object.
    """

    # remove whitespace
    api_url = api_url.strip()
    api_token = api_token.strip()

    session = UserSession(api_url, api_token)
    if session.is_token_expired():
        raise Exception("The provided API token had expired.")

    session.store(session_path)
    if verbose:
        print(f"Login token stored at: {session_path}")

    return session


def create_session_from_credentials(api_url: str, username: str, password: str, verbose=False) -> UserSession:
    """Retrieves an API token and creates a session file from the provided credentials.

    Args:
        api_url (str): The URL of the API.
        username (str): ReCodEx username.
        password (str): ReCodEx password.
        verbose (bool, optional): Whether status messages should be printed to stdin. Defaults to False.

    Returns:
        UserSession: Returns a session object used to create a client object.
    """

    # remove whitespace
    api_url = api_url.strip()
    username = username.strip()
    password = password.strip()

    client = Client("", api_url)

    if verbose:
        print("Connecting...")
    token = client.get_login_token(username, password)
    session = UserSession(api_url, token)

    session.store(session_path)
    if verbose:
        print(f"Login token stored at: {session_path}")

    return session


def remove_session():
    """Deletes the session file, effectively logging the user out.
    """

    if os.path.exists(session_path):
        os.remove(session_path)


def refresh_session():
    """Refreshes the session token and updates the session file.
    """
    _load_session_and_create_client(force_refresh=True)


def _load_session_and_create_client(force_refresh: bool = False) -> Client:
    """Loads the session from a file and creates a client object.
    If the session file is missing or expired, an exception will be thrown.

    Args:
        force_refresh (bool, optional): Whether the token should be refreshed even if it is not
                                        close to expiration. Defaults to False.

    Raises:
        Exception: Thrown when the session file is missing or expired.
    """

    session = load_session()
    if session is None:
        raise Exception("No session file was found.")

    if session.is_token_expired():
        raise Exception("The session token expired.")

    return _create_client_from_session(session, force_refresh)


def _create_client_from_session(session: UserSession, force_refresh: bool = False) -> Client:
    """Creates a client object and refreshes the API token if it almost expired.

    Args:
        session (UserSession): The session containing the endpoint URL and API token.

    Raises:
        Exception: Thrown when the session expired, the token was not provided, or the API URL was missing.

    Returns:
        Client: Returns a client object.
    """

    if session.is_token_expired():
        raise Exception("The session token expired.")
    if session.get_api_token() is None:
        raise Exception("No session token was not found in the session.")
    if session.get_api_url() is None:
        raise Exception("No API URL was found in the session.")

    client = Client(session.get_api_token(), session.get_api_url())

    # refresh token if necessary
    if session.is_token_almost_expired() or force_refresh:
        session = session.replace_token(client.get_refresh_token())
        session.store(session_path)
        # recreate client
        client = Client(session.get_api_token(), session.get_api_url())  # type: ignore
    return client
