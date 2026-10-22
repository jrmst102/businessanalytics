"""Start the local dashboard: ``python launch.py``.

Works from any working directory, binds to this computer only, opens the
browser (or prints the URL), and gives readable messages for a missing
dependency or an occupied port.
"""
import argparse
import importlib.util
import socket
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

APP_PATH = Path(__file__).resolve().parent / 'app.py'
REQUIRED = ['streamlit', 'sklearn', 'pandas', 'numpy', 'matplotlib']


def missing_dependencies():
    return [name for name in REQUIRED if importlib.util.find_spec(name) is None]


def port_is_free(port, host='127.0.0.1'):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex((host, port)) != 0


def main():
    parser = argparse.ArgumentParser(description='Launch "Business Analytics in Action: From Model to App".')
    parser.add_argument('--port', type=int, default=8501, help='Local port (default 8501).')
    parser.add_argument('--no-browser', action='store_true', help='Print the URL instead of opening a browser.')
    args = parser.parse_args()

    if not APP_PATH.exists():
        sys.exit(f'app.py was not found next to launch.py (looked in {APP_PATH.parent}).')

    missing = missing_dependencies()
    if missing:
        sys.exit('Missing Python packages: ' + ', '.join(missing) + '.\n'
                 'Activate your virtual environment and run:\n'
                 f'    {sys.executable} -m pip install -r "{APP_PATH.parent / "requirements.txt"}"\n'
                 'Then start the app again with: python launch.py')

    if not port_is_free(args.port):
        sys.exit(f'Port {args.port} is already in use (another dashboard may still be running).\n'
                 f'Close it, or start this app on another port:  python launch.py --port {args.port + 1}')

    url = f'http://localhost:{args.port}'
    command = [sys.executable, '-m', 'streamlit', 'run', str(APP_PATH),
               '--server.address', '127.0.0.1', '--server.port', str(args.port),
               '--server.headless', 'true', '--browser.gatherUsageStats', 'false']
    print(f'Starting the dashboard at {url}')
    print('Stop the app with Ctrl+C in this window.')
    if not args.no_browser:
        def open_browser():
            if not webbrowser.open(url):
                print(f'Could not open a browser automatically. Open this link: {url}')
        threading.Timer(2.5, open_browser).start()
    else:
        print(f'Open this link in your browser: {url}')
    try:
        sys.exit(subprocess.call(command))
    except KeyboardInterrupt:
        print('\nDashboard stopped.')


if __name__ == '__main__':
    main()
