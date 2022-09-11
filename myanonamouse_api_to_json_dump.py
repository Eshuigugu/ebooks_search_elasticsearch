from time import sleep
import requests
import json
from datetime import datetime


def main():
    my_cookies = {
        'mam_id': ''
    }
    json_dict = {
        "tor": {
            "main_cat": ["14", "15"],  # limit query to ebooks and music
            "sortType": "dateAsc",
            "startNumber": 0
        },
        "isbn": "true",
        "perpage": 100
    }
    len_data = 100
    json_dict['tor']['startNumber'] = 0

    wanted_columns = ['title', 'authors', 'ISBN', 'ASIN', 'url']
    rename_cols = {'isbn': 'ISBN'}
    while len_data == 100:
        sleep(1)
        r = sess.post('https://www.myanonamouse.net/tor/js/loadSearchJSONbasic.php', json=json_dict, cookies=my_cookies, timeout=30)
        if 'data' not in r.text:
            r = sess.post('https://www.myanonamouse.net/tor/js/loadSearchJSONbasic.php', json=json_dict, cookies=my_cookies, timeout=30)
        resp_dict = r.json()
        json_dict['tor']['startNumber'] += 100
        if 'data' not in resp_dict:
            print(resp_dict)

        with open('myanonamouse.json', 'a') as f:
            for row in resp_dict['data']:
                # sometimes type(title) == int
                row['title'] = str(row['title'])
                row = {rename_cols[k] if k in rename_cols else k: v for k, v in row.items()}
                try:
                    # sometimes author_info isn't proper JSON
                    row['authors'] = list(json.loads(row['author_info']).values()) if row['author_info'] else ''
                except:
                    print(row['author_info'])
                    row['authors'] = ''
                row['url'] = f"https://www.myanonamouse.net/t/{row['id']}"
                # deal with ISBNs that are ASINs
                if type(row['ISBN']) != str:
                    row['ISBN'] = str(row['ISBN'])
                if row['ISBN'].startswith('ASIN:'):
                    row['ASIN'] = row['ISBN'][5:].lstrip()
                    row['ISBN'] = ''
                # remove unwanted columns
                row = {k:v for k,v in row.items() if k in wanted_columns and v}
                f.write( json.dumps(row) + '\n')
        len_data = len(resp_dict['data'])
        # reassure developer that things are happening
        print(datetime.fromisoformat(resp_dict['data'][-1]['added']).isoformat(), json_dict['tor']['startNumber'])


sess = requests.Session()
if __name__ == '__main__':
    main()

