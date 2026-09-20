#!/usr/bin/env python3
"""
Development server script that starts the Flask app and opens a browser.
Usage: python dev.py
Or via npm: npm run start:dev
"""
import os
import sys
import time
import socket
import subprocess
import shutil
import platform
import webbrowser
import threading
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def is_port_in_use(port: int) -> bool:
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return False
        except OSError:
            return True


def find_available_port(start: int, end: int) -> int | None:
    """Find an available port in the range"""
    for port in range(start, end + 1):
        if not is_port_in_use(port):
            return port
    return None


def wait_for_server(url: str, timeout: int = 30) -> bool:
    """Wait for the server to be ready"""
    import urllib.request
    import urllib.error
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except (urllib.error.URLError, OSError):
            time.sleep(0.5)
    return False


def open_browser(url: str, delay: float = 2.0):
    """Open browser after server is ready"""
    # Wait a bit for server to start
    time.sleep(delay)
    # Then wait for server to actually respond
    if wait_for_server(url, timeout=10):
        print(f"🌐 Opening browser at {url}")
        webbrowser.open(url)
    else:
        print(f"⚠️  Server not responding yet, but opening browser anyway at {url}")
        webbrowser.open(url)


def main():
    # 1) Ensure DB migrations are applied
    try:
        alembic_bin = shutil.which("alembic")
        if alembic_bin:
            print("⚙️  Applying migrations (alembic upgrade heads)…")
            env = os.environ.copy()
            project_root = Path(__file__).parent
            env["PYTHONPATH"] = str(project_root)
            env.setdefault("DATABASE_URL", "sqlite:///local.db")
            subprocess.run([alembic_bin, "upgrade", "heads"], check=True, env=env, cwd=project_root)
        else:
            print("⚠️  Alembic not found in PATH; skipping automatic migrations.")
    except Exception as e:
        print(f"⚠️  Migrations step skipped: {e}")

    # 2) Pick a free port
    requested = int(os.getenv("PORT", "5000"))
    chosen = requested
    if is_port_in_use(requested):
        alt = find_available_port(5001, 65535)
        if alt:
            print(f"⚠️  Port {requested} busy — starting on {alt}")
            chosen = alt
        else:
            print(f"❌ Port {requested} busy and no alternates free in 5001-65535.")
            print("🔁 Free a local port or set PORT to one manually, then re-run dev.py.")
            sys.exit(1)

    # 3) Run with gunicorn if available; else Flask dev server
    is_windows = platform.system() == "Windows"
    gunicorn_bin = shutil.which("gunicorn") if not is_windows else None
    
    url = f"http://127.0.0.1:{chosen}"
    
    if gunicorn_bin:
        print(f"🚀 Starting gunicorn on port {chosen}…")
        print(f"🌐 Browser will open at {url} in a few seconds...")
        
        # Start browser opener in background before execv
        browser_thread = threading.Thread(target=open_browser, args=(url, 3.0), daemon=True)
        browser_thread.start()
        
        # Use execv to replace current process (browser thread will continue)
        os.execv(
            gunicorn_bin,
            [
                "gunicorn",
                "app:app",
                "--workers", "2",
                "--threads", "4",
                "--timeout", "120",
                "-b", f"0.0.0.0:{chosen}"
            ]
        )
    else:
        if is_windows:
            print(f"🚀 Starting Flask dev server on {url} (Windows detected, skipping gunicorn)")
        else:
            print(f"🚀 Starting Flask dev server on {url}")
        print(f"🌐 Browser will open automatically...")
        
        # Start browser opener in background
        browser_thread = threading.Thread(target=open_browser, args=(url,), daemon=True)
        browser_thread.start()
        
        # Import app after setting up environment
        os.chdir(project_root)
        from app import app
        
        # Run Flask dev server
        app.run(host="127.0.0.1", port=chosen, use_reloader=False, debug=True)


if __name__ == "__main__":
    main()
