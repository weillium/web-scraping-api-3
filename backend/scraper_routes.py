from flask import Blueprint, request, jsonify
from datetime import datetime
from db import get_db_connection
from bs4 import BeautifulSoup, Tag
import requests
import json
import logging
import re
from collections import OrderedDict

bp = Blueprint('scraper_routes', __name__)

@bp.route('/scrapers', methods=['GET'])
def get_scrapers():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM scrapers')
    scrapers = cursor.fetchall()
    conn.close()
    return jsonify([dict(scraper) for scraper in scrapers])

@bp.route('/scrapers', methods=['POST'])
def create_scraper():
    data = request.json
    scraper_name = data.get('scraper_name')
    scraping_url = data.get('scraping_url')

    if not scraper_name or not scraping_url:
        return jsonify({'error': 'scraper_name and scraping_url are required'}), 400

    created_on = datetime.utcnow()
    last_scraped_on = None

    conn = get_db_connection()
    cursor = conn.cursor()

    # Create new scraper_config record
    cursor.execute(
        'INSERT INTO scraper_config (trim_input, group_row_count, created_on, last_updated_on) VALUES (?, ?, ?, ?)',
        (None, None, created_on, None)
    )
    scraper_config_id = cursor.lastrowid

    # Create new scraper record with generated scraper_config_id
    cursor.execute(
        'INSERT INTO scrapers (scraper_name, scraping_url, scraper_config_id, created_on, last_scraped_on) VALUES (?, ?, ?, ?, ?)',
        (scraper_name, scraping_url, scraper_config_id, created_on, last_scraped_on)
    )
    conn.commit()
    scraper_id = cursor.lastrowid
    conn.close()

    return jsonify({'message': 'Scraper created', 'scraper_id': scraper_id, 'scraper_config_id': scraper_config_id}), 201

