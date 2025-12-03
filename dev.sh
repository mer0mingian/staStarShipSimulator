#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
export FLASK_APP=sta.web.app:create_app
export FLASK_DEBUG=1
flask run --host=0.0.0.0 --port=5001
