import click
import os
import base64
import secrets
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
from thunder import utils

OAUTH_URL = "https://console.thundercompute.com/settings/tokens"
CONSOLE_URL = "https://console.thundercompute.com/settings/billing"


def get_token_from_user():
    try:
        return click.prompt("Token", type=str, hide_input=False)
    except (KeyboardInterrupt, EOFError):
        click.echo("\nLogin cancelled")
        exit(1)

def delete_data():
    credentials_file_path = get_credentials_file_path()
    try:
        os.remove(credentials_file_path)
    except OSError:
        pass

def get_credentials_file_path():
    home_dir = os.path.expanduser("~")
    credentials_dir = os.path.join(home_dir, ".thunder")
    if not os.path.exists(credentials_dir):
        os.makedirs(credentials_dir, mode=0o700, exist_ok=True)
    credentials_file_path = os.path.join(credentials_dir, "token")
    return credentials_file_path

def generate_state():
    """Generate random state parameter for OAuth."""
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')

class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""
    token = None
    error = None
    expected_state = None

    def log_message(self, format, *args):
        """Suppress default HTTP server logging."""
        pass

    def do_GET(self):
        """Handle callback GET request."""
        parsed = urlparse(self.path)
        if parsed.path == '/callback':
            params = parse_qs(parsed.query)

            # Verify state parameter
            received_state = params.get('state', [None])[0]
            if received_state != CallbackHandler.expected_state:
                CallbackHandler.error = "Invalid state parameter"
                self.send_response(400)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                error_html = self._error_html("Invalid state parameter. Please return to the CLI and try again.")
                self.wfile.write(error_html.encode('utf-8'))
                return

            if 'token' in params:
                CallbackHandler.token = params['token'][0]
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                success_html = self._success_html()
                self.wfile.write(success_html.encode('utf-8'))
            elif 'error' in params:
                error_desc = params.get('error_description', ['Unknown error'])[0]
                CallbackHandler.error = f"{params['error'][0]}: {error_desc}"
                self.send_response(400)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                error_html = self._error_html(CallbackHandler.error)
                self.wfile.write(error_html.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    @staticmethod
    def _success_html():
        """Return success HTML matching VSCode extension style."""
        return """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8" /><title>Thunder Compute Login</title><link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;600&display=swap" rel="stylesheet"><style>body{font-family:'Geist',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:0;padding:24px;background:#0a0a0a;color:#f0f0f0;text-align:center;}a{color:#369eff;text-decoration:none;font-weight:600;}</style></head><body><h1>Login complete</h1><p>You can close this tab and return to the CLI.</p><p><a href="https://console.thundercompute.com" target="_blank" rel="noreferrer">Open Thunder Console</a></p></body></html>"""

    @staticmethod
    def _error_html(message):
        """Return error HTML matching VSCode extension style."""
        # Basic HTML escaping
        escaped = message.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#x27;')
        return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8" /><title>Thunder Compute Login Error</title><link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;600&display=swap" rel="stylesheet"><style>body{{font-family:'Geist',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:0;padding:24px;background:#1c1c1c;color:#f8f8f8;text-align:center;}}p{{max-width:420px;margin:16px auto;line-height:1.5;}}a{{color:#ff8a80;text-decoration:none;font-weight:600;}}</style></head><body><h1>Login failed</h1><p>{escaped}</p><p>Please return to the CLI and try again.</p></body></html>"""

def start_callback_server():
    """Start local HTTP server for OAuth callback."""
    server = HTTPServer(('localhost', 0), CallbackHandler)
    port = server.server_port

    # Run server in background thread
    server_thread = threading.Thread(target=server.handle_request, daemon=True)
    server_thread.start()

    return server, port, server_thread


def try_oauth_login():
    """Attempt OAuth login flow using console page."""
    try:
        # Generate state parameter for CSRF protection
        state = generate_state()
        CallbackHandler.expected_state = state

        # Start local callback server
        server, port, server_thread = start_callback_server()
        return_uri = f"http://127.0.0.1:{port}/callback"

        # Build console login URL with state and return_uri
        from urllib.parse import quote
        login_url = (
            f"https://console.thundercompute.com/login/vscode"
            f"?state={state}"
            f"&return_uri={quote(return_uri, safe='')}"
        )

        click.echo("Opening browser for authentication...")
        click.echo("Press Ctrl+C to cancel and enter token manually.")

        # Open browser
        if not webbrowser.open(login_url):
            click.echo(click.style("Could not open browser automatically.", fg="yellow"))
            click.echo(f"Please open this URL manually: {login_url}")

        # Wait for callback (with timeout)
        server_thread.join(timeout=120)  # 2 minute timeout

        # Check for results
        if CallbackHandler.token:
            return CallbackHandler.token, None
        elif CallbackHandler.error:
            return None, CallbackHandler.error
        else:
            return None, "Authentication timeout - no response received"

    except KeyboardInterrupt:
        return None, "cancelled"
    except Exception as e:
        return None, f"OAuth error: {str(e)}"
    finally:
        try:
            server.server_close()
        except:
            pass

def login():
    credentials_file_path = get_credentials_file_path()

    # Check if a saved token exists
    if os.path.exists(credentials_file_path):
        with open(credentials_file_path, "r", encoding="utf-8") as f:
            token = f.read().strip()

        if token:
            click.echo(
                "Already logged in. You can log out using `tnr logout` and try again."
            )
            return token  # Return the valid token, skip the login process

    # Try OAuth login first
    token, error = try_oauth_login()

    # If OAuth succeeded, save and return
    if token:
        success, error_message = utils.validate_token(token)
        if success:
            with open(credentials_file_path, "w", encoding="utf-8") as f:
                f.write(token)
            os.chmod(credentials_file_path, 0o600)
            click.echo(
                click.style(
                    f"Success! Return to the console and add a payment method: {CONSOLE_URL}",
                    fg="green",
                )
            )
            return token
        else:
            click.echo(click.style(f"Token validation failed: {error_message}", fg="red"))
            # Fall through to manual entry

    # If OAuth was cancelled or failed, fall back to manual token entry
    if error == "cancelled":
        click.echo("\nOAuth cancelled. You can enter your token manually instead.")
    elif error:
        click.echo(click.style(f"OAuth login failed: {error}", fg="yellow"))
        click.echo("Falling back to manual token entry.")

    click.echo(
        f"\nPlease click the following link and generate an API token in the Thunder Compute console: {OAUTH_URL}"
    )

    # Wait for user to input the token
    success = False
    num_attempts = 0
    while not success and num_attempts < 5:
        token = get_token_from_user()

        success, error_message = utils.validate_token(token)

        if not success:
            click.echo(
                click.style(
                    error_message,
                    fg="red",
                    bold=True,
                )
            )
            if error_message.startswith("Failed to authenticate"):
                exit(1)
            num_attempts += 1

    if not success and num_attempts == 5:
        click.echo(
            click.style(
                f"Failed to log in to thunder compute. Please double check your API token and try again.",
                fg="red",
                bold=True,
            )
        )
        exit(1)

    with open(credentials_file_path, "w", encoding="utf-8") as f:
        f.write(token)
    os.chmod(credentials_file_path, 0o600)
    click.echo(
        click.style(
            f"Success! Return to the console and add a payment method: {CONSOLE_URL}",
            fg="green",
        )
    )


def logout():
    delete_data()
    click.echo(
        click.style(
            "Logged out successfully",
            fg="green",
        )
    )


if __name__ == "__main__":
    login()