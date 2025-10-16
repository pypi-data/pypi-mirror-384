import re
from typing import TYPE_CHECKING, Callable, List, Optional, Union
from urllib.parse import urljoin, urlparse

from ..command_executor import CommandExecutor
from ..command_executor_local import CommandExecutorLocal
from ..commands.ubuntu.curl_commands_ubuntu import CurlCommandsUbuntu
from ..types.exec_result import ExecResult
from ..types.security_scan_result import SecurityCheckResult, WebSecurityScanResult
from .resource_base import ResourceBase

if TYPE_CHECKING:
    from ..store.data_models.server import Server


class WebSecurityScanner(ResourceBase):
    """Scanner for detecting information disclosure from web applications and infrastructure."""

    def __init__(self, executor: Union[CommandExecutor, CommandExecutorLocal], progress_callback: Optional[Callable[[str, str], None]] = None):
        """
        Initialize the WebSecurityScanner.
        
        Args:
            executor: Command executor for running HTTP requests (usually CommandExecutorLocal for external scanning)
            progress_callback: Optional callback for streaming progress updates
        """
        self.executor = executor
        self.curl_commands = CurlCommandsUbuntu()
        self.progress_callback = progress_callback

    def _report_progress(self, message: str, end: str = "\n") -> None:
        """Report progress using the configured callback if available.

        Args:
            message: The progress message to report
            end: The end character for the message (e.g., "\n" or "")
        """
        if self.progress_callback:
            self.progress_callback(message, end)

    def scan_target(self, target_url: str, categories: Optional[List[str]] = None, test_connectivity: bool = True) -> WebSecurityScanResult:
        """
        Perform a comprehensive security scan on the target URL.
        
        Args:
            target_url: The URL to scan (e.g., "https://example.com")
            categories: Optional list of categories to scan. If None, scans all categories.
                       Available: ["infrastructure", "frameworks", "development", "files"]
            test_connectivity: Whether to run the basic connectivity test. Should only be True for main server URLs.
        
        Returns:
            WebSecurityScanResult with all check results
        """
        all_checks: List[SecurityCheckResult] = []
        
        # Default to all categories if none specified
        if categories is None:
            categories = ["infrastructure", "frameworks", "development", "files"]

        self._report_progress(f"🔍 Scanning {target_url}")

        # Infrastructure checks (Caddy disclosure)
        if "infrastructure" in categories:
            self._report_progress("📋 [yellow]Running infrastructure checks...[/yellow]", end="")
            all_checks.extend(self._scan_infrastructure_disclosure(target_url, test_connectivity=test_connectivity))
            self._report_progress(" [green]✔[/green]")

        # Framework disclosure checks
        if "frameworks" in categories:
            self._report_progress("📋 [yellow]Running framework checks...[/yellow]", end="")
            all_checks.extend(self._scan_framework_disclosure(target_url))
            self._report_progress(" [green]✔[/green]")

        # Development/debug mode checks
        if "development" in categories:
            self._report_progress("📋 [yellow]Running development checks...[/yellow]", end="")
            all_checks.extend(self._scan_development_disclosure(target_url))
            self._report_progress(" [green]✔[/green]")

        # File/artifact exposure checks
        if "files" in categories:
            self._report_progress("📋 [yellow]Running file exposure checks...[/yellow]", end="")
            all_checks.extend(self._scan_file_exposure(target_url))
            self._report_progress(" [green]✔[/green]")

        # Create and return results
        result = WebSecurityScanResult.create(target_url, all_checks)
        
        # Report completion with summary
        failed_count = result.failed_checks
        if failed_count == 0:
            self._report_progress("🎉 [green]Scan complete - No issues found[/green]")
        else:
            critical_high = result.summary.get("critical", 0) + result.summary.get("high", 0)
            if critical_high > 0:
                self._report_progress(f"⚠️  [red]Scan complete - {failed_count} issues found ({critical_high} critical/high)[/red]")
            else:
                self._report_progress(f"⚠️  [yellow]Scan complete - {failed_count} issues found (medium/low)[/yellow]")
        
        return result

    def scan_server_apps(self, server: "Server", categories: Optional[List[str]] = None) -> List[WebSecurityScanResult]:
        """
        Scan all deployed applications on a server for security issues.
        
        Args:
            server: Server object containing deployed apps
            categories: Optional list of categories to scan
        
        Returns:
            List of WebSecurityScanResult for each URL scanned
        """
        scan_results: List[WebSecurityScanResult] = []
        
        # Get all URLs to scan for this server
        urls_to_scan = self._get_server_scan_urls(server)
        
        self._report_progress(f"🔍 Starting security scan of server {server.name} and all deployed applications")
        
        for i, url_info in enumerate(urls_to_scan, 1):
            self._report_progress(f"\n📊 Scanning {i}/{len(urls_to_scan)}: {url_info['context']}")
            try:
                result = self.scan_target(
                    url_info["url"], 
                    categories, 
                    test_connectivity=url_info.get("test_connectivity", True)
                )
                # Add context about what was scanned
                result.target_url = f"{result.target_url} ({url_info['context']})"
                scan_results.append(result)
            except Exception as e:
                self._report_progress(f"❌ [red]Failed to scan {url_info['context']}: {str(e)}[/red]")
                # Create a failed scan result for this URL
                failed_check = SecurityCheckResult(
                    check_name="scan_connectivity",
                    passed=False,
                    severity="medium",
                    description=f"Failed to scan {url_info['context']}",
                    details=f"Unable to connect to {url_info['url']}: {str(e)}",
                    category="infrastructure"
                )
                failed_result = WebSecurityScanResult.create(url_info["url"], [failed_check])
                failed_result.target_url = f"{failed_result.target_url} ({url_info['context']})"
                scan_results.append(failed_result)
        
        return scan_results

    def _get_server_scan_urls(self, server: "Server") -> List[dict]:
        """
        Get all URLs that should be scanned for a server.
        
        Args:
            server: Server object with deployed apps
            
        Returns:
            List of dictionaries with 'url', 'context', and 'test_connectivity' keys
        """
        urls_to_scan = []
        
        # Always scan the main server URL with the static test endpoint
        main_url = f"https://{server.hostname_or_ip}"
        urls_to_scan.append({
            "url": main_url,
            "context": "Main server endpoint",
            "test_connectivity": True  # Only test connectivity on main server
        })
        
        # Add deployed apps with their custom domains
        for app in server.apps:
            if app.custom_domain:
                app_url = f"https://{app.custom_domain}"
                urls_to_scan.append({
                    "url": app_url,
                    "context": f"App: {app.name}",
                    "test_connectivity": False  # Skip connectivity test for apps
                })
        
        return urls_to_scan

    def _test_basic_connectivity(self, target_url: str) -> SecurityCheckResult:
        """
        Test basic connectivity using the /caddyfile-static-hello endpoint.
        This follows the same pattern as existing EasyRunner connectivity tests.
        """
        from urllib.parse import urlparse
        
        # Parse the target URL to get the host
        parsed_url = urlparse(target_url)
        
        # For server IP connectivity tests, use HTTP on port 80 (where the static endpoint is configured)
        # This matches the pattern in ip_tables.py
        if parsed_url.hostname and (parsed_url.hostname.replace('.', '').isdigit() or ':' in parsed_url.hostname):
            # This looks like an IP address, use HTTP for the static endpoint test
            test_url = f"http://{parsed_url.hostname}/caddyfile-static-hello"
        else:
            # For domain names, use the original scheme
            test_url = urljoin(target_url, "/caddyfile-static-hello")
        
        cmd = self.curl_commands.get_with_timeout(test_url, timeout_seconds=10)
        result = self.executor.execute(cmd)
        
        if result.success and result.stdout:
            response_body, status_code = self.curl_commands.parse_curl_response_with_status(result.stdout)
            
            # Check for the expected response from Caddy
            if status_code == 200 and "Hello, caddyfile-static-hello is running!" in response_body:
                return SecurityCheckResult(
                    check_name="basic_connectivity",
                    passed=True,
                    severity="medium",
                    description="Basic connectivity test passed",
                    details="Static test endpoint responds correctly",
                    category="infrastructure"
                )
            else:
                return SecurityCheckResult(
                    check_name="basic_connectivity",
                    passed=False,
                    severity="medium",
                    description="Basic connectivity test failed",
                    details=f"Static test endpoint returned status {status_code}",
                    category="infrastructure"
                )
        else:
            return SecurityCheckResult(
                check_name="basic_connectivity",
                passed=False,
                severity="medium",
                description="Basic connectivity test failed",
                details="Unable to reach static test endpoint",
                category="infrastructure"
            )

    def _scan_infrastructure_disclosure(self, target_url: str, test_connectivity: bool = True) -> List[SecurityCheckResult]:
        """Check for infrastructure information disclosure (Caddy, etc.)."""
        checks: List[SecurityCheckResult] = []

        # Test basic connectivity first using the static hello endpoint (only for main server)
        if test_connectivity:
            checks.append(self._test_basic_connectivity(target_url))

        # Check for Caddy server header disclosure
        checks.append(self._check_caddy_server_header(target_url))
        
        # Check for Caddy admin API exposure
        checks.append(self._check_caddy_api_exposure(target_url))
        
        # Check for Caddy error page disclosure
        checks.append(self._check_caddy_error_pages(target_url))

        return checks

    def _scan_framework_disclosure(self, target_url: str) -> List[SecurityCheckResult]:
        """Check for web framework information disclosure."""
        checks: List[SecurityCheckResult] = []

        # Get headers for framework detection
        headers_result = self._get_response_headers(target_url)
        if headers_result.success and headers_result.stdout:
            headers_text = headers_result.stdout

            # Check for various framework signatures
            checks.append(self._check_react_disclosure(target_url, headers_text))
            checks.append(self._check_nextjs_disclosure(target_url, headers_text))
            checks.append(self._check_django_disclosure(target_url, headers_text))
            checks.append(self._check_flask_disclosure(target_url, headers_text))
            checks.append(self._check_fastapi_disclosure(target_url, headers_text))
            checks.append(self._check_express_disclosure(target_url, headers_text))
            checks.append(self._check_nodejs_disclosure(target_url, headers_text))

        return checks

    def _scan_development_disclosure(self, target_url: str) -> List[SecurityCheckResult]:
        """Check for development/debug mode information disclosure."""
        checks: List[SecurityCheckResult] = []

        # Check for development mode indicators
        checks.append(self._check_source_maps_exposure(target_url))
        checks.append(self._check_hot_reload_endpoints(target_url))
        checks.append(self._check_debug_error_pages(target_url))
        
        # FastAPI specific development checks
        checks.append(self._check_fastapi_docs_exposure(target_url))
        checks.append(self._check_openapi_schema_exposure(target_url))

        return checks

    def _scan_file_exposure(self, target_url: str) -> List[SecurityCheckResult]:
        """Check for exposed sensitive files and directories."""
        checks: List[SecurityCheckResult] = []

        # Common sensitive files to check
        sensitive_files = [
            ".env",
            ".env.local", 
            ".env.production",
            "package.json",
            "requirements.txt",
            "poetry.lock",
            "package-lock.json",
            "yarn.lock",
            "web.config",
            ".htaccess"
        ]

        for file_path in sensitive_files:
            checks.append(self._check_file_exposure(target_url, file_path))

        # Common sensitive directories
        sensitive_dirs = [
            ".git/",
            ".svn/",
            "node_modules/",
            "__pycache__/",
            "backup/",
            "backups/"
        ]

        for dir_path in sensitive_dirs:
            checks.append(self._check_directory_exposure(target_url, dir_path))

        return checks

    def _check_caddy_server_header(self, target_url: str) -> SecurityCheckResult:
        """Check if Caddy server header is exposed."""
        from urllib.parse import urlparse
        
        headers_result = self._get_response_headers(target_url)
        
        # If HTTPS fails for IP addresses, try HTTP as fallback (for health check endpoint)
        if not headers_result.success:
            parsed_url = urlparse(target_url)
            if parsed_url.hostname and (parsed_url.hostname.replace('.', '').isdigit() or ':' in parsed_url.hostname):
                # This looks like an IP address, try HTTP as fallback
                http_url = f"http://{parsed_url.hostname}"
                headers_result = self._get_response_headers(http_url)
        
        if not headers_result.success:
            return SecurityCheckResult(
                check_name="caddy_server_header",
                passed=False,
                severity="medium",
                description="Unable to check server headers",
                details=f"Failed to get headers: {headers_result.stderr}",
                category="infrastructure"
            )

        headers_text = headers_result.stdout or ""
        parsed_url = urlparse(target_url)
        
        # Check for Caddy in server header (case insensitive)
        server_header_match = re.search(r'server:\s*caddy', headers_text, re.IGNORECASE)
        if server_header_match:
            # For IP addresses, this might be the health check endpoint which is expected to show Caddy
            if parsed_url.hostname and (parsed_url.hostname.replace('.', '').isdigit() or ':' in parsed_url.hostname):
                return SecurityCheckResult(
                    check_name="caddy_server_header",
                    passed=True,
                    severity="medium",
                    description="Server header shows Caddy (expected for health check endpoint)",
                    details="IP-based health check endpoint appropriately identifies Caddy",
                    category="infrastructure"
                )
            else:
                # For domain names, Caddy disclosure should be flagged
                return SecurityCheckResult(
                    check_name="caddy_server_header",
                    passed=False,
                    severity="medium",
                    description="Caddy server header disclosed",
                    details="The 'Server' header reveals that Caddy is being used",
                    remediation="Configure Caddy to suppress or modify the Server header",
                    category="infrastructure"
                )

        # Check for Caddy in via header (case insensitive) 
        via_header_match = re.search(r'via:\s*[^,]*caddy', headers_text, re.IGNORECASE)
        if via_header_match:
            return SecurityCheckResult(
                check_name="caddy_server_header",
                passed=False,
                severity="medium",
                description="Caddy server disclosed in Via header",
                details="The 'Via' header reveals that Caddy is being used as a proxy",
                remediation="Configure Caddy to suppress or modify the Via header",
                category="infrastructure"
            )

        return SecurityCheckResult(
            check_name="caddy_server_header",
            passed=True,
            severity="medium",
            description="Server header does not disclose Caddy",
            category="infrastructure"
        )

    def _check_caddy_api_exposure(self, target_url: str) -> SecurityCheckResult:
        """Check if Caddy admin API is accessible externally."""
        parsed_url = urlparse(target_url)
        api_url = f"{parsed_url.scheme}://{parsed_url.netloc}:2019/config"
        
        cmd = self.curl_commands.get_with_timeout(api_url, timeout_seconds=5)
        result = self.executor.execute(cmd)
        
        if result.success and result.stdout:
            _, status_code = self.curl_commands.parse_curl_response_with_status(result.stdout)
            
            if status_code in [200, 201]:
                return SecurityCheckResult(
                    check_name="caddy_api_exposure",
                    passed=False,
                    severity="critical",
                    description="Caddy admin API is externally accessible",
                    details=f"Caddy API responded with status {status_code}",
                    remediation="Ensure Caddy admin API (port 2019) is blocked by firewall",
                    category="infrastructure"
                )

        return SecurityCheckResult(
            check_name="caddy_api_exposure",
            passed=True,
            severity="critical",
            description="Caddy admin API is not externally accessible",
            category="infrastructure"
        )

    def _check_caddy_error_pages(self, target_url: str) -> SecurityCheckResult:
        """Check if Caddy default error pages are exposed."""
        # Try to trigger a 404 error with a random path
        test_url = urljoin(target_url, "/nonexistent-path-for-security-test-" + "x" * 20)
        
        cmd = self.curl_commands.get_with_timeout(test_url, timeout_seconds=5)
        result = self.executor.execute(cmd)
        
        if result.success and result.stdout:
            response_body, status_code = self.curl_commands.parse_curl_response_with_status(result.stdout)
            
            if status_code == 404 and response_body:
                # Check for Caddy default error page patterns
                if re.search(r'caddy', response_body, re.IGNORECASE):
                    return SecurityCheckResult(
                        check_name="caddy_error_pages",
                        passed=False,
                        severity="low",
                        description="Caddy default error page exposed",
                        details="404 error page contains 'Caddy' references",
                        remediation="Configure custom error pages in Caddy",
                        category="infrastructure"
                    )

        return SecurityCheckResult(
            check_name="caddy_error_pages",
            passed=True,
            severity="low", 
            description="No Caddy references found in error pages",
            category="infrastructure"
        )

    def _check_react_disclosure(self, target_url: str, headers_text: str) -> SecurityCheckResult:
        """Check for React framework disclosure."""
        # Check headers first
        if re.search(r'x-powered-by:\s*react', headers_text, re.IGNORECASE):
            return SecurityCheckResult(
                check_name="react_disclosure",
                passed=False,
                severity="low",
                description="React framework disclosed in headers",
                details="X-Powered-By header reveals React usage",
                remediation="Remove or modify X-Powered-By header",
                category="frameworks"
            )

        # Check for React development mode in page content
        cmd = self.curl_commands.get_with_timeout(target_url)
        result = self.executor.execute(cmd)
        
        if result.success and result.stdout:
            response_body, _ = self.curl_commands.parse_curl_response_with_status(result.stdout)
            
            # Check for React development mode indicators
            if re.search(r'__REACT_DEVTOOLS_GLOBAL_HOOK__', response_body, re.IGNORECASE):
                return SecurityCheckResult(
                    check_name="react_disclosure",
                    passed=False,
                    severity="medium",
                    description="React development mode detected",
                    details="React DevTools hooks found in page source",
                    remediation="Build React app in production mode",
                    category="frameworks"
                )

        return SecurityCheckResult(
            check_name="react_disclosure",
            passed=True,
            severity="low",
            description="No React framework disclosure detected",
            category="frameworks"
        )

    def _check_nextjs_disclosure(self, target_url: str, headers_text: str) -> SecurityCheckResult:
        """Check for Next.js framework disclosure."""
        disclosure_details = []
        
        # Check for X-Powered-By header (should be removed)
        if re.search(r'x-powered-by:\s*next\.js', headers_text, re.IGNORECASE):
            disclosure_details.append("X-Powered-By header reveals Next.js usage")
        
        # Check for Next.js cache headers (reveal implementation details)
        if re.search(r'x-nextjs-cache:', headers_text, re.IGNORECASE):
            disclosure_details.append("X-NextJS-Cache header reveals caching strategy")
            
        # Check for Next.js prerender headers (reveal build strategy)
        if re.search(r'x-nextjs-prerender:', headers_text, re.IGNORECASE):
            disclosure_details.append("X-NextJS-Prerender header reveals build strategy")
            
        # Check for Next.js stale time headers (reveal cache timing)
        if re.search(r'x-nextjs-stale-time:', headers_text, re.IGNORECASE):
            disclosure_details.append("X-NextJS-Stale-Time header reveals cache configuration")

        if disclosure_details:
            return SecurityCheckResult(
                check_name="nextjs_disclosure",
                passed=False,
                severity="low",
                description="Next.js framework disclosed in headers",
                details="; ".join(disclosure_details),
                remediation="Remove X-Powered-By header in next.config.js and consider hiding other Next.js-specific headers",
                category="frameworks"
            )

        # Check for Next.js specific paths
        nextjs_paths = ["/_next/static/", "/_next/webpack-hmr"]
        
        for path in nextjs_paths:
            test_url = urljoin(target_url, path)
            cmd = self.curl_commands.get_with_timeout(test_url, timeout_seconds=5)
            result = self.executor.execute(cmd)
            
            if result.success and result.stdout:
                _, status_code = self.curl_commands.parse_curl_response_with_status(result.stdout)
                
                if status_code in [200, 201, 302]:
                    return SecurityCheckResult(
                        check_name="nextjs_disclosure",
                        passed=False,
                        severity="low",
                        description="Next.js framework disclosed via paths",
                        details=f"Next.js path {path} is accessible",
                        remediation="Configure reverse proxy to block /_next/ paths if not needed",
                        category="frameworks"
                    )

        return SecurityCheckResult(
            check_name="nextjs_disclosure",
            passed=True,
            severity="low",
            description="No Next.js framework disclosure detected",
            category="frameworks"
        )

    def _check_django_disclosure(self, target_url: str, headers_text: str) -> SecurityCheckResult:
        """Check for Django framework disclosure."""
        # Check for Django version in headers
        django_header_match = re.search(r'server:.*django[/\s]([0-9.]+)', headers_text, re.IGNORECASE)
        
        if django_header_match:
            return SecurityCheckResult(
                check_name="django_disclosure",
                passed=False,
                severity="medium",
                description="Django framework and version disclosed",
                details=f"Server header reveals Django version: {django_header_match.group(1)}",
                remediation="Configure web server to suppress version information",
                category="frameworks"
            )

        # Check for Django debug pages by triggering errors
        debug_url = urljoin(target_url, "/nonexistent-django-debug-test")
        cmd = self.curl_commands.get_with_timeout(debug_url, timeout_seconds=5)
        result = self.executor.execute(cmd)
        
        if result.success and result.stdout:
            response_body, status_code = self.curl_commands.parse_curl_response_with_status(result.stdout)
            
            if status_code in [404, 500] and response_body:
                # Check for specific Django debug page indicators (more precise detection)
                django_debug_patterns = [
                    r'<h1>.*Django.*</h1>',  # Django debug page title
                    r'<title>.*Django.*Debug.*</title>',  # Debug page title
                    r'<div id="summary">.*Traceback.*</div>',  # Django traceback section
                    r'class="django-debug-toolbar"',  # Django debug toolbar
                    r'<h2>Request information</h2>',  # Django debug request info
                    r'django\.contrib\.staticfiles',  # Django staticfiles references
                    r'<pre class="exception_value">',  # Django exception format
                    r'Django version.*Python version'  # Django debug footer
                ]
                
                # Require multiple indicators to reduce false positives
                matches = sum(1 for pattern in django_debug_patterns if re.search(pattern, response_body, re.IGNORECASE))
                
                if matches >= 2:  # Require at least 2 Django-specific patterns
                    return SecurityCheckResult(
                        check_name="django_disclosure",
                        passed=False,
                        severity="high",
                        description="Django debug mode enabled",
                        details="Django debug page detected in error response",
                        remediation="Set DEBUG = False in Django settings",
                        category="frameworks"
                    )

        return SecurityCheckResult(
            check_name="django_disclosure",
            passed=True,
            severity="medium",
            description="No Django framework disclosure detected",
            category="frameworks"
        )

    def _check_flask_disclosure(self, target_url: str, headers_text: str) -> SecurityCheckResult:
        """Check for Flask framework disclosure."""
        # Check for Werkzeug/Flask in server headers
        flask_header_match = re.search(r'server:.*werkzeug[/\s]([0-9.]+)', headers_text, re.IGNORECASE)
        
        if flask_header_match:
            return SecurityCheckResult(
                check_name="flask_disclosure",
                passed=False,
                severity="medium",
                description="Flask/Werkzeug framework disclosed",
                details=f"Server header reveals Werkzeug version: {flask_header_match.group(1)}",
                remediation="Use production WSGI server like Gunicorn instead of Werkzeug",
                category="frameworks"
            )

        return SecurityCheckResult(
            check_name="flask_disclosure",
            passed=True,
            severity="medium",
            description="No Flask framework disclosure detected",
            category="frameworks"
        )

    def _check_fastapi_disclosure(self, target_url: str, headers_text: str) -> SecurityCheckResult:
        """Check for FastAPI framework disclosure."""
        # Check for uvicorn in server headers
        if re.search(r'server:\s*uvicorn', headers_text, re.IGNORECASE):
            return SecurityCheckResult(
                check_name="fastapi_disclosure",
                passed=False,
                severity="medium",
                description="FastAPI/Uvicorn framework disclosed",
                details="Server header reveals Uvicorn (FastAPI) usage",
                remediation="Configure reverse proxy to suppress server headers",
                category="frameworks"
            )

        return SecurityCheckResult(
            check_name="fastapi_disclosure",
            passed=True,
            severity="medium",
            description="No FastAPI framework disclosure detected",
            category="frameworks"
        )

    def _check_express_disclosure(self, target_url: str, headers_text: str) -> SecurityCheckResult:
        """Check for Express.js framework disclosure."""
        if re.search(r'x-powered-by:\s*express', headers_text, re.IGNORECASE):
            return SecurityCheckResult(
                check_name="express_disclosure",
                passed=False,
                severity="low",
                description="Express.js framework disclosed",
                details="X-Powered-By header reveals Express.js usage",
                remediation="Use app.disable('x-powered-by') in Express.js",
                category="frameworks"
            )

        return SecurityCheckResult(
            check_name="express_disclosure",
            passed=True,
            severity="low",
            description="No Express.js framework disclosure detected",
            category="frameworks"
        )

    def _check_nodejs_disclosure(self, target_url: str, headers_text: str) -> SecurityCheckResult:
        """Check for Node.js runtime disclosure."""
        # Check for Node.js in headers
        nodejs_match = re.search(r'x-powered-by:.*node\.js[/\s]?([0-9.]*)', headers_text, re.IGNORECASE)
        
        if nodejs_match:
            version_info = nodejs_match.group(1) if nodejs_match.group(1) else "version unknown"
            return SecurityCheckResult(
                check_name="nodejs_disclosure",
                passed=False,
                severity="low",
                description="Node.js runtime disclosed",
                details=f"X-Powered-By header reveals Node.js {version_info}",
                remediation="Remove X-Powered-By header in application",
                category="frameworks"
            )

        return SecurityCheckResult(
            check_name="nodejs_disclosure",
            passed=True,
            severity="low",
            description="No Node.js runtime disclosure detected",
            category="frameworks"
        )

    def _check_source_maps_exposure(self, target_url: str) -> SecurityCheckResult:
        """Check if JavaScript source maps are publicly accessible."""
        # Common source map paths
        source_map_paths = [
            "/static/js/main.js.map",
            "/assets/js/app.js.map",
            "/_next/static/chunks/main.js.map",
            "/js/app.js.map"
        ]

        for path in source_map_paths:
            test_url = urljoin(target_url, path)
            cmd = self.curl_commands.get_with_timeout(test_url, timeout_seconds=5)
            result = self.executor.execute(cmd)
            
            if result.success and result.stdout:
                response_body, status_code = self.curl_commands.parse_curl_response_with_status(result.stdout)
                
                if status_code == 200 and response_body and '"mappings"' in response_body:
                    return SecurityCheckResult(
                        check_name="source_maps_exposure",
                        passed=False,
                        severity="medium",
                        description="JavaScript source maps exposed",
                        details=f"Source map accessible at {path}",
                        remediation="Remove source maps from production build or block access",
                        category="development"
                    )

        return SecurityCheckResult(
            check_name="source_maps_exposure",
            passed=True,
            severity="medium",
            description="No exposed source maps detected",
            category="development"
        )

    def _check_hot_reload_endpoints(self, target_url: str) -> SecurityCheckResult:
        """Check for development hot reload endpoints."""
        # Common hot reload endpoints
        hot_reload_paths = [
            "/_next/webpack-hmr",
            "/sockjs-node/",
            "/__webpack_dev_server__/",
            "/hot-update.json"
        ]

        for path in hot_reload_paths:
            test_url = urljoin(target_url, path)
            cmd = self.curl_commands.get_with_timeout(test_url, timeout_seconds=5)
            result = self.executor.execute(cmd)
            
            if result.success and result.stdout:
                _, status_code = self.curl_commands.parse_curl_response_with_status(result.stdout)
                
                if status_code in [200, 201, 101]:  # 101 for WebSocket upgrade
                    return SecurityCheckResult(
                        check_name="hot_reload_endpoints",
                        passed=False,
                        severity="medium",
                        description="Development hot reload endpoints exposed",
                        details=f"Hot reload endpoint accessible at {path}",
                        remediation="Ensure application is built for production",
                        category="development"
                    )

        return SecurityCheckResult(
            check_name="hot_reload_endpoints",
            passed=True,
            severity="medium",
            description="No hot reload endpoints detected",
            category="development"
        )

    def _check_debug_error_pages(self, target_url: str) -> SecurityCheckResult:
        """Check for debug information in error pages."""
        # Try to trigger a server error
        error_url = urljoin(target_url, "/trigger-error-for-security-test")
        cmd = self.curl_commands.get_with_timeout(error_url, timeout_seconds=5)
        result = self.executor.execute(cmd)
        
        if result.success and result.stdout:
            response_body, status_code = self.curl_commands.parse_curl_response_with_status(result.stdout)
            
            if status_code >= 400 and response_body:
                # Look for debug information patterns
                debug_patterns = [
                    r'traceback|stack trace',
                    r'debug.*mode|mode.*debug',
                    r'werkzeug.*debugger',
                    r'django.*debug',
                    r'file.*line.*in'
                ]
                
                for pattern in debug_patterns:
                    if re.search(pattern, response_body, re.IGNORECASE):
                        return SecurityCheckResult(
                            check_name="debug_error_pages",
                            passed=False,
                            severity="high",
                            description="Debug information in error pages",
                            details="Error page contains debug information or stack traces",
                            remediation="Configure production error pages without debug info",
                            category="development"
                        )

        return SecurityCheckResult(
            check_name="debug_error_pages",
            passed=True,
            severity="high",
            description="No debug information in error pages",
            category="development"
        )

    def _check_fastapi_docs_exposure(self, target_url: str) -> SecurityCheckResult:
        """Check if FastAPI automatic documentation is publicly accessible."""
        docs_paths = ["/docs", "/redoc"]
        
        for path in docs_paths:
            test_url = urljoin(target_url, path)
            cmd = self.curl_commands.get_with_timeout(test_url, timeout_seconds=5)
            result = self.executor.execute(cmd)
            
            if result.success and result.stdout:
                response_body, status_code = self.curl_commands.parse_curl_response_with_status(result.stdout)
                
                if status_code == 200 and response_body:
                    # Check for FastAPI docs indicators
                    if re.search(r'swagger|redoc|openapi', response_body, re.IGNORECASE):
                        return SecurityCheckResult(
                            check_name="fastapi_docs_exposure",
                            passed=False,
                            severity="medium",
                            description="FastAPI documentation publicly accessible",
                            details=f"API documentation accessible at {path}",
                            remediation="Disable docs in production or add authentication",
                            category="development"
                        )

        return SecurityCheckResult(
            check_name="fastapi_docs_exposure",
            passed=True,
            severity="medium",
            description="No public FastAPI documentation detected",
            category="development"
        )

    def _check_openapi_schema_exposure(self, target_url: str) -> SecurityCheckResult:
        """Check if OpenAPI schema is publicly accessible."""
        schema_url = urljoin(target_url, "/openapi.json")
        cmd = self.curl_commands.get_with_timeout(schema_url, timeout_seconds=5)
        result = self.executor.execute(cmd)
        
        if result.success and result.stdout:
            response_body, status_code = self.curl_commands.parse_curl_response_with_status(result.stdout)
            
            if status_code == 200 and response_body:
                # Check for OpenAPI schema structure
                if re.search(r'"openapi":|"swagger":|"paths":', response_body):
                    return SecurityCheckResult(
                        check_name="openapi_schema_exposure",
                        passed=False,
                        severity="medium",
                        description="OpenAPI schema publicly accessible",
                        details="API schema accessible at /openapi.json",
                        remediation="Disable schema endpoint in production or add authentication",
                        category="development"
                    )

        return SecurityCheckResult(
            check_name="openapi_schema_exposure",
            passed=True,
            severity="medium",
            description="No public OpenAPI schema detected",
            category="development"
        )

    def _check_file_exposure(self, target_url: str, file_path: str) -> SecurityCheckResult:
        """Check if a specific file is publicly accessible."""
        test_url = urljoin(target_url, file_path)
        cmd = self.curl_commands.get_with_timeout(test_url, timeout_seconds=5)
        result = self.executor.execute(cmd)
        
        if result.success and result.stdout:
            response_body, status_code = self.curl_commands.parse_curl_response_with_status(result.stdout)
            
            if status_code == 200 and response_body:
                # Basic check that it's not just an error page
                if len(response_body.strip()) > 0 and not re.search(r'not found|404|error', response_body, re.IGNORECASE):
                    severity = "high" if file_path.startswith(".env") else "medium"
                    return SecurityCheckResult(
                        check_name=f"file_exposure_{file_path.replace('/', '_').replace('.', '_')}",
                        passed=False,
                        severity=severity,
                        description=f"Sensitive file exposed: {file_path}",
                        details=f"File {file_path} is publicly accessible",
                        remediation=f"Block access to {file_path} or remove from web root",
                        category="files"
                    )

        return SecurityCheckResult(
            check_name=f"file_exposure_{file_path.replace('/', '_').replace('.', '_')}",
            passed=True,
            severity="medium",
            description=f"File {file_path} not exposed",
            category="files"
        )

    def _check_directory_exposure(self, target_url: str, dir_path: str) -> SecurityCheckResult:
        """Check if a directory is publicly accessible."""
        test_url = urljoin(target_url, dir_path)
        cmd = self.curl_commands.get_with_timeout(test_url, timeout_seconds=5)
        result = self.executor.execute(cmd)
        
        if result.success and result.stdout:
            response_body, status_code = self.curl_commands.parse_curl_response_with_status(result.stdout)
            
            if status_code == 200 and response_body:
                # Check for directory listing patterns
                if re.search(r'index of|directory listing|parent directory', response_body, re.IGNORECASE):
                    severity = "critical" if dir_path.startswith(".git") else "high"
                    return SecurityCheckResult(
                        check_name=f"directory_exposure_{dir_path.replace('/', '_').replace('.', '_')}",
                        passed=False,
                        severity=severity,
                        description=f"Directory listing exposed: {dir_path}",
                        details=f"Directory {dir_path} shows file listing",
                        remediation=f"Block access to {dir_path} or disable directory listing",
                        category="files"
                    )

        return SecurityCheckResult(
            check_name=f"directory_exposure_{dir_path.replace('/', '_').replace('.', '_')}",
            passed=True,
            severity="high",
            description=f"Directory {dir_path} not exposed",
            category="files"
        )

    def _get_response_headers(self, target_url: str) -> ExecResult:
        """Get HTTP response headers for analysis."""
        cmd = self.curl_commands.get_headers_only(target_url)
        return self.executor.execute(cmd)
