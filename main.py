import time
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
import json
from bs4 import BeautifulSoup
import os
import pickle
import re
from query_functions import reduce_title, reduce_author_str, query_elasticsearch, titles_similar, get_work_id
import jellyfish
from search_calishot import search_calishot
from appdirs import user_data_dir

# this script does create some files under this directory
appname = "MAM_search_elasticsearch"
appauthor = "Eshuigugu"
data_dir = user_data_dir(appname, appauthor)


if not os.path.isdir(data_dir):
    os.makedirs(data_dir)
sess_filepath = os.path.join(data_dir, 'session.pkl')


def indented_print(*argv, indent=0):
    print(' ' * indent + ' '.join(argv))


def search_mam(title_author):
    query = f'@(title,author) "{title_author}"/0.75'
    query = re.sub('[/\\\\~\-]', ' ', query)
    start_num = 0
    json_dict = {
        "tor": {
            "main_cat": ["14", "15"],  # limit query to ebooks and music
            "startNumber": str(start_num),
            "text": query,
        },
    }
    # don't need go out of the way for authentication if
    # get_mam_requests() was called before this function because session (AKA sess) has the appropriate cookies
    try:
        response = sess.post('https://www.myanonamouse.net/tor/js/loadSearchJSONbasic.php', json=json_dict, timeout=20)
    except:
        time.sleep(10)
        response = sess.post('https://www.myanonamouse.net/tor/js/loadSearchJSONbasic.php', json=json_dict, timeout=20)
    resp_dict = response.json()
    if 'data' not in resp_dict:
        return []
    for row in resp_dict['data']:
        try:
            row['authors'] = list(json.loads(row['author_info']).values()) if row['author_info'] else ''
        except:
            row['authors'] = ''
        row['url'] = f"https://www.myanonamouse.net/t/{row['id']}"
        row['source_name'] = 'myanonamouse'
        row['title'] = str(row['title'])
    return resp_dict['data']


def get_mam_requests(limit=5000):
    keepGoing = True
    start_idx = 0
    req_books = []

    # fetch list of requests to search for
    while keepGoing:
        time.sleep(1)
        url = 'https://www.myanonamouse.net/tor/json/loadRequests.php'
        headers = {}
        # fill in mam_id for first run
        # headers['cookie'] = 'mam_id='

        params = {
            'tor[text]': '',
            'tor[srchIn][title]': 'true',
            'tor[viewType]': 'unful',
            'tor[cat][]': 'm14',  # search ebooks category
            'tor[startDate]': '',
            'tor[endDate]': '',
            'tor[startNumber]': f'{start_idx}',
            'tor[sortType]': 'dateD'
        }
        data = MultipartEncoder(fields=params)
        sess.headers['Content-type'] = data.content_type
        # headers['Content-type'] = data.content_type
        r = sess.post(url, data=data)
        req_books += r.json()['data']
        total_items = r.json()['found']
        start_idx += 100
        keepGoing = min(total_items, limit) > start_idx and not \
            {x['id'] for x in req_books}.intersection(blacklist)

    # saving the session lets you reuse the cookies returned by MAM which means you won't have to manually update the mam_id value as often
    with open(sess_filepath, 'wb') as f:
        pickle.dump(sess, f)

    with open(mam_blacklist_filepath, 'a') as f:
        for book in req_books:
            f.write(str(book['id']) + '\n')
            book['url'] = 'https://www.myanonamouse.net/tor/viewRequest.php/' + \
                          str(book['id'])[:-5] + '.' + str(book['id'])[-5:]
            book['title'] = BeautifulSoup(book["title"], features="lxml").text
            book['authors'] = [author for k, author in json.loads(book['authors']).items()]
    return req_books


def reduce_author_str(author):
    return ' '.join([x for x in author.split(' ') if len(x) > 1])


def split_str_to_set(authors):
    return {x.lower() for x in re.split('[ .,&\\\\;]', (' '.join(authors) if type(authors) == list else authors)) if len(x) > 1}


def search_elasticsearch(title, authors):
    query_str = f'{reduce_title(title)} {reduce_author_str(authors[0])}'
    hits = query_elasticsearch(title=title, authors=' '.join(authors))
    hits += search_calishot(query_str)
    if hits:
        # filter results
        hits = [x for x in hits if 'authors' in x]
        for x in hits:
            if type(x['title']) != str:
                x['title'] = str(x['title'])
        hits = [result for result in hits if titles_similar(title, result['title']) and
                split_str_to_set(authors) & split_str_to_set(result['authors'])]
    # if there's no hits try a lax search by work ID
    if not hits:
        # search by work id
        work_ids = get_work_id(query_str)
        hits = query_elasticsearch(work_id=' '.join(work_ids))
        # filter results
        hits = [result for result in hits if
                len(split_str_to_set(title) & split_str_to_set(result['title'])) >=
                min(len(split_str_to_set(title)), len(split_str_to_set(result['title']))) * 0.75]
        if not hits:
            return []
        print(f'got hits from work id')
    if hits:
        # check MAM API to alert user for possible dupes
        mam_hits = search_mam(query_str)
        hits += [result for result in mam_hits if titles_similar(title, result['title']) and
                 split_str_to_set(authors) & split_str_to_set(result['authors'])]
    # ensure each result is unique
    hits = list({x['url']: x for x in hits}.values())
    # sort results from most > least similar
    hits.sort(key=lambda x: jellyfish.damerau_levenshtein_distance(title, x['title']))
    return hits


def main():
    req_books = get_mam_requests()
    print(f'got {len(req_books)} from MAM requests api')
    req_books_reduced = [x for x in req_books if
                         x['cat_name'].startswith('Ebooks')
                         and x['filled'] == 0
                         and x['torsatch'] == 0
                         and x['id'] not in blacklist]
    start_time = time.time()
    for book in req_books_reduced:
        title = book['title']
        authors = book['authors']
        search_results = search_elasticsearch(title, authors)
        result_sources = [x['source_name'] for x in search_results]
        all_hits_sources.append(result_sources)
        if search_results:
            indented_print(str(book['title'])[:200])
            indented_print(book['url'], indent=1)
            if 'myanonamouse' in result_sources:
                # seperate into MAM and non MAM results
                mam_results = [x for x in search_results if 'myanonamouse' == x['source_name']]
                search_results = [x for x in search_results if 'myanonamouse' != x['source_name']]
                indented_print(f'book is on MAM', indent=1)
                indented_print(mam_results[0]['title'], indent=2)
                indented_print(mam_results[0]['url'], indent=3)
            # only show max of 5 results
            if search_results:
                indented_print(f'got {len(search_results)} hits', indent=1)
                if len(search_results) > 5:
                    indented_print(f'showing first 5 results', indent=2)
            for result in search_results[:5]:
                # print title up to 100 chars, and book url
                indented_print(result['title'][:200], indent=2)
                indented_print(result['url'], indent=3)
            print()
    end_time = time.time()
    print(f'done. took {round(end_time-start_time, 1)} seconds to find {len(all_hits_sources) - all_hits_sources.count([])} of {len(req_books_reduced)} books')


mam_blacklist_filepath = os.path.join(data_dir, 'blacklisted_ids.txt')
if os.path.exists(mam_blacklist_filepath):
    with open(mam_blacklist_filepath, 'r') as f:
        blacklist = set([int(x.strip()) for x in f.readlines()])
else:
    blacklist = set()

if os.path.exists(sess_filepath):
    sess = pickle.load(open(sess_filepath, 'rb'))
else:
    sess = requests.Session()

all_hits_sources = []
if __name__ == '__main__':
    main()
