import http.server
import socketserver
import threading
import urllib.parse
from typing import Optional


class OAuthCallbackServer(socketserver.TCPServer):
    """Custom TCPServer with OAuth state tracking."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.authorization_code: Optional[str] = None
        self.oauth_error: Optional[str] = None


class OAuthCallbackHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler for OAuth callback."""

    def __init__(self, *args, **kwargs):
        # Suppress default HTTP server logging
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        # Suppress HTTP server logs
        pass

    def do_GET(self):
        """Handle OAuth callback GET request."""
        if self.path.startswith('/callback'):
            # Parse authorization code from URL
            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)

            code = query_params.get('code', [None])[0]
            error = query_params.get('error', [None])[0]

            # Cast server to our custom type that has the OAuth attributes
            oauth_server = self.server  # type: ignore[assignment]

            if error:
                oauth_server.oauth_error = error  # type: ignore[attr-defined]
                self.send_error_page(f"Authorization failed: {error}")
            elif code:
                oauth_server.authorization_code = code  # type: ignore[attr-defined]
                self.send_success_page()
            else:
                oauth_server.oauth_error = "No authorization code received"  # type: ignore[attr-defined]
                self.send_error_page("No authorization code received")

            # Signal to shut down server
            threading.Thread(target=self.server.shutdown).start()
        else:
            self.send_error(404)

    def send_success_page(self):
        """Send success page to browser."""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        success_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>EasyRunner GitHub Authorization</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                    .success { color: #28a745; }
                    .logo { font-size: 24px; font-weight: bold; color: #28a745; margin-bottom: 20px; }
                </style>
            </head>
            <body>
                <div class="logo">EasyRunner</div>
                <h1 class="success">Authorization Successful!</h1>
                <p>You can close this tab and return to your terminal.</p>
                <p>EasyRunner now has access to manage deploy keys for your repositories.</p>
                <p><a href="https://easyrunner.xyz">EasyRunner.xyz</a></p>
            </body>
            </html>
        """
        self.wfile.write(success_html.encode('utf-8'))

    def send_error_page(self, error_message: str):
        """Send error page to browser."""
        self.send_response(400)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        error_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>EasyRunner GitHub Authorization</title>
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                    .error {{ color: #dc3545; }}
                    .logo {{ font-size: 24px; font-weight: bold; color: #007bff; margin-bottom: 20px; }}
                </style>
            </head>
            <body>
                <div class="logo">EasyRunner</div>
                <h1 class="error">Authorization Failed</h1>
                <p>{error_message}</p>
                <p>Please try running the auth command again.</p>
            </body>
            </html>
        """
        self.wfile.write(error_html.encode('utf-8'))
