import json
import re
import requests
import os
from time import sleep

cols = ['title', 'authors', 'work_id', 'url', 'source_name']

host_conn = 'http://ip:port'

sess = requests.Session()


def insert_document(doc):
    uid = re.sub('[^\w_\-]', '', doc['url'])
    r = sess.put(host_conn + f'/ebooks/_doc/{uid}?pretty', data=json.dumps(doc),
                 headers={'Content-Type': 'application/json'})
    sleep(0.0001)
    if r.status_code > 300:
        sleep(20)
    return r


def reduce_author_str(author):
    return ' '.join([x for x in author.split(' ') if len(x) > 1])


def get_work_id(query_str, goodreads_url=f'https://www.goodreads.com/book/auto_complete'):
    sleep(0.2)
    r = sess.get(goodreads_url, params={'format': 'json', 'q': query_str}, timeout=10)
    if r.status_code == 200:
        return {x['workId'] for x in r.json()}


def valid_isbn(isbn):
    chars = '0123456789X'
    isbn_sum = 0
    isbn = [x for x in isbn if x in chars]
    if len(isbn) not in [10, 13]:
        return False
    for x in range(1, len(isbn) + 1):
        isbn_sum += chars.index(isbn[-x]) * x
    return not isbn_sum % 11


def reduce_title(title):
    return re.sub(' *(?:[\-:].*|\(.*\))* *$', '', str(title))


def json_file_to_elasticsearch(filename):
    with open(filename, 'r') as f:
        i = 0
        for line in f.readlines():
            # line = f.readline()
            row = json.loads(line)
            row['source_name'] = filename[:-5]
            title = row['title']
            authors = row['authors'] if 'authors' in row else ''
            work_ids = set()
            for author in authors:
                query_str = f'{reduce_title(title)} {reduce_author_str(author)}'
                work_ids |= get_work_id(query_str)
                if work_ids:break
            if 'ASIN' in row and row['ASIN']:
                asins = re.findall('\w{10}', row['ASIN'])
                for asin in asins:
                    work_ids |= get_work_id(asin)
            if 'ISBN' in row and row['ISBN']:
                isbns = re.findall('(?:[\dxX]-?)+', row['ISBN'])
                for isbn in isbns:
                    if valid_isbn(isbn):
                        work_ids |= get_work_id(isbn)
            row['work_id'] = ' '.join(work_ids)
            row = {k: row[k] for k in set(row.keys()).intersection(cols)}
            r = insert_document(row)
            i += 1
            if i % 100 == 0:
                print(row, r, r.json())


if __name__ == '__main__':
    json_file_to_elasticsearch('myanonamouse.json')
    import overdrive_html_to_json_dump
    for filename in overdrive_html_to_json_dump.filenames:
        json_file_to_elasticsearch(filename)
    json_file_to_elasticsearch('libgen_fiction.json')
    json_file_to_elasticsearch('libgen_nonfiction.json')
    json_file_to_elasticsearch('ebookhunter.json')
    json_file_to_elasticsearch('trantor.json')

