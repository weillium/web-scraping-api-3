import os
import logging

logging.basicConfig(level=logging.INFO)

from flask import Flask
from flask_cors import CORS
from db import close_connection
from routes import register_routes

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000", "http://10.0.0.164:3000"]}})

register_routes(app)

app.teardown_appcontext(close_connection)

@app.route('/health')
def health_check():
    return 'OK', 200

# For Gunicorn, ensure it binds to the port from environment variable
port = int(os.environ.get('PORT', 8000))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
