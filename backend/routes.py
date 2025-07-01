from flask import Blueprint, request, jsonify
from bs4 import BeautifulSoup
import requests
from datetime import datetime
from backend.db import get_db_connection

bp = Blueprint('routes', __name__)

from backend.scraper_routes import bp as scraper_bp
from backend.scraper_config_routes import bp as scraper_config_bp


def register_routes(app):
    app.register_blueprint(scraper_bp)
    app.register_blueprint(scraper_config_bp)
