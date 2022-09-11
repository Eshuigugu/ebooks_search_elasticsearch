import jellyfish
import requests
import json
from time import sleep
import re


HOST_CONN = 'http://HOST:PORT'
GOODREADS_URL = 'https://www.goodreads.com/book/auto_complete'
sess = requests.Session()


# can query title, authors, work_id
def query_elasticsearch(**kwargs):
    query_json = {
        "from": 0, "size": 100,
        "query": {
            "bool": {
                "should": [
                    {"match": {k: {"query": v
                                   }
                               }} for k, v in kwargs.items()
                ]
            },
        }
    }

    r = sess.get(HOST_CONN + '/ebooks/_search', json=query_json)
    if 200 <= r.status_code < 300:
        return [x['_source'] for x in r.json()['hits']['hits']]
    else:
        print(r.status_code, r.text)
    return []


def reduce_author_str(author):
    return ' '.join([x for x in author.split(' ') if len(x) > 1])


def get_work_id(query_str):
    sleep(0.2)
    try:
        r = sess.get(GOODREADS_URL, params={'format': 'json', 'q': query_str}, timeout=10)
    except:
        sleep(10)
        return get_work_id(query_str)
    if r.status_code == 200:
        return {x['workId'] for x in r.json()}
    else:
        print(f'goodreads auto complete status code {r.status_code} {r.text[:100]}')
    return set()


def reduce_title(title):
    return re.sub(' *(?:[\-:].*|\(.*\))* *$', '', str(title))


def remove_title_junk(title):
    # remove stuff in parenthesis at end of string
    title = re.sub('(\(.*\)|\[.*\])* *$', '', str(title))
    # remove junk strings and subtitles like "^the" or ": a novel" at start and end of string
    title = re.sub('(^(a |the) *|[-: ](a novel|and other stories|a novella'
                   '|a memoir|a thriller|stories|poems|an anthology).*$)', '', title, flags=re.IGNORECASE)
    if title.lower().startswith('the '):
        title = title[4:]
    return title


def titles_similar(title, title2):
    if title == title2:
        return True

    title, title2 = remove_title_junk(title.lower()).replace(' ', ''), remove_title_junk(title2.lower()).replace(' ', '')
    if not (title and title2):
        return title == title2

    # if you're seaching for something with numbers they should match except for leading 0s
    if re.search('(?<!^)\d+', title) or re.search('(?<!^)\d+', title2):
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


if __name__ == '__main__':
    title, author, work_id = 'The Great Gatsby', 'Scott Fitzgerald', '245494'
    hits = query_elasticsearch(title=title, authors=author, work_id=work_id)
    print(len(hits))
    print(json.dumps(hits[:5], indent=2))

