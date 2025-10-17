import time

import requests
import typer

from ..utils.config import (
    API_BASE_URL,
    ID_STYLE,
    MAX_POLL_ATTEMPTS,
    POLL_INTERVAL,
)
from ..utils.utils import (
    confirm,
    get_authenticated_session,
    handle_http_error,
    open_browser,
    prompt,
    save_cookie,
    print_success,
    print_error,
    print_warning,
    print_info,
)

app = typer.Typer()


@app.command("signin")
def signin():
    """Sign in to the API."""
    try:
        session = get_authenticated_session()
        response = session.get(f"{API_BASE_URL}/v1/auth/session")
        if response.status_code == 200:
            print_success("Already signed in")
            return
        web = confirm("Use web browser to sign in?")
        if web:
            signin_web()
            return
        email = prompt("Email")
        password = prompt("Password", hide_input=True)
        response = requests.post(
            f"{API_BASE_URL}/v1/auth/signin",
            json={"email": email, "password": password},
        )
        response.raise_for_status()
        if response.status_code == 204:
            set_cookie = response.headers.get("Set-Cookie")
            if set_cookie:
                cookie_value = set_cookie.split(";")[0]
                save_cookie(cookie_value)
                print_success("Successfully signed in!")
            else:
                print_warning("No Set-Cookie header received")
        else:
            try:
                print_error(response.json())
            except requests.exceptions.JSONDecodeError:
                print_error(f"Server response (not JSON): {response.text}")
                print_error(
                    f"Status code: '[{ID_STYLE}]{response.status_code}[/{ID_STYLE}]'"
                )
    except requests.HTTPError as e:
        handle_http_error(e)


@app.command("signout")
def signout():
    """Sign out of the API."""
    try:
        get_authenticated_session()
        save_cookie("")
        print_success("Successfully signed out")
    except requests.HTTPError as e:
        handle_http_error(e)


def signin_web():
    """Sign in to the API via browser."""
    try:
        response = requests.post(f"{API_BASE_URL}/v1/auth/cli-login")
        response.raise_for_status()
        data = response.json()

        login_token = data.get("login_token")
        login_url = data.get("login_url")
        if not login_token or not login_url:
            print_error("Server did not return a login token or URL.")
            return

        open_browser(login_url)
        print_info(
            "Please complete the login in your browser. Waiting for completion..."
        )

        for _ in range(MAX_POLL_ATTEMPTS):  # Poll for up to 2 minutes
            poll = requests.get(
                f"{API_BASE_URL}/v1/auth/cli-check-login", params={"token": login_token}
            )
            poll.raise_for_status()
            poll_data = poll.json()
            if poll_data.get("status") == "complete" and poll_data.get(
                "session_cookie"
            ):
                save_cookie(f"appSession={poll_data['session_cookie']}")
                print_success("Successfully signed in!")
                return
            time.sleep(POLL_INTERVAL)
        print_warning("Login not completed in time. Please try again.")
    except requests.HTTPError as e:
        handle_http_error(e)
    except Exception as e:
        print_error(str(e))
