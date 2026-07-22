# /cmms-backend/run.py
import os
from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    # Default False (aman untuk production kalau lupa di-set). Dev lokal: set
    # FLASK_DEBUG=true di .env untuk dapat auto-reload + debugger.
    debug = os.environ.get('FLASK_DEBUG', 'false').strip().lower() in ('1', 'true', 'yes')
    socketio.run(app, debug=debug, port=5000)