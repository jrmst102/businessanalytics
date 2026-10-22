"""Start the local dashboard: ``python launch.py``.

Starts the Python engine API (engine_api.py) and the Node.js web server
(server/server.js), opens the browser (or prints the URL), and gives readable
messages for a missing dependency, missing Node.js, or an occupied port.
Works from any working directory and binds to this computer only.
"""
import argparse
import importlib.util
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
REQUIRED_PYTHON = ['flask', 'waitress', 'sklearn', 'pandas', 'numpy']


def missing_dependencies():
    return [name for name in REQUIRED_PYTHON if importlib.util.find_spec(name) is None]


def port_is_free(port, host='127.0.0.1'):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex((host, port)) != 0


def wait_for(url, seconds=60):
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2):
                return True
        except OSError:
            time.sleep(0.5)
    return False


def main():
    parser = argparse.ArgumentParser(description='Launch "Business Analytics in Action: From Model to App".')
    parser.add_argument('--port', type=int, default=8080, help='Dashboard port (default 8080).')
    parser.add_argument('--engine-port', type=int, default=8000, help='Engine API port (default 8000).')
    parser.add_argument('--no-browser', action='store_true', help='Print the URL instead of opening a browser.')
    args = parser.parse_args()

    missing = missing_dependencies()
    if missing:
        sys.exit('Missing Python packages: ' + ', '.join(missing) + '.\n'
                 'Activate your virtual environment and run:\n'
                 f'    {sys.executable} -m pip install -r "{APP_DIR / "requirements.txt"}"\n'
                 'Then start the app again with: python launch.py')
    node = shutil.which('node')
    if node is None:
        sys.exit('Node.js was not found. Install Node.js 18 or newer from https://nodejs.org, '
                 'then start the app again with: python launch.py')
    if not (APP_DIR / 'server' / 'node_modules').exists():
        sys.exit('The web server packages are not installed yet. Run once:\n'
                 f'    npm install --prefix "{APP_DIR / "server"}"\n'
                 'Then start the app again with: python launch.py')
    for port, what in [(args.port, 'dashboard'), (args.engine_port, 'engine API')]:
        if not port_is_free(port):
            sys.exit(f'Port {port} ({what}) is already in use (another dashboard may still be running).\n'
                     f'Close it, or start this app on other ports: '
                     f'python launch.py --port {args.port + 1} --engine-port {args.engine_port + 1}')

    url = f'http://localhost:{args.port}'
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))  # clean up children on kill
    engine = subprocess.Popen(
        [sys.executable, str(APP_DIR / 'engine_api.py'), '--port', str(args.engine_port)])
    web = None
    try:
        if not wait_for(f'http://127.0.0.1:{args.engine_port}/api/health'):
            sys.exit('The engine API did not start; see the messages above.')
        web = subprocess.Popen(
            [node, str(APP_DIR / 'server' / 'server.js')],
            env={**os.environ, 'PORT': str(args.port), 'HOST': '127.0.0.1',
                 'ENGINE_URL': f'http://127.0.0.1:{args.engine_port}'})
        if not wait_for(f'{url}/healthz', 30):
            sys.exit('The web server did not start; see the messages above.')
        print(f'Dashboard running at {url}')
        print('Stop the app with Ctrl+C in this window.')
        if args.no_browser or not webbrowser.open(url):
            print(f'Open this link in your browser: {url}')
        web.wait()
    except KeyboardInterrupt:
        print('\nDashboard stopped.')
    finally:
        for process in (web, engine):
            if process is not None and process.poll() is None:
                process.terminate()


if __name__ == '__main__':
    main()
