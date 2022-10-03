import json
import re
import requests
import os
from time import sleep
from query_functions import get_work_id
cols = ['title', 'authors', 'work_id', 'url', 'source_name']

HOST_CONN = 'http://HOST:PORT'

sess = requests.Session()


def insert_document(doc):
    uid = re.sub('[^\w_\-]', '', doc['url'])
    r = sess.put(HOST_CONN + f'/ebooks/_doc/{uid}?pretty', data=json.dumps(doc),
                 headers={'Content-Type': 'application/json'})
    sleep(0.0001)
    if r.status_code > 300:
        sleep(20)
    return r


def insert_many(rows):
    data_str = []
    for row in rows:
        uid = re.sub('[^\w_\-]', '', row['url'])
        data_str += [json.dumps({"index": {"_id": uid}}) + '\n']
        data_str += [json.dumps(row) + '\n']
    data_str = ''.join(data_str)

    r = sess.post(HOST_CONN + f'/ebooks/_doc/_bulk?pretty', data=data_str,
                  headers={'Content-Type': 'application/json'})
    if r.status_code > 300:
        sleep(20)
    return r


def doc_exists(doc_url):
    uid = re.sub('[^\w_\-]', '', doc_url)
    return sess.get(HOST_CONN + f'/ebooks/_doc/{uid}').json()['found']


def valid_isbn(isbn):
    chars = '0123456789X'
    isbn_sum = 0
    isbn = [x for x in isbn if x in chars]
    if len(isbn) not in [10, 13]:
        return False
    for x in range(1, len(isbn) + 1):
        isbn_sum += chars.index(isbn[-x]) * x
    return not isbn_sum % 11


# querying goodreads so we can search by work_id doesn't help since we're searching and filtering by title
def json_file_to_elasticsearch(filename, query_goodreads=False, num_to_skip=0):
    with open(filename, 'r') as f:
        i = 0
        rows = []
        for line in f.readlines():
            i += 1
            if i < num_to_skip:continue  # skip some
            row = json.loads(line)
            row['title'] = str(row['title'])
            row['source_name'] = filename[:-5]
            if 'authors' not in row:continue
            if query_goodreads:
                work_ids = set()
                identifiers = []
                if 'ASIN' in row and row['ASIN']:
                    asins = re.findall('\w{10}', row['ASIN'])
                    identifiers += asins
                if 'ISBN' in row and row['ISBN']:
                    isbns = re.findall('(?:[\dxX]-?)+', row['ISBN'])
                    isbns = [re.sub('[^0123456789X]', '', isbn) for isbn in isbns if valid_isbn(isbn)]
                    identifiers += isbns
                for identifier in identifiers:
                    work_ids |= get_work_id(identifier)
                row['work_id'] = list(work_ids)
            row = {k: row[k] for k in set(row.keys()).intersection(cols)}
            if i % 10_000 == 0:
                r = insert_many(rows)
                print(i, row, r, r.text[:200])
                rows = []
            rows.append(row)
    insert_many(rows)


if __name__ == '__main__':
    json_file_to_elasticsearch('myanonamouse.json')
    import overdrive_html_to_json_dump
    for filename in overdrive_html_to_json_dump.filenames:
        json_file_to_elasticsearch(filename)
    json_file_to_elasticsearch('libgen_fiction.json')
    json_file_to_elasticsearch('libgen_nonfiction.json')
    json_file_to_elasticsearch('ebookhunter.json')
    json_file_to_elasticsearch('trantor.json')
    json_file_to_elasticsearch('zlib.json')

