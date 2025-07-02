import os
import json
import boto3
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import g

# Use environment variables for RDS connection
RDS_HOST = os.environ.get('RDS_HOST')
RDS_PORT = os.environ.get('RDS_PORT', 5432)
RDS_DBNAME = os.environ.get('RDS_DBNAME')
RDS_USER = os.environ.get('RDS_USER')
RDS_SECRET_ARN = os.environ.get('RDS_SECRET_ARN')


# Function to get secret from AWS Secrets Manager

def get_secret():
    if not RDS_SECRET_ARN:
        return None
    client = boto3.client('secretsmanager', region_name='us-west-1')
    response = client.get_secret_value(SecretId=RDS_SECRET_ARN)
    secret_string = response.get('SecretString')
    if secret_string:
        secret = json.loads(secret_string)
        return secret.get('password')
    return None


# Get password from Secrets Manager
RDS_PASSWORD = get_secret()


def get_db_connection():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = psycopg2.connect(
            host=RDS_HOST,
            port=RDS_PORT,
            dbname=RDS_DBNAME,
            user=RDS_USER,
            password=RDS_PASSWORD,
            cursor_factory=RealDictCursor
        )
    return db


def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Drop existing tables
    cursor.execute('DROP TABLE IF EXISTS scrapers')
    cursor.execute('DROP TABLE IF EXISTS scraper_config')
    cursor.execute('DROP TABLE IF EXISTS scraper_config_row_labels')
    cursor.execute('DROP TABLE IF EXISTS scraper_config_tags')

    # Recreate tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scrapers (
            scraper_id SERIAL PRIMARY KEY,
            scraper_name TEXT NOT NULL,
            scraping_url TEXT NOT NULL,
            scraper_config_id INTEGER NOT NULL,
            created_on TIMESTAMP NOT NULL,
            last_scraped_on TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scraper_config (
            scraper_config_id SERIAL PRIMARY KEY,
            config_name TEXT NOT NULL,
            created_on TIMESTAMP NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scraper_config_row_labels (
            row_label_id SERIAL PRIMARY KEY,
            scraper_config_id INTEGER NOT NULL,
            label TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scraper_config_tags (
            tag_id SERIAL PRIMARY KEY,
            scraper_config_id INTEGER NOT NULL,
            tag TEXT NOT NULL
        )
    ''')

    conn.commit()
