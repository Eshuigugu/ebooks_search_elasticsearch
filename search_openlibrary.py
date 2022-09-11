import time
import requests


OL_API_URL = 'https://openlibrary.org/search.json'
OL_BASE_URL = 'https://openlibrary.org'


def search_openlibrary(query):
    request_params = {
        'q': query,
        'has_fulltext': True,
        'mode': 'ebooks',
        'limit': 100
    }

    time.sleep(1)
    try:
        r = sess.get(OL_API_URL, params=request_params, timeout=60)
    except requests.ConnectionError:
        # fail silently
        return []
    rows = r.json()['docs']
    rows = [x for x in rows if x["ebook_access"] == "borrowable"]

    # try fetching the cover images to ensure the calibre libraries are online
    for x in rows:
        x['url'] = OL_BASE_URL + x['key']
        if 'subtitle' in x:
            x['title'] = x['title'] + ': ' + x['subtitle']
        x['authors'] = x['author_name'] if 'author_name' in x else (x['publisher'] if 'publisher' in x else [])
        x['source_name'] = 'openlibrary'
    return rows


sess = requests.Session()
