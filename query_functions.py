import jellyfish
import requests
import json
from time import sleep
import re


host_conn = 'http://ip:port'
sess = requests.Session()

# can query title, authors, work_id
def query_elasticsearch(**kwargs):
    query_json = {
        "from": 0, "size": 100,
        "query": {
            "bool": {
                "should": [
                    {"match": {k: v}} for k, v in kwargs.items()
                ]
            },
        }
    }

    r = sess.get(host_conn + '/ebooks/_search', json=query_json)
    if 200 <= r.status_code < 300:
        return r.json()['hits']['hits']
    else:
        print(r.status_code, r.text)
    return []


def reduce_author_str(author):
    return ' '.join([x for x in author.split(' ') if len(x) > 1])


def get_work_id(query_str, goodreads_url=f'https://www.goodreads.com/book/auto_complete'):
    sleep(0.2)
    try:
        r = sess.get(goodreads_url, params={'format': 'json', 'q': query_str}, timeout=10)
    except:
        sleep(10)
        return get_work_id(query_str)
    if r.status_code == 200:
        return {x['workId'] for x in r.json()}
    else:
        print(f'goodreads ac status code {r.status_code} {r.text[:100]}')
    return set()


def reduce_title(title):
    return re.sub(' *(?:[\-:].*|\(.*\))* *$', '', str(title))


def titles_similar(title, title2):
    if title == title2:
        return True

    # sometime's title start with "the " I dont like it
    remove_the = lambda x: x[4:] if x.startswith('the ') else x


    title, title2 = remove_the(title.lower()).replace(' ', ''), remove_the(title2.lower()).replace(' ', '')
    if not (title and title2):
        return title == title2

    if re.search('(?<!^)\d+', title) or re.search('(?<!^)\d+', title2): # if you're seaching for something with nums the nums should match except for leading 0s
        rm_regex = '[^0-9]|(?<!\d)0'
        if re.sub(rm_regex,'', title) != re.sub(rm_regex, '', title2):
            return False

    if len(title) < len(title2):  # sometimes it's title: subtitle or subtitle: title
        if title in {x.strip() for x in re.split(r'[:\-]', title2)}:
            return True

    # if it's a long title and both titles share all the same words
    if title.count(' ') >= 4 and set(title.lower().split(' ')) == set(title2.lower().split(' ')):
        return True

    if title == title2:
        return True
    elif re.sub('[ \.]', '', title.lower()) == re.sub('[ \.]', '', title2.lower()):
        return True
    elif jellyfish.damerau_levenshtein_distance(title, title2) <= 1:  # allow the titles to be 1 char different
        return True
    elif jellyfish.damerau_levenshtein_distance(title, title2) / len(title) < 0.05: # allow the titles to be 5% different
        return True
    elif jellyfish.jaro_winkler_similarity(title.lower(), title2.lower()) > 0.92 and len(title) > 30:
        return True
    return False

