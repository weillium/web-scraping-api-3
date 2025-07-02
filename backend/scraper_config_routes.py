from flask import Blueprint, request, jsonify
from datetime import datetime
from db import get_db_connection
from bs4 import BeautifulSoup, Tag
import requests
import re
from collections import OrderedDict

bp = Blueprint('scraper_config_routes', __name__)

# --- Scraper Config Routes ---

@bp.route('/scraper-config', methods=['GET'])
def list_scraper_configs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM scraper_config')
    configs = cursor.fetchall()
    conn.close()
    return jsonify([dict(config) for config in configs])

@bp.route('/scraper-config/<int:scraper_config_id>', methods=['GET'])
def get_scraper_config(scraper_config_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM scraper_config WHERE scraper_config_id = ?', (scraper_config_id,))
    config = cursor.fetchone()
    conn.close()
    if config is None:
        return jsonify({'error': 'Scraper config not found'}), 404
    return jsonify(dict(config))

@bp.route('/scraper-config', methods=['POST'])
def create_scraper_config():
    data = request.json
    trim_input = data.get('trim_input')
    group_row_count = data.get('group_row_count')
    created_on = datetime.utcnow()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO scraper_config (trim_input, group_row_count, created_on, last_updated_on) VALUES (?, ?, ?, ?)',
        (trim_input, group_row_count, created_on, None)
    )
    conn.commit()
    scraper_config_id = cursor.lastrowid
    conn.close()
    return jsonify({'message': 'Scraper config created', 'scraper_config_id': scraper_config_id}), 201

