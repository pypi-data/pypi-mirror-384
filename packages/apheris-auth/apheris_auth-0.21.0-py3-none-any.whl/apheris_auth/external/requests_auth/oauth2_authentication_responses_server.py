import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from socket import socket
from typing import Any, Tuple
from urllib.parse import parse_qs, urlparse

from oauthlib.oauth2.rfc6749.errors import MismatchingStateError
from termcolor import cprint

from ...config import is_interactive
from ...core.log import logger
from ...core.session import SessionAudience
from .errors import (
    GrantNotProvided,
    InvalidGrantRequest,
    StateNotProvided,
    TimeoutOccurred,
)


class OAuth2ResponseHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        logger.debug(f"GET received on {self.path}")
        try:
            args = self._get_params()
            self._parse_grant(args)
        except Exception as e:
            self.server.request_error = e
            logger.error(f"GET received on {self.path}")
            logger.exception(f"Unable to properly perform authentication. {e}")
            self.send_html(
                self.error_page(
                    "Unable to properly perform authentication, please "
                    "check your terminal for more details."
                )
            )

    def do_POST(self):
        logger.debug(f"POST received on {self.path}")
        try:
            form_dict = self._get_form()
            self._parse_grant(form_dict)
        except Exception as e:
            self.server.request_error = e
            logger.exception(f"Unable to properly perform authentication: {e}")
            self.send_html(
                self.error_page(
                    "Unable to properly perform authentication, please"
                    "check your terminal for more details."
                )
            )

    def _parse_grant(self, arguments: dict):
        grants = arguments.get(self.server.grant_details.name)
        if not grants or len(grants) > 1:
            if "error" in arguments:
                raise InvalidGrantRequest(arguments)
            raise GrantNotProvided(self.server.grant_details.name, arguments)
        logger.debug(f"Received grants: {grants}")
        grant = grants[0]
        states = arguments.get("state")
        if not states or len(states) > 1:
            raise StateNotProvided(arguments)
        logger.debug(f"Received states: {states}")
        state = states[0]
        if state and state != self.server.grant_details.state:
            raise MismatchingStateError()
        self.server.grant = state, grant
        self.send_html(self.success_page())

    def _get_form(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body_str = self.rfile.read(content_length).decode("utf-8")
        return parse_qs(body_str, keep_blank_values=1)

    def _get_params(self):
        return parse_qs(urlparse(self.path).query)

    def send_html(self, html_content: str):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(str.encode(html_content))
        logger.debug("HTML content sent to client.")

    def success_page(self):
        return f"""<h1 style="color: #5e9ca0;">&nbsp;</h1>
            <p>&nbsp;</p>
            <p>&nbsp;</p>
            <p>&nbsp;</p>
            <center style="background-color: lightgreen; color: #839496; font-family:
            'DejaVu Sans Mono', monospace; font-size: 13.5pt;">
            <span style="color: #3d8080; font-weight: bold;">
            You have successfully authorized Apheris with
            {self.server.grant_details.session_audience.value},
            <br> please check your terminal for complete login status.
            <br> you may close this page now.
            </center>
            </pre>"""

    def error_page(self, text: str):
        return f"""<h1 style="color: #5e9ca0;">&nbsp;</h1>
            <p>&nbsp;</p>
            <p>&nbsp;</p>
            <p>&nbsp;</p>
            <center style="background-color: #f08080; color: #839496; font-family:
            'DejaVu Sans Mono', monospace; font-size: 13.5pt;">
            <span style="color: #3d8080; font-weight: bold;">
            {text},
            <br>While authorizing Apheris with
            {self.server.grant_details.session_audience.value}
            </center>
            </pre>"""

    def log_message(self, format: str, *args):
        """Make sure that messages are logged even with pythonw
        (seems like a bug in BaseHTTPRequestHandler)."""
        logger.debug(format, *args)


class GrantDetails:
    def __init__(
        self,
        url: str,
        name: str,
        reception_timeout: float,
        redirect_uri_port: int,
        session_audience: SessionAudience,
        state: str,
    ):
        self.url = url
        self.name = name
        self.reception_timeout = reception_timeout
        self.redirect_uri_port = redirect_uri_port
        self.session_audience = session_audience
        self.state = state


class FixedHttpServer(HTTPServer):
    def __init__(self, grant_details: GrantDetails):
        # Running in docker will default to the fallback flow if not overridden,
        # this is the only way to have 0.0.0.0
        callback_server_address = "127.0.0.1"
        if Path("/.dockerenv").exists():
            callback_server_address = "0.0.0.0"
            logger.info(
                """Running in a docker container: allowing less strict local callback server address"""  # noqa:E501
            )
        super().__init__(
            (callback_server_address, grant_details.redirect_uri_port),
            OAuth2ResponseHandler,
        )
        self.timeout = grant_details.reception_timeout
        logger.debug(f"Timeout is set to {self.timeout} seconds.")
        self.grant_details = grant_details
        self.request_error = None
        self.grant: Any = False

    def finish_request(self, request: socket, client_address):
        """
        Make sure that timeout is used by the request
        (seems like a bug in HTTPServer).
        """
        request.settimeout(self.timeout)
        HTTPServer.finish_request(self, request, client_address)

    def ensure_no_error_occurred(self):
        if self.request_error:
            # Raise error encountered while processing a request if any
            raise self.request_error
        return not self.grant

    def handle_timeout(self):
        raise TimeoutOccurred(self.timeout)


def request_new_grant(grant_details: GrantDetails) -> Tuple[str, str]:
    """
    Ask for a new OAuth2 grant.
    :return: A tuple (state, grant)
    :raises InvalidGrantRequest: If the request was invalid.
    :raises TimeoutOccurred: If not retrieved within timeout.
    :raises GrantNotProvided: If grant is not provided in response
            (but no error occurred).
    :raises StateNotProvided: If state if not provided in addition to the grant.
    """
    logger.debug(f"Requesting new {grant_details.name}...")

    with FixedHttpServer(grant_details) as server:
        browser_open_url(grant_details.url)
        return _wait_for_grant(server)


def print_url(url, is_notebook: bool):
    if not is_notebook:
        print(url)
        return
    try:
        from IPython.display import HTML, display

        message = f"""<a
            href="{url}"
            target="_blank"
            style="font-size: 20px; text-decoration: none; color: DodgerBlue"
            >Open link in new tab</a>"""
        display(HTML(message))
    except ImportError:
        print(url)


def browser_open_url(url: str):
    logger.debug(f"Opening browser on {url}")
    try:
        if not webbrowser.open_new_tab(url):
            raise webbrowser.Error
    except webbrowser.Error:
        # In a notebook it is expected for the browser not to open
        if not is_interactive():
            logger.warning(
                "Unable to open URL with browser, user should open url manually."
            )
            cprint(
                "If your browser didn't open, please open the following URL manually:",
                "yellow",
            )
        print_url(url, is_interactive())


def _wait_for_grant(server: FixedHttpServer) -> str:
    """
    :return: A dict , The grant response as json.
    :raises InvalidGrantRequest: If the request was invalid.
    :raises TimeoutOccurred: If not retrieved within timeout.
    :raises GrantNotProvided: If grant is not provided in response
            (but no error occurred).
    :raises StateNotProvided: If state was not provided in addition to the grant.
    """
    logger.debug("Waiting for user authentication...")
    while not server.grant:
        server.handle_request()
        server.ensure_no_error_occurred()
    return server.grant


def is_notebook() -> bool:
    try:
        shell = get_ipython().__class__.__name__
        if shell == "ZMQInteractiveShell":
            return True  # Jupyter notebook or qtconsole
        else:
            return False  # Other type (?)
    except NameError:
        return False  # Probably standard Python interpreter
