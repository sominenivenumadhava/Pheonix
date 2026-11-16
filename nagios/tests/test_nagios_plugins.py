import os
import sys
import subprocess
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone
import pytest

PYTHON_EXE = sys.executable
SCRIPT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "plugins"))
HEALTH_PLUGIN = os.path.join(SCRIPT_DIR, "check_portal_health.py")
ERRORS_PLUGIN = os.path.join(SCRIPT_DIR, "check_web_errors.py")

# --- Mock HTTP Server for Testing check_portal_health ---
class MockPortalHandler(BaseHTTPRequestHandler):
    mode = "healthy"
    delay = 0.0

    def do_GET(self):
        if self.delay > 0:
            time.sleep(self.delay)

        if self.path == "/health":
            if self.mode == "healthy":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status": "healthy", "db": "ok", "version": "1.0.0"}')
            elif self.mode == "db_failed":
                self.send_response(503)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status": "unhealthy", "db": "failed"}')
            elif self.mode == "invalid_json":
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b'NOT JSON')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass # Suppress test server logs

@pytest.fixture(scope="module")
def mock_server():
    server = HTTPServer(("127.0.0.1", 0), MockPortalHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    yield server, port
    server.shutdown()

# ==============================================================================
# TESTS FOR check_portal_health.py
# ==============================================================================
def test_portal_health_ok(mock_server):
    """Simulate healthy portal: HTTP 200, fast response, db ok -> Exit 0 (OK)."""
    server, port = mock_server
    MockPortalHandler.mode = "healthy"
    MockPortalHandler.delay = 0.0

    cmd = [PYTHON_EXE, HEALTH_PLUGIN, "-H", "127.0.0.1", "-p", str(port), "-u", "/health", "-w", "500", "-c", "1500"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    print("\n[REAL OUTPUT - HEALTHY]:", result.stdout.strip())
    assert result.returncode == 0
    assert "PORTAL HEALTH OK" in result.stdout
    assert "db=ok" in result.stdout
    assert "'time'=" in result.stdout

def test_portal_health_warning_slow(mock_server):
    """Simulate slow portal: response latency exceeds warning threshold -> Exit 1 (WARNING)."""
    server, port = mock_server
    MockPortalHandler.mode = "healthy"
    MockPortalHandler.delay = 0.12 # 120ms delay

    # Warning threshold set to 80ms, Critical set to 500ms
    cmd = [PYTHON_EXE, HEALTH_PLUGIN, "-H", "127.0.0.1", "-p", str(port), "-u", "/health", "-w", "80", "-c", "500"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    print("\n[REAL OUTPUT - SLOW/WARNING]:", result.stdout.strip())
    assert result.returncode == 1
    assert "PORTAL HEALTH WARNING" in result.stdout
    assert "exceeds warning threshold" in result.stdout

def test_portal_health_critical_db_down(mock_server):
    """Simulate database outage: HTTP 503 db=failed -> Exit 2 (CRITICAL)."""
    server, port = mock_server
    MockPortalHandler.mode = "db_failed"
    MockPortalHandler.delay = 0.0

    cmd = [PYTHON_EXE, HEALTH_PLUGIN, "-H", "127.0.0.1", "-p", str(port), "-u", "/health", "-w", "500", "-c", "1500"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    print("\n[REAL OUTPUT - DB FAILED/CRITICAL]:", result.stdout.strip())
    assert result.returncode == 2
    assert "PORTAL HEALTH CRITICAL" in result.stdout

def test_portal_health_critical_connection_refused():
    """Simulate application down: connection refused on closed port -> Exit 2 (CRITICAL)."""
    cmd = [PYTHON_EXE, HEALTH_PLUGIN, "-H", "127.0.0.1", "-p", "59999", "-u", "/health", "-t", "1.0"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    print("\n[REAL OUTPUT - CONNECTION REFUSED/CRITICAL]:", result.stdout.strip())
    assert result.returncode == 2
    assert "PORTAL HEALTH CRITICAL" in result.stdout
    assert "Connection refused" in result.stdout or "unreachable" in result.stdout

def test_portal_health_critical_latency(mock_server):
    """Simulate high latency exceeding critical threshold -> Exit 2 (CRITICAL)."""
    server, port = mock_server
    MockPortalHandler.mode = "healthy"
    MockPortalHandler.delay = 0.15 # 150ms delay

    # Warning threshold 50ms, Critical threshold 100ms
    cmd = [PYTHON_EXE, HEALTH_PLUGIN, "-H", "127.0.0.1", "-p", str(port), "-u", "/health", "-w", "50", "-c", "100"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    print("\n[REAL OUTPUT - HIGH LATENCY/CRITICAL]:", result.stdout.strip())
    assert result.returncode == 2
    assert "PORTAL HEALTH CRITICAL" in result.stdout
    assert "exceeds critical threshold" in result.stdout

# ==============================================================================
# TESTS FOR check_web_errors
# ==============================================================================
def create_dummy_log(tmp_path, error_5xx_count: int, normal_count: int = 10):
    log_file = tmp_path / "access.log"
    now_str = datetime.now(timezone.utc).strftime("%d/%b/%Y:%H:%M:%S +0000")
    lines = []

    for _ in range(normal_count):
        lines.append(f'192.168.56.1 - - [{now_str}] "GET / HTTP/1.1" 200 4500 "-" "Mozilla/5.0"\n')

    for _ in range(error_5xx_count):
        lines.append(f'192.168.56.1 - - [{now_str}] "GET /api/bookings HTTP/1.1" 500 120 "-" "Mozilla/5.0"\n')

    log_file.write_text("".join(lines), encoding="utf-8")
    return str(log_file)

def test_web_errors_ok(tmp_path):
    """Simulate normal web traffic with 0 5xx errors -> Exit 0 (OK)."""
    log_path = create_dummy_log(tmp_path, error_5xx_count=0)

    cmd = [PYTHON_EXE, ERRORS_PLUGIN, "-f", log_path, "-w", "5", "-c", "20", "-m", "5"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    print("\n[REAL OUTPUT - WEB ERRORS OK]:", result.stdout.strip())
    assert result.returncode == 0
    assert "WEB ERRORS OK" in result.stdout
    assert "Found 0 HTTP 5xx errors" in result.stdout
    assert "'errors_5xx'=0;5;20;0;" in result.stdout

def test_web_errors_warning(tmp_path):
    """Simulate elevated errors (7 errors >= warning threshold 5) -> Exit 1 (WARNING)."""
    log_path = create_dummy_log(tmp_path, error_5xx_count=7)

    cmd = [PYTHON_EXE, ERRORS_PLUGIN, "-f", log_path, "-w", "5", "-c", "20", "-m", "5"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    print("\n[REAL OUTPUT - WEB ERRORS WARNING]:", result.stdout.strip())
    assert result.returncode == 1
    assert "WEB ERRORS WARNING" in result.stdout
    assert "Found 7 HTTP 5xx errors" in result.stdout

def test_web_errors_critical(tmp_path):
    """Simulate high error spike (25 errors >= critical threshold 20) -> Exit 2 (CRITICAL)."""
    log_path = create_dummy_log(tmp_path, error_5xx_count=25)

    cmd = [PYTHON_EXE, ERRORS_PLUGIN, "-f", log_path, "-w", "5", "-c", "20", "-m", "5"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    print("\n[REAL OUTPUT - WEB ERRORS CRITICAL]:", result.stdout.strip())
    assert result.returncode == 2
    assert "WEB ERRORS CRITICAL" in result.stdout
    assert "Found 25 HTTP 5xx errors" in result.stdout

def test_web_errors_unknown_missing_file():
    """Simulate non-existent log file -> Exit 3 (UNKNOWN)."""
    cmd = [PYTHON_EXE, ERRORS_PLUGIN, "-f", "non_existent_log_file_12345.log"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    print("\n[REAL OUTPUT - WEB ERRORS UNKNOWN]:", result.stdout.strip())
    assert result.returncode == 3
    assert "WEB ERRORS UNKNOWN" in result.stdout
    assert "does not exist" in result.stdout
