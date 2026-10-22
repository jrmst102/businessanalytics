#!/usr/bin/env bash
# Container entrypoint: run the Python engine API and the Node.js dashboard.
# If either process exits, the container exits so the platform restarts it.
set -e
python engine_api.py --port 8000 &
node server/server.js &
wait -n
exit 1
