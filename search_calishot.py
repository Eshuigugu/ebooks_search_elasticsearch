import time
import requests
import json


def test_url(img_url, sess=requests.Session()):
    try:
        return sess.get(img_url, timeout=10).status_code == 200
    except:
        return False


def search_calishot(query):
    request_params = {
        '_search': query,
        '_sort': 'uuid'
    }

    time.sleep(1)
    try:
        r = sess.get(calishot_url, params=request_params, timeout=60)
    except requests.ConnectionError:
        # fail silently
        return []
    columns = r.json()['columns']

    # restructure the JSON results
    results = [{k: json.loads(v) if v and k in json_columns else v for k, v in
                zip(columns, x)} for x in r.json()['rows']]

    # try fetching the cover images to ensure the calibre libraries are online
    results = [x for x in results if test_url(x['cover']['img_src'], sess=sess)]
    for x in results:
        x['url'] = x['title']['href']
        x['title'] = x['title']['label']
        x['source_name'] = 'calishot'
    return results


sess = requests.Session()
json_columns = ['cover', 'title', 'authors', 'links', 'tags', 'identifiers', 'formats']
# get a working calishot host
for calishot_url in ['https://eng.calishot.xyz/index-eng/summary.json', 'https://calishot-eng-2.herokuapp.com/index-eng/summary.json']:
    if test_url(calishot_url, sess=sess):
        break