@bp.route('/scraper-config/<int:scraper_config_id>', methods=['PUT'])
def update_scraper_config(scraper_config_id):
    data = request.json
    trim_input = data.get('trim_input')
    group_row_count = data.get('group_row_count')
    last_updated_on = datetime.utcnow()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM scraper_config WHERE scraper_config_id = ?', (scraper_config_id,))
    if cursor.fetchone() is None:
        conn.close()
        return jsonify({'error': 'Scraper config not found'}), 404

    cursor.execute(
        'UPDATE scraper_config SET trim_input = ?, group_row_count = ?, last_updated_on = ? WHERE scraper_config_id = ?',
        (trim_input, group_row_count, last_updated_on, scraper_config_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Scraper config updated'})

@bp.route('/scraper-config/<int:scraper_config_id>', methods=['DELETE'])
def delete_scraper_config(scraper_config_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM scraper_config WHERE scraper_config_id = ?', (scraper_config_id,))
    if cursor.fetchone() is None:
        conn.close()
        return jsonify({'error': 'Scraper config not found'}), 404

    cursor.execute('DELETE FROM scraper_config WHERE scraper_config_id = ?', (scraper_config_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Scraper config deleted'})

# --- Scraper Config Row Labels Routes ---

@bp.route('/scraper-config/<int:scraper_config_id>/row-labels', methods=['GET'])
def list_row_labels(scraper_config_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM scraper_config_row_labels WHERE scraper_config_id = ?', (scraper_config_id,))
    row_labels = cursor.fetchall()
    conn.close()
    return jsonify([dict(row_label) for row_label in row_labels])

@bp.route('/scraper-config/row-labels/<int:row_label_id>', methods=['GET'])
def get_row_label(row_label_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM scraper_config_row_labels WHERE scraper_config_row_label_id = ?', (row_label_id,))
    row_label = cursor.fetchone()
    conn.close()
    if row_label is None:
        return jsonify({'error': 'Row label not found'}), 404
    return jsonify(dict(row_label))

@bp.route('/scraper-config/<int:scraper_config_id>/row-labels', methods=['POST'])
def create_row_label(scraper_config_id):
    data = request.json
    row_orders = data.get('row_order')
    row_labels = data.get('row_label')
    created_on = datetime.utcnow()
    last_updated_on = created_on

    if not row_orders or not row_labels:
        return jsonify({'error': 'row_order and row_label are required'}), 400

    if not isinstance(row_orders, list):
        row_orders = [row_orders]
    if not isinstance(row_labels, list):
        row_labels = [row_labels]

    if len(row_orders) != len(row_labels):
        return jsonify({'error': 'row_order and row_label must have the same length'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    for row_order, row_label in zip(row_orders, row_labels):
        cursor.execute(
            'INSERT INTO scraper_config_row_labels (scraper_config_id, row_order, row_label, created_on, last_updated_on) VALUES (?, ?, ?, ?, ?)',
            (scraper_config_id, row_order, row_label, created_on, last_updated_on)
        )

    conn.commit()
    conn.close()
    return jsonify({'message': 'Row labels created'}), 201

@bp.route('/scraper-config/row-labels/<int:row_label_id>', methods=['PUT'])
def update_row_label(row_label_id):
    data = request.json
    row_order = data.get('row_order')
    row_label = data.get('row_label')
    last_updated_on = datetime.utcnow()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM scraper_config_row_labels WHERE scraper_config_row_label_id = ?', (row_label_id,))
    if cursor.fetchone() is None:
        conn.close()
        return jsonify({'error': 'Row label not found'}), 404

    cursor.execute(
        'UPDATE scraper_config_row_labels SET row_order = ?, row_label = ?, last_updated_on = ? WHERE scraper_config_row_label_id = ?',
        (row_order, row_label, last_updated_on, row_label_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Row label updated'})

@bp.route('/scraper-config/row-labels/<int:row_label_id>', methods=['DELETE'])
def delete_row_label(row_label_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM scraper_config_row_labels WHERE scraper_config_row_label_id = ?', (row_label_id,))
    if cursor.fetchone() is None:
        conn.close()
        return jsonify({'error': 'Row label not found'}), 404

    cursor.execute('DELETE FROM scraper_config_row_labels WHERE scraper_config_row_label_id = ?', (row_label_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Row label deleted'})

@bp.route('/scraper-config/<int:scraper_config_id>/tags', methods=['DELETE'])
def delete_all_tags(scraper_config_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM scraper_config_tags WHERE scraper_config_id = ?', (scraper_config_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'All tags deleted'})

@bp.route('/scraper-config/<int:scraper_config_id>/row-labels', methods=['DELETE'])
def delete_all_row_labels(scraper_config_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM scraper_config_row_labels WHERE scraper_config_id = ?', (scraper_config_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'All row labels deleted'})

# --- Scraper Config Tags Routes ---

@bp.route('/scraper-config/<int:scraper_config_id>/tags', methods=['GET'])
def list_tags(scraper_config_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch tags for the scraper config
    cursor.execute('SELECT * FROM scraper_config_tags WHERE scraper_config_id = ?', (scraper_config_id,))
    tags = cursor.fetchall()

    conn.close()

    return jsonify([dict(tag) for tag in tags])

@bp.route('/scraper-config/tags/<int:tag_id>', methods=['GET'])
def get_tag(tag_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM scraper_config_tags WHERE scraper_config_tag_id = ?', (tag_id,))
    tag = cursor.fetchone()
    conn.close()
    if tag is None:
        return jsonify({'error': 'tag not found'}), 404
    return jsonify(dict(tag))

@bp.route('/scraper-config/<int:scraper_config_id>/tags', methods=['POST'])
def create_tag(scraper_config_id):
    data = request.json
    tags = data.get('tag')
    created_on = datetime.utcnow()
    last_updated_on = created_on

    if not tags:
        return jsonify({'error': 'tag is required'}), 400

    if not isinstance(tags, list):
        tags = [tags]

    conn = get_db_connection()
    cursor = conn.cursor()

    for tag in tags:
        cursor.execute(
            'INSERT INTO scraper_config_tags (scraper_config_id, tag, created_on, last_updated_on) VALUES (?, ?, ?, ?)',
            (scraper_config_id, tag, created_on, last_updated_on)
        )

    conn.commit()
    conn.close()
    return jsonify({'message': 'tags created'}), 201

@bp.route('/scraper-config/tags/<int:tag_id>', methods=['PUT'])
def update_tag(tag_id):
    data = request.json
    tag = data.get('tag')
    last_updated_on = datetime.utcnow()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM scraper_config_tags WHERE scraper_config_tag_id = ?', (tag_id,))
    if cursor.fetchone() is None:
        conn.close()
        return jsonify({'error': 'tag not found'}), 404

    cursor.execute(
        'UPDATE scraper_config_tags SET tag = ?, last_updated_on = ? WHERE scraper_config_tag_id = ?',
        (tag, last_updated_on, tag_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Tag updated'})

@bp.route('/scraper-config/tags/<int:tag_id>', methods=['DELETE'])
def delete_tag(tag_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM scraper_config_tags WHERE scraper_config_tag_id = ?', (tag_id,))
    if cursor.fetchone() is None:
        conn.close()
        return jsonify({'error': 'tag not found'}), 404

    cursor.execute('DELETE FROM scraper_config_tags WHERE scraper_config_tag_id = ?', (tag_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'tag deleted'})