@bp.route('/scrapers', methods=['PUT'])
def update_scraper():
    data = request.json
    scraper_id = data.get('scraper_id')
    scraper_name = data.get('scraper_name')
    scraping_url = data.get('scraping_url')
    scraper_config_id = data.get('scraper_config_id')

    if not scraper_id:
        return jsonify({'error': 'scraper_id is required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM scrapers WHERE scraper_id = ?', (scraper_id,))
    existing_scraper = cursor.fetchone()
    if existing_scraper is None:
        conn.close()
        return jsonify({'error': 'Scraper not found'}), 404

    # Fallback to existing scraper_config_id if not provided
    if not scraper_config_id:
        scraper_config_id = existing_scraper['scraper_config_id']

    cursor.execute(
        'UPDATE scrapers SET scraper_name = ?, scraping_url = ?, scraper_config_id = ? WHERE scraper_id = ?',
        (scraper_name, scraping_url, scraper_config_id, scraper_id)
    )
    conn.commit()
    conn.close()

    return jsonify({'message': 'Scraper updated'})

@bp.route('/scrapers', methods=['DELETE'])
def delete_scraper():
    data = request.json
    scraper_id = data.get('scraper_id')

    if not scraper_id:
        return jsonify({'error': 'scraper_id is required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM scrapers WHERE scraper_id = ?', (scraper_id,))
    if cursor.fetchone() is None:
        conn.close()
        return jsonify({'error': 'Scraper not found'}), 404

    cursor.execute('DELETE FROM scrapers WHERE scraper_id = ?', (scraper_id,))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Scraper deleted'})

@bp.route('/scrapers/<int:scraper_id>', methods=['GET'])
def get_scraper(scraper_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM scrapers WHERE scraper_id = ?', (scraper_id,))
    scraper = cursor.fetchone()
    conn.close()

    if scraper is None:
        return jsonify({'error': 'Scraper not found'}), 404

    return jsonify(dict(scraper))

@bp.route('/scrape/<int:scraper_id>', methods=['GET'])
def scrape(scraper_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get scraper by id
    cursor.execute('SELECT * FROM scrapers WHERE scraper_id = ?', (scraper_id,))
    scraper = cursor.fetchone()
    if scraper is None:
        conn.close()
        return jsonify({'error': 'Scraper not found'}), 404

    scraper_config_id = scraper['scraper_config_id']

    # Get scraper config
    cursor.execute('SELECT * FROM scraper_config WHERE scraper_config_id = ?', (scraper_config_id,))
    config = cursor.fetchone()
    if config is None:
        conn.close()
        return jsonify({'error': 'Scraper config not found'}), 404

    trim_tag = config['trim_input']
    group_row_count = config['group_row_count']

    # Get scraper URL
    scraping_url = scraper['scraping_url']

    # Get row labels
    cursor.execute('SELECT row_label FROM scraper_config_row_labels WHERE scraper_config_id = ? ORDER BY row_order', (scraper_config_id,))
    row_labels = [row['row_label'] for row in cursor.fetchall()]

    # Get tags
    cursor.execute('SELECT tag FROM scraper_config_tags WHERE scraper_config_id = ?', (scraper_config_id,))
    tags = [row['tag'] for row in cursor.fetchall()]

    conn.close()

    # Strip angle brackets from tags
    tags = [tag.strip('<>') for tag in tags]

    debug_info = {
        'trim_tag': trim_tag,
        'group_row_count': group_row_count,
        'row_labels': row_labels,
        'tags': tags
    }

    try:
        response = requests.get(scraping_url)
        response.raise_for_status()
    except Exception as e:
        return jsonify({'error': f'Failed to fetch URL: {str(e)}'}), 500

    soup = BeautifulSoup(response.text, 'html.parser')

    if trim_tag:
        def parse_trim_input(trim_input):
            tag_match = re.match(r'<(\w+)([^>]*)>', trim_input)
            if not tag_match:
                return None, {}
            tag_name = tag_match.group(1)
            attr_string = tag_match.group(2).strip()
            attrs = {}
            if attr_string:
                class_match = re.search(r'class=["\']([^"\']+)["\']', attr_string)
                if class_match:
                    attrs['class'] = class_match.group(1).split()
            return tag_name, attrs

        tag_name, attrs = parse_trim_input(trim_tag)
        if tag_name:
            trimmed_soup = soup.find(tag_name, attrs=attrs)
            if trimmed_soup:
                soup = trimmed_soup
            else:
                return jsonify({'error': 'Trim tag not found in page'}), 404

    def extract_text_sequentially(parent, tag_names):
        result = []
        for child in parent.descendants:
            if child.name in tag_names and isinstance(child, Tag):
                text = child.get_text(strip=True)
                if text:
                    result.append(text)
        return result

    logging.info(f'Extracting text using tags: {tags}')
    cells = extract_text_sequentially(soup, tags)
    logging.info(f'Extracted cells: {cells}')

    if not group_row_count or group_row_count <= 0:
        group_row_count = len(row_labels) if row_labels else len(cells)
    if group_row_count == 0:
        group_row_count = 1

    if row_labels:
        effective_row_labels = row_labels
    else:
        # Generate keys from last tag name in each tag path
        effective_row_labels = []
        for tag_path in tags:
            tag_names = tag_path.strip('<>').split('><')
            effective_row_labels.append(tag_names[-1] if tag_names else tag_path)

    grouped_data = []
    for i in range(0, len(cells), group_row_count):
        group = cells[i:i+group_row_count]
        # Include last group even if smaller than group_row_count
        if len(group) == 0:
            break
        item = {effective_row_labels[j]: group[j] for j in range(min(len(effective_row_labels), len(group)))}
        grouped_data.append(item)

    logging.info(f'Grouped data: {grouped_data}')

    return jsonify({'data': grouped_data, 'debug_info': debug_info})


@bp.route('/raw/<int:scraper_id>', methods=['GET'])
def raw_scrape(scraper_id):
    output_format = request.args.get('output_format')
    if output_format not in ['html', 'json']:
        return jsonify({'error': 'Invalid or missing output_format parameter'}), 400

    trim_tag = request.args.get('trim_tag')
    group_row_count = request.args.get('group_row_count', type=int)

    # Accept tags and row_labels as optional array parameters
    tags = request.args.getlist('tags') + request.args.getlist('tags[]')  # list of strings
    row_labels = request.args.getlist('row_labels') + request.args.getlist('row_labels[]')  # list of strings

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get scraper by id
    cursor.execute('SELECT * FROM scrapers WHERE scraper_id = ?', (scraper_id,))
    scraper = cursor.fetchone()
    if scraper is None:
        conn.close()
        logging.error(f'Scraper with id {scraper_id} not found')
        return jsonify({'error': 'Scraper not found'}), 404

    scraping_url = scraper['scraping_url']
    conn.close()

    try:
        response = requests.get(scraping_url)
        response.raise_for_status()
    except Exception as e:
        logging.error(f'Failed to fetch URL {scraping_url}: {str(e)}')
        return jsonify({'error': f'Failed to fetch URL: {str(e)}'}), 500

    soup = BeautifulSoup(response.text, 'html.parser')

    if trim_tag:
        def parse_trim_input(trim_input):
            tag_match = re.match(r'<(\w+)([^>]*)>', trim_input)
            if not tag_match:
                return None, {}
            tag_name = tag_match.group(1)
            attr_string = tag_match.group(2).strip()
            attrs = {}
            if attr_string:
                class_match = re.search(r'class=["\']([^"\']+)["\']', attr_string)
                if class_match:
                    attrs['class'] = class_match.group(1).split()
            return tag_name, attrs

        tag_name, attrs = parse_trim_input(trim_tag)
        if tag_name:
            trimmed_soup = soup.find(tag_name, attrs=attrs)
            if trimmed_soup:
                soup = trimmed_soup
                logging.info(f'Trimmed soup HTML: {str(soup)[:500]}')
            else:
                logging.error(f'Trim tag {trim_tag} not found in page')
                return jsonify({'error': 'Trim tag not found in page'}), 404

    if output_format == 'html':
        return soup.prettify(), 200, {'Content-Type': 'text/html; charset=utf-8'}

    # Helper function to traverse nested tags and find all matching elements
    def traverse_nested_tags_all(soup_obj, nested_tag_path):
        tags = nested_tag_path.strip('<>').split('><')
        logging.info(f'Traversing nested tags: {tags}')

        # If first tag matches soup_obj tag, skip it
        if tags and soup_obj.name == tags[0]:
            tags = tags[1:]

        current_elements = [soup_obj]
        for tag in tags:
            next_elements = []
            for elem in current_elements:
                found = elem.find_all(tag) if elem else []
                logging.info(f'Found {len(found)} elements for tag "{tag}"')
                next_elements.extend(found)
            current_elements = next_elements
            if not current_elements:
                logging.info(f'No elements found for tag "{tag}", stopping traversal')
                break
        return current_elements

    # Extract text sequentially from nested tag paths, collecting all matching elements
    def extract_text_sequentially_nested(parent, nested_tag_paths):
        result = []
        for nested_path in nested_tag_paths:
            elements = traverse_nested_tags_all(parent, nested_path)
            for element in elements:
                text = element.get_text(strip=True)
                if text:
                    result.append(text)
        return result

    # Strip angle brackets from tags
    tags = [tag.strip() for tag in tags]

    logging.info(f'Raw endpoint called with tags: {tags}')
    logging.info(f'Raw endpoint called with row_labels: {row_labels}')
    logging.info(f'Raw endpoint called with group_row_count: {group_row_count}')

    cells = extract_text_sequentially_nested(soup, tags)

    logging.info(f'Extracted cells: {cells}')

    if not group_row_count or group_row_count <= 0:
        group_row_count = len(row_labels) if row_labels else len(cells)
    if group_row_count == 0:
        group_row_count = 1

    effective_row_labels = row_labels if row_labels else tags

    grouped_data = []
    for i in range(0, len(cells), group_row_count):
        group = cells[i:i+group_row_count]
        if len(group) < group_row_count:
            break
        item = {effective_row_labels[j]: group[j] for j in range(min(len(effective_row_labels), len(group)))}
        grouped_data.append(item)

    logging.info(f'Grouped data: {grouped_data}')

    return jsonify({'data': grouped_data})


@bp.route('/raw/<int:scraper_id>/tags', methods=['GET'])
def raw_list_tags(scraper_id):
    trim_tag = request.args.get('trim_tag')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch the scraping URL for the scraper
    cursor.execute('SELECT scraping_url FROM scrapers WHERE scraper_id = ?', (scraper_id,))
    scraper = cursor.fetchone()
    if scraper is None:
        conn.close()
        return jsonify({'error': 'Scraper not found'}), 404

    scraping_url = scraper['scraping_url']

    try:
        response = requests.get(scraping_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        if trim_tag:
            def parse_trim_input(trim_input):
                tag_match = re.match(r'<(\w+)([^>]*)>', trim_input)
                if not tag_match:
                    return None, {}
                tag_name = tag_match.group(1)
                attr_string = tag_match.group(2).strip()
                attrs = {}
                if attr_string:
                    class_match = re.search(r'class=["\']([^"\']+)["\']', attr_string)
                    if class_match:
                        attrs['class'] = class_match.group(1).split()
                return tag_name, attrs

            tag_name, attrs = parse_trim_input(trim_tag)
            if tag_name:
                trimmed_soup = soup.find(tag_name, attrs=attrs)
                if trimmed_soup:
                    soup = trimmed_soup
                else:
                    return jsonify({'error': 'Trim tag not found in page'}), 404

        # Extract tags and descendent tags with counts and example output
        tag_info = {}

        def add_tag_info(tag_path, element):
            if tag_path not in tag_info:
                tag_info[tag_path] = {
                    'tag': tag_path,
                    'count': 0,
                    'example_output': ''
                }
            tag_info[tag_path]['count'] += 1
            if not tag_info[tag_path]['example_output']:
                tag_info[tag_path]['example_output'] = element.get_text(strip=True)

        def traverse(element, path=''):
            if not hasattr(element, 'name') or element.name is None:
                return
            current_path = f"{path}<{element.name}>"
            add_tag_info(current_path, element)
            for child in element.children:
                traverse(child, current_path)

        traverse(soup)

        tags_list = list(tag_info.values())

    except Exception as e:
        conn.close()
        return jsonify({'error': f'Failed to fetch URL: {str(e)}'}), 500

    conn.close()

    return jsonify({'tags': tags_list})
